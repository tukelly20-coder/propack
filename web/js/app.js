/**
 * Main Application - SPA Router & Initialization
 * Quản lý routing, authentication, và tab switching
 */

// ============================================
// APP STATE
// ============================================

const AppState = {
    currentTab: 'projects',
    isAuthenticated: false,
    currentUser: null,
    modulesLoaded: {
        projects: false,
        notices: false,
        taomabanve: false,
        profile: false,
        ai: false
    }
};

// ============================================
// INITIALIZATION
// ============================================

$(document).ready(async function() {
    console.log('[App] Initializing...');
    
    // Setup event listeners
    setupNavigation();
    setupAuth();
    setupLogout();
    setupLanguageSelector();
    
    // Initialize language from localStorage
    initLanguage();
    
    // Check initial hash or default to projects
    handleRouteChange();
    
    // Listen for hash changes
    window.addEventListener('hashchange', handleRouteChange);
    
    console.log('[App] Initialization complete');
});

// ============================================
// LANGUAGE SELECTOR
// ============================================

function setupLanguageSelector() {
    console.log('[App] setupLanguageSelector called');
    
    // Language selector dropdown
    $(document).on('click', '[data-lang]', function(e) {
        e.preventDefault();
        const lang = $(this).data('lang');
        console.log('[App] Language clicked from dropdown:', lang);
        changeLanguage(lang);
        updateLanguageLabel();
    });
    
    // Listen for language changes from other modules
    window.addEventListener('languageChanged', function(e) {
        console.log('[App] languageChanged event received:', e.detail?.language);
        updateLanguageLabel();
    });
}

function initLanguage() {
    const savedLang = localStorage.getItem('language') || 'vi';
    window.currentLanguage = savedLang;
    // Translate page immediately on init
    if (typeof translatePage === 'function') {
        translatePage();
    }
    updateLanguageLabel();
}

function updateLanguageLabel() {
    const langLabel = window.currentLanguage === 'zh' ? t('language_zh') : t('language_vi');
    $('#current-lang-label').text(langLabel);
    
    // Update active state in dropdown
    $('#lang-option-vi').toggleClass('active', window.currentLanguage === 'vi');
    $('#lang-option-zh').toggleClass('active', window.currentLanguage === 'zh');
}

// ============================================
// ROUTING
// ============================================

/**
 * Xử lý thay đổi hash/route
 */
function handleRouteChange() {
    const hash = window.location.hash.slice(1) || 'projects';
    const validTabs = ['projects', 'notices', 'taomabanve', 'profile', 'ai'];
    
    if (!validTabs.includes(hash)) {
        window.location.hash = 'projects';
        return;
    }
    
    switchTab(hash);
}

/**
 * Chuyển đổi tab
 * @param {string} tab - Tên tab
 */
async function switchTab(tab) {
    console.log('[App] Switching to tab:', tab);
    
    // Update state
    AppState.currentTab = tab;
    
    // Update nav links
    updateNavLinks(tab);
    
    // Show/hide tab content
    const tabPane = document.getElementById(tab + '-content');
    if (tabPane) {
        // Hide all tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('show', 'active');
        });
        
        // Show selected tab pane
        tabPane.classList.add('show', 'active');
    }
    
    // Load module if not loaded
    if (!AppState.modulesLoaded[tab]) {
        await loadModule(tab);
    }
    
    // Trigger tab-specific init
    triggerTabInit(tab);
    
    // NEW: Update AI System State when user switches tabs
    if (typeof updateAISystemState === 'function') {
        updateAISystemState(null, 'tab_' + tab, 'switch_tab');
    }
}

/**
 * Cập nhật nav links
 * @param {string} activeTab - Tab đang active
 */
