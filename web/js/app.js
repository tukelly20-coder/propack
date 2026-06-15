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
    let savedLang = 'vi';
    try {
        savedLang = localStorage.getItem('language') || 'vi';
    } catch (e) {
        console.warn('[App] localStorage access denied:', e.message);
    }
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
}

/**
 * Cập nhật nav links
 * @param {string} activeTab - Tab đang active
 */
function updateNavLinks(activeTab) {
    // Update compact menu links
    document.querySelectorAll('.app-shell-menu .nav-link').forEach(link => {
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
         const script = document.createElement('script');
         script.id = src.replace('.js', '').split('/').pop() + '-script';
         const assetVersion = window.APP_ASSET_VERSION || '';
         const versionSeparator = src.includes('?') ? '&' : '?';
         script.src = assetVersion ? `${src}${versionSeparator}v=${encodeURIComponent(assetVersion)}` : src;
         script.onload = resolve;
         script.onerror = reject;
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
            refreshNoticeBadgeCount();
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
        const result = await login(username, password, rememberMe);
        
        if (result.success) {
            AppState.isAuthenticated = true;
            AppState.currentUser = result.user;
            
            // Persistence is now handled by APIClient.login based on rememberMe parameter
            // Remove the ad-hoc localStorage write here
            
            hideLoginModal();
            showUserSection(result.user);
            
            showToast(t('toast_success'), t('toast_login_success'), 'success');
            refreshNoticeBadgeCount();
            
            // Load initial module
            loadModule(AppState.currentTab);
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
    $('#user-section').css('display', 'flex');
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
        try {
            await logout();
        } catch (e) {
            console.error('[App] Logout API error:', e);
        }
    } finally {
        AppState.isAuthenticated = false;
        AppState.currentUser = null;
        
        // Clear localStorage
        try {
            localStorage.removeItem('current_user');
        } catch (e) {
            console.warn('[App] localStorage remove failed:', e.message);
        }
        
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
    // Compact menu links
    document.querySelectorAll('.app-shell-menu .nav-link[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            window.location.hash = tab;

            const menuToggle = document.getElementById('app-menu-toggle');
            if (menuToggle) {
                const menu = bootstrap.Dropdown.getInstance(menuToggle);
                if (menu) menu.hide();
            }
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
            
            // Update compact menu active state
            document.querySelectorAll('.app-shell-menu .nav-link').forEach(link => {
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
 * Setup Submit Log modal handlers
 */
function setupSubmitLogModal() {
    // Submit log form handler
    $(document).on('click', '#btn-submit-log-confirm', handleSubmitLog);
    
    // Manage inert attribute to prevent focus issues
    $('#log-modal').on('shown.bs.modal', function() {
        // Remove inert from modal content to keep it interactive
        $(this).find('.modal-content').removeAttr('inert');
        // Add inert to everything outside the modal to trap focus
        $('body > *').not('#log-modal').not('[role="dialog"]').attr('inert', '');
    });
    
    $('#log-modal').on('hidden.bs.modal', function() {
        // Remove inert from outside elements
        $('body > [inert]').removeAttr('inert');
        // Ensure modal content has no inert attribute
        $(this).find('.modal-content').removeAttr('inert');
    });
}

/**
 * Handle submit log form submission
 */
async function handleSubmitLog() {
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
    
    try {
        const result = await submitLog(logType, logContent);
        
        if (result.success) {
            showToast(t('toast_success'), t('toast_feedback_sent'), 'success');
            $('#log-content').val('');
            $('#log-modal').modal('hide');
        } else {
            throw new Error(result.error || 'Không thể gửi phản hồi');
        }
    } catch (error) {
        console.error('[App] Submit log error:', error);
        $('#log-error-text').text(error.message || t('feedback_error'));
        $('#log-error').removeClass('d-none');
    } finally {
        $('#submit-log-spinner').addClass('d-none');
        $('#btn-submit-log-confirm').prop('disabled', false);
    }
}

// ============================================
// NOTICE BADGE UPDATE
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

async function refreshNoticeBadgeCount() {
    try {
        if (!AppState.isAuthenticated) {
            updateNoticeBadge(0);
            return;
        }
        const result = await getPendingCount();
        const count = typeof result?.count === 'number' ? result.count : 0;
        updateNoticeBadge(count);
    } catch (error) {
        console.warn('[App] Cannot refresh notice badge:', error);
    }
}

// ============================================
// EXPORT TO GLOBAL
// ============================================

window.switchTab = switchTab;
window.updateNoticeBadge = updateNoticeBadge;
window.refreshNoticeBadgeCount = refreshNoticeBadgeCount;
window.AppState = AppState;
