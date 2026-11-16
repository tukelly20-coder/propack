/**
 * API Client cho Project Tracking Web
 * Giao tiếp với REST API (server.py)
 * Lưu ý: Dùng relative URL để hỗ trợ cả local và remote access
 */

// storage-polyfill đã wrap localStorage an toàn, dùng trực tiếp

// Dùng relative URL - tự động sử dụng domain hiện tại
// Khi chạy local: http://localhost:8001
// Khi chạy remote: http://propackvp.duckdns.org:8001
const API_BASE_URL = '/api';
const REQUEST_TIMEOUT = 30000; // 30 seconds timeout

class APIClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    /**
     * Gửi request chung với timeout
     */
    async request(method, endpoint, data = null, params = {}) {
        let url = `${this.baseUrl}${endpoint}`;
        
        // Thêm query parameters cho GET request
        if (method === 'GET' && Object.keys(params).length > 0) {
            const queryString = new URLSearchParams(params).toString();
            url += `?${queryString}`;
        }
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        };
        
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            clearTimeout(timeoutId);
            const result = await response.json();
            
            if (!response.ok) {
                // Handle rate limiting
                if (response.status === 429) {
                    throw new Error(result.error || 'Quá nhiều lần thử. Vui lòng thử lại sau.');
                }
                throw new Error(result.error || 'Có lỗi xảy ra');
            }
            
            return result;
        } catch (error) {
            clearTimeout(timeoutId);
            
            // Check for different error types
            if (error.name === 'TimeoutError' || error.name === 'AbortError') {
                console.error('Request timeout:', error);
                const timeoutError = new Error('Yêu cầu hết thời gian. Vui lòng kiểm tra kết nối mạng.');
                timeoutError.code = 'TIMEOUT';
                throw timeoutError;
            }
            
            // Check if it's a network error (server not running or unreachable)
            if (error.name === 'TypeError' && error.message && error.message.includes('fetch')) {
                console.error('Network error:', error);
                const networkError = new Error('Không thể kết nối server. Vui lòng kiểm tra server đang chạy trên cổng 8001.');
                networkError.code = 'NETWORK_ERROR';
                throw networkError;
            }
            
            // Check for CORS or other network issues
            if (error.name === 'TypeError') {
                console.error('Network/CORS error:', error);
                const networkError = new Error('Lỗi kết nối mạng. Vui lòng kiểm tra server đang chạy.');
                networkError.code = 'NETWORK_ERROR';
                throw networkError;
            }
            
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Đăng nhập
     * @param {string} username - Tên đăng nhập
     * @param {string} password - Mật khẩu
     * @param {boolean} persist - Có lưu thông tin đăng nhập vào localStorage không (mặc định: true)
     */
    async login(username, password, persist = true) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
            
            const response = await fetch(`${this.baseUrl}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: controller.signal,
                body: JSON.stringify({ username, password })
            });
            
            clearTimeout(timeoutId);
            const result = await response.json();
            console.log('Login response:', result); // Debug log
            console.log('Response ok:', response.ok); // Debug log
            console.log('Result success:', result.success); // Debug log
            
            if (response.ok && result.success) {
                // Only persist to localStorage if persist is true
                if (persist) {
                    localStorage.setItem('auth_token', result.token);
                    localStorage.setItem('current_user', JSON.stringify(result.user));
                    
                    localStorage.removeItem('token_expiration');
                }
                
                return result;
            } else {
                // Create error with more details
                console.error('Login failed:', result); // Debug log
                const error = new Error(result.error || 'Đăng nhập thất bại');
                error.code = result.code || 'LOGIN_FAILED';
                error.remaining_attempts = result.remaining_attempts;
                error.status = response.status;
                throw error;
            }
        } catch (error) {
            // Check for different error types
            console.error('Login catch error:', error); // Debug log
            
            // Handle abort/timeout
            if (error.name === 'AbortError') {
                const timeoutError = new Error('Yêu cầu hết thời gian. Vui lòng kiểm tra server đang chạy trên cổng 8001.');
                timeoutError.code = 'TIMEOUT';
                throw timeoutError;
            }
            
            // Check if it's a network error (server not running)
            if (error.name === 'TypeError' && error.message && error.message.includes('fetch')) {
                console.error('Network error during login:', error);
                const networkError = new Error('Không thể kết nối server. Vui lòng kiểm tra server.py đang chạy trên cổng 8001.');
                networkError.code = 'NETWORK_ERROR';
                throw networkError;
            }
            
            // Check for CORS or other network issues
            if (error.name === 'TypeError') {
                console.error('Network/CORS error during login:', error);
                const networkError = new Error('Lỗi kết nối mạng. Vui lòng kiểm tra server đang chạy.');
                networkError.code = 'NETWORK_ERROR';
                throw networkError;
            }
            
            // If it's already our custom error, rethrow it
            if (error.code) {
                throw error;
            }
            
            console.error('Login error:', error);
            const genericError = new Error(error.message || 'Đăng nhập thất bại. Vui lòng thử lại.');
            genericError.code = 'LOGIN_ERROR';
            throw genericError;
        }
    }

    /**
     * Đăng xuất
     */
    async logout() {
        const token = localStorage.getItem('auth_token');
        
        try {
            if (token) {
                await fetch(`${this.baseUrl}/logout`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    signal: AbortSignal.timeout(5000)
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Always clear local storage
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');
            localStorage.removeItem('token_expiration');
        }
    }

    /**
     * Lấy thông tin user hiện tại
     */
    async getCurrentUser() {
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
            return { authenticated: false, user: null, reason: 'no_token' };
        }
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
            
            const response = await fetch(`${this.baseUrl}/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const result = await response.json();
            
            if (result.authenticated) {
                // Update localStorage with latest user data
                localStorage.setItem('current_user', JSON.stringify(result.user));
                
                localStorage.removeItem('token_expiration');
                
                // Check if token is expiring soon
                if (result.expiring_soon) {
                    console.warn('Token sắp hết hạn');
                }
                
                return result;
            } else {
                // Only clear the saved login when the server has positively rejected
                // the token. Transient startup/proxy errors should not force re-login.
                if (['invalid_token', 'expired', 'no_token'].includes(result.reason)) {
                    localStorage.removeItem('auth_token');
                    localStorage.removeItem('current_user');
                    localStorage.removeItem('token_expiration');
                }
                return { authenticated: false, user: null, reason: result.reason || 'invalid' };
            }
        } catch (error) {
            console.error('Get current user error:', error);
            
            // Handle timeout
            if (error.name === 'AbortError') {
                // Server not responding - return network error but don't invalidate token
                return { 
                    authenticated: false, 
                    user: null, 
                    reason: 'network_error', 
                    error: 'Server không phản hồi. Vui lòng kiểm tra server đang chạy.' 
                };
            }
            
            // Handle network errors
            if (error.name === 'TypeError') {
                return { 
                    authenticated: false, 
                    user: null, 
                    reason: 'network_error', 
                    error: 'Không thể kết nối server. Vui lòng kiểm tra server đang chạy.' 
                };
            }
            
            return { authenticated: false, user: null, reason: 'error' };
        }
    }

    /**
     * Kiểm tra token sắp hết hạn không
     */
    isTokenExpiringSoon() {
        return false;
    }

    /**
     * Lấy thời gian còn lại của token (seconds)
     */
    getTokenTimeRemaining() {
        return Infinity;
    }

    /**
     * Lấy tất cả dự án (có phân trang)
     */
    async getProjects(params = {}) {
        const defaultParams = {
            page: 1,
            limit: 50,
            sort_by: 'Tracking ID',
            sort_order: 'asc'
        };
        
        return this.request('GET', '/projects', null, { ...defaultParams, ...params });
    }

    /**
     * Lấy chi tiết một dự án
     */
    async getProject(id) {
        return this.request('GET', `/projects/${id}`);
    }

    /**
     * Thêm dự án mới
     */
    async createProject(projectData) {
        return this.request('POST', '/projects', projectData);
    }

    /**
     * Cập nhật dự án
     */
    async updateProject(id, projectData) {
        return this.request('PUT', `/projects/${id}`, projectData);
    }

    /**
     * Khóa một ô project trước khi chỉnh sửa
     */
    async lockProjectCell(id, fieldName) {
        return this.request('POST', `/projects/${id}/locks`, { field_name: fieldName });
    }

    /**
     * Mở khóa một ô project
     */
    async unlockProjectCell(id, fieldName) {
        return this.request('DELETE', `/projects/${id}/locks`, { field_name: fieldName });
    }

    /**
     * Lấy danh sách ô đang bị khóa
     */
    async getProjectLocks() {
        return this.request('GET', '/projects/locks');
    }

    /**
     * Lấy tùy chỉnh giao diện theo user hiện tại.
     */
    async getUserPreference(key) {
        return this.request('GET', `/user-preferences/${encodeURIComponent(key)}`);
    }

    /**
     * Lưu tùy chỉnh giao diện theo user hiện tại.
     */
    async setUserPreference(key, value) {
        return this.request('PUT', `/user-preferences/${encodeURIComponent(key)}`, { value });
    }

    /**
     * Mở stream realtime cho projects (SSE)
     */
    createProjectStream(params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = query
            ? `${this.baseUrl}/projects/stream?${query}`
            : `${this.baseUrl}/projects/stream`;
        return new EventSource(url);
    }

    /**
     * Tra tài liệu kỹ thuật theo mã liệu/mã bản vẽ.
     */
    async getMaterialDocuments(code, params = {}) {
        return this.request('GET', `/materials/${encodeURIComponent(code)}/documents`, null, params);
    }

    /**
     * Liệt kê nội dung thư mục vật liệu qua server.
     */
    async getMaterialFolder(listUrl) {
        return this.request('GET', listUrl.replace(/^\/api/, ''));
    }

    /**
     * Lấy lịch sử chỉnh sửa của project hoặc một field.
     */
    async getProjectChangeLogs(id, params = {}) {
        return this.request('GET', `/projects/${id}/changes`, null, params);
    }

    /**
     * Hoàn tác một dòng lịch sử chỉnh sửa.
     */
    async revertProjectChange(changeId, data = {}) {
        return this.request('POST', `/projects/changes/${changeId}/revert`, data);
    }

    /**
     * Broadcast ô project user đang chọn.
     */
    async updateProjectCursor(cursorData) {
        return this.request('POST', '/projects/cursor', cursorData);
    }

    /**
     * Lấy bình luận của project hoặc field.
     */
    async getProjectComments(id, params = {}) {
        return this.request('GET', `/projects/${id}/comments`, null, params);
    }

    /**
     * Thêm bình luận cho project hoặc field.
     */
    async addProjectComment(id, commentData) {
        return this.request('POST', `/projects/${id}/comments`, commentData);
    }

    /**
     * Xóa mềm bình luận.
     */
    async deleteProjectComment(commentId) {
        return this.request('DELETE', `/projects/comments/${commentId}`);
    }

    /**
     * Xóa dự án (có thể xóa nhiều)
     */
    async deleteProjects(ids, role = '') {
        const idsString = Array.isArray(ids) ? ids.join(',') : ids;
        const suffix = role ? `?role=${encodeURIComponent(role)}` : '';
        return this.request('DELETE', `/projects/${idsString}${suffix}`);
    }

    /**
     * Khôi phục dự án đã xóa từ snapshot undo
     */
    async restoreProjects(records) {
        return this.request('POST', '/projects/restore', { records });
    }

    /**
     * Tìm kiếm dự án (với pagination)
     */
    async searchProjects(searchText, columns = [], page = 1, limit = 50, sort_by = 'Tracking ID', sort_order = 'asc') {
        return this.request('POST', '/projects/search', { 
            search: searchText, 
            columns,
            page,
            limit,
            sort_by,
            sort_order
        });
    }

    /**
     * Lọc dự án (với pagination)
     */
    async filterProjects(filters, page = 1, limit = 50, sort_by = 'Tracking ID', sort_order = 'asc') {
        return this.request('POST', '/projects/filter', {
            ...filters,
            page,
            limit,
            sort_by,
            sort_order
        });
    }

    /**
     * Kiểm tra kết nối server
     */
    async healthCheck() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout for health check
            
            const response = await fetch(`${this.baseUrl}/health`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            
            // Determine specific error type
            if (error.name === 'AbortError') {
                return { 
                    status: 'error', 
                    message: 'Server không phản hồi. Vui lòng kiểm tra server.py đang chạy trên cổng 8001.' 
                };
            }
            
            if (error.name === 'TypeError' && error.message?.includes('fetch')) {
                return { 
                    status: 'error', 
                    message: 'Không thể kết nối server. Vui lòng kiểm tra server.py đang chạy trên cổng 8001.' 
                };
            }
            
            return { status: 'error', message: 'Lỗi kết nối: ' + error.message };
        }
    }

    /**
     * Gửi log lên server
     */
    async submitLog(logContent, logType = 'general') {
        const token = localStorage.getItem('auth_token');
        
        try {
            const response = await fetch(`${this.baseUrl}/logs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                signal: AbortSignal.timeout(REQUEST_TIMEOUT),
                body: JSON.stringify({
                    content: logContent,
                    type: logType
                })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Lỗi khi gửi log');
            }
            
            return result;
        } catch (error) {
            console.error('Submit log error:', error);
            if (error.name === 'TimeoutError' || error.name === 'AbortError') {
                throw new Error('Yêu cầu hết thời gian. Vui lòng thử lại.');
            }
            throw error;
        }
    }
    
    // ============== Code Creation API Methods ==============
    
    /**
     * Tạo mã bản vẽ mới
     */
    async createCode(name, category, employee, planCode = '') {
        try {
            const response = await fetch(`${this.baseUrl}/codes/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: AbortSignal.timeout(REQUEST_TIMEOUT),
                body: JSON.stringify({
                    name: name,
                    category: category,
                    employee: employee,
                    plan_code: planCode
                })
            });
            
            const result = await response.json();
            
            // Check HTTP status
            if (!response.ok) {
                // Server returned error status
                const errorMsg = result.error || `Lỗi HTTP ${response.status}: ${response.statusText}`;
                console.error('Create code HTTP error:', response.status, errorMsg);
                throw new Error(errorMsg);
            }
            
            // Check success flag in response
            if (result.success === false) {
                console.error('Create code failed:', result.error);
                throw new Error(result.error || 'Tạo mã thất bại');
            }
            
            // Verify code exists in response
            if (!result.code) {
                console.error('Create code response missing code:', result);
                throw new Error('Phản hồi server không hợp lệ - thiếu mã');
            }
            
            return result;
        } catch (error) {
            console.error('Create code error:', error);
            
            // Handle different error types
            if (error.name === 'TimeoutError' || error.name === 'AbortError') {
                throw new Error('Yêu cầu hết thời gian. Vui lòng kiểm tra kết nối và thử lại.');
            }
            
            if (error.name === 'TypeError' && error.message?.includes('fetch')) {
                throw new Error('Không thể kết nối server. Vui lòng kiểm tra server đang chạy.');
            }
            
            // Re-throw known errors
            if (error.message) {
                throw error;
            }
            
            // Generic error
            throw new Error('Lỗi không xác định khi tạo mã. Vui lòng thử lại.');
        }
    }
    
    /**
     * Lấy lịch sử tạo mã (có phân trang)
     */
    async getCodeHistory(page = 1, limit = 100, search = '') {
        const params = { page, limit };
        if (search) {
            params.search = search;
        }
        return this.request('GET', '/codes/history', null, params);
    }
    
    /**
     * Xóa bản ghi lịch sử
     */
    async deleteCodeHistory(code, password) {
        if (!code) {
            throw new Error('Mã không được để trống');
        }
        
        if (!password) {
            throw new Error('Mật khẩu không được để trống');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/codes/history/${encodeURIComponent(code)}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: AbortSignal.timeout(REQUEST_TIMEOUT),
                body: JSON.stringify({ password })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `Lỗi HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error('Delete history error:', error);
            if (error.name === 'TimeoutError' || error.name === 'AbortError') {
                throw new Error('Yêu cầu hết thời gian. Vui lòng thử lại.');
            }
            if (error.name === 'TypeError' && error.message?.includes('fetch')) {
                throw new Error('Không thể kết nối server. Vui lòng kiểm tra server đang chạy.');
            }
            throw error;
        }
    }
    
    /**
     * Xuất lịch sử mã
     */
    async exportCodeHistory() {
        return this.request('GET', '/codes/export');
    }
    
    // ============== Notice/Pending Tab API Methods ==============
    
    /**
     * Lấy danh sách thông báo chờ xử lý
     */
    async getPendingNotices(userId = null) {
        const params = {};
        if (userId) {
            params.user_id = userId;
        }
        return this.request('GET', '/notices/pending', null, params);
    }
    
    /**
     * Lấy số lượng thông báo chờ
     */
    async getPendingCount(userId = null) {
        const params = {};
        if (userId) {
            params.user_id = userId;
        }
        return this.request('GET', '/notices/count', null, params);
    }
    
    /**
     * Lấy tất cả thông báo cho kỹ sư (pending + accepted)
     */
    async getAllNoticesForEngineer(engineerName) {
        return this.request('GET', '/notices/engineer', null, { engineer_name: engineerName });
    }
    
    /**
     * Nhận job (kỹ sư nhận công việc)
     */
    async acceptJob(trackingId, engineerName) {
        return this.request('POST', '/notices/accept', {
            tracking_id: trackingId,
            engineer_name: engineerName
        });
    }

    /**
     * Mở stream realtime cho notices (SSE)
     */
    createNoticeStream(params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = query
            ? `${this.baseUrl}/notices/stream?${query}`
            : `${this.baseUrl}/notices/stream`;
        return new EventSource(url);
    }
    
    /**
     * Lấy danh sách khách hàng cho dropdown
     */
    async getCustomers() {
        return this.request('GET', '/customers');
    }
}

// Export singleton instance
const api = new APIClient();

// Export standalone functions for easy access
async function login(username, password, persist = true) {
    return api.login(username, password, persist);
}

async function logout() {
    return api.logout();
}

async function getCurrentUser() {
    return api.getCurrentUser();
}

async function submitLog(logContent, logType) {
    return api.submitLog(logContent, logType);
}

// Notice Tab functions
async function getPendingNotices(userId = null) {
    return api.getPendingNotices(userId);
}

async function getPendingCount(userId = null) {
    return api.getPendingCount(userId);
}

async function getAllNoticesForEngineer(engineerName) {
    return api.getAllNoticesForEngineer(engineerName);
}

async function acceptJob(trackingId, engineerName) {
    return api.acceptJob(trackingId, engineerName);
}

function openNoticeStream(params = {}) {
    return api.createNoticeStream(params);
}

// Export functions to global scope for browser usage
// This makes them available to other JS files like notices.js
window.login = login;
window.logout = logout;
window.getCurrentUser = getCurrentUser;
window.submitLog = submitLog;
window.getPendingNotices = getPendingNotices;
window.getPendingCount = getPendingCount;
window.getAllNoticesForEngineer = getAllNoticesForEngineer;
window.acceptJob = acceptJob;
window.openNoticeStream = openNoticeStream;
async function getCustomers() {
    return api.getCustomers();
}
window.getCustomers = getCustomers;

// Also export the API client instance
window.api = api;

// Export class for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, api, login, logout, getCurrentUser, submitLog, getPendingNotices, getPendingCount, getAllNoticesForEngineer, acceptJob, openNoticeStream };
}
