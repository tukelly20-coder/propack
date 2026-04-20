/**
 * Profile Page JavaScript
 * Xử lý các chức năng cho trang Hồ Sơ Cá Nhân
 */

$(document).ready(function() {
    // Khởi tạo
    initProfile();
    
    // Sự kiện nút
    $('#btn-save-profile').on('click', saveProfile);
    $('#btn-change-password').on('click', showPasswordModal);
    $('#btn-refresh-profile').on('click', loadProfile);
    $('#btn-confirm-change-password').on('click', changePassword);
    
    // Toggle password visibility
    setupPasswordToggles();
});

// Khởi tạo trang profile
async function initProfile() {
    try {
        // Kiểm tra đăng nhập
        const authResult = await getCurrentUser();
        
        if (!authResult.authenticated) {
            showToast('Vui lòng đăng nhập để xem hồ sơ', 'error');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
            return;
        }
        
        // Hiển thị thông tin user
        displayUserInfo(authResult.user);
        
    } catch (error) {
        console.error('Init profile error:', error);
        showToast('Lỗi khởi tạo hồ sơ: ' + error.message, 'error');
    }
}

// Hiển thị thông tin user
function displayUserInfo(user) {
    if (!user) return;
    
    // Thông tin header
    $('#profile-username').text(user.username || 'Unknown');
    $('#profile-role').text(getRoleName(user.role) || 'User');
    $('#user-name').text(user.username || 'Unknown');
    
    // Thông tin cơ bản
    $('#field-username').val(user.username || '');
    $('#field-role').val(getRoleName(user.role) || '');
    $('#field-fullname').val(user.full_name || '');
    $('#field-employee-id').val(user.employee_id || '');
    $('#field-department').val(user.department || '');
    $('#field-status').val(user.status === 'active' ? 'Hoạt động' : 'Không hoạt động');
    
    // Thông tin liên lạc
    $('#field-email').val(user.email || '');
    $('#field-phone').val(user.phone || '');
    
    // Lịch sử
    $('#field-last-login').val(formatDateTime(user.last_login));
    $('#field-created-at').val(formatDateTime(user.user_created_at));
}

// Lấy thông tin profile từ server
async function loadProfile() {
    try {
        const authResult = await getCurrentUser();
        
        if (authResult.authenticated) {
            displayUserInfo(authResult.user);
            showToast('Đã làm mới thông tin', 'success');
        }
    } catch (error) {
        console.error('Load profile error:', error);
        showToast('Lỗi tải thông tin: ' + error.message, 'error');
    }
}

// Lưu thông tin profile
async function saveProfile() {
    const btn = $('#btn-save-profile');
    const originalText = btn.html();
    
    try {
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Đang lưu...');

        const userData = {
            full_name: $('#field-fullname').val().trim(),
            employee_id: $('#field-employee-id').val().trim(),
            department: $('#field-department').val().trim(),
            email: $('#field-email').val().trim(),
            phone: $('#field-phone').val().trim()
        };

        const token = getAuthToken();
        if (!token) {
            throw new Error('Phiên đăng nhập hết hạn');
        }
        
        const response = await fetch('/api/user/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cập nhật localStorage
            const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}');
            const updatedUser = { ...currentUser, ...userData };
            localStorage.setItem('current_user', JSON.stringify(updatedUser));
            
            showToast('Lưu thông tin thành công!', 'success');
        } else {
            throw new Error(result.error || 'Lỗi lưu thông tin');
        }
        
    } catch (error) {
        console.error('Save profile error:', error);
        showToast('Lỗi lưu thông tin: ' + error.message, 'error');
    } finally {
        btn.prop('disabled', false).html(originalText);
    }
}

// Hiển thị modal đổi mật khẩu
function showPasswordModal() {
    $('#password-modal').modal('show');
    $('#password-form')[0].reset();
    $('#password-error').addClass('d-none');
    $('#password-success').addClass('d-none');
}

// Đổi mật khẩu
async function changePassword() {
    const btn = $('#btn-confirm-change-password');
    const originalText = btn.html();
    const currentPassword = $('#current-password').val();
    const newPassword = $('#new-password').val();
    const confirmPassword = $('#confirm-password').val();
    
    // Validate
    if (!currentPassword) {
        showPasswordError('Vui lòng nhập mật khẩu hiện tại');
        return;
    }
    
    if (!newPassword) {
        showPasswordError('Vui lòng nhập mật khẩu mới');
        return;
    }
    
    if (newPassword.length < 4) {
        showPasswordError('Mật khẩu mới phải có ít nhất 4 ký tự');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showPasswordError('Mật khẩu mới không khớp');
        return;
    }
    
    try {
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Đang xử lý...');
        
        const token = getAuthToken();
        if (!token) {
            throw new Error('Phiên đăng nhập hết hạn');
        }
        
        const response = await fetch('/api/user/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            $('#password-success').removeClass('d-none');
            $('#password-error').addClass('d-none');
            
            // Đóng modal sau 2 giây
            setTimeout(() => {
                $('#password-modal').modal('hide');
            }, 2000);
        } else {
            throw new Error(result.error || 'Đổi mật khẩu thất bại');
        }
        
    } catch (error) {
        console.error('Change password error:', error);
        showPasswordError(error.message || 'Lỗi đổi mật khẩu');
    } finally {
        btn.prop('disabled', false).html(originalText);
    }
}

// Hiển thị lỗi đổi mật khẩu
function showPasswordError(message) {
    $('#password-error-text').text(message);
    $('#password-error').removeClass('d-none');
    $('#password-success').addClass('d-none');
}

// Setup toggle password visibility
function setupPasswordToggles() {
    const toggles = [
        { btn: '#toggle-current-password', input: '#current-password', icon: '#toggle-current-password-icon' },
        { btn: '#toggle-new-password', input: '#new-password', icon: '#toggle-new-password-icon' },
        { btn: '#toggle-confirm-password', input: '#confirm-password', icon: '#toggle-confirm-password-icon' }
    ];
    
    toggles.forEach(toggle => {
        $(toggle.btn).on('click', function() {
            const input = $(toggle.input);
            const icon = $(toggle.icon);
            
            if (input.attr('type') === 'password') {
                input.attr('type', 'text');
                icon.removeClass('bi-eye').addClass('bi-eye-slash');
            } else {
                input.attr('type', 'password');
                icon.removeClass('bi-eye-slash').addClass('bi-eye');
            }
        });
    });
}

// Lấy tên vai trò
function getRoleName(role) {
    const roles = {
        'admin': 'Quản trị viên',
        'manager': 'Quản lý',
        'engineer': 'Kỹ sư',
        'designer': 'Nhà thiết kế',
        'user': 'Người dùng'
    };
    return roles[role] || role;
}

// Định dạng ngày giờ
function formatDateTime(dateString) {
    if (!dateString) return 'Chưa có';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('vi-VN');
    } catch {
        return dateString;
    }
}

// Hiển thị toast notification
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('toast');
    const toast = new bootstrap.Toast(toastEl);
    
    $('#toast-message').text(message);
    $('#toast-title').text(type === 'success' ? 'Thành công' : type === 'error' ? 'Lỗi' : 'Thông báo');
    
    toastEl.classList.remove('bg-success', 'bg-danger', 'bg-info', 'bg-warning');
    toastEl.classList.add(type === 'success' ? 'bg-success text-white' : type === 'error' ? 'bg-danger text-white' : 'bg-info text-white');
    
    toast.show();
}

// Đăng xuất
$('#btn-logout').on('click', async function() {
    try {
        await logout();
        window.location.href = 'index.html';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = 'index.html';
    }
});
