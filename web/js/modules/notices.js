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
    statusFilter: 'all',
    urgencyFilter: 'all',
    searchText: '',
    isLoading: false,
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
    
    // Render the module content
    renderNoticesContent();
    
    // Setup event listeners
    setupNoticesEvents();
    
    // Load data
    loadNotices();
    
    // Auto refresh every 30 seconds
    startAutoRefresh();
}

/**
 * Render Notices module content - Synced with Projects UI
 */
function renderNoticesContent() {
    const container = document.getElementById('notices-container');
    
    container.innerHTML = `
        <!-- Optimized Toolbar -->
        <div class="card mb-3">
            <div class="card-body py-2">
                <!-- Row 1: Action Buttons -->
                <div class="row g-2 align-items-center mb-2">
                    <!-- Group 1: Main Actions -->
                    <div class="col-auto">
                        <div class="btn-group" role="group">
                            <button class="btn btn-success btn-sm" id="btn-add-notice" title="${t('add_notice')}">
                                <i class="bi bi-plus-circle"></i> ${t('add')}
                            </button>
                            <button class="btn btn-warning btn-sm" id="btn-edit-notice" disabled title="${t('edit_notice')}">
                                <i class="bi bi-pencil"></i> ${t('edit')}
                            </button>
                            <button class="btn btn-danger btn-sm" id="btn-delete-notice" disabled title="${t('delete_notice')}">
                                <i class="bi bi-trash"></i> ${t('delete')}
                            </button>
                        </div>
                    </div>
                    
                    <div class="col-auto"><div class="vr"></div></div>
                    
                    <!-- Group 2: Quick Actions -->
                    <div class="col-auto">
                        <button class="btn btn-secondary btn-sm" id="btn-refresh-notice" title="${t('refresh')}">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" id="btn-toggle-columns-notice" title="${t('toggle_columns')}">
                            <i class="bi bi-layout-columns"></i> <span class="d-none d-md-inline">${t('btn_toggle_columns')}</span>
                        </button>
                    </div>
                    
                    <div class="col-auto"><div class="vr"></div></div>
                    
                    <!-- Group 3: Export -->
                    <div class="col-auto">
                        <div class="dropdown">
                            <button class="btn btn-info btn-sm dropdown-toggle" type="button" 
                                    data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-download"></i> ${t('export')}
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
                    
                    <!-- Group 4: Search & Filters -->
                    <div class="col ms-auto">
                        <div class="d-flex float-end align-items-center gap-2">
                            <!-- Quick Status Filter -->
                            <select class="form-select form-select-sm" id="filter-status-notice" style="width: 140px;" title="${t('notice_filter_status')}">
                                <option value="">${t('notice_all_status')}</option>
                                <option value="pending">${t('status_pending_option')}</option>
                                <option value="accepted">${t('status_accepted')}</option>
                            </select>
                            
                            <!-- Quick Urgency Filter -->
                            <select class="form-select form-select-sm" id="filter-urgency-notice" style="width: 130px;" title="${t('notice_filter_urgency')}">
                                <option value="">${t('notice_all_urgency')}</option>
                                <option value="normal">${t('urgency_normal')}</option>
                                <option value="urgent">${t('urgency_urgent')}</option>
                                <option value="very_urgent">${t('urgency_very_urgent')}</option>
                            </select>
                            
                            <!-- Search Input -->
                            <div class="input-group input-group-sm">
                                <input type="text" class="form-control" id="search-input-notice" 
                                       placeholder="${t('search_placeholder')}" style="width: 200px;">
                                <button class="btn btn-outline-secondary" type="button" id="btn-clear-search-notice" title="${t('clear_search')}">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Stats Cards -->
                <div class="row g-2">
                    <div class="col-auto">
                        <div class="d-flex align-items-center gap-2">
                            <span class="bg-primary text-white px-2 py-1 rounded"><i class="bi bi-list-ul"></i> ${t('stat_total')}: <span id="stat-total-notices">0</span></span>
                            <span class="bg-danger text-white px-2 py-1 rounded"><i class="bi bi-clock"></i> ${t('stat_pending')}: <span id="stat-pending-notices">0</span></span>
                            <span class="bg-success text-white px-2 py-1 rounded"><i class="bi bi-check-circle"></i> ${t('stat_accepted')}: <span id="stat-accepted-notices">0</span></span>
                            <span class="bg-warning text-dark px-2 py-1 rounded"><i class="bi bi-exclamation-triangle"></i> ${t('stat_urgent')}: <span id="stat-urgent-notices">0</span></span>
                        </div>
                    </div>
                    <div class="col-auto ms-auto">
                        <small class="text-muted"><i class="bi bi-info-circle"></i> ${t('auto_refresh_note')}</small>
                    </div>
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

        <!-- Data Table -->
        <div class="card">
            <div class="card-body p-0">
                <div class="table-responsive" style="max-height: calc(100vh - 250px); overflow-y: auto;">
                    <table id="notices-table" class="table table-striped table-hover table-bordered mb-0" 
                           style="width: 100%; table-layout: fixed;">
                        <thead class="table-light sticky-top">
                            <tr>
                                <th class="sticky-column" style="width: 40px;"><input type="checkbox" id="select-all-notices"></th>
                                <th class="sticky-column" style="width: 50px;">${t('notice_stt')}</th>
                                <th class="sticky-column" style="width: 130px;">${t('notice_tracking_id')}</th>
                                <th style="width: 100px;">${t('notice_ngay')}</th>
                                <th style="width: 120px;">${t('notice_khachhang')}</th>
                                <th style="width: 150px;">${t('notice_sanpham')}</th>
                                <th style="width: 70px;">${t('notice_soluong')}</th>
                                <th style="width: 100px;">${t('notice_nhanvienkd')}</th>
                                <th style="width: 80px;">${t('notice_kysu')}</th>
                                <th style="width: 90px;">${t('notice_dokhan')}</th>
                                <th style="width: 100px;">${t('notice_trangthai')}</th>
                                <th class="sticky-column" style="width: 50px;">${t('notice_actions')}</th>
                            </tr>
                        </thead>
                        <tbody id="notices-table-body">
                            <!-- Data will be loaded here -->
                        </tbody>
                    </table>
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
            <div class="modal-dialog modal-lg modal-dialog-scrollable modal-fullscreen-sm-down">
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
        
        <!-- View Detail Modal -->
        <div class="modal fade" id="view-modal-notice" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable modal-fullscreen-sm-down">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title"><i class="bi bi-eye"></i> ${t('view_project_title')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="view-content-notice">
                        <!-- Content will be loaded here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('close')}</button>
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
                        <p>${t('confirm_delete_notice_message', { count: 0 })}</p>
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
    // Add button
    $('#btn-add-notice').click(function() {
        showNoticeModal();
    });
    
    // Edit button
    $('#btn-edit-notice').click(function() {
        if (NoticesState.selectedIds.length === 1) {
            editNotice(NoticesState.selectedIds[0]);
        }
    });
    
    // Delete button
    $('#btn-delete-notice').click(function() {
        if (NoticesState.selectedIds.length > 0) {
            showDeleteConfirmModalNotice();
        }
    });
    
    // Refresh button
    $('#btn-refresh-notice').click(function() {
        loadNotices();
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
    
    // Save button
    $('#btn-save-notice').click(function() {
        saveNotice();
    });
    
    // Confirm delete button
    $('#btn-confirm-delete-notice').click(function() {
        deleteSelectedNotices();
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
        // Status filter
        if (NoticesState.statusFilter) {
            const noticeStatus = notice['Trạng thái'] || notice.status || 'pending';
            if (NoticesState.statusFilter !== noticeStatus) return false;
        }
        
        // Urgency filter
        if (NoticesState.urgencyFilter) {
            const urgency = notice['Độ khẩn'] || notice.urgency || 'normal';
            if (NoticesState.urgencyFilter !== urgency) return false;
        }
        
        // Search filter
        if (NoticesState.searchText) {
            const searchLower = NoticesState.searchText.toLowerCase();
            const match = 
                (notice['Tracking ID'] || '').toLowerCase().includes(searchLower) ||
                (notice['Khách hàng'] || '').toLowerCase().includes(searchLower) ||
                (notice['Tên sản phẩm'] || notice['Sản phẩm'] || '').toLowerCase().includes(searchLower) ||
                (notice['Nhân viên KD'] || '').toLowerCase().includes(searchLower);
            if (!match) return false;
        }
        
        return true;
    });
    
    NoticesState.filteredNotices = filtered;
    NoticesState.totalRecords = filtered.length;
    NoticesState.totalPages = Math.ceil(NoticesState.totalRecords / NoticesState.pageSize) || 1;
    
    // Apply pagination
    const start = (NoticesState.currentPage - 1) * NoticesState.pageSize;
    const end = start + NoticesState.pageSize;
    const paginatedData = filtered.slice(start, end);
    
    renderNoticesTable(paginatedData);
    updatePaginationNotice();
    updateStats(filtered);
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Load notices data
 */
async function loadNotices() {
    console.log('[Notices] Loading notices...');
    
    const tbody = $('#notices-table-body');
    tbody.html(createLoadingState(12));
    
    NoticesState.isLoading = true;
    updateToolbarStateNotice();
    
    try {
        const result = await getPendingNotices();
        
        if (result && Array.isArray(result)) {
            NoticesState.notices = result;
            
            // Calculate stats
            NoticesState.stats.total = result.length;
            NoticesState.stats.pending = result.filter(n => (n['Trạng thái'] || n.status || 'pending') === 'pending').length;
            NoticesState.stats.accepted = result.filter(n => (n['Trạng thái'] || n.status) === 'accepted').length;
            NoticesState.stats.urgent = result.filter(n => (n['Độ khẩn'] || n.urgency) !== 'normal').length;
            
            // Apply filters and pagination
            filterNotices();
            
            // Update global notice badge
            updateNoticeBadge(NoticesState.stats.pending);
        } else {
            NoticesState.notices = [];
            NoticesState.filteredNotices = [];
            NoticesState.totalRecords = 0;
            NoticesState.totalPages = 1;
            tbody.html(createEmptyState('Không có thông báo nào', 12));
        }
    } catch (error) {
        console.error('[Notices] Load error:', error);
        tbody.html(createErrorState('Lỗi tải dữ liệu: ' + error.message, 12));
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
        tbody.html(createEmptyState('Không có thông báo nào', 12));
        return;
    }
    
    let html = '';
    
    // Calculate starting index for this page
    const startIndex = (NoticesState.currentPage - 1) * NoticesState.pageSize;
    
    data.forEach((notice, index) => {
        const status = notice['Trạng thái'] || notice.status || 'pending';
        const urgency = notice['Độ khẩn'] || notice.urgency || 'normal';
        const rowNum = startIndex + index + 1;
        const isSelected = NoticesState.selectedIds.includes(notice['Tracking ID']);
        
        html += `<tr class="${isSelected ? 'table-primary' : ''} notice-row urgency-${urgency}" data-id="${notice['Tracking ID']}">`;
        
        // Column: Checkbox
        if (NoticesState.visibleColumns.checkbox) {
            html += `<td class="sticky-column"><input type="checkbox" class="row-checkbox" ${isSelected ? 'checked' : ''}></td>`;
        }
        
        // Column: STT
        if (NoticesState.visibleColumns.stt) {
            html += `<td class="sticky-column">${rowNum}</td>`;
        }
        
        // Column: Tracking ID
        if (NoticesState.visibleColumns.tracking_id) {
            html += `<td class="sticky-column"><a href="#" class="view-link view-notice" data-id="${notice['Tracking ID']}">${notice['Tracking ID'] || '-'}</a></td>`;
        }
        
        // Column: Ngày
        if (NoticesState.visibleColumns.ngay) {
            html += `<td>${formatDate(notice['Ngày'])}</td>`;
        }
        
        // Column: Khách hàng
        if (NoticesState.visibleColumns.khachhang) {
            html += `<td>${escapeHtml(notice['Khách hàng'] || '')}</td>`;
        }
        
        // Column: Sản phẩm
        if (NoticesState.visibleColumns.sanpham) {
            html += `<td>${escapeHtml(notice['Tên sản phẩm'] || notice['Sản phẩm'] || '')}</td>`;
        }
        
        // Column: Số lượng
        if (NoticesState.visibleColumns.soluong) {
            html += `<td>${notice['Số lượng'] || '-'}</td>`;
        }
        
        // Column: Nhân viên KD
        if (NoticesState.visibleColumns.nhanvienkd) {
            html += `<td>${escapeHtml(notice['Nhân viên KD'] || '')}</td>`;
        }
        
        // Column: Kỹ sư
        if (NoticesState.visibleColumns.kysu) {
            html += `<td>${escapeHtml(notice['Kỹ sư'] || '')}</td>`;
        }
        
        // Column: Độ khẩn
        if (NoticesState.visibleColumns.dokhan) {
            html += `<td>${getUrgencyBadge(urgency)}</td>`;
        }
        
        // Column: Trạng thái
        if (NoticesState.visibleColumns.trangthai) {
            html += `<td>${getStatusBadge(status)}</td>`;
        }
        
        // Column: Actions (Quick actions menu)
        if (NoticesState.visibleColumns.actions) {
            html += `<td class="sticky-column">
                <div class="dropdown">
                    <button class="btn btn-sm btn-light p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="bi bi-three-dots-vertical"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        ${status === 'pending' ? 
                            `<li><a class="dropdown-item quick-accept-notice" href="#" data-id="${notice['Tracking ID']}">
                                <i class="bi bi-check-circle text-success"></i> Nhận việc
                            </a></li>` : ''
                        }
                        <li><a class="dropdown-item quick-view-notice" href="#" data-id="${notice['Tracking ID']}">
                            <i class="bi bi-eye text-info"></i> Xem chi tiết
                        </a></li>
                        <li><a class="dropdown-item quick-edit-notice" href="#" data-id="${notice['Tracking ID']}">
                            <i class="bi bi-pencil text-warning"></i> Sửa
                        </a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item quick-delete-notice text-danger" href="#" data-id="${notice['Tracking ID']}">
                            <i class="bi bi-trash"></i> Xóa
                        </a></li>
                    </ul>
                </div>
            </td>`;
        }
        
        html += '</tr>';
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
    
    // Accept button
    $('.quick-accept-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        acceptNotice(id);
    });
    
    // View button
    $('.quick-view-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        viewNotice(id);
    });
    
    // Edit button
    $('.quick-edit-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        editNotice(id);
    });
    
    // Delete button
    $('.quick-delete-notice').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        NoticesState.selectedIds = [id];
        showDeleteConfirmModalNotice();
    });
    
    // View link
    $('.view-notice').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        viewNotice(id);
    });
    
    // Row click for selection
    $('#notices-table-body tr').click(function(e) {
        if (e.target.type !== 'checkbox' && !$(e.target).closest('.dropdown').length) {
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
    
    $('#notices-table-body tr').each(function() {
        const checkbox = $(this).find('input[type="checkbox"]');
        if (checkbox.is(':checked')) {
            NoticesState.selectedIds.push($(this).data('id'));
        }
    });
    
    // Update row styling
    $('#notices-table-body tr').removeClass('table-primary');
    NoticesState.selectedIds.forEach(id => {
        $(`#notices-table-body tr[data-id="${id}"]`).addClass('table-primary');
    });
    
    updateToolbarStateNotice();
    
    // Update select all checkbox
    const allChecked = NoticesState.selectedIds.length === NoticesState.filteredNotices.length && NoticesState.filteredNotices.length > 0;
    $('#select-all-notices').prop('checked', allChecked);
}

