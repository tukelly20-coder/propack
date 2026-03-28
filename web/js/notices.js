// ============================================
// Notice Tab JavaScript
// ============================================

// State management
const NoticeState = {
    notices: [],
    filteredNotices: [],
    selectedNotice: null,
    currentUser: null,
    autoRefreshInterval: null,
    AUTO_REFRESH_MS: 30000 // 30 seconds
};

// Initialize when document is ready
$(document).ready(function() {
    console.log('[Notices] Document ready');
    setupEventListeners();
    loadNotices();
    startAutoRefresh();
});

// Setup event listeners
function setupEventListeners() {
    console.log('[Notices] Setting up event listeners...');
    
    // Filter by status
    $('input[name="status-filter"]').change(function() {
        applyFilters();
    });
    
    // Filter by urgency
    $('#urgency-filter').change(function() {
        applyFilters();
    });
    
    // Search input
    $('#search-input').on('input', function() {
        applyFilters();
    });
    
    // Refresh button
    $('#btn-refresh').click(function() {
        loadNotices();
    });
    
    // Logout button
    $('#btn-logout').click(async function() {
        try {
            await logout();
            window.location.href = 'index.html';
        } catch (error) {
            console.error('Logout failed:', error);
        }
    });
}

// Load notices from API
async function loadNotices() {
    console.log('[Notices] Loading notices...');
    const tbody = $('#notices-table-body');
    tbody.html('<tr><td colspan="11" class="text-center py-4"><div class="spinner-border spinner-border-sm" role="status"></div> Đang tải...</td></tr>');
    
    try {
        // Get user info
        const userResult = await getCurrentUser();
        if (!userResult.authenticated) {
            window.location.href = 'index.html';
            return;
        }
        
        NoticeState.currentUser = userResult.user;
        const userId = userResult.user.id;
        
        // Load notices based on user role
        let result;
        if (userResult.user.role === 'engineer') {
            // Engineers see all notices (pending + accepted)
            result = await getAllNoticesForEngineer(userResult.user.username);
        } else {
            // Others see pending notices
            result = await getPendingNotices(userId);
        }
        
        if (result.success) {
            NoticeState.notices = result.data || [];
            applyFilters();
            updateStats();
        } else {
            throw new Error(result.error || 'Failed to load notices');
        }
    } catch (error) {
        console.error('Load notices error:', error);
        let errorMessage = 'Lỗi tải thông báo';
        if (error.message) {
            if (error.message.includes('kết nối')) {
                errorMessage = 'Không thể kết nối server. Vui lòng kiểm tra kết nối.';
            } else {
                errorMessage = 'Lỗi tải thông báo: ' + error.message;
            }
        }
        tbody.html('<tr><td colspan="11" class="text-center text-danger py-4">' + errorMessage + '</td></tr>');
    }
}

// Apply filters to notices
function applyFilters() {
    const statusFilter = $('input[name="status-filter"]:checked').val();
    const urgencyFilter = $('#urgency-filter').val();
    const searchText = $('#search-input').val().toLowerCase().trim();
    
    let filtered = [...NoticeState.notices];
    
    // Filter by status
    if (statusFilter === 'pending') {
        filtered = filtered.filter(n => n.is_pending === 'yes');
    } else if (statusFilter === 'accepted') {
        filtered = filtered.filter(n => n.is_pending === 'no');
    }
    
    // Filter by urgency
    if (urgencyFilter !== 'all') {
        filtered = filtered.filter(n => n.urgency_level === urgencyFilter);
    }
    
    // Filter by search text
    if (searchText) {
        filtered = filtered.filter(n => {
            const customer = (n['Khách hàng'] || '').toLowerCase();
            const product = (n['Tên sản phẩm'] || '').toLowerCase();
            const trackingId = (n['Tracking ID'] || '').toString().toLowerCase();
            const sales = (n['Nhân viên KD'] || '').toLowerCase();
            const engineer = (n['Kỹ sư'] || '').toLowerCase();
            
            return customer.includes(searchText) || 
                   product.includes(searchText) || 
                   trackingId.includes(searchText) ||
                   sales.includes(searchText) ||
                   engineer.includes(searchText);
        });
    }
    
    NoticeState.filteredNotices = filtered;
    renderNoticesTable();
}

