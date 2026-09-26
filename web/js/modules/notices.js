/**
 * Notices Module
 * Quản lý thông báo chờ xử lý - Extracted from notices.html
 * Đồng bộ UI với Projects module
 */

// ============================================
// STATE
// ============================================

const NoticesState = {
    notices: [],
    filteredNotices: [],
    statusFilter: '',
    urgencyFilter: '',
    searchText: '',
    isLoading: false,
    currentUserName: '',
    currentUserRole: '',
    currentUserId: null,
    // Selection
    selectedIds: [],
    // Pagination
    currentPage: 1,
    pageSize: 50,
    totalRecords: 0,
    totalPages: 1,
    // Stats
    stats: {
        total: 0,
        pending: 0,
        accepted: 0,
        urgent: 0
    },
    // Realtime stream
    stream: null,
    streamConnected: false,
    reconnectTimer: null,
    reconnectAttempts: 0,
    refreshTimer: null,
    initialized: false,
    lastLoadedAt: null,
    // Column visibility
    visibleColumns: {
        'checkbox': true,
        'stt': true,
        'tracking_id': true,
        'ngay': true,
        'khachhang': true,
        'sanpham': true,
        'soluong': true,
        'nhanvienkd': true,
        'kysu': true,
        'dokhan': true,
        'trangthai': true,
        'actions': true
    },
    // Available columns config
    columnsConfig: [
        { key: 'stt', label: 'STT', default: true },
        { key: 'tracking_id', label: 'Tracking ID', default: true },
        { key: 'ngay', label: 'Ngày', default: true },
        { key: 'khachhang', label: 'Khách hàng', default: true },
        { key: 'sanpham', label: 'Sản phẩm', default: true },
        { key: 'soluong', label: 'Số lượng', default: true },
        { key: 'nhanvienkd', label: 'Nhân viên KD', default: true },
        { key: 'kysu', label: 'Kỹ sư', default: true },
        { key: 'dokhan', label: 'Độ khẩn', default: true },
        { key: 'trangthai', label: 'Trạng thái', default: true }
    ]
};

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize Notices module
 */
function initNoticesModule() {
    console.log('[Notices] Initializing...');
    if (NoticesState.initialized) return;
    NoticesState.initialized = true;
    const currentUser = AppState.currentUser || {};
    NoticesState.currentUserName = currentUser.full_name || currentUser.username || '';
    NoticesState.currentUserRole = currentUser.role || '';
    NoticesState.currentUserId = currentUser.user_id || null;
    
    // Render the module content
    renderNoticesContent();
    
    // Setup event listeners
    setupNoticesEvents();
    
    // Load data
    loadNotices();
    
    // Auto refresh every 30 seconds
    startAutoRefresh();
    setupNoticeRealtimeStream();
}

/**
 * Render Notices module content - Synced with Projects UI
 */