function updateNavLinks(activeTab) {
    // Update navbar links
    document.querySelectorAll('.navbar .nav-link').forEach(link => {
        const linkTab = link.dataset.tab;
        if (linkTab === activeTab) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Update tab buttons
    document.querySelectorAll('#main-tabs .nav-link').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.getElementById('tab-' + activeTab);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// ============================================
// MODULE LOADING
// ============================================

/**
 * Load module JS
 * @param {string} tab - Tên tab
 */
async function loadModule(tab) {
    console.log('[App] Loading module:', tab);
    
    const loadingEl = document.getElementById(tab + '-loading');
    const containerEl = document.getElementById(tab + '-container');
    
    // Show loading
    if (loadingEl) loadingEl.style.display = 'flex';
    if (containerEl) containerEl.style.display = 'none';
    
    try {
        switch (tab) {
            case 'projects':
                await loadProjectsModule();
                break;
            case 'notices':
                await loadNoticesModule();
                break;
            case 'taomabanve':
                await loadTaomabanveModule();
                break;
            case 'profile':
                await loadProfileModule();
                break;
            case 'ai':
                await loadAIModule();
                break;
        }
        
        AppState.modulesLoaded[tab] = true;
    } catch (error) {
        console.error('[App] Error loading module:', tab, error);
        showToast('Lỗi', 'Không thể tải module: ' + tab, 'error');
    }
    
    // Hide loading, show content
    if (loadingEl) loadingEl.style.display = 'none';
    if (containerEl) containerEl.style.display = 'block';
}

/**
 * Load Projects module
 */
async function loadProjectsModule() {
    // Dynamically load the projects module script
    if (!document.getElementById('projects-script')) {
        await loadScript('js/modules/projects.js');
    }
    // Call init if exists
    if (typeof window.initProjectsModule === 'function') {
        window.initProjectsModule();
    }
}

/**
 * Load Notices module
 */
async function loadNoticesModule() {
    if (!document.getElementById('notices-script')) {
        await loadScript('js/modules/notices.js');
    }
    if (typeof window.initNoticesModule === 'function') {
        window.initNoticesModule();
    }
}

/**
 * Load Create Code module
 */
async function loadTaomabanveModule() {
    if (!document.getElementById('taomabanve-script')) {
        await loadScript('js/modules/taomabanve.js');
    }
    if (typeof window.initTaomabanveModule === 'function') {
        window.initTaomabanveModule();
    }
}

/**
 * Load Profile module
 */
async function loadProfileModule() {
    if (!document.getElementById('profile-script')) {
        await loadScript('js/modules/profile.js');
    }
    if (typeof window.initProfileModule === 'function') {
        window.initProfileModule();
    }
}

/**
 * Load AI module
 */
async function loadAIModule() {
    if (!document.getElementById('ai-script')) {
        await loadScript('js/modules/ai.js');
    }
    if (typeof window.initAIModule === 'function') {
        window.initAIModule();
    }
}

/**
 * Load script dynamically
 * @param {string} src - Đường dẫn script
 * @returns {Promise}
 */
function loadScript(src) {
    return new Promise((resolve, reject) => {
        // Check if script already exists
        const filename = src.split('/').pop(); // e.g., 'projects.js'
        const scriptId = filename.replace('.js', '') + '-script'; // e.g., 'projects-script'

        if (document.getElementById(scriptId)) {
            console.log('[App] Script already loaded:', src);
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.id = scriptId;
        script.src = src;
        script.onload = () => {
            console.log('[App] Script loaded successfully:', src);
            resolve();
        };
        script.onerror = (err) => {
            console.error('[App] Script failed to load:', src, err);
            reject(new Error(`Failed to load script: ${src}`));
        };
        document.head.appendChild(script);
    });
}

/**
 * Trigger tab-specific initialization
 * @param {string} tab - Tên tab
 */
function triggerTabInit(tab) {
    switch (tab) {
        case 'projects':
            if (typeof window.onProjectsTabInit === 'function') {
                window.onProjectsTabInit();
            }
            break;
        case 'notices':
            if (typeof window.onNoticesTabInit === 'function') {
                window.onNoticesTabInit();
            }
            break;
        case 'taomabanve':
            if (typeof window.onTaomabanveTabInit === 'function') {
                window.onTaomabanveTabInit();
            }
            break;
        case 'profile':
            if (typeof window.onProfileTabInit === 'function') {
                window.onProfileTabInit();
            }
            break;
        case 'ai':
            if (typeof window.onAITabInit === 'function') {
                window.onAITabInit();
            }
            break;
    }
}

// ============================================
// AUTHENTICATION
// ============================================

/**
 * Setup authentication handlers
 */
function setupAuth() {
    // Login form handler
    $('#login-form').submit(handleLogin);
    
    // Toggle password visibility
    $('#toggle-password').click(function() {
        const passwordInput = $('#login-password');
        const icon = $('#toggle-password-icon');
        
        if (passwordInput.attr('type') === 'password') {
            passwordInput.attr('type', 'text');
            icon.removeClass('bi-eye').addClass('bi-eye-slash');
        } else {
            passwordInput.attr('type', 'password');
            icon.removeClass('bi-eye-slash').addClass('bi-eye');
        }
    });
    
    // Check auth status
    checkAuthStatus();
}

/**
 * Check authentication status
 */
async function checkAuthStatus() {
    try {
        const result = await getCurrentUser();
        
        if (result.authenticated) {
            AppState.isAuthenticated = true;
            AppState.currentUser = result.user;
            showUserSection(result.user);
        } else {
            // Show login modal if not authenticated
            showLoginModal();
        }
    } catch (error) {
        console.error('[App] Auth check failed:', error);
        showLoginModal();
    }
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();
    
    const username = $('#login-username').val().trim();
    const password = $('#login-password').val();
    const rememberMe = $('#remember-me').is(':checked');
    
    if (!username || !password) {
        showLoginError(t('login_error'));
        return;
    }
    
    // Show loading
    $('#login-spinner').removeClass('d-none');
    $('#login-btn-text').text(t('logging_in'));
    $('#btn-login-submit').prop('disabled', true);
    $('#login-error').addClass('d-none');
    
    try {
        const result = await login(username, password);
        
        if (result.success) {
            AppState.isAuthenticated = true;
            AppState.currentUser = result.user;
            
            // Save to localStorage if remember me
            if (rememberMe) {
                localStorage.setItem('current_user', JSON.stringify(result.user));
            }
            
            hideLoginModal();
            showUserSection(result.user);
            
            showToast(t('toast_success'), t('toast_login_success'), 'success');
            
            // Dispatch custom event for modules that need to reload after login
            // This will trigger AI module to reload sessions if already loaded
            window.dispatchEvent(new CustomEvent('userAuthenticated', {
                detail: { user: result.user }
            }));
            
            // NOTE: Do NOT call loadModule here - it was already called during initial tab switch
            // The modulesLoaded flag will be set when the module finishes loading
        } else {
            showLoginError(result.error || t('login_failed'));
        }
    } catch (error) {
        console.error('[App] Login error:', error);
        showLoginError(error.message || t('login_failed_retry'));
    } finally {
        $('#login-spinner').addClass('d-none');
        $('#login-btn-text').text(t('login_btn'));
        $('#btn-login-submit').prop('disabled', false);
    }
}

/**
 * Show login modal
 */
function showLoginModal() {
    const modal = new bootstrap.Modal('#login-modal');
    modal.show();
}

/**
 * Hide login modal
 */
function hideLoginModal() {
    const modal = bootstrap.Modal.getInstance('#login-modal');
    if (modal) {
        modal.hide();
    }
    $('#auth-overlay').hide();
    $('#main-content').show();
}

/**
 * Show login error
 * @param {string} message - Thông báo lỗi
 */
function showLoginError(message) {
    $('#login-error-text').text(message || t('login_error'));
    $('#login-error').removeClass('d-none');
}

/**
 * Show user section
 * @param {object} user - Thông tin user
 */
function showUserSection(user) {
    $('#user-section').show();
    $('#user-name').text(user.full_name || user.username);
    $('#auth-overlay').hide();
    $('#main-content').show();
    
    // Hide login modal if visible
    $('#login-modal').modal('hide');
}

// ============================================
// LOGOUT
// ============================================

/**
 * Setup logout handler
 */
function setupLogout() {
    $('#btn-logout').click(async function() {
        if (confirm(t('confirm_logout'))) {
            await handleLogout();
        }
    });
}

/**
 * Handle logout
 */
async function handleLogout() {
    try {
        await logout();
    } catch (error) {
        console.error('[App] Logout error:', error);
    } finally {
        AppState.isAuthenticated = false;
        AppState.currentUser = null;
        
        // Reset modules
        AppState.modulesLoaded = {
            projects: false,
            notices: false,
            taomabanve: false,
            profile: false,
            ai: false
        };
        
        // Clear containers
        ['projects', 'notices', 'taomabanve', 'profile', 'ai'].forEach(tab => {
            const container = document.getElementById(tab + '-container');
            if (container) container.innerHTML = '';
        });
        
        $('#user-section').hide();
        showLoginModal();
        
        showToast(t('toast_success'), t('toast_logout_success'), 'success');
    }
}

// ============================================
// NAVIGATION
// ============================================

/**
 * Setup navigation event listeners
 */
function setupNavigation() {
    // Navbar links
    document.querySelectorAll('.navbar .nav-link[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            window.location.hash = tab;
        });
    });
    
    // Tab buttons
    document.querySelectorAll('#main-tabs .nav-link').forEach(btn => {
        btn.addEventListener('shown.bs.tab', function(e) {
            const target = e.target;
            const targetId = target.getAttribute('data-bs-target');
            const tabName = targetId.replace('-content', '');
            
            AppState.currentTab = tabName;
            window.location.hash = tabName;
            
            // Update navbar active state
            document.querySelectorAll('.navbar .nav-link').forEach(link => {
                link.classList.remove('active');
                if (link.dataset.tab === tabName) {
                    link.classList.add('active');
                }
            });
        });
    });
    
    // Submit Log button handler
    setupSubmitLogModal();
}

/**
 * Handle submit log form submission with files
 */
async function handleSubmitLogWithFiles() {
    const logType = $('#log-type').val();
    const logContent = $('#log-content').val().trim();
    
    if (!logContent) {
        $('#log-error-text').text(t('feedback_content_required'));
        $('#log-error').removeClass('d-none');
        return;
    }
    
    $('#log-error').addClass('d-none');
    
    // Show loading
    $('#submit-log-spinner').removeClass('d-none');
    $('#btn-submit-log-confirm').prop('disabled', true);
    
    // Update status
    if (logFileHandler && logFileHandler.hasFiles()) {
        showUploadStatus('Đang tải files lên...', '');
    }
    
    try {
        let result;
        
        // Get files
        const files = logFileHandler ? logFileHandler.getFiles() : [];
        
        if (files.length > 0) {
            // Submit with files using XHR for progress
            result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                const formData = new FormData();
                
                formData.append('content', logContent);
                formData.append('type', logType);
                formData.append('device_info_json', JSON.stringify(getDeviceInfo()));
                
                // Append files
                for (let i = 0; i < files.length; i++) {
                    formData.append('attachments', files[i]);
                }
                
                // Progress handler
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        showUploadStatus(`Đang tải lên: ${percent}%`, '');
                    }
                });
                
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
                
                // Open and send
                xhr.open('POST', '/api/logs');
                const token = getAuthToken();
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }
                xhr.timeout = 300000; // 5 minutes for large uploads
                xhr.send(formData);
            });
        } else {
            // Submit without files (original method)
            result = await submitLog(logType, logContent);
        }
        
        if (result.success) {
            // Success message with file count
            const message = result.files_count > 0 
                ? `${t('toast_feedback_sent')} (${result.files_count} file(s))`
                : t('toast_feedback_sent');
            showToast(t('toast_success'), message, 'success');
            
            // Clear form
            $('#log-content').val('');
            if (logFileHandler) {
                logFileHandler.clearFiles();
            }
            $('#log-modal').modal('hide');
        } else {
            throw new Error(result.error || 'Không thể gửi phản hồi');
        }
    } catch (error) {
        console.error('[App] Submit log error:', error);
        $('#log-error-text').text(error.message || t('feedback_error'));
        $('#log-error').removeClass('d-none');
        showUploadStatus('', '');
    } finally {
        $('#submit-log-spinner').addClass('d-none');
        $('#btn-submit-log-confirm').prop('disabled', false);
    }
}

