/**
 * Shared Components for SPA
 * Chứa các hàm dùng chung: Toast, Modal, Loading, Utilities
 */

// ============================================
// TOAST NOTIFICATIONS
// ============================================

/**
 * Hiển thị toast notification
 * @param {string} title - Tiêu đề toast
 * @param {string} message - Nội dung toast  
 * @param {string} type - Loại: 'success', 'error', 'warning', 'info'
 */
function showToast(title, message, type = 'info') {
    const toastEl = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toastEl || !toastTitle || !toastMessage) {
        console.warn('Toast elements not found');
        return;
    }
    
    // Use translations for title (key) and message
    toastTitle.textContent = translations[title] ? t(title) : (translations[currentLanguage]?.[title] || title);
    // Try to translate message if it's a key
    toastMessage.textContent = translations[currentLanguage]?.[message] ? t(message) : message;
    
    const header = toastEl.querySelector('.toast-header');
    header.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info', 'bg-primary', 'text-white');
    
    switch (type) {
        case 'success':
            header.classList.add('bg-success', 'text-white');
            break;
        case 'error':
            header.classList.add('bg-danger', 'text-white');
            break;
        case 'warning':
            header.classList.add('bg-warning');
            break;
        default:
            header.classList.add('bg-info', 'text-white');
    }
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

/**
 * Hiển thị loading toast - Non-blocking
 * @param {string} message - Thông báo loading
 */
function showLoading(message) {
    const toastEl = document.getElementById('loading-toast');
    const toastMessage = document.getElementById('loading-toast-message');
    
    if (!toastEl || !toastMessage) {
        console.warn('Loading toast elements not found');
        return;
    }
    
    // Use translation key or message
    const loadingText = message || t('loading_data');
    toastMessage.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span><span>' + loadingText + '</span>';
    
    const toast = new bootstrap.Toast(toastEl, {
        autohide: false,
        delay: 999999
    });
    toast.show();
}

/**
 * Ẩn loading toast
 */
function hideLoading() {
    const toastEl = document.getElementById('loading-toast');
    if (toastEl) {
        const toast = bootstrap.Toast.getInstance(toastEl);
        if (toast) {
            toast.hide();
        }
    }
}

// ============================================
// MODAL HELPERS
// ============================================

/**
 * Hiển thị modal
 * @param {string} modalId - ID của modal
 */
function showModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

/**
 * Ẩn modal
 * @param {string} modalId - ID của modal
 */
function hideModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
            modal.hide();
        }
    }
}

/**
 * Tạo confirm delete modal HTML
 * @param {string} title - Tiêu đề modal
 * @param {string} message - Nội dung thông báo
 * @param {number} count - Số lượng item sẽ xóa
 * @returns {string} HTML string
 */
function createConfirmDeleteModal(title, message, count) {
    return `
        <div class="modal fade" id="confirm-delete-modal" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-exclamation-triangle"></i> ${title}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message} <span id="delete-count">${count}</span> dự án đã chọn không?</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Hủy</button>
                        <button type="button" class="btn btn-danger" id="btn-confirm-delete">Xóa</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Tạo view detail modal HTML
 * @param {object} data - Dữ liệu chi tiết
 * @returns {string} HTML string
 */
function createViewDetailModal(data) {
    let content = '<div class="detail-section">';
    
    for (const [key, value] of Object.entries(data)) {
        if (value) {
            content += `
                <div class="detail-item">
                    <strong>${key}:</strong>
                    <span>${escapeHtml(String(value))}</span>
                </div>
            `;
        }
    }
    
    content += '</div>';
    
    return `
        <div class="modal fade" id="view-modal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title"><i class="bi bi-eye"></i> Chi tiết dự án</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="view-content">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Đóng</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Chuỗi cần escape
 * @returns {string}
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format ngày giờ
 * @param {string|Date} dateStr - Chuỗi ngày hoặc Date object
 * @param {string} locale - Locale: 'vi-VN' hoặc 'zh-CN'
 * @returns {string}
 */
function formatDateTime(dateStr, locale = 'vi-VN') {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString(locale);
    } catch {
        return dateStr;
    }
}

/**
 * Format ngày
 * @param {string|Date} dateStr - Chuỗi ngày hoặc Date object
 * @param {string} locale - Locale
 * @returns {string}
 */