// Render notices table
function renderNoticesTable() {
    const tbody = $('#notices-table-body');
    const notices = NoticeState.filteredNotices;
    
    if (notices.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="11"><i class="bi bi-inbox d-block mb-2" style="font-size: 2rem;"></i>Không có thông báo nào</td></tr>');
        return;
    }
    
    const fragment = document.createDocumentFragment();
    
    notices.forEach((notice, index) => {
        const tr = document.createElement('tr');
        tr.className = 'notice-row';
        
        // Determine urgency class
        let urgencyClass = 'urgency-normal';
        let urgencyText = 'Bình thường';
        let urgencyBadgeClass = 'success';
        if (notice.urgency_level === 'urgent') {
            urgencyClass = 'urgency-urgent';
            urgencyText = 'Khẩn cấp';
            urgencyBadgeClass = 'warning text-dark';
        } else if (notice.urgency_level === 'very_urgent') {
            urgencyClass = 'urgency-very_urgent';
            urgencyText = 'Rất khẩn';
            urgencyBadgeClass = 'danger';
        }
        
        // Determine status
        const isPending = notice.is_pending === 'yes';
        const statusClass = isPending ? 'status-pending' : 'status-accepted';
        const statusText = isPending ? 'Chờ duyệt' : 'Đã nhận';
        
        // Engineer can accept job if pending
        const canAccept = isPending && NoticeState.currentUser && 
                         NoticeState.currentUser.role === 'engineer';
        
        tr.className += ' ' + urgencyClass;
        tr.dataset.trackingId = notice['Tracking ID'];
        
        tr.innerHTML =
            '<td>' + (index + 1) + '</td>' +
            '<td><strong>' + escapeHtml(notice['Tracking ID'] || '') + '</strong></td>' +
            '<td>' + formatDateTime(notice['Ngày']) + '</td>' +
            '<td>' + escapeHtml(notice['Khách hàng'] || '') + '</td>' +
            '<td>' + escapeHtml(notice['Tên sản phẩm'] || '') + '</td>' +
            '<td>' + escapeHtml(notice['Số lượng'] || '') + '</td>' +
            '<td>' + escapeHtml(notice['Nhân viên KD'] || '') + '</td>' +
            '<td>' + escapeHtml(notice['Kỹ sư'] || '-') + '</td>' +
            '<td><span class="badge bg-' + urgencyBadgeClass + '">' + urgencyText + '</span></td>' +
            '<td class="' + statusClass + '">' + statusText + '</td>' +
            '<td>' +
                '<button class="btn btn-sm btn-outline-info me-1 btn-view" data-id="' + notice['Tracking ID'] + '" title="Xem chi tiết">' +
                    '<i class="bi bi-eye"></i>' +
                '</button>' +
                (canAccept ? '<button class="btn btn-sm btn-success btn-accept" data-id="' + notice['Tracking ID'] + '" title="Nhận job">' +
                    '<i class="bi bi-check-lg"></i>' +
                '</button>' : '') +
            '</td>';
        
        fragment.appendChild(tr);
    });
    
    tbody.empty();
    tbody[0].appendChild(fragment);
    
    // Add click handlers
    $('.btn-view').click(function(e) {
        e.stopPropagation();
        const trackingId = $(this).data('id');
        viewNoticeDetails(trackingId);
    });
    
    $('.btn-accept').click(function(e) {
        e.stopPropagation();
        const trackingId = $(this).data('id');
        // Use window.acceptJob to call the API function
        window.acceptJob(trackingId);
    });
    
    // Row click to view details
    $('.notice-row').dblclick(function() {
        const trackingId = $(this).data('trackingId');
        viewNoticeDetails(trackingId);
    });
}

// Update statistics
function updateStats() {
    const notices = NoticeState.notices;
    const total = notices.length;
    const pending = notices.filter(n => n.is_pending === 'yes').length;
    const accepted = notices.filter(n => n.is_pending === 'no').length;
    const urgent = notices.filter(n => n.urgency_level === 'urgent' || n.urgency_level === 'very_urgent').length;
    
    $('#stat-total').text(total);
    $('#stat-pending').text(pending);
    $('#stat-accepted').text(accepted);
    $('#stat-urgent').text(urgent);
}