function renderNoticesContent() {
    const container = document.getElementById('notices-container');
    
    container.innerHTML = `
        <!-- Compact Toolbar -->
        <div class="card mb-2 notices-toolbar-card">
            <div class="card-body py-2">
                <div class="notices-toolbar">
                    <div class="notices-toolbar-actions">
                        <button class="btn btn-outline-secondary btn-sm" id="btn-refresh-notice" title="${t('refresh')}">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                        <div class="dropdown">
                            <button class="btn btn-outline-secondary btn-sm dropdown-toggle" type="button" 
                                    data-bs-toggle="dropdown" aria-expanded="false" title="${t('export')}">
                                <i class="bi bi-download"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" id="btn-export-excel-notice">
                                    <i class="bi bi-file-earmark-excel text-success"></i> ${t('export_excel')}
                                </a></li>
                                <li><a class="dropdown-item" href="#" id="btn-export-csv-notice">
                                    <i class="bi bi-file-earmark-text text-primary"></i> ${t('export_csv')}
                                </a></li>
                            </ul>
                        </div>
                    </div>

                    <div class="notices-toolbar-stats">
                        <span class="notice-stat-chip"><i class="bi bi-collection"></i>${t('stat_total')}: <strong id="stat-total-notices">0</strong></span>
                        <span class="notice-stat-chip is-pending"><i class="bi bi-tags"></i>Cần phân loại: <strong id="stat-pending-notices">0</strong></span>
                        <span class="notice-stat-chip is-urgent"><i class="bi bi-lightning-charge"></i>${t('stat_urgent')}: <strong id="stat-urgent-notices">0</strong></span>
                    </div>

                    <div class="notices-toolbar-filters">
                        <select class="form-select form-select-sm" id="filter-urgency-notice" title="${t('notice_filter_urgency')}">
                            <option value="">${t('notice_all_urgency')}</option>
                            <option value="normal">${t('urgency_normal')}</option>
                            <option value="urgent">${t('urgency_urgent')}</option>
                            <option value="very_urgent">${t('urgency_very_urgent')}</option>
                        </select>
                        <div class="input-group input-group-sm notices-search">
                            <input type="text" class="form-control" id="search-input-notice" 
                                   placeholder="Tìm mã, khách hàng, quy cách...">
                            <button class="btn btn-outline-secondary" type="button" id="btn-clear-search-notice" title="${t('clear_search')}">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                        <span class="notice-realtime-status" id="notice-realtime-status" title="${t('auto_refresh_note')}">
                            <i class="bi bi-broadcast-pin"></i> Đang kết nối
                        </span>
                    </div>
                </div>
                <div class="notices-toolbar-subline">
                    <span id="notice-scope-label">${getNoticeScopeLabel()}</span>
                    <span id="notice-last-updated">Chưa tải dữ liệu</span>
                </div>
            </div>
        </div>
        
        <!-- Column Visibility Dropdown (Hidden by default) -->
        <div class="column-selector-popup" id="column-selector-notice" style="display: none;">
            <div class="column-selector-header">
                <h6 class="mb-0"><i class="bi bi-layout-columns"></i> ${t('column_selector_title')}</h6>
                <button type="button" class="btn-close" id="btn-close-column-selector-notice"></button>
            </div>
            <div class="column-selector-body" id="column-selector-body-notice">
                <!-- Generated by JS -->
            </div>
            <div class="column-selector-footer">
                    <button class="btn btn-sm btn-outline-secondary" id="btn-reset-columns-notice">${t('column_reset')}</button>
                    <button class="btn btn-sm btn-primary" id="btn-apply-columns-notice">${t('column_apply')}</button>
            </div>
        </div>

        <!-- Facebook-style Notice Feed -->
        <div class="card notices-feed-card">
            <div class="card-header notices-feed-header">
                <div class="d-flex align-items-center gap-2">
                    <input type="checkbox" id="select-all-notices" class="form-check-input">
                    <span class="fw-semibold">${t('notices_title')}</span>
                </div>
                <small class="text-muted" id="notice-selection-info">0 đã chọn</small>
            </div>
            <div class="card-body p-0">
                <div class="notice-feed-list" id="notices-table-body">
                    <!-- Feed items will be loaded here -->
                </div>
            </div>
        </div>
        
        <!-- Pagination with Jump to Page -->
        <div class="card mt-2">
            <div class="card-body py-2">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <span id="page-info-notice">${t('page_info', { start: 0, end: 0, total: 0 })}</span>
                    </div>
                    <div class="col-auto ms-auto">
                        <nav>
                            <ul class="pagination mb-0" id="pagination-notice">
                                <!-- Pagination will be generated here -->
                            </ul>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <div class="d-flex align-items-center gap-2">
                            <select class="form-select form-select-sm" id="page-size-notice" style="width: auto;">
                                <option value="10">10 ${t('per_page')}</option>
                                <option value="25">25 ${t('per_page')}</option>
                                <option value="50" selected>50 ${t('per_page')}</option>
                                <option value="100">100 ${t('per_page')}</option>
                            </select>
                            <span class="text-muted">|</span>
                            <div class="input-group input-group-sm" style="width: 120px;">
                                <input type="number" class="form-control" id="jump-to-page-notice" 
                                       placeholder="${t('page')}" min="1">
                                <button class="btn btn-outline-secondary" type="button" id="btn-jump-to-page-notice" title="${t('jump_to_page')}">
                                    <i class="bi bi-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Add/Edit Modal -->
        <div class="modal fade" id="notice-modal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="modal-title-notice">${t('add_notice')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="notice-form">
                            <input type="hidden" id="notice-tracking-id">
                            
                            <!-- Thông tin cơ bản -->
                            <h6 class="border-bottom pb-2 mb-3">${t('basic_info')}</h6>
                            <div class="row g-3">
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_ngay_khoitao')}</label>
                                    <input type="datetime-local" class="form-control" id="notice-field-ngay">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_khachhang_required')}</label>
                                    <input type="text" class="form-control" id="notice-field-khachhang" required>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_nhanvienkd')}</label>
                                    <input type="text" class="form-control" id="notice-field-nhanvienkd">
                                </div>
                            </div>
                            
                            <!-- Thông tin sản phẩm -->
                            <h6 class="border-bottom pb-2 mb-3 mt-4">${t('product_info')}</h6>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label">${t('notice_form_tensanpham_required')}</label>
                                    <input type="text" class="form-control" id="notice-field-sanpham" required>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('notice_form_soluong')}</label>
                                    <input type="number" class="form-control" id="notice-field-soluong">
                                </div>
                            </div>
                            
                            <!-- Thông tin kỹ thuật -->
                            <h6 class="border-bottom pb-2 mb-3 mt-4">${t('technical_info')}</h6>
                            <div class="row g-3">
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_kysu')}</label>
                                    <input type="text" class="form-control" id="notice-field-kysu">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_dokhan')}</label>
                                    <select class="form-select" id="notice-field-dokhan">
                                        <option value="normal">${t('urgency_normal_option')}</option>
                                        <option value="urgent">${t('urgency_urgent_option')}</option>
                                        <option value="very_urgent">${t('urgency_very_urgent_option')}</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">${t('notice_form_trangthai')}</label>
                                    <select class="form-select" id="notice-field-trangthai">
                                        <option value="pending">${t('status_pending_option')}</option>
                                        <option value="accepted">${t('status_accepted')}</option>
                                        <option value="in_progress">${t('status_in_progress')}</option>
                                        <option value="completed">${t('status_completed_option')}</option>
                                    </select>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-primary" id="btn-save-notice">${t('save')}</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Confirm Delete Modal -->
        <div class="modal fade" id="confirm-delete-modal-notice" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-exclamation-triangle"></i> ${t('confirm_delete_notice')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${t('confirm_delete_notice_message', { count: 0 })} <strong id="delete-count-notice">0</strong></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-danger" id="btn-confirm-delete-notice">${t('delete')}</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup Notices event listeners - Synced with Projects
 */
function setupNoticesEvents() {
    // View selected button
    $('#btn-view-selected-notice').click(function() {
        if (NoticesState.selectedIds.length === 1) {
            viewNotice(NoticesState.selectedIds[0]);
        }
    });
    
    // Refresh button
    $('#btn-refresh-notice').click(function() {
        loadNotices({ silent: true });
    });
    
    // Column toggle button
    $('#btn-toggle-columns-notice').click(function() {
        toggleColumnSelectorNotice();
    });
    
    // Close column selector
    $('#btn-close-column-selector-notice').click(function() {
        $('#column-selector-notice').hide();
    });
    
    // Reset columns
    $('#btn-reset-columns-notice').click(function() {
        resetColumnVisibilityNotice();
    });
    
    // Apply columns
    $('#btn-apply-columns-notice').click(function() {
        applyColumnVisibilityNotice();
        $('#column-selector-notice').hide();
    });
    
    // Export Excel button
    $('#btn-export-excel-notice').click(function(e) {
        e.preventDefault();
        exportNoticeToExcel();
    });
    
    // Export CSV button
    $('#btn-export-csv-notice').click(function(e) {
        e.preventDefault();
        exportNoticeToCSV();
    });
    
    // Filter: Status
    $('#filter-status-notice').change(function() {
        NoticesState.statusFilter = $(this).val();
        NoticesState.currentPage = 1;
        filterNotices();
    });
    
    // Filter: Urgency
    $('#filter-urgency-notice').change(function() {
        NoticesState.urgencyFilter = $(this).val();
        NoticesState.currentPage = 1;
        filterNotices();
    });
    
    // Search input
    $('#search-input-notice').on('input', debounce(function() {
        NoticesState.searchText = $(this).val();
        NoticesState.currentPage = 1;
        filterNotices();
    }, 500));
    
    // Clear search
    $('#btn-clear-search-notice').click(function() {
        $('#search-input-notice').val('');
        NoticesState.searchText = '';
        NoticesState.currentPage = 1;
        filterNotices();
    });
    
    // Page size change
    $('#page-size-notice').change(function() {
        NoticesState.pageSize = parseInt($(this).val());
        NoticesState.currentPage = 1;
        filterNotices();
    });
    
    // Jump to page
    $('#btn-jump-to-page-notice').click(function() {
        const page = parseInt($('#jump-to-page-notice').val());
        if (page >= 1 && page <= NoticesState.totalPages) {
            NoticesState.currentPage = page;
            filterNotices();
        } else {
            showToast('Lỗi', `Vui lòng nhập trang từ 1 đến ${NoticesState.totalPages}`, 'warning');
        }
    });
    
    // Enter key for jump to page
    $('#jump-to-page-notice').keypress(function(e) {
        if (e.which === 13) {
            $('#btn-jump-to-page-notice').click();
        }
    });
    
    // Select all checkbox
    $('#select-all-notices').change(function() {
        const isChecked = $(this).is(':checked');
        $('#notices-table-body input[type="checkbox"]').prop('checked', isChecked);
        updateSelectedIdsNotice();
    });
    
    // Close column selector when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('#column-selector-notice, #btn-toggle-columns-notice').length) {
            $('#column-selector-notice').hide();
        }
    });
    
    // Initialize column selector
    initColumnSelectorNotice();
}

/**
 * Filter notices based on current filters and pagination
 */
function filterNotices() {
    // Apply all filters
    const filtered = NoticesState.notices.filter(notice => {
        const normalizedStatus = getNormalizedNoticeStatus(notice);
        const normalizedUrgency = getNormalizedNoticeUrgency(notice);

        // Status filter
        if (NoticesState.statusFilter) {
            if (NoticesState.statusFilter !== normalizedStatus) return false;
        }
        
        // Urgency filter
        if (NoticesState.urgencyFilter) {
            if (NoticesState.urgencyFilter !== normalizedUrgency) return false;
        }
        
        // Search filter
        if (NoticesState.searchText) {
            const searchLower = normalizeNoticeSearchText(NoticesState.searchText);
            if (!getNoticeSearchText(notice).includes(searchLower)) return false;
        }
        
        return true;
    }).sort(compareNoticesForFeed);
    
    NoticesState.filteredNotices = filtered;
    NoticesState.totalRecords = filtered.length;
    NoticesState.totalPages = Math.ceil(NoticesState.totalRecords / NoticesState.pageSize) || 1;
    NoticesState.currentPage = Math.min(Math.max(NoticesState.currentPage, 1), NoticesState.totalPages);
    pruneSelectedNotices();
    
    // Apply pagination
    const start = (NoticesState.currentPage - 1) * NoticesState.pageSize;
    const end = start + NoticesState.pageSize;
    const paginatedData = filtered.slice(start, end);
    
    renderNoticesTable(paginatedData);
    updatePaginationNotice();
    updateStats(filtered);
    updateToolbarStateNotice();
    updateNoticeLastLoadedText();
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Load notices data
 */
async function loadNotices(options = {}) {
    console.log('[Notices] Loading notices...');
    
    const tbody = $('#notices-table-body');
    const silent = !!options.silent;
    const hasExistingRows = NoticesState.notices.length > 0 || $('#notices-table-body .notice-item').length > 0;
    if (!silent || !hasExistingRows) {
        tbody.html(createNoticeFeedLoadingState());
    }
    
    NoticesState.isLoading = true;
    updateToolbarStateNotice();
    
    try {
        const currentUser = AppState.currentUser || {};
        NoticesState.currentUserName = currentUser.full_name || currentUser.username || '';
        NoticesState.currentUserRole = currentUser.role || '';
        NoticesState.currentUserId = currentUser.user_id || null;

        const normalizedRole = String(NoticesState.currentUserRole || '').toLowerCase();
        let result = [];
        if ((normalizedRole === 'engineer' || normalizedRole === 'eng') && NoticesState.currentUserName) {
            result = await getAllNoticesForEngineer(NoticesState.currentUserName);
        } else {
            // Thông báo cần hiển thị toàn bộ dự án 待接收, không lọc theo user tạo.
            result = await getPendingNotices();
        }
        
        const noticeRows = Array.isArray(result)
            ? result
            : (result && Array.isArray(result.data) ? result.data : []);

        if (result && result.success === false) {
            throw new Error(result.error || 'Không thể tải thông báo');
        }

        if (noticeRows.length > 0 || (result && (Array.isArray(result) || result.success))) {
            NoticesState.notices = noticeRows
                .map(normalizeNotice)
                .filter(isNoticeNeedsClassification)
                .sort(compareNoticesForFeed);
            NoticesState.selectedIds = [];
            NoticesState.lastLoadedAt = new Date();
             
            // Calculate stats
            NoticesState.stats.total = NoticesState.notices.length;
            NoticesState.stats.pending = NoticesState.notices.length;
            NoticesState.stats.accepted = 0;
            NoticesState.stats.urgent = NoticesState.notices.filter(n => getNormalizedNoticeUrgency(n) !== 'normal').length;
             
            // Apply filters and pagination
            filterNotices();

            const scopeLabel = getNoticeScopeLabel();
            $('#notice-scope-label').text(scopeLabel);
            updateNoticeLastLoadedText();
             
            // Update global notice badge
            updateNoticeBadge(NoticesState.stats.pending);
        } else {
            NoticesState.notices = [];
            NoticesState.filteredNotices = [];
            NoticesState.totalRecords = 0;
            NoticesState.totalPages = 1;
            NoticesState.lastLoadedAt = new Date();
            tbody.html(createNoticeFeedEmptyState('Không có thông báo cần phân loại'));
            filterNotices();
        }
    } catch (error) {
        console.error('[Notices] Load error:', error);
        if (!silent || !hasExistingRows) {
            tbody.html(createNoticeFeedErrorState('Lỗi tải dữ liệu: ' + error.message));
        }
    } finally {
        NoticesState.isLoading = false;
        updateToolbarStateNotice();
    }
}

/**
 * Render notices table - Synced with Projects table format
 * @param {Array} notices - Array of notices (paginated data)
 */
function renderNoticesTable(notices) {
    const tbody = $('#notices-table-body');
    const data = notices || NoticesState.filteredNotices;
    
    if (data.length === 0) {
        tbody.html(createNoticeFeedEmptyState('Không có thông báo nào'));
        return;
    }
    
    let html = '';
    
    // Calculate starting index for this page
    const startIndex = (NoticesState.currentPage - 1) * NoticesState.pageSize;
    
    data.forEach((notice, index) => {
        const status = getNormalizedNoticeStatus(notice);
        const urgency = getNormalizedNoticeUrgency(notice);
        const trackingId = String(getNoticeValue(notice, ['Tracking ID', 'tracking_id'], '-'));
        const isSelected = NoticesState.selectedIds.includes(trackingId);
        const productName = getNoticeValue(notice, ['Tên sản phẩm', 'Sản phẩm', 'ten_san_pham'], '-');
        const spec = getNoticeValue(notice, ['Quy cách', 'quy_cach'], '');
        const planCode = getNoticeValue(notice, ['Mã bản vẽ', 'ma_ban_ve'], '');
        const productType = getNoticeValue(notice, ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], '');
        const customer = getNoticeValue(notice, ['Khách hàng', 'khach_hang'], '-');
        const engineer = getNoticeValue(notice, ['Người nhận', 'accepted_by', 'Nhân viên thiết kế', 'Kỹ sư'], getPendingReceiverText());
        const salesperson = getNoticeValue(notice, ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], '-');
        const quantity = getNoticeValue(notice, ['Số lượng', 'so_luong'], '-');
        const relativeTime = formatNoticeTime(getNoticeValue(notice, ['Ngày', 'Created_Date'], ''));
        const recordNo = startIndex + index + 1;
        const initials = getNoticeInitials(customer || productName);
        const quantityText = String(quantity || '-');
        const needsClassification = isNoticeNeedsClassification(notice);
        const itemTitle = productName && productName !== '-' ? productName : (spec || 'Chưa có tên sản phẩm');
        const itemClasses = [
            isSelected ? 'selected' : '',
            `notice-${status}`,
            `urgency-${urgency}`,
            needsClassification ? 'notice-classification' : ''
        ].filter(Boolean).join(' ');
        
        html += `
            <div class="notice-item ${itemClasses}" data-id="${trackingId}">
                <div class="notice-item-left">
                    <input type="checkbox" class="row-checkbox form-check-input" aria-label="Chọn thông báo ${trackingId}" ${isSelected ? 'checked' : ''}>
                    <div class="notice-avatar ${status === 'pending' ? 'unread' : ''}">
                        <span>${escapeHtml(initials)}</span>
                    </div>
                </div>
                <div class="notice-item-main">
                    <div class="notice-item-head">
                        <a href="#" class="view-link view-notice" data-id="${trackingId}">#${trackingId}</a>
                        ${planCode ? `<span class="notice-plan-code">${escapeHtml(String(planCode))}</span>` : ''}
                        <span class="notice-record-no">STT ${recordNo}</span>
                        <span class="notice-dot ${status === 'pending' ? '' : 'd-none'}"></span>
                    </div>
                    <div class="notice-item-title">${escapeHtml(String(itemTitle))}</div>
                    <div class="notice-item-message">
                        ${buildNoticeMessage(notice, customer, productName, status)}
                    </div>
                    <div class="notice-item-meta">
                        <span><i class="bi bi-person-badge"></i> KD: ${escapeHtml(String(salesperson))}</span>
                        <span><i class="bi bi-person-workspace"></i> KS: ${escapeHtml(String(engineer))}</span>
                        <span><i class="bi bi-box-seam"></i> SL: ${escapeHtml(quantityText)}</span>
                        ${spec ? `<span><i class="bi bi-rulers"></i> ${escapeHtml(String(spec))}</span>` : ''}
                        <span><i class="bi bi-clock"></i> ${relativeTime}</span>
                    </div>
                </div>
                <div class="notice-item-right">
                    ${needsClassification ? '<span class="notice-classification-badge"><i class="bi bi-tags"></i> Cần phân loại</span>' : ''}
                    ${productType ? `<span class="notice-product-type">${escapeHtml(String(productType))}</span>` : ''}
                    ${getNoticeUrgencyBadge(urgency)}
                    <div class="notice-actions">
                        ${needsClassification ? `
                            <button class="btn btn-sm btn-warning quick-classify-notice" data-id="${trackingId}">
                                <i class="bi bi-tags"></i> Phân loại
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-secondary quick-view-notice" data-id="${trackingId}">
                            <i class="bi bi-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    tbody.html(html);
    
    // Setup click handlers
    setupNoticesRowHandlers();
}

/**
 * Setup notice row event handlers - Synced with Projects
 */
function setupNoticesRowHandlers() {
    // Row checkbox
    $('#notices-table-body input[type="checkbox"]').change(function() {
        updateSelectedIdsNotice();
    });
    
    $('.quick-classify-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        openNoticeClassification(id);
    });
    
    // View button
    $('.quick-view-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        viewNotice(id);
    });
    
    // View link
    $('.view-notice').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        viewNotice(id);
    });
    
    // Row click for selection
    $('#notices-table-body .notice-item').click(function(e) {
        if (e.target.type !== 'checkbox' && !$(e.target).closest('.notice-actions, .view-link, button').length) {
            const checkbox = $(this).find('input[type="checkbox"]');
            checkbox.prop('checked', !checkbox.is(':checked'));
            updateSelectedIdsNotice();
        }
    });
}

/**
 * Update selected IDs for notices
 */
function updateSelectedIdsNotice() {
    NoticesState.selectedIds = [];
    
    $('#notices-table-body .notice-item').each(function() {
        const checkbox = $(this).find('input[type="checkbox"]');
        if (checkbox.is(':checked')) {
            NoticesState.selectedIds.push(String($(this).data('id')));
        }
    });
    
    // Update row styling
    $('#notices-table-body .notice-item').removeClass('selected');
    NoticesState.selectedIds.forEach(id => {
        $(`#notices-table-body .notice-item[data-id="${id}"]`).addClass('selected');
    });
    
    updateToolbarStateNotice();
    $('#notice-selection-info').text(`${NoticesState.selectedIds.length} đã chọn`);
    
    // Update select all checkbox
    const renderedItems = $('#notices-table-body .notice-item').length;
    const allChecked = NoticesState.selectedIds.length === renderedItems && renderedItems > 0;
    $('#select-all-notices').prop('checked', allChecked);
}