/**
 * Update toolbar button states
 */
function updateToolbarStateNotice() {
    const count = NoticesState.selectedIds.length;
    
    $('#btn-edit-notice').prop('disabled', count !== 1);
    $('#btn-delete-notice').prop('disabled', count === 0);
    
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
        pending: notices.filter(n => (n['Trạng thái'] || n.status || 'pending') === 'pending').length,
        accepted: notices.filter(n => (n['Trạng thái'] || n.status) === 'accepted').length,
        urgent: notices.filter(n => (n['Độ khẩn'] || n.urgency) !== 'normal').length
    };
    
    $('#stat-total-notices').text(stats.total);
    $('#stat-pending-notices').text(stats.pending);
    $('#stat-accepted-notices').text(stats.accepted);
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
    if (!confirm('Bạn có muốn nhận công việc này?')) {
        return;
    }
    
    showLoading('Đang nhận việc...');
    
    try {
        const engineerName = AppState.currentUser?.full_name || AppState.currentUser?.username;
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
    const notice = NoticesState.notices.find(n => n['Tracking ID'] === id);
    
    if (notice) {
        // Lọc bỏ key trùng lặp: chỉ hiển thị key người dùng cuối, không hiển thị key kỹ thuật
        const preferredKeys = {
            'Ngày': 'Ngày khởi tạo',
            'is_pending': 'Trạng thái chờ',
            'accepted_by': 'Người nhận',
            'accepted_at': 'Thời gian nhận',
            'user_id': 'User ID',
            'urgency_level': 'Mức độ khẩn cấp',
            'desired_solution_time': 'Thời gian hoàn thành kế hoạch'
        };
        
        const displayData = {};
        
        for (const [key, value] of Object.entries(notice)) {
            if (value !== undefined && value !== null && value !== '') {
                // Nếu key là key kỹ thuật và có key người dùng cuối thì bỏ qua
                if (preferredKeys[key] && notice[preferredKeys[key]] !== undefined) {
                    continue;
                }
                displayData[key] = value;
            }
        }
        
        let html = '<div class="detail-section">';
        
        for (const [key, value] of Object.entries(displayData)) {
            html += `
                <div class="detail-item">
                    <strong>${key}:</strong>
                    <span>${escapeHtml(String(value))}</span>
                </div>
            `;
        }
        
        html += '</div>';
        
        $('#view-content-notice').html(html);
        
        const modal = new bootstrap.Modal('#view-modal-notice');
        modal.show();
    }
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
    const notice = NoticesState.notices.find(n => n['Tracking ID'] === id);
    
    if (notice) {
        $('#notice-tracking-id').val(id);
        $('#modal-title-notice').text('Sửa thông báo');
        
        // Fill form fields
        $('#notice-field-ngay').val(notice['Ngày'] || '');
        $('#notice-field-khachhang').val(notice['Khách hàng'] || '');
        $('#notice-field-nhanvienkd').val(notice['Nhân viên KD'] || '');
        $('#notice-field-sanpham').val(notice['Tên sản phẩm'] || notice['Sản phẩm'] || '');
        $('#notice-field-soluong').val(notice['Số lượng'] || '');
        $('#notice-field-kysu').val(notice['Kỹ sư'] || '');
        $('#notice-field-dokhan').val(notice['Độ khẩn'] || 'normal');
        $('#notice-field-trangthai').val(notice['Trạng thái'] || 'pending');
        
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
            result = await api.updateNotice(trackingId, formData);
        } else {
            result = await api.createNotice(formData);
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
        const result = await api.deleteNotices(ids);
        
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
            loadNotices();
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
        'pending': 'Chờ duyệt',
        'accepted': 'Đã nhận',
        'in_progress': 'Đang làm',
        'completed': 'Hoàn thành'
    };
    
    const cls = classes[status] || 'secondary';
    const label = labels[status] || status;
    
    return `<span class="badge bg-${cls}">${label}</span>`;
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initNoticesModule = initNoticesModule;
window.onNoticesTabInit = function() {
    // Called when notices tab is shown
    if (!NoticesState.isLoading && NoticesState.notices.length === 0) {
        loadNotices();
    }
};