// View notice details
function viewNoticeDetails(trackingId) {
    const notice = NoticeState.notices.find(n => n['Tracking ID'] === trackingId);
    if (!notice) return;
    
    const content = $('#view-content');
    
    // Determine urgency badge
    let urgencyBadge = '';
    if (notice.urgency_level === 'very_urgent') {
        urgencyBadge = '<span class="badge bg-danger">Rất khẩn</span>';
    } else if (notice.urgency_level === 'urgent') {
        urgencyBadge = '<span class="badge bg-warning text-dark">Khẩn cấp</span>';
    } else {
        urgencyBadge = '<span class="badge bg-success">Bình thường</span>';
    }
    
    // Status text
    const statusHtml = notice.is_pending === 'yes' 
        ? '<span class="text-danger fw-bold">Chờ duyệt</span>' 
        : '<span class="text-success fw-bold">Đã nhận</span>';
    
    let detailsHtml = '<div class="container-fluid">';
    detailsHtml += '<div class="row">';
    
    // Left column - Project Info
    detailsHtml += '<div class="col-md-6 detail-section">';
    detailsHtml += '<h6><i class="bi bi-folder"></i> Thông tin dự án</h6>';
    detailsHtml += '<div class="detail-item"><strong>Tracking ID:</strong><span>' + escapeHtml(notice['Tracking ID'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Ngày:</strong><span>' + formatDateTime(notice['Ngày']) + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Khách hàng:</strong><span>' + escapeHtml(notice['Khách hàng'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Nhân viên KD:</strong><span>' + escapeHtml(notice['Nhân viên KD'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Tên sản phẩm:</strong><span>' + escapeHtml(notice['Tên sản phẩm'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Quy cách:</strong><span>' + escapeHtml(notice['Quy cách'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Số lượng:</strong><span>' + escapeHtml(notice['Số lượng'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Mã PO:</strong><span>' + escapeHtml(notice['Mã PO'] || '') + '</span></div>';
    detailsHtml += '</div>';
    
    // Right column - Technical Info
    detailsHtml += '<div class="col-md-6 detail-section">';
    detailsHtml += '<h6><i class="bi bi-gear"></i> Thông tin kỹ thuật</h6>';
    detailsHtml += '<div class="detail-item"><strong>Mã bản vẽ:</strong><span>' + escapeHtml(notice['Mã bản vẽ'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Mã bản vẽ KT:</strong><span>' + escapeHtml(notice['Mã bản vẽ KT'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Mã mẹ:</strong><span>' + escapeHtml(notice['Mã mẹ'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Loại sản phẩm:</strong><span>' + escapeHtml(notice['Loại sản phẩm'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Kỹ sư:</strong><span>' + escapeHtml(notice['Kỹ sư'] || '-') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Tình trạng:</strong><span>' + escapeHtml(notice['Tình trạng'] || '') + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Độ khẩn:</strong><span>' + urgencyBadge + '</span></div>';
    detailsHtml += '<div class="detail-item"><strong>Trạng thái:</strong><span>' + statusHtml + '</span></div>';
    detailsHtml += '</div>';
    
    detailsHtml += '</div></div>';
    
    content.html(detailsHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('view-modal'));
    modal.show();
}

// Accept job
async function acceptJob(trackingId) {
    if (!NoticeState.currentUser) {
        showToast('Lỗi', 'Vui lòng đăng nhập lại', 'error');
        return;
    }
    
    const confirmMsg = 'Bạn có chắc chắn muốn nhận job ' + trackingId + '?';
    if (!confirm(confirmMsg)) {
        return;
    }
    
    showLoading('Đang nhận job...');
    
    try {
        // Call API function from window (exported from api.js)
        const result = await window.acceptJob(trackingId, NoticeState.currentUser.username);
        
        if (result.success) {
            showToast('Thành công', 'Đã nhận job ' + trackingId, 'success');
            await loadNotices();
        } else {
            throw new Error(result.error || 'Không thể nhận job');
        }
    } catch (error) {
        console.error('Accept job error:', error);
        showToast('Lỗi', error.message || 'Không thể nhận job', 'error');
    } finally {
        hideLoading();
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (NoticeState.autoRefreshInterval) {
        clearInterval(NoticeState.autoRefreshInterval);
    }
    
    NoticeState.autoRefreshInterval = setInterval(function() {
        console.log('[Notices] Auto-refreshing...');
        loadNotices();
    }, NoticeState.AUTO_REFRESH_MS);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (NoticeState.autoRefreshInterval) {
        clearInterval(NoticeState.autoRefreshInterval);
        NoticeState.autoRefreshInterval = null;
    }
}

// Format datetime for display
function formatDateTime(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('vi-VN');
    } catch {
        return dateStr;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show toast notification
function showToast(title, message, type = 'info') {
    const toastEl = $('#toast');
    const toastTitle = $('#toast-title');
    const toastMessage = $('#toast-message');
    
    toastTitle.text(title);
    toastMessage.text(message);
    
    const header = toastEl.find('.toast-header');
    header.removeClass('bg-success bg-danger bg-warning bg-info bg-primary');
    
    switch (type) {
        case 'success':
            header.addClass('bg-success text-white');
            break;
        case 'error':
            header.addClass('bg-danger text-white');
            break;
        case 'warning':
            header.addClass('bg-warning');
            break;
        default:
            header.addClass('bg-info text-white');
    }
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Show loading toast - Non-blocking
function showLoading(message) {
    const toastEl = document.getElementById('loading-toast');
    const toastMessage = document.getElementById('loading-toast-message');
    
    toastMessage.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span><span>' + (message || 'Đang tải...') + '</span>';
    
    const toast = new bootstrap.Toast(toastEl, {
        autohide: false,
        delay: 999999
    });
    toast.show();
}

// Hide loading toast
function hideLoading() {
    const toastEl = document.getElementById('loading-toast');
    const toast = bootstrap.Toast.getInstance(toastEl);
    if (toast) {
        toast.hide();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