/**
 * Update toolbar button states
 */
function updateToolbarStateNotice() {
    const count = NoticesState.selectedIds.length;
    const selectedClassificationCount = NoticesState.selectedIds
        .map(id => findNoticeById(id))
        .filter(n => n && isNoticeNeedsClassification(n))
        .length;
    
    $('#btn-view-selected-notice').prop('disabled', count !== 1);
    
    const start = (NoticesState.currentPage - 1) * NoticesState.pageSize + 1;
    const end = Math.min(NoticesState.currentPage * NoticesState.pageSize, NoticesState.totalRecords);
    
    $('#page-info-notice').text(
        NoticesState.totalRecords > 0 
        ? `Hiển thị ${start} - ${end} của ${NoticesState.totalRecords} bản ghi`
        : 'Hiển thị 0 - 0 của 0 bản ghi'
    );
}

/**
 * Update pagination
 */
function updatePaginationNotice() {
    const pagination = $('#pagination-notice');
    
    if (NoticesState.totalPages <= 1) {
        pagination.html('');
        return;
    }
    
    pagination.html(createPagination(NoticesState.currentPage, NoticesState.totalPages));
    
    // Add click handlers
    $('.page-link').click(function(e) {
        e.preventDefault();
        const page = parseInt($(this).data('page'));
        if (page >= 1 && page <= NoticesState.totalPages) {
            NoticesState.currentPage = page;
            filterNotices();
        }
    });
}