// ============================================
// FILE UPLOAD HANDLER
// ============================================

let logFileHandler = null;

/**
 * File Upload Handler Class
 * Quản lý việc chọn file, drag-drop, preview
 */
class FileUploadHandler {
    constructor() {
        this.files = [];
        this.init();
    }
    
    init() {
        const uploadArea = document.getElementById('log-upload-area');
        const fileInput = document.getElementById('log-attachments');
        
        if (!uploadArea || !fileInput) {
            console.error('[FileUploadHandler] Upload elements not found');
            return;
        }
        
        // Click to select files
        uploadArea.addEventListener('click', (e) => {
            if (e.target.closest('.remove-file-btn')) return;
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
            fileInput.value = ''; // Reset for re-selection
        });
        
        // Drag and drop events
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
        
        console.log('[FileUploadHandler] Initialized');
    }
    
    handleFiles(fileList) {
        for (let i = 0; i < fileList.length; i++) {
            const file = fileList[i];
            // Check file type
            if (!this.isValidFileType(file)) {
                showToast('Lỗi', 'Chỉ chấp nhận file ảnh và video', 'error');
                continue;
            }
            this.files.push(file);
        }
        this.renderPreview();
    }
    
    isValidFileType(file) {
        const validTypes = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm',
            'video/x-matroska', 'video/x-flv', 'video/x-ms-wmv'
        ];
        return validTypes.includes(file.type);
    }
    
    hasFiles() {
        return this.files.length > 0;
    }
    
    getFiles() {
        return this.files;
    }
    
    removeFile(index) {
        this.files.splice(index, 1);
        this.renderPreview();
    }
    
    clearFiles() {
        this.files = [];
        this.renderPreview();
    }
    
    renderPreview() {
        const previewContainer = document.getElementById('log-upload-preview');
        const uploadArea = document.getElementById('log-upload-area');
        
        if (!previewContainer) return;
        
        if (this.files.length === 0) {
            previewContainer.innerHTML = '';
            if (uploadArea) uploadArea.classList.remove('has-files');
            return;
        }
        
        if (uploadArea) uploadArea.classList.add('has-files');
        
        let html = '<div class="upload-preview-grid">';
        this.files.forEach((file, index) => {
            const isImage = file.type.startsWith('image/');
            const previewClass = isImage ? 'image-preview' : 'video-preview';
            const iconClass = isImage ? 'bi-image' : 'bi-video';
            
            html += `
                <div class="preview-item">
                    <div class="${previewClass}">
                        ${isImage 
                            ? `<img src="${URL.createObjectURL(file)}" alt="${file.name}" style="width:100%;height:100%;object-fit:cover;">` 
                            : `<div class="video-placeholder"><i class="bi ${iconClass}"></i></div>`
                        }
                    </div>
                    <div class="preview-info">
                        <span class="preview-name" title="${file.name}">${this.truncateName(file.name)}</span>
                        <span class="preview-size">${this.formatSize(file.size)}</span>
                    </div>
                    <button class="remove-file-btn" onclick="logFileHandler.removeFile(${index})" title="Xóa">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            `;
        });
        html += '</div>';
        previewContainer.innerHTML = html;
    }
    
    truncateName(name) {
        if (name.length <= 20) return name;
        return name.substring(0, 15) + '...' + name.substring(name.lastIndexOf('.'));
    }
    
    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    }
}

