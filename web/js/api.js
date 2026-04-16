/**
 * API Client cho Project Tracking Web
 * Giao tiếp với REST API (server.py)
 * Lưu ý: Dùng relative URL để hỗ trợ cả local và remote access
 */

// Dùng relative URL - tự động sử dụng domain hiện tại
// Khi chạy local: http://localhost:8001
// Khi chạy remote: http://propackvp.duckdns.org:8001
const API_BASE_URL = '/api';
const REQUEST_TIMEOUT = 30000; // 30 seconds timeout

// ============== STORAGE UTILITIES (Fallback for Tracking Prevention) ==============
// Memory fallback cho Tracking Prevention block localStorage
let _authTokenMemory = null;
let _currentUserMemory = null;
let _tokenExpirationMemory = null;

/**
 * Lấy auth token với fallback: localStorage → sessionStorage → memory
 */
function getAuthToken() {

    // Thử localStorage trước
    try {
        const token = localStorage.getItem('auth_token');
        if (token) {
            return token;
        }
    } catch (e) {
        console.warn('[Auth] localStorage unavailable:', e.message);
    }

    // Fallback sang sessionStorage
    try {
        const token = sessionStorage.getItem('auth_token');
        if (token) {
            return token;
        }
    } catch (e) {
        console.warn('[Auth] sessionStorage unavailable:', e.message);
    }

    // Fallback cuối cùng: memory
    if (_authTokenMemory) {
        return _authTokenMemory;
    }

    return null;
}

/**
 * Lấy current user với fallback
 */
function getCurrentUserData() {
    // Thử localStorage trước
    try {
        const userStr = localStorage.getItem('current_user');
        if (userStr) {
            return JSON.parse(userStr);
        }
    } catch (e) {
        console.warn('[Auth] localStorage unavailable:', e.message);
    }

    // Fallback sang sessionStorage
    try {
        const userStr = sessionStorage.getItem('current_user');
        if (userStr) {
            return JSON.parse(userStr);
        }
    } catch (e) {
        console.warn('[Auth] sessionStorage unavailable:', e.message);
    }

    // Fallback cuối cùng: memory
    return _currentUserMemory;
}

/**
 * Lấy token expiration với fallback
 */
function getTokenExpiration() {
    // Thử localStorage trước
    try {
        const expStr = localStorage.getItem('token_expiration');
        if (expStr) {
            return parseInt(expStr);
        }
    } catch (e) {
        console.warn('[Auth] localStorage unavailable:', e.message);
    }

    // Fallback sang sessionStorage
    try {
        const expStr = sessionStorage.getItem('token_expiration');
        if (expStr) {
            return parseInt(expStr);
        }
    } catch (e) {
        console.warn('[Auth] sessionStorage unavailable:', e.message);
    }

    // Fallback cuối cùng: memory
    return _tokenExpirationMemory;
}

/**
 * Lưu token với fallback: localStorage → sessionStorage → memory
 */
function saveAuthToken(token, user, expiresIn) {

    // Luôn lưu memory trước (backup cuối cùng)
    _authTokenMemory = token;
    _currentUserMemory = user;
    if (expiresIn) {
        _tokenExpirationMemory = Date.now() + (expiresIn * 1000);
    }

    let saved = false;

    // Thử localStorage trước
    try {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('current_user', JSON.stringify(user));
        if (expiresIn) {
            localStorage.setItem('token_expiration', (Date.now() + expiresIn * 1000).toString());
        }
        saved = true;
    } catch (e) {
        console.warn('[Auth] localStorage blocked:', e.message);
    }

    // Nếu localStorage không hoạt động, thử sessionStorage
    if (!saved) {
        try {
            sessionStorage.setItem('auth_token', token);
            sessionStorage.setItem('current_user', JSON.stringify(user));
            if (expiresIn) {
                sessionStorage.setItem('token_expiration', (Date.now() + expiresIn * 1000).toString());
            }
        } catch (e2) {
            // Silent fail - memory fallback active
        }
    }

    console.log('[Auth] Memory fallback - _authTokenMemory:', _authTokenMemory ? _authTokenMemory.substring(0, 20) + '...' : 'none');
}

/**
 * Xóa token khỏi tất cả storage
 */
function clearAuthToken() {
    _authTokenMemory = null;
    _currentUserMemory = null;
    _tokenExpirationMemory = null;

    // Xóa localStorage
    try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        localStorage.removeItem('token_expiration');
    } catch (e) {
        // Ignore
    }

    // Xóa sessionStorage
    try {
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('current_user');
        sessionStorage.removeItem('token_expiration');
    } catch (e) {
        // Ignore
    }
}

/**
 * Lấy thông tin thiết bị và trình duyệt
 * Sử dụng để gửi kèm trong log/feedback
 */