/**
 * Update statistics display
 * @param {Array} data - Optional filtered data
 */
function updateStats(data) {
    const notices = data || NoticesState.notices;
    
    const stats = {
        total: notices.length,
        pending: notices.filter(isNoticeNeedsClassification).length,
        accepted: 0,
        urgent: notices.filter(n => getNormalizedNoticeUrgency(n) !== 'normal').length
    };
    
    $('#stat-total-notices').text(stats.total);
    $('#stat-pending-notices').text(stats.pending);
    $('#stat-urgent-notices').text(stats.urgent);
}

// ============================================
// ACTIONS
// ============================================

/**
 * Accept notice/job
 * @param {string} id - Tracking ID
 */
async function acceptNotice(id) {
    const notice = findNoticeById(id);
    if (notice && isNoticeNeedsClassification(notice)) {
        openNoticeClassification(id);
        return;
    }
    if (!notice || getNormalizedNoticeStatus(notice) !== 'pending') {
        showToast('Thông báo', 'Công việc này không còn ở trạng thái chờ nhận', 'warning');
        return;
    }
    
    showLoading('Đang nhận việc...');
    
    try {
        const engineerName = AppState.currentUser?.full_name || AppState.currentUser?.username;
        if (!engineerName) {
            throw new Error('Không xác định được người dùng hiện tại');
        }
        const result = await acceptJob(id, engineerName);
        
        if (result.success) {
            showToast('Thành công', 'Đã nhận công việc', 'success');
            loadNotices();
        } else {
            throw new Error(result.error || 'Có lỗi xảy ra');
        }
    } catch (error) {
        console.error('[Notices] Accept error:', error);
        showToast('Lỗi', error.message || 'Không thể nhận việc', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * View notice details - Updated for new modal ID
 * @param {string} id - Tracking ID
 */
async function viewNotice(id) {
    const opened = await openProjectDetailFromNotice(id);
    if (opened) {
        return;
    }

    let notice = findNoticeById(id);
    if (!notice) {
        try {
            const remote = await api.getProject(id);
            if (remote) {
                notice = normalizeNotice(remote);
            }
        } catch (e) {
            console.warn('[Notices] Cannot fetch notice detail by id:', id, e);
        }
    }
    
    if (notice) {
        openNoticeClassification(id);
    }
}

async function openProjectDetailFromNotice(id) {
    try {
        if (typeof window.viewProject !== 'function') {
            if (typeof loadScript === 'function' && !document.getElementById('projects-script')) {
                await loadScript('js/modules/projects.js');
            }
            if (typeof window.initProjectsModule === 'function') {
                window.initProjectsModule();
            }
        }

        if (typeof window.viewProject === 'function') {
            await window.viewProject(id);
            return true;
        }
    } catch (error) {
        console.warn('[Notices] Cannot open standard project detail modal:', error);
    }
    return false;
}

/**
 * Show notice modal for add
 */
function showNoticeModal() {
    $('#notice-form')[0].reset();
    $('#notice-tracking-id').val('');
    $('#modal-title-notice').text('Thêm thông báo mới');
    
    // Set default date
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $('#notice-field-ngay').val(now.toISOString().slice(0, 16));
    
    const modal = new bootstrap.Modal('#notice-modal');
    modal.show();
}

/**
 * Edit notice
 * @param {string} id - Tracking ID
 */
async function editNotice(id) {
    const notice = findNoticeById(id);
    
    if (notice) {
        $('#notice-tracking-id').val(id);
        $('#modal-title-notice').text('Sửa thông báo');
        
        // Fill form fields
        $('#notice-field-ngay').val(notice['Ngày'] || '');
        $('#notice-field-khachhang').val(notice['Khách hàng'] || '');
        $('#notice-field-nhanvienkd').val(notice['Nhân viên KD'] || '');
        $('#notice-field-sanpham').val(notice['Tên sản phẩm'] || notice['Sản phẩm'] || '');
        $('#notice-field-soluong').val(notice['Số lượng'] || '');
        $('#notice-field-kysu').val(notice['Nhân viên thiết kế'] || notice['Kỹ sư'] || notice['Người nhận'] || '');
        $('#notice-field-dokhan').val(getNormalizedNoticeUrgency(notice));
        $('#notice-field-trangthai').val(getNormalizedNoticeStatus(notice));
        
        const modal = new bootstrap.Modal('#notice-modal');
        modal.show();
    }
}

/**
 * Save notice
 */
async function saveNotice() {
    const trackingId = $('#notice-tracking-id').val();
    
    const formData = {
        'Ngày': $('#notice-field-ngay').val(),
        'Khách hàng': $('#notice-field-khachhang').val(),
        'Nhân viên KD': $('#notice-field-nhanvienkd').val(),
        'Tên sản phẩm': $('#notice-field-sanpham').val(),
        'Số lượng': $('#notice-field-soluong').val(),
        'Kỹ sư': $('#notice-field-kysu').val(),
        'Độ khẩn': $('#notice-field-dokhan').val(),
        'Trạng thái': $('#notice-field-trangthai').val()
    };
    
    // Remove empty values
    Object.keys(formData).forEach(key => {
        if (!formData[key]) delete formData[key];
    });
    
    // Add tracking ID if editing
    if (trackingId) {
        formData['Tracking ID'] = trackingId;
    }
    
    showLoading('Đang lưu thông báo...');
    
    try {
        let result;
        
        if (trackingId) {
            result = await api.updateProject(trackingId, {
                Created_Date: formData['Ngày'],
                khach_hang: formData['Khách hàng'],
                nhan_vien_kinh_doanh: formData['Nhân viên KD'],
                ten_san_pham: formData['Tên sản phẩm'],
                so_luong: formData['Số lượng'],
                nhan_vien_thiet_ke: formData['Kỹ sư'],
                urgency_level: formData['Độ khẩn']
            });
        } else {
            result = await api.createProject({
                Created_Date: formData['Ngày'],
                khach_hang: formData['Khách hàng'],
                nhan_vien_kinh_doanh: formData['Nhân viên KD'],
                ten_san_pham: formData['Tên sản phẩm'],
                so_luong: formData['Số lượng'],
                nhan_vien_thiet_ke: formData['Kỹ sư'],
                urgency_level: formData['Độ khẩn'],
                nguoi_lien_he_kh: formData['Khách hàng'] || 'N/A'
            });
        }
        
        if (result.success) {
            showToast('Thành công', trackingId ? 'Cập nhật thông báo thành công' : 'Tạo thông báo thành công', 'success');
            
            // Hide modal
            bootstrap.Modal.getInstance('#notice-modal').hide();
            
            // Reload data
            loadNotices();
        } else {
            throw new Error(result.error || 'Có lỗi xảy ra');
        }
    } catch (error) {
        console.error('[Notices] Save error:', error);
        showToast('Lỗi', error.message || 'Không thể lưu thông báo', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Show delete confirm modal
 */
function showDeleteConfirmModalNotice() {
    $('#delete-count-notice').text(NoticesState.selectedIds.length);
    
    const modal = new bootstrap.Modal('#confirm-delete-modal-notice');
    modal.show();
}

/**
 * Delete selected notices
 */
async function deleteSelectedNotices() {
    const ids = NoticesState.selectedIds;
    
    showLoading('Đang xóa thông báo...');
    
    try {
        const result = await api.deleteProjects(ids, 'admin');
        
        if (result.success) {
            showToast('Thành công', `Đã xóa ${ids.length} thông báo`, 'success');
            
            // Hide modal
            bootstrap.Modal.getInstance('#confirm-delete-modal-notice').hide();
            
            // Clear selection
            NoticesState.selectedIds = [];
            
            // Reload data
            loadNotices();
        } else {
            throw new Error(result.error || 'Có lỗi xảy ra');
        }
    } catch (error) {
        console.error('[Notices] Delete error:', error);
        showToast('Lỗi', error.message || 'Không thể xóa thông báo', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// COLUMN SELECTOR
// ============================================

/**
 * Initialize column selector for notices
 */
function initColumnSelectorNotice() {
    const body = $('#column-selector-body-notice');
    let html = '';
    
    NoticesState.columnsConfig.forEach(col => {
        const isVisible = NoticesState.visibleColumns[col.key] !== false;
        html += `
            <div class="form-check">
                <input class="form-check-input column-checkbox" type="checkbox" 
                       value="${col.key}" id="col-notice-${col.key}" ${isVisible ? 'checked' : ''}>
                <label class="form-check-label" for="col-notice-${col.key}">${col.label}</label>
            </div>
        `;
    });
    
    // Add checkbox column
    html += `
        <div class="form-check">
            <input class="form-check-input column-checkbox" type="checkbox" 
                   value="checkbox" id="col-notice-checkbox" ${NoticesState.visibleColumns.checkbox ? 'checked' : ''}>
            <label class="form-check-label" for="col-notice-checkbox">Chọn</label>
        </div>
        <div class="form-check">
            <input class="form-check-input column-checkbox" type="checkbox" 
                   value="actions" id="col-notice-actions" ${NoticesState.visibleColumns.actions ? 'checked' : ''}>
            <label class="form-check-label" for="col-notice-actions">Hành động</label>
        </div>
    `;
    
    body.html(html);
}

/**
 * Toggle column selector popup
 */
function toggleColumnSelectorNotice() {
    const selector = $('#column-selector-notice');
    selector.toggle();
}

/**
 * Reset column visibility to default
 */
function resetColumnVisibilityNotice() {
    NoticesState.columnsConfig.forEach(col => {
        NoticesState.visibleColumns[col.key] = col.default;
    });
    NoticesState.visibleColumns.checkbox = true;
    NoticesState.visibleColumns.actions = true;
    
    // Update checkboxes
    $('.column-checkbox').each(function() {
        const key = $(this).val();
        if (key === 'checkbox' || key === 'actions') {
            $(this).prop('checked', true);
        } else {
            const config = NoticesState.columnsConfig.find(c => c.key === key);
            $(this).prop('checked', config ? config.default : true);
        }
    });
    
    renderNoticesTable();
}

/**
 * Apply column visibility changes
 */
function applyColumnVisibilityNotice() {
    $('.column-checkbox').each(function() {
        const key = $(this).val();
        NoticesState.visibleColumns[key] = $(this).is(':checked');
    });
    
    renderNoticesTable();
}

// ============================================
// EXPORT
// ============================================

/**
 * Export to Excel
 */
function exportNoticeToExcel() {
    if (NoticesState.filteredNotices.length === 0) {
        showToast('Cảnh báo', 'Không có dữ liệu để xuất', 'warning');
        return;
    }
    
    showLoading('Đang xuất Excel...');
    
    try {
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(NoticesState.filteredNotices);
        XLSX.utils.book_append_sheet(wb, ws, 'Thông báo');
        XLSX.writeFile(wb, 'thong_bao_' + new Date().toISOString().slice(0, 10) + '.xlsx');
        
        showToast('Thành công', 'Đã xuất file Excel', 'success');
    } catch (error) {
        console.error('[Notices] Export error:', error);
        showToast('Lỗi', 'Không thể xuất Excel', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Export to CSV
 */
function exportNoticeToCSV() {
    if (NoticesState.filteredNotices.length === 0) {
        showToast('Cảnh báo', 'Không có dữ liệu để xuất', 'warning');
        return;
    }
    
    showLoading('Đang xuất CSV...');
    
    try {
        const headers = Object.keys(NoticesState.filteredNotices[0]);
        let csv = headers.join(',') + '\n';
        
        NoticesState.filteredNotices.forEach(row => {
            const values = headers.map(h => {
                const val = row[h] || '';
                return '"' + String(val).replace(/"/g, '""') + '"';
            });
            csv += values.join(',') + '\n';
        });
        
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'thong_bao_' + new Date().toISOString().slice(0, 10) + '.csv';
        link.click();
        
        showToast('Thành công', 'Đã xuất file CSV', 'success');
    } catch (error) {
        console.error('[Notices] Export CSV error:', error);
        showToast('Lỗi', 'Không thể xuất CSV', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// AUTO REFRESH
// ============================================

let autoRefreshInterval = null;

/**
 * Start auto refresh
 */
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        if (!NoticesState.isLoading) {
            loadNotices({ silent: true });
        }
    }, 30000);
}

/**
 * Stop auto refresh
 */
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function isNoticeRealtimeEligibleRole(role) {
    const normalized = String(role || '').toLowerCase().trim();
    return normalized === 'engineer' || normalized === 'eng' || normalized === 'admin';
}

function setupNoticeRealtimeStream() {
    if (!isNoticeRealtimeEligibleRole(NoticesState.currentUserRole)) {
        updateNoticeRealtimeStatus('Role này dùng auto refresh 30 giây', false);
        return;
    }
    connectNoticeRealtimeStream();

    window.addEventListener('beforeunload', () => {
        disconnectNoticeRealtimeStream();
        stopAutoRefresh();
    });
}

function connectNoticeRealtimeStream() {
    disconnectNoticeRealtimeStream();

    const params = {
        role: NoticesState.currentUserRole || '',
        username: NoticesState.currentUserName || '',
        user_id: NoticesState.currentUserId || ''
    };

    try {
        NoticesState.stream = openNoticeStream(params);
    } catch (error) {
        console.error('[Notices] Cannot open realtime stream:', error);
        scheduleNoticeRealtimeReconnect();
        return;
    }

    NoticesState.stream.onopen = function() {
        NoticesState.streamConnected = true;
        NoticesState.reconnectAttempts = 0;
        updateNoticeRealtimeStatus('Realtime: Đang kết nối', true);
    };

    NoticesState.stream.onmessage = function(event) {
        if (!event || !event.data) return;
        try {
            const payload = JSON.parse(event.data);
            handleRealtimeNoticeEvent(payload);
        } catch (error) {
            console.warn('[Notices] Invalid realtime payload:', error);
        }
    };

    NoticesState.stream.onerror = function() {
        NoticesState.streamConnected = false;
        updateNoticeRealtimeStatus('Realtime: Mất kết nối, đang thử lại...', false);
        disconnectNoticeRealtimeStream();
        scheduleNoticeRealtimeReconnect();
    };
}

function disconnectNoticeRealtimeStream() {
    NoticesState.streamConnected = false;
    if (NoticesState.stream) {
        try {
            NoticesState.stream.close();
        } catch (error) {
            console.warn('[Notices] Stream close warning:', error);
        }
        NoticesState.stream = null;
    }
}

function scheduleNoticeRealtimeReconnect() {
    if (NoticesState.reconnectTimer) return;
    NoticesState.reconnectAttempts += 1;
    const delay = Math.min(3000 * NoticesState.reconnectAttempts, 20000);
    NoticesState.reconnectTimer = setTimeout(() => {
        NoticesState.reconnectTimer = null;
        if (isNoticeRealtimeEligibleRole(NoticesState.currentUserRole)) {
            connectNoticeRealtimeStream();
        }
    }, delay);
}

function handleRealtimeNoticeEvent(payload) {
    if (!payload || !payload.type) return;

    if (payload.type === 'connected') {
        updateNoticeRealtimeStatus('Realtime: Đang kết nối', true);
        return;
    }

    if (payload.type === 'new_project_pending') {
        const trackingId = payload.tracking_id || payload.record?.tracking_id || '';
        showToast('Thông báo mới', `Có cập nhật dự án #${trackingId}`, 'info');
        queueRealtimeNoticeRefresh();
        return;
    }

    if (payload.type === 'job_accepted') {
        queueRealtimeNoticeRefresh();
    }
}

function queueRealtimeNoticeRefresh() {
    if (NoticesState.refreshTimer) {
        clearTimeout(NoticesState.refreshTimer);
    }
    NoticesState.refreshTimer = setTimeout(async () => {
        NoticesState.refreshTimer = null;
        if (!NoticesState.isLoading) {
            await loadNotices({ silent: true });
        }
        refreshPendingNoticeBadge();
    }, 300);
}

async function refreshPendingNoticeBadge() {
    updateNoticeBadge(NoticesState.stats.pending || 0);
}

function updateNoticeRealtimeStatus(text, connected) {
    const statusEl = $('#notice-realtime-status');
    if (!statusEl.length) return;

    const icon = connected ? 'bi-broadcast-pin' : 'bi-wifi-off';
    const compactText = String(text || '')
        .replace(/^Realtime:\s*/i, '')
        .replace(/\.{3}$/, '')
        .trim();
    statusEl.html(`<i class="bi ${icon}"></i> ${escapeHtml(compactText || 'Đang kết nối')}`);
    statusEl.removeClass('connected disconnected');
    statusEl.addClass(connected ? 'connected' : 'disconnected');
}

// ============================================
// HELPERS
// ============================================

/**
 * Get status badge HTML
 * @param {string} status - Trạng thái
 * @returns {string}
 */
function getStatusBadge(status) {
    if (!status) return '-';
    
    const classes = {
        'pending': 'danger',
        'accepted': 'success',
        'in_progress': 'warning',
        'completed': 'info'
    };
    
    const labels = {
        'pending': '待接收 / Chờ nhận',
        'accepted': 'Đã nhận',
        'in_progress': 'Đang làm',
        'completed': 'Hoàn thành'
    };
    
    const cls = classes[status] || 'secondary';
    const label = labels[status] || getNoticeStatusLabel(status);
    
    return `<span class="badge rounded-pill bg-${cls}">${label}</span>`;
}

function getNoticeStatusLabel(status) {
    const labels = {
        pending: '待接收 / Chờ nhận',
        accepted: 'Đã nhận',
        in_progress: 'Đang làm',
        completed: 'Hoàn thành'
    };
    return labels[status] || status || '-';
}

function getNormalizedNoticeStatus(notice) {
    const raw = String(
        getNoticeValue(notice, ['Trạng thái', 'status', 'is_pending', 'Trạng thái chờ'], '')
    ).toLowerCase().trim();
    if (raw === 'yes' || raw === 'pending' || raw === 'chờ nhận' || raw === '待接收') return 'pending';
    if (raw === 'no' || raw === 'accepted' || raw === 'đã nhận' || raw === '已接收') return 'accepted';
    if (raw === 'in_progress' || raw === 'đang làm') return 'in_progress';
    if (raw === 'completed' || raw === 'hoàn thành') return 'completed';
    return 'pending';
}

async function openNoticeClassification(id) {
    const notice = findNoticeById(id);
    const planCode = notice ? getNoticeValue(notice, ['Mã bản vẽ', 'ma_ban_ve'], '') : '';
    const searchValue = String(planCode || id || '').trim();

    if (typeof window.switchTab === 'function') {
        await window.switchTab('projects');
    } else {
        window.location.hash = '#projects';
    }

    setTimeout(() => {
        const searchInput = $('#search-input-project');
        if (searchInput.length && searchValue) {
            searchInput.val(searchValue).trigger('input');
        }
        setTimeout(() => {
            if (typeof window.focusProjectRowById === 'function') {
                window.focusProjectRowById(String(id), 'loaisanpham');
            }
            showToast('Thông báo', 'Đã focus dòng cần phân loại. Hãy chọn cột 产品类型 / Loại sản phẩm.', 'info');
        }, 450);
    }, 250);
}

function getNormalizedNoticeUrgency(notice) {
    const raw = String(
        getNoticeValue(notice, ['Độ khẩn', 'Tính cấp bách', 'urgency_level', 'urgency'], 'normal')
    ).toLowerCase().trim();
    if (raw === 'very_urgent' || raw === 'rất khẩn' || raw === '很急') return 'very_urgent';
    if (raw === 'urgent' || raw === 'khẩn' || raw === '急') return 'urgent';
    return 'normal';
}

function normalizeNoticeSearchText(value) {
    return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function getNoticeSearchText(notice) {
    const searchableValues = [
        getNoticeValue(notice, ['Tracking ID', 'tracking_id'], ''),
        getNoticeValue(notice, ['Khách hàng', 'khach_hang'], ''),
        getNoticeValue(notice, ['Tên sản phẩm', 'Sản phẩm', 'ten_san_pham'], ''),
        getNoticeValue(notice, ['Quy cách', 'quy_cach'], ''),
        getNoticeValue(notice, ['Mã PO', 'ma_po'], ''),
        getNoticeValue(notice, ['Mã bản vẽ', 'ma_ban_ve'], ''),
        getNoticeValue(notice, ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], ''),
        getNoticeValue(notice, ['Tình trạng hoàn thành dự án', 'Tình trạng', 'tinh_trang_hoan_thanh'], ''),
        getNoticeValue(notice, ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], ''),
        getNoticeValue(notice, ['Nhân viên thiết kế', 'Kỹ sư', 'accepted_by'], '')
    ];
    return normalizeNoticeSearchText(searchableValues.join(' '));
}

function compareNoticesForFeed(a, b) {
    const statusWeight = { pending: 0, in_progress: 1, accepted: 2, completed: 3 };
    const urgencyWeight = { very_urgent: 0, urgent: 1, normal: 2 };
    const statusDiff = (statusWeight[getNormalizedNoticeStatus(a)] ?? 9) - (statusWeight[getNormalizedNoticeStatus(b)] ?? 9);
    if (statusDiff !== 0) return statusDiff;

    const urgencyDiff = (urgencyWeight[getNormalizedNoticeUrgency(a)] ?? 9) - (urgencyWeight[getNormalizedNoticeUrgency(b)] ?? 9);
    if (urgencyDiff !== 0) return urgencyDiff;

    return getNoticeTimestamp(b) - getNoticeTimestamp(a);
}

function getNoticeTimestamp(notice) {
    const dateText = getNoticeValue(notice, ['Ngày', 'Created_Date'], '');
    const date = new Date(dateText);
    return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function pruneSelectedNotices() {
    const visibleIds = new Set(NoticesState.filteredNotices.map(n => String(getNoticeValue(n, ['Tracking ID', 'tracking_id'], ''))));
    NoticesState.selectedIds = NoticesState.selectedIds.filter(id => visibleIds.has(String(id)));
}

function getNoticeInitials(value) {
    const words = String(value || '')
        .trim()
        .split(/\s+/)
        .filter(Boolean);
    if (words.length === 0) return 'TB';
    return words.slice(0, 2).map(word => word[0]).join('').toUpperCase();
}

function buildNoticeMessage(notice, customer, productName, status) {
    if (isNoticeNeedsClassification(notice)) {
        return 'Không đoán được <strong>产品类型</strong> từ quy cách/thư mục. Hãy chọn loại sản phẩm hoặc bổ sung keyword rule.';
    }
    const safeCustomer = escapeHtml(String(customer || 'Khách hàng'));
    const safeProduct = escapeHtml(String(productName || 'sản phẩm'));
    const verb = 'cần kiểm tra cho';
    return `<strong>${safeCustomer}</strong> ${verb} <strong>${safeProduct}</strong>`;
}

function isNoticeNeedsClassification(notice) {
    const statusText = String(getNoticeValue(notice, ['Tình trạng hoàn thành dự án', 'Tình trạng', 'tinh_trang_hoan_thanh'], '')).toLowerCase();
    const productType = String(getNoticeValue(notice, ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], '')).trim();
    return !productType && (
        statusText.includes('cần phân loại sản phẩm')
        || statusText.includes('không đoán được')
        || statusText.includes('khong doan duoc')
    );
}

function updateNoticeLastLoadedText() {
    const target = $('#notice-last-updated');
    if (!target.length) return;
    if (!NoticesState.lastLoadedAt) {
        target.text('Chưa tải dữ liệu');
        return;
    }
    target.text(`Cập nhật ${formatNoticeTime(NoticesState.lastLoadedAt.toISOString())}`);
}

function getNoticeValue(notice, keys, fallback = '') {
    for (const key of keys) {
        const value = notice[key];
        if (value === undefined || value === null) continue;
        if (typeof value === 'string' && value.trim() === '') continue;
        return value;
    }
    return fallback;
}

function getPendingReceiverText() {
    return window.currentLanguage === 'zh' ? '未接收' : 'Chưa nhận';
}

function getNoticeScopeLabel() {
    return 'Thông báo cần phân loại sản phẩm';
}

function normalizeNotice(rawNotice) {
    const notice = { ...rawNotice };
    notice['Tracking ID'] = getNoticeValue(rawNotice, ['Tracking ID', 'tracking_id'], '');
    notice['Ngày'] = getNoticeValue(rawNotice, ['Ngày', 'Created_Date'], '');
    notice['Khách hàng'] = getNoticeValue(rawNotice, ['Khách hàng', 'khach_hang'], '');
    notice['Nhân viên KD'] = getNoticeValue(rawNotice, ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], '');
    notice['Tên sản phẩm'] = getNoticeValue(rawNotice, ['Tên sản phẩm', 'Sản phẩm', 'ten_san_pham'], '');
    notice['Quy cách'] = getNoticeValue(rawNotice, ['Quy cách', 'quy_cach'], '');
    notice['Số lượng'] = getNoticeValue(rawNotice, ['Số lượng', 'so_luong'], '');
    notice['Mã PO'] = getNoticeValue(rawNotice, ['Mã PO', 'ma_po'], '');
    notice['Mã bản vẽ'] = getNoticeValue(rawNotice, ['Mã bản vẽ', 'ma_ban_ve'], '');
    notice['Mã bản vẽ kỹ thuật (sau khi đặt hàng)'] = getNoticeValue(rawNotice, ['Mã bản vẽ kỹ thuật (sau khi đặt hàng)', 'ma_ban_ve_ky_thuat'], '');
    notice['Mã mẹ'] = getNoticeValue(rawNotice, ['Mã mẹ', 'Mã mẹ ', 'ma_me'], '');
    notice['Loại sản phẩm'] = getNoticeValue(rawNotice, ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], '');
    notice['Nhân viên thiết kế'] = getNoticeValue(rawNotice, ['Nhân viên thiết kế', 'Kỹ sư', 'Kỹ sư thiết kế', 'nhan_vien_thiet_ke'], '');
    notice['Người nhận'] = getNoticeValue(rawNotice, ['Người nhận', 'accepted_by'], '');
    notice['Tính cấp bách'] = getNormalizedNoticeUrgency(rawNotice);
    notice['Trạng thái'] = getNormalizedNoticeStatus(rawNotice);
    return notice;
}

function findNoticeById(id) {
    const target = String(id);
    return NoticesState.notices.find(n => String(n['Tracking ID']) === target);
}

async function acceptSelectedNotices() {
    const pendingIds = NoticesState.selectedIds
        .map(id => findNoticeById(id))
        .filter(n => n && getNormalizedNoticeStatus(n) === 'pending' && !isNoticeNeedsClassification(n))
        .map(n => n['Tracking ID']);

    if (pendingIds.length === 0) {
        showToast('Thông báo', 'Không có công việc thường để nhận. Dòng cần phân loại hãy bấm nút Phân loại.', 'warning');
        return;
    }

    const engineerName = AppState.currentUser?.full_name || AppState.currentUser?.username;
    if (!engineerName) {
        showToast('Lỗi', 'Không xác định được người dùng hiện tại', 'error');
        return;
    }

    showLoading('Đang nhận công việc đã chọn...');
    try {
        const results = await Promise.allSettled(
            pendingIds.map(trackingId => acceptJob(trackingId, engineerName))
        );
        const successCount = results.filter(result => result.status === 'fulfilled' && result.value?.success).length;

        if (successCount > 0) {
            showToast('Thành công', `Đã nhận ${successCount}/${pendingIds.length} công việc`, 'success');
        } else {
            showToast('Thông báo', 'Không có công việc nào được nhận', 'warning');
        }
        loadNotices();
    } catch (error) {
        console.error('[Notices] Bulk accept error:', error);
        showToast('Lỗi', error.message || 'Không thể nhận công việc đã chọn', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Get urgency badge HTML
 * @param {string} urgency - urgency level
 * @returns {string}
 */
function getNoticeUrgencyBadge(urgency) {
    const normalized = urgency || 'normal';
    const classes = {
        normal: 'bg-success-subtle text-success-emphasis',
        urgent: 'bg-warning-subtle text-warning-emphasis',
        very_urgent: 'bg-danger-subtle text-danger-emphasis'
    };
    return `<span class="badge rounded-pill ${classes[normalized] || 'bg-secondary-subtle text-secondary-emphasis'}">${getNoticeUrgencyLabel(normalized)}</span>`;
}

function getNoticeUrgencyLabel(urgency) {
    const labels = {
        normal: 'Thường',
        urgent: 'Khẩn',
        very_urgent: 'Rất khẩn'
    };
    return labels[urgency] || urgency || '-';
}

/**
 * Build "time ago" label from notice date
 * @param {string} dateText
 * @returns {string}
 */
function formatNoticeTime(dateText) {
    if (!dateText) return 'Không rõ thời gian';
    const date = new Date(dateText);
    if (Number.isNaN(date.getTime())) return String(dateText);

    const diffMs = Date.now() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    if (diffMinutes < 1) return 'Vừa xong';
    if (diffMinutes < 60) return `${diffMinutes} phút trước`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours} giờ trước`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return formatDate(dateText);
}

function createNoticeFeedLoadingState() {
    return `
        <div class="notice-feed-skeleton">
            <div class="notice-skeleton-item"></div>
            <div class="notice-skeleton-item"></div>
            <div class="notice-skeleton-item"></div>
        </div>
    `;
}

function createNoticeFeedEmptyState(message) {
    return `
        <div class="empty-state">
            <i class="bi bi-bell-slash"></i>
            <p class="mb-0">${escapeHtml(message)}</p>
        </div>
    `;
}

function createNoticeFeedErrorState(message) {
    return `
        <div class="empty-state text-danger">
            <i class="bi bi-exclamation-circle"></i>
            <p class="mb-0">${escapeHtml(message)}</p>
        </div>
    `;
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initNoticesModule = initNoticesModule;
window.onNoticesTabInit = function() {
    // Called when notices tab is shown
    const currentUser = AppState.currentUser || {};
    NoticesState.currentUserName = currentUser.full_name || currentUser.username || '';
    NoticesState.currentUserRole = currentUser.role || '';
    NoticesState.currentUserId = currentUser.user_id || null;

    if (isNoticeRealtimeEligibleRole(NoticesState.currentUserRole) && !NoticesState.streamConnected && !NoticesState.stream) {
        connectNoticeRealtimeStream();
    }

    if (!NoticesState.isLoading && NoticesState.notices.length === 0) {
        loadNotices();
    }
};