/**
 * Show upload status message
 * @param {string} message - Thông báo
 * @param {string} type - Loại (success, error, '')
 */
function showUploadStatus(message, type) {
    const statusEl = document.getElementById('log-upload-status');
    if (!statusEl) return;
    
    if (!message) {
        statusEl.innerHTML = '';
        statusEl.style.display = 'none';
        return;
    }
    
    statusEl.innerHTML = message;
    statusEl.style.display = 'block';
    if (type) {
        statusEl.className = `alert alert-${type === 'success' ? 'success' : 'danger'} mt-2`;
    } else {
        statusEl.className = 'alert alert-info mt-2';
    }
}

// ============================================
// SUBMIT LOG MODAL
// ============================================

/**
 * Setup Submit Log modal handlers
 */
function setupSubmitLogModal() {
    // Initialize file upload handler
    logFileHandler = new FileUploadHandler();
    
    // Submit log form handler
    $(document).on('click', '#btn-submit-log-confirm', handleSubmitLogWithFiles);
    
    // Clear files when modal is closed
    $('#log-modal').on('hidden.bs.modal', function() {
        if (logFileHandler) {
            logFileHandler.clearFiles();
        }
        $('#log-content').val('');
        $('#log-error').addClass('d-none');
    });
}

// ============================================
// EXPORT TO GLOBAL
// ============================================

window.switchTab = switchTab;
window.updateNoticeBadge = updateNoticeBadge;
window.AppState = AppState;
window.logFileHandler = logFileHandler;

// ============================================
// NOTICE BADGE UPDATE (Moved after file handler)
// ============================================

/**
 * Cập nhật số lượng thông báo chờ
 * @param {number} count - Số lượng
 */
function updateNoticeBadge(count) {
    const badge = document.getElementById('notice-badge');
    const tabBadge = document.getElementById('tab-notice-badge');
    
    if (count > 0) {
        if (badge) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        }
        if (tabBadge) {
            tabBadge.textContent = count > 99 ? '99+' : count;
            tabBadge.style.display = 'inline-block';
        }
    } else {
        if (badge) badge.style.display = 'none';
        if (tabBadge) tabBadge.style.display = 'none';
    }
}
