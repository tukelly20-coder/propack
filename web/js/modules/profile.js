/**
 * Profile Module
 * Quản lý hồ sơ cá nhân - Extracted from profile.html
 */

// ============================================
// STATE
// ============================================

const ProfileState = {
    user: null,
    isLoading: false,
    isSaving: false,
    isDirty: false
};

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize Profile module
 */
function initProfileModule() {
    console.log('[Profile] Initializing...');
    
    // Render the module content
    renderProfileContent();
    
    // Translate content to current language
    translatePage();
    
    // Setup event listeners
    setupProfileEvents();
    
    // Load user profile
    loadProfile();
}

/**
 * Render Profile module content
 */
function renderProfileContent() {
    const container = document.getElementById('profile-container');
    
    container.innerHTML = `
        <div class="profile-container">
            <!-- Profile Header -->
            <div class="profile-header text-center">
                <div class="profile-avatar mx-auto mb-3" id="profile-avatar">
                    <i class="bi bi-person-fill"></i>
                </div>
                <h3 id="profile-username" data-i18n="form_username">用户名</h3>
                <p class="mb-0" id="profile-role" data-i18n="form_role">角色</p>
            </div>
            
            <!-- Profile Card -->
            <div class="card profile-card">
                <div class="card-body">
                    <!-- Thông tin cơ bản -->
                    <div class="profile-section">
                        <h5 class="mb-3"><i class="bi bi-person-badge"></i> <span data-i18n="basic_info">基本信息</span></h5>
                        <form id="profile-form">
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label profile-label" data-i18n="form_username">用户名</label>
                                    <input type="text" class="form-control read-only-field" id="field-username-profile" readonly>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label profile-label" data-i18n="form_role">角色</label>
                                    <input type="text" class="form-control read-only-field" id="field-role-profile" readonly>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label profile-label" data-i18n="form_fullname">姓名</label>
                                    <input type="text" class="form-control" id="field-fullname-profile" data-i18n-placeholder="form_fullname_placeholder" placeholder="输入姓名">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label profile-label"><span data-i18n="form_employee_id">员工编号</span></label>
                                    <input type="text" class="form-control" id="field-employee-id-profile" data-i18n-placeholder="form_employee_id_placeholder" placeholder="输入员工编号">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label profile-label" data-i18n="form_department">部门</label>
                                    <input type="text" class="form-control" id="field-department-profile" data-i18n-placeholder="form_department_placeholder" placeholder="输入部门">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label profile-label" data-i18n="form_status">状态</label>
                                    <input type="text" class="form-control read-only-field" id="field-status-profile" readonly>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Thông tin liên lạc -->
                    <div class="profile-section">
                        <h5 class="mb-3"><i class="bi bi-envelope"></i> <span data-i18n="contact_info">联系方式</span></h5>
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label profile-label" data-i18n="form_email">邮箱</label>
                                <input type="email" class="form-control" id="field-email-profile" data-i18n-placeholder="form_email_placeholder" placeholder="输入邮箱地址">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label profile-label" data-i18n="form_phone">电话</label>
                                <input type="tel" class="form-control" id="field-phone-profile" data-i18n-placeholder="form_phone_placeholder" placeholder="输入电话号码">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Lịch sử đăng nhập -->
                    <div class="profile-section">
                        <h5 class="mb-3"><i class="bi bi-clock-history"></i> <span data-i18n="login_history">登录历史</span></h5>
                        <div class="profile-readonly-stack">
                            <div class="profile-readonly-item">
                                <span class="profile-readonly-icon"><i class="bi bi-box-arrow-in-right"></i></span>
                                <div class="profile-readonly-content">
                                    <span class="profile-readonly-label" data-i18n="form_last_login">最后登录</span>
                                    <strong id="field-last-login-profile">-</strong>
                                </div>
                            </div>
                            <div class="profile-readonly-item">
                                <span class="profile-readonly-icon"><i class="bi bi-calendar-plus"></i></span>
                                <div class="profile-readonly-content">
                                    <span class="profile-readonly-label" data-i18n="form_created_at">账号创建时间</span>
                                    <strong id="field-created-at-profile">-</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Buttons -->
                    <div class="profile-section">
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-primary" id="btn-save-profile">
                                <i class="bi bi-save"></i> <span data-i18n="save_profile">保存资料</span>
                            </button>
                            <button type="button" class="btn btn-warning" id="btn-change-password-profile">
                                <i class="bi bi-key"></i> <span data-i18n="change_password">修改密码</span>
                            </button>
                            <button type="button" class="btn btn-secondary" id="btn-refresh-profile">
                                <i class="bi bi-arrow-clockwise"></i> <span data-i18n="refresh_profile">刷新</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Change Password Modal -->
        <div class="modal fade" id="password-modal-profile" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title"><i class="bi bi-key"></i> <span data-i18n="password_change_title">修改密码</span></h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="password-form-profile">
                            <div class="mb-3">
                                <label for="current-password-profile" class="form-label" data-i18n="current_password">当前密码</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-lock"></i></span>
                                    <input type="password" class="form-control" id="current-password-profile" required>
                                    <button class="btn btn-outline-secondary" type="button" id="toggle-current-password-profile">
                                        <i class="bi bi-eye" id="toggle-current-password-icon-profile"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="new-password-profile" class="form-label" data-i18n="new_password">新密码</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
                                    <input type="password" class="form-control" id="new-password-profile" required>
                                    <button class="btn btn-outline-secondary" type="button" id="toggle-new-password-profile">
                                        <i class="bi bi-eye" id="toggle-new-password-icon-profile"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="confirm-password-profile" class="form-label" data-i18n="confirm_password">确认新密码</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
                                    <input type="password" class="form-control" id="confirm-password-profile" required>
                                    <button class="btn btn-outline-secondary" type="button" id="toggle-confirm-password-profile">
                                        <i class="bi bi-eye" id="toggle-confirm-password-icon-profile"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="alert alert-danger d-none" id="password-error-profile">
                                <i class="bi bi-exclamation-circle-fill me-2"></i>
                                <span id="password-error-text-profile"></span>
                            </div>
                            <div class="alert alert-success d-none" id="password-success-profile">
                                <i class="bi bi-check-circle-fill me-2"></i>
                                <span data-i18n="toast_password_changed">修改密码成功！</span>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-i18n="cancel">取消</button>
                        <button type="button" class="btn btn-warning" id="btn-confirm-change-password-profile">
                            <span class="spinner-border spinner-border-sm d-none" id="password-spinner-profile"></span>
                            <i class="bi bi-check-lg"></i> <span data-i18n="confirm_password_btn">确认</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup Profile event listeners
 */
function setupProfileEvents() {
    // Save profile button
    $('#btn-save-profile').off('click.profile').on('click.profile', function() {
        saveProfile();
    });
    
    // Change password button
    $('#btn-change-password-profile').off('click.profile').on('click.profile', function() {
        showPasswordModal();
    });
    
    // Refresh button
    $('#btn-refresh-profile').off('click.profile').on('click.profile', function() {
        loadProfile();
    });

    $('#profile-container').off('input.profile change.profile', 'input:not([readonly])').on('input.profile change.profile', 'input:not([readonly])', function() {
        ProfileState.isDirty = true;
        updateProfileActionState();
    });
    
    // Toggle password visibility
    setupPasswordToggles();
    
    // Confirm change password
    $('#btn-confirm-change-password-profile').off('click.profile').on('click.profile', function() {
        changePassword();
    });
}

/**
 * Setup password toggle buttons
 */
function setupPasswordToggles() {
    // Current password
    $('#toggle-current-password-profile').off('click.profile').on('click.profile', function() {
        togglePasswordVisibility('current-password-profile', 'toggle-current-password-icon-profile');
    });
    
    // New password
    $('#toggle-new-password-profile').off('click.profile').on('click.profile', function() {
        togglePasswordVisibility('new-password-profile', 'toggle-new-password-icon-profile');
    });
    
    // Confirm password
    $('#toggle-confirm-password-profile').off('click.profile').on('click.profile', function() {
        togglePasswordVisibility('confirm-password-profile', 'toggle-confirm-password-icon-profile');
    });
}

/**
 * Toggle password visibility
 * @param {string} inputId - Input field ID
 * @param {string} iconId - Icon button ID
 */
function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Load user profile
 */
async function loadProfile() {
    console.log('[Profile] Loading profile...');
    
    ProfileState.isLoading = true;
    updateProfileActionState();
    
    try {
        const result = await getCurrentUser();
        
        if (result.authenticated && result.user) {
            ProfileState.user = result.user;
            populateProfileForm(result.user);
            ProfileState.isDirty = false;
        } else {
            showToast(t('error'), t('error_loading_profile'), 'error');
        }
    } catch (error) {
        console.error('[Profile] Load error:', error);
        showToast(t('error'), t('error_loading') + ': ' + error.message, 'error');
    } finally {
        ProfileState.isLoading = false;
        updateProfileActionState();
    }
}

/**
 * Populate profile form with user data
 * @param {object} user - User data
 */
function populateProfileForm(user) {
    const displayName = user.full_name || user.username || '-';
    const roleLabel = getProfileRoleLabel(user.role);
    $('#profile-username').text(displayName);
    $('#profile-role').text(roleLabel);
    $('#profile-avatar').attr('data-initials', getProfileInitials(displayName));
    
    $('#field-username-profile').val(user.username || '');
    $('#field-role-profile').val(roleLabel);
    $('#field-fullname-profile').val(user.full_name || '');
    $('#field-employee-id-profile').val(user.employee_id || '');
    $('#field-department-profile').val(user.department || '');
    $('#field-status-profile').val(getProfileStatusLabel(user.status));
    
    $('#field-email-profile').val(user.email || '');
    $('#field-phone-profile').val(user.phone || '');
    
    $('#field-last-login-profile').text(formatProfileDateTime(getFirstProfileValue(user, ['last_login', 'lastLogin'])));
    $('#field-created-at-profile').text(formatProfileDateTime(getFirstProfileValue(user, ['user_created_at', 'created_at', 'createdAt'])));
}

function getFirstProfileValue(source, keys) {
    for (const key of keys) {
        const value = source?.[key];
        if (value !== undefined && value !== null && String(value).trim() !== '') {
            return value;
        }
    }
    return '';
}

function formatProfileDateTime(value) {
    return value ? formatDateTime(value) : '-';
}

function getProfileInitials(name) {
    const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return 'U';
    return parts.slice(-2).map(part => part.charAt(0).toUpperCase()).join('');
}

function getProfileRoleLabel(role) {
    const value = String(role || '').trim();
    if (!value) return '-';
    if (value.toLowerCase() === 'admin') return t('role_admin') || 'Admin';
    return value;
}

function getProfileStatusLabel(status) {
    const value = String(status || '').trim().toLowerCase();
    if (value === 'active') return t('status_active_profile') || 'Active';
    if (value === 'inactive') return t('status_inactive_profile') || 'Inactive';
    return status || '-';
}

function getProfileAuthToken() {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || '';
}

function updateProfileActionState() {
    const busy = ProfileState.isLoading || ProfileState.isSaving;
    $('#btn-save-profile').prop('disabled', busy || !ProfileState.isDirty);
    $('#btn-refresh-profile, #btn-change-password-profile').prop('disabled', busy);
    $('#profile-container').toggleClass('is-profile-busy', busy);
}

function validateProfileFormData(formData) {
    const email = String(formData.email || '').trim();
    const phone = String(formData.phone || '').trim();
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return t('profile_invalid_email') || 'Email không hợp lệ';
    }
    if (phone && !/^[0-9+()\-\s.]{6,24}$/.test(phone)) {
        return t('profile_invalid_phone') || 'Số điện thoại không hợp lệ';
    }
    return '';
}

// ============================================
// ACTIONS
// ============================================

/**
 * Save profile - gọi API để lưu vào database
 */
async function saveProfile() {
    if (ProfileState.isSaving) return;
    const formData = {
        full_name: $('#field-fullname-profile').val().trim(),
        employee_id: $('#field-employee-id-profile').val().trim(),
        department: $('#field-department-profile').val().trim(),
        email: $('#field-email-profile').val().trim(),
        phone: $('#field-phone-profile').val().trim()
    };

    const validationError = validateProfileFormData(formData);
    if (validationError) {
        showToast(t('warning'), validationError, 'warning');
        return;
    }
    
    ProfileState.isSaving = true;
    updateProfileActionState();
    showLoading(t('saving') + ' ' + t('profile_title').toLowerCase() + '...');
    
    try {
        const token = getProfileAuthToken();
        if (!token) {
            showToast(t('error'), t('error_session_expired'), 'error');
            return;
        }
        
        const response = await fetch('/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(t('success'), t('toast_profile_saved'), 'success');
            
            // Update session storage with new data
            if (result.user) {
                if (localStorage.getItem('current_user')) {
                    localStorage.setItem('current_user', JSON.stringify(result.user));
                }
                if (sessionStorage.getItem('current_user')) {
                    sessionStorage.setItem('current_user', JSON.stringify(result.user));
                }
                ProfileState.user = result.user;
                populateProfileForm(result.user);
                window.dispatchEvent(new CustomEvent('appUserChanged', { detail: { user: result.user } }));
            }
            ProfileState.isDirty = false;
        } else {
            showToast(t('error'), result.error || t('error_saving_profile'), 'error');
        }
    } catch (error) {
        console.error('[Profile] Save error:', error);
        showToast(t('error'), t('error_saving') + ': ' + error.message, 'error');
    } finally {
        ProfileState.isSaving = false;
        updateProfileActionState();
        hideLoading();
    }
}

/**
 * Show password change modal
 */
function showPasswordModal() {
    // Reset form
    $('#password-form-profile')[0].reset();
    $('#password-error-profile').addClass('d-none');
    $('#password-success-profile').addClass('d-none');
    
    const modal = new bootstrap.Modal('#password-modal-profile');
    modal.show();
}

/**
 * Change password - gọi API để đổi mật khẩu
 */
async function changePassword() {
    const currentPassword = $('#current-password-profile').val();
    const newPassword = $('#new-password-profile').val();
    const confirmPassword = $('#confirm-password-profile').val();
    
    // Validate
    if (!currentPassword || !newPassword || !confirmPassword) {
        showPasswordError(t('error_fill_all_fields'));
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showPasswordError(t('password_not_match'));
        return;
    }
    
    if (newPassword.length < 6) {
        showPasswordError(t('password_min_length'));
        return;
    }
    
    // Show loading
    $('#password-spinner-profile').removeClass('d-none');
    $('#btn-confirm-change-password-profile').prop('disabled', true);
    
    try {
        const token = getProfileAuthToken();
        if (!token) {
            showPasswordError(t('error_session_expired'));
            return;
        }
        
        const response = await fetch('/api/profile/password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            $('#password-error-profile').addClass('d-none');
            $('#password-success-profile').removeClass('d-none');
            
            showToast(t('success'), t('toast_password_changed'), 'success');
            
            setTimeout(() => {
                bootstrap.Modal.getInstance('#password-modal-profile').hide();
            }, 2000);
        } else {
            showPasswordError(result.error || t('error_saving'));
        }
    } catch (error) {
        console.error('[Profile] Change password error:', error);
        showPasswordError(error.message || t('error_saving'));
    } finally {
        $('#password-spinner-profile').addClass('d-none');
        $('#btn-confirm-change-password-profile').prop('disabled', false);
    }
}

/**
 * Show password error
 * @param {string} message - Error message
 */
function showPasswordError(message) {
    $('#password-error-text-profile').text(message);
    $('#password-error-profile').removeClass('d-none');
    $('#password-success-profile').addClass('d-none');
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initProfileModule = initProfileModule;
window.onProfileTabInit = function() {
    // Called when profile tab is shown
    loadProfile();
};