function getDeviceInfo() {
    // Detect device type
    const userAgent = navigator.userAgent || '';
    let deviceType = 'desktop';
    if (/Mobi|Android|iPhone|iPad|iPod/i.test(userAgent)) {
        if (/iPad|Tablet/i.test(userAgent)) {
            deviceType = 'tablet';
        } else {
            deviceType = 'mobile';
        }
    }

    // Get timezone
    let timezone = 'unknown';
    try {
        timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (e) {
        // Ignore
    }

    return {
        userAgent: userAgent,
        browserName: navigator.appName || 'unknown',
        browserVersion: navigator.appVersion || 'unknown',
        platform: navigator.platform || 'unknown',
        language: navigator.language || 'unknown',
        languages: navigator.languages ? navigator.languages.join(',') : '',
        cookieEnabled: navigator.cookieEnabled !== false,
        onLine: navigator.onLine === true,
        doNotTrack: navigator.doNotTrack || null,
        screenWidth: screen.width || 0,
        screenHeight: screen.height || 0,
        innerWidth: window.innerWidth || 0,
        innerHeight: window.innerHeight || 0,
        deviceType: deviceType,
        timezone: timezone
    };
}

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

        // Add auth token if available (with fallback support)
        const token = getAuthToken();
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
     */
    async login(username, password) {
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
                // Save token and user with fallback support
                saveAuthToken(result.token, result.user, result.expires_in);

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
        const token = getAuthToken();

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
            // Always clear all storages
            clearAuthToken();
        }
    }

    /**
     * Lấy thông tin user hiện tại
     */
    async getCurrentUser() {
        const token = getAuthToken();

        if (!token) {
            return { authenticated: false, user: null, reason: 'no_token' };
        }

        // Check local expiration first
        const expirationTime = getTokenExpiration();
        if (expirationTime) {
            if (Date.now() >= expirationTime) {
                // Token expired locally
                clearAuthToken();
                return { authenticated: false, user: null, reason: 'expired' };
            }
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
                // Update storage with latest user data
                const user = result.user;
                saveAuthToken(token, user, result.expires_in);

                // Check if token is expiring soon
                if (result.expiring_soon) {
                    console.warn('Token sắp hết hạn');
                }

                return result;
            } else {
                // Token expired or invalid
                clearAuthToken();
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
        const expirationTime = getTokenExpiration();
        if (!expirationTime) return false;

        const fiveMinutes = 5 * 60 * 1000;

        return (expirationTime - Date.now()) < fiveMinutes;
    }

    /**
     * Lấy thời gian còn lại của token (seconds)
     */
    getTokenTimeRemaining() {
        const expirationTime = getTokenExpiration();
        if (!expirationTime) return 0;

        const remaining = Math.floor((expirationTime - Date.now()) / 1000);
        return Math.max(0, remaining);
    }

    /**
     * Lấy tất cả dự án (có phân trang)
     */
    async getProjects(params = {}) {
        const defaultParams = {
            page: 1,
            limit: 50,
            sort_by: 'Tracking ID',
            sort_order: 'desc'
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
     * Xóa dự án (có thể xóa nhiều)
     */
    async deleteProjects(ids, role = 'admin') {
        const idsString = Array.isArray(ids) ? ids.join(',') : ids;
        return this.request('DELETE', `/projects/${idsString}?role=${role}`);
    }

    /**
     * Tìm kiếm dự án (với pagination)
     */
    async searchProjects(searchText, columns = [], page = 1, limit = 50, sort_by = 'Tracking ID', sort_order = 'desc') {
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
    async filterProjects(filters, page = 1, limit = 50, sort_by = 'Tracking ID', sort_order = 'desc') {
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
     * Gửi log lên server (JSON - không có files)
     */
    async submitLog(logContent, logType = 'general', deviceInfo = null) {
        const token = getAuthToken();

        // Get device info if not provided
        const device_info = deviceInfo || getDeviceInfo();

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
                    type: logType,
                    device_info: device_info
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

    /**
     * Gửi log với files đính kèm (multipart/form-data)
     * @param {string} logContent - Nội dung log
     * @param {string} logType - Loại log
     * @param {FileList|Array} files - Danh sách files cần upload
     * @param {Object} deviceInfo - Thông tin thiết bị
     * @param {Function} onProgress - Callback cho progress (0-100)
     * @returns {Promise}
     */
    async submitLogWithFiles(logContent, logType = 'general', files = [], deviceInfo = null, onProgress = null) {
        const token = getAuthToken();

        // Get device info if not provided
        const device_info = deviceInfo || getDeviceInfo();

        const formData = new FormData();
        formData.append('content', logContent);
        formData.append('type', logType);
        formData.append('device_info_json', JSON.stringify(device_info));

        // Append files
        if (files && files.length > 0) {
            for (let i = 0; i < files.length; i++) {
                formData.append('attachments', files[i]);
            }
        }

        try {
            // Create xhr for progress tracking (fetch doesn't support upload progress natively)
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                
                // Progress handler
                if (onProgress) {
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            const percent = Math.round((e.loaded / e.total) * 100);
                            onProgress(percent);
                        }
                    });
                }

                // Load handler
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const result = JSON.parse(xhr.responseText);
                            if (result.success) {
                                resolve(result);
                            } else {
                                reject(new Error(result.error || 'Lỗi khi gửi log'));
                            }
                        } catch (e) {
                            reject(new Error('Phản hồi server không hợp lệ'));
                        }
                    } else {
                        try {
                            const result = JSON.parse(xhr.responseText);
                            reject(new Error(result.error || `Lỗi HTTP ${xhr.status}`));
                        } catch (e) {
                            reject(new Error(`Lỗi HTTP ${xhr.status}: ${xhr.statusText}`));
                        }
                    }
                });

                // Error handler
                xhr.addEventListener('error', () => {
                    reject(new Error('Lỗi kết nối. Vui lòng kiểm tra server đang chạy.'));
                });

                // Timeout handler
                xhr.addEventListener('timeout', () => {
                    reject(new Error('Yêu cầu hết thời gian. Vui lòng thử lại.'));
                });

                // Open and send
                xhr.open('POST', `${this.baseUrl}/logs`);
                xhr.setRequestHeader('Authorization', token ? `Bearer ${token}` : '');
                xhr.timeout = REQUEST_TIMEOUT * 2; // Double timeout for large uploads
                xhr.send(formData);
            });
        } catch (error) {
            console.error('Submit log with files error:', error);
            throw error;
        }
    }

    // ============== Code Creation API Methods ==============

    /**
     * Tạo mã bản vẽ mới
     */
    async createCode(name, category, employee) {
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
                    employee: employee
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
    async getCodeHistory(page = 1, limit = 100) {
        return this.request('GET', '/codes/history', null, { page, limit });
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
     * Lấy danh sách khách hàng cho dropdown
     */
    async getCustomers() {
        return this.request('GET', '/customers');
    }
}

// Export singleton instance
const api = new APIClient();

// Export storage helper functions for other modules
// Export storage helper functions for other modules
window.getAuthToken = getAuthToken;
window.getCurrentUserData = getCurrentUserData;
window.getTokenExpiration = getTokenExpiration;
window.saveAuthToken = saveAuthToken;
window.clearAuthToken = clearAuthToken;
window.getDeviceInfo = getDeviceInfo;

/**
 * Lấy user_id từ current user data
 * Dùng cho xác thực AI chat API qua X-User-ID header
 */
function getUserId() {
    const user = getCurrentUserData();
    if (user && user.user_id) {
        return user.user_id;
    }
    return null;
}

window.getUserId = getUserId;

// ============== OVERRIDE localStorage.setItem FOR EDGE TRACKING PREVENTION ==============
// Override localStorage.setItem to ALWAYS cache auth_token to memory
// This ensures token is available even when localStorage is blocked by Edge
const originalSetItem = localStorage.setItem.bind(localStorage);
localStorage.setItem = function (key, value) {
    try {
        originalSetItem(key, value);
    } catch (e) {
        console.warn('[Auth] localStorage.setItem blocked:', e.message);
    }
    // ALWAYS cache auth_token to memory (this is the key fix for Edge)
    if (key === 'auth_token') {
        _authTokenMemory = value;
        console.log('[Auth] Token cached to memory (Edge protection fallback)');
    }
    if (key === 'current_user') {
        try {
            _currentUserMemory = JSON.parse(value);
        } catch (e) { }
    }
    if (key === 'token_expiration') {
        _tokenExpirationMemory = parseInt(value);
    }
};

// Export standalone functions for easy access
async function login(username, password) {
    return api.login(username, password);
}

async function logout() {
    return api.logout();
}

async function getCurrentUser() {
    return api.getCurrentUser();
}

async function submitLog(logContent, logType, deviceInfo = null) {
    return api.submitLog(logContent, logType, deviceInfo);
}

async function submitLogWithFiles(logContent, logType, files, deviceInfo = null, onProgress = null) {
    return api.submitLogWithFiles(logContent, logType, files, deviceInfo, onProgress);
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

// Export functions to global scope for browser usage
// This makes them available to other JS files like notices.js
window.login = login;
window.logout = logout;
window.getCurrentUser = getCurrentUser;
window.submitLog = submitLog;
window.submitLogWithFiles = submitLogWithFiles;
window.getPendingNotices = getPendingNotices;
window.getPendingCount = getPendingCount;
window.getAllNoticesForEngineer = getAllNoticesForEngineer;
window.acceptJob = acceptJob;
async function getCustomers() {
    return api.getCustomers();
}
window.getCustomers = getCustomers;

// Also export the API client instance
window.api = api;

// Export class for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, api, login, logout, getCurrentUser, submitLog, submitLogWithFiles, getPendingNotices, getPendingCount, getAllNoticesForEngineer, acceptJob };
}