function formatDate(dateStr, locale = 'vi-VN') {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString(locale);
    } catch {
        return dateStr;
    }
}

/**
 * Format thời gian tương đối
 * @param {Date|string} date - Ngày cần format
 * @param {string} lang - Ngôn ngữ: 'vi' hoặc 'zh'
 * @returns {string}
 */
function getRelativeTime(date, lang = null) {
    if (!date) return '-';
    
    // Use current language if not specified
    const currentLang = lang || window.currentLanguage || 'vi';
    
    const now = new Date();
    const targetDate = new Date(date);
    const diff = now - targetDate;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) {
        return seconds + ' ' + t('seconds_ago');
    } else if (minutes < 60) {
        return minutes + ' ' + t('minutes_ago');
    } else if (hours < 24) {
        return hours + ' ' + t('hours_ago');
    } else if (days === 1) {
        return t('yesterday');
    } else if (days < 7) {
        return days + ' ' + t('days_ago');
    } else {
        return formatDate(date, currentLang === 'zh' ? 'zh-CN' : 'vi-VN');
    }
}

/**
 * Debounce function
 * @param {Function} func - Hàm cần debounce
 * @param {number} wait - Thời gian chờ (ms)
 * @returns {Function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Kiểm tra object có rỗng không
 * @param {object} obj - Object cần kiểm tra
 * @returns {boolean}
 */
function isEmptyObject(obj) {
    return obj && Object.keys(obj).length === 0 && obj.constructor === Object;
}

// ============================================
// PAGINATION
// ============================================

/**
 * Tạo pagination HTML
 * @param {number} currentPage - Trang hiện tại
 * @param {number} totalPages - Tổng số trang
 * @param {Function} onPageChange - Callback khi đổi trang
 * @returns {string} HTML string
 */
function createPagination(currentPage, totalPages, onPageChange) {
    if (totalPages <= 1) return '';
    
    let html = '<nav><ul class="pagination mb-0">';
    
    // Previous button
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}">${t('previous_page')}</a>
    </li>`;
    
    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" data-page="${i}">${i}</a>
        </li>`;
    }
    
    // Next button
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage + 1}">${t('next_page')}</a>
    </li>`;
    
    html += '</ul></nav>';
    
    return html;
}

// ============================================
// TABLE HELPERS
// ============================================

/**
 * Tạo empty state HTML cho table
 * @param {string} message - Thông báo
 * @param {number} colspan - Số cột
 * @returns {string}
 */
function createEmptyState(message, colspan = 8) {
    const text = message || t('no_data');
    return `
        <tr class="empty-row">
            <td colspan="${colspan}" class="text-center text-muted py-4">
                <i class="bi bi-inbox d-block mb-2" style="font-size: 2rem; opacity: 0.5;"></i>
                ${text}
            </td>
        </tr>
    `;
}

/**
 * Tạo loading state HTML cho table
 * @param {number} colspan - Số cột
 * @returns {string}
 */
function createLoadingState(colspan = 8) {
    return `
        <tr class="loading-row">
            <td colspan="${colspan}" class="text-center py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted">${t('loading_data')}</p>
            </td>
        </tr>
    `;
}

/**
 * Tạo error state HTML cho table
 * @param {string} message - Thông báo lỗi
 * @param {number} colspan - Số cột
 * @returns {string}
 */
function createErrorState(message, colspan = 8) {
    const text = message || t('load_error');
    return `
        <tr class="error-row">
            <td colspan="${colspan}" class="text-center text-danger py-4">
                <i class="bi bi-exclamation-triangle d-block mb-2" style="font-size: 2rem;"></i>
                ${text}
            </td>
        </tr>
    `;
}

// ============================================
// EXPORT TO GLOBAL
// ============================================

// Export functions to global scope
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showModal = showModal;
window.hideModal = hideModal;
window.createConfirmDeleteModal = createConfirmDeleteModal;
window.createViewDetailModal = createViewDetailModal;
window.escapeHtml = escapeHtml;
window.formatDateTime = formatDateTime;
window.formatDate = formatDate;
window.getRelativeTime = getRelativeTime;
window.debounce = debounce;
window.isEmptyObject = isEmptyObject;
window.createPagination = createPagination;
window.createEmptyState = createEmptyState;
window.createLoadingState = createLoadingState;
window.createErrorState = createErrorState;
