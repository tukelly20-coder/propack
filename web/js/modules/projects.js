/**
 * Projects Module
 * Quản lý danh sách dự án - Extracted from index.html
 */

// ============================================
// STATE
// ============================================

const ProjectsState = {
    projects: [],
    currentPage: 1,
    pageSize: 50,
    totalRecords: 0,
    totalPages: 1,
    selectedIds: [],
    isLoading: false,
    searchText: '',
    // Quick filters
    filterStatus: '',
    filterUrgency: '',
    filterCustomer: '',
    // Customers list for dropdown
    customers: [],
    // Column visibility
    visibleColumns: {
        'stt': true,
        'tracking_id': true,
        'ngay': true,
        'khachhang': true,
        'nhanvienkd': true,
        'tensanpham': true,
        'quycach': true,
        'lienhe': true,
        'soluong': true,
        'mapo': true,
        'mabave': true,
        'mabavkythuat': true,
        'mame': true,
        'loaisanpham': true,
        'kysu': true,
        'tinhtrang': true,
        'dokhan': true,
        'tg_mongmuon': true,
        'tg_hoanthanh': true,
        'trangthai': true,
        'nguoinhan': true
    },
    // Available columns config
    columnsConfig: [
        { key: 'stt', label: 'STT', default: true },
        { key: 'tracking_id', label: 'Tracking ID', default: true },
        { key: 'ngay', label: 'Ngày', default: true },
        { key: 'khachhang', label: 'Khách hàng', default: true },
        { key: 'nhanvienkd', label: 'Nhân viên KD', default: true },
        { key: 'tensanpham', label: 'Tên sản phẩm', default: true },
        { key: 'quycach', label: 'Quy cách', default: true },
        { key: 'lienhe', label: 'Người liên hệ (KH)', default: true },
        { key: 'soluong', label: 'Số lượng', default: true },
        { key: 'mapo', label: 'Mã PO', default: true },
        { key: 'mabavkythuat', label: 'Mã bản vẽ KT', default: true },
        { key: 'mabave', label: 'Mã bản vẽ', default: true },
        { key: 'mame', label: 'Mã mẹ', default: true },
        { key: 'loaisanpham', label: 'Loại sản phẩm', default: false },
        { key: 'dokhan', label: 'Độ khẩn', default: true },
        { key: 'tinhtrang', label: 'Tình trạng', default: true },
        { key: 'kysu', label: 'Kỹ sư', default: false },
        { key: 'tg_mongmuon', label: 'TG mong muốn', default: false },
        { key: 'tg_hoanthanh', label: 'TG hoàn thành', default: false },
        { key: 'trangthai', label: 'Trạng thái', default: true },
        { key: 'nguoinhan', label: 'Người nhận', default: false }
    ]
};

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize Projects module
 */
function initProjectsModule() {
    console.log('[Projects] Initializing...');
    
    // Render the module content
    renderProjectsContent();
    
    // Translate the rendered content based on current language
    if (typeof translatePage === 'function') {
        translatePage();
    }
    
    // Setup event listeners
    setupProjectsEvents();
    
    // Setup language change listener
    setupProjectsLanguageListener();
    
    // Pre-load customers for dropdown
    loadCustomers();
    
    // Load data
    loadProjects();
}

/**
 * Render Projects module content
 */
function renderProjectsContent() {
    const container = document.getElementById('projects-container');
    
    container.innerHTML = `
        <!-- Optimized Toolbar -->
        <div class="card mb-3">
            <div class="card-body py-2">
                <!-- Row 1: Action Buttons -->
                <div class="row g-2 align-items-center mb-2">
                    <!-- Group 1: Main Actions -->
                    <div class="col-auto">
                        <div class="btn-group" role="group">
                            <button class="btn btn-success btn-sm" id="btn-add-project" title="${t('add_project')}">
                                <i class="bi bi-plus-circle"></i> <span data-i18n="add">${t('add')}</span>
                            </button>
                            <button class="btn btn-warning btn-sm" id="btn-edit-project" disabled title="${t('edit_project')}">
                                <i class="bi bi-pencil"></i> <span data-i18n="edit">${t('edit')}</span>
                            </button>
                            <button class="btn btn-danger btn-sm" id="btn-delete-project" disabled title="${t('delete_project')}">
                                <i class="bi bi-trash"></i> <span data-i18n="delete">${t('delete')}</span>
                            </button>
                        </div>
                    </div>
                    
                    <div class="col-auto"><div class="vr"></div></div>
                    
                    <!-- Group 2: Quick Actions -->
                    <div class="col-auto">
                        <button class="btn btn-secondary btn-sm" id="btn-refresh-project" title="${t('refresh_projects')}">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" id="btn-toggle-columns" title="${t('toggle_columns')}">
                            <i class="bi bi-layout-columns"></i> <span class="d-none d-md-inline" data-i18n="btn_toggle_columns">${t('btn_toggle_columns')}</span>
                        </button>
                    </div>
                    
                    <div class="col-auto"><div class="vr"></div></div>
                    
                    <!-- Group 3: Export -->
                    <div class="col-auto">
                        <div class="dropdown">
                            <button class="btn btn-info btn-sm dropdown-toggle" type="button" 
                                    data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-download"></i> <span data-i18n="export">${t('export')}</span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" id="btn-export-excel-project">
                                    <i class="bi bi-file-earmark-excel text-success"></i> <span data-i18n="export_excel">${t('export_excel')}</span>
                                </a></li>
                                <li><a class="dropdown-item" href="#" id="btn-export-csv-project">
                                    <i class="bi bi-file-earmark-text text-primary"></i> <span data-i18n="export_csv">${t('export_csv')}</span>
                                </a></li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Group 4: Search & Filters -->
                    <div class="col ms-auto">
                        <div class="d-flex float-end align-items-center gap-2">
                            <!-- Quick Status Filter -->
                            <select class="form-select form-select-sm" id="filter-status" style="width: 140px;" title="${t('filter_status')}">
                                <option value="">${t('all_status')}</option>
                                <option value="pending">${t('status_pending')}</option>
                                <option value="in_progress">${t('status_in_progress')}</option>
                                <option value="completed">${t('status_completed')}</option>
                            </select>
                            
                            <!-- Quick Urgency Filter -->
                            <select class="form-select form-select-sm" id="filter-urgency" style="width: 130px;" title="${t('filter_urgency')}">
                                <option value="">${t('all_urgency')}</option>
                                <option value="normal">${t('urgency_normal')}</option>
                                <option value="urgent">${t('urgency_urgent')}</option>
                                <option value="very_urgent">${t('urgency_very_urgent')}</option>
                            </select>
                            
                            <!-- Search Input -->
                            <div class="input-group input-group-sm">
                                <input type="text" class="form-control" id="search-input-project" 
                                       placeholder="${t('search_placeholder')}" data-i18n-placeholder="search_placeholder" style="width: 200px;">
                                <button class="btn btn-outline-secondary" type="button" id="btn-clear-search" title="${t('clear_search')}">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Column Visibility Dropdown (Hidden by default) -->
        <div class="column-selector-popup" id="column-selector" style="display: none;">
            <div class="column-selector-header">
                <h6 class="mb-0"><i class="bi bi-layout-columns"></i> <span data-i18n="column_selector_title">${t('column_selector_title')}</span></h6>
                <button type="button" class="btn-close" id="btn-close-column-selector"></button>
            </div>
            <div class="column-selector-body" id="column-selector-body">
                <!-- Generated by JS -->
            </div>
            <div class="column-selector-footer">
                <button class="btn btn-sm btn-outline-secondary" id="btn-reset-columns" data-i18n="column_reset">${t('column_reset')}</button>
                <button class="btn btn-sm btn-primary" id="btn-apply-columns" data-i18n="column_apply">${t('column_apply')}</button>
            </div>
        </div>

        <!-- Data Table -->
        <div class="card">
            <div class="card-body p-0">
                <div class="table-responsive" style="max-height: calc(100vh - 280px); overflow-y: auto;">
                    <table id="projects-table" class="table table-striped table-hover table-bordered mb-0" 
                           style="width: 100%; table-layout: fixed;">
                        <thead class="table-light">
                            <tr>
                                <th style="width: 50px;" data-i18n="col_stt">${t('col_stt')}</th>
                                <th style="width: 130px;" data-i18n="col_tracking_id">${t('col_tracking_id')}</th>
                                <th style="width: 100px;" data-i18n="col_ngay">${t('col_ngay')}</th>
                                <th style="width: 120px;" data-i18n="col_khachhang">${t('col_khachhang')}</th>
                                <th style="width: 100px;" data-i18n="col_nhanvienkd">${t('col_nhanvienkd')}</th>
                                <th style="width: 150px;" data-i18n="col_tensanpham">${t('col_tensanpham')}</th>
                                <th style="width: 120px;" data-i18n="col_quycach">${t('col_quycach')}</th>
                                <th style="width: 100px;" data-i18n="col_lienhe_kh">${t('col_lienhe_kh')}</th>
                                <th style="width: 70px;" data-i18n="col_soluong">${t('col_soluong')}</th>
                                <th style="width: 100px;" data-i18n="col_mapo">${t('col_mapo')}</th>
                                <th style="width: 120px;" data-i18n="col_mabavkythuat">${t('col_mabavkythuat')}</th>
                                <th style="width: 120px;" data-i18n="col_mabave">${t('col_mabave')}</th>
                                <th style="width: 100px;" data-i18n="col_mame">${t('col_mame')}</th>
                                <th style="width: 100px;" data-i18n="col_loaisanpham">${t('col_loaisanpham')}</th>
                                <th style="width: 90px;" data-i18n="col_dokhan">${t('col_dokhan')}</th>
                                <th style="width: 100px;" data-i18n="col_tinhtrang">${t('col_tinhtrang')}</th>
                                <th style="width: 80px;" data-i18n="col_kysu">${t('col_kysu')}</th>
                                <th style="width: 140px;" data-i18n="col_tg_mongmuon">${t('col_tg_mongmuon')}</th>
                                <th style="width: 140px;" data-i18n="col_tg_hoanthanh">${t('col_tg_hoanthanh')}</th>
                                <th style="width: 100px;" data-i18n="col_trangthai">${t('col_trangthai')}</th>
                                <th style="width: 100px;" data-i18n="col_nguoinhan">${t('col_nguoinhan')}</th>
                                <th style="width: 50px;" data-i18n="col_actions">${t('col_actions')}</th>
                            </tr>
                        </thead>
                        <tbody id="projects-table-body">
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
                        <span id="page-info-project">${t('page_info', { start: 0, end: 0, total: 0 })}</span>
                    </div>
                    <div class="col-auto ms-auto">
                        <nav>
                            <ul class="pagination mb-0" id="pagination-project">
                                <!-- Pagination will be generated here -->
                            </ul>
                        </nav>
                    </div>
                    <div class="col-auto">
                        <div class="d-flex align-items-center gap-2">
                            <select class="form-select form-select-sm" id="page-size-project" style="width: auto;">
                                <option value="10">10 ${t('per_page')}</option>
                                <option value="25">25 ${t('per_page')}</option>
                                <option value="50" selected>50 ${t('per_page')}</option>
                                <option value="100">100 ${t('per_page')}</option>
                            </select>
                            <span class="text-muted">|</span>
                            <div class="input-group input-group-sm" style="width: 120px;">
                                <input type="number" class="form-control" id="jump-to-page" 
                                       placeholder="${t('page')}" data-i18n-placeholder="page" min="1">
                                <button class="btn btn-outline-secondary" type="button" id="btn-jump-to-page" title="${t('jump_to_page')}" data-i18n-title="jump_to_page">
                                    <i class="bi bi-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Add/Edit Modal -->
        <div class="modal fade" id="project-modal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="modal-title-project">${t('add_project_title')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="project-form">
                            <input type="hidden" id="tracking-id">
                            
                            <!-- Thông tin cơ bản -->
                            <div class="section-header">
                                <h6 class="section-title">${t('basic_info')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">${t('form_ngay_khoitao')}</label>
                                    <input type="datetime-local" class="form-control" id="field-ngay">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_khachhang_required')}</label>
                                    <div class="row g-2">
                                        <div class="col-md-6">
                                            <select class="form-select" id="field-khachhang-select">
                                                <option value="">${t('select_customer')}</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <input type="text" class="form-control" id="field-khachhang"
                                                   placeholder="Nhập khách hàng">
                                        </div>
                                    </div>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_nhanvienkd')}</label>
                                    <input type="text" class="form-control" id="field-nhanvienkd">
                                </div>
                            </div>
                            
                            <!-- Thông tin sản phẩm -->
                            <div class="section-header">
                                <h6 class="section-title">${t('product_info')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">${t('form_tensanpham_required')}</label>
                                    <input type="text" class="form-control" id="field-tensanpham">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_quycach')}</label>
                                    <input type="text" class="form-control" id="field-quycach">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_lienhe_kh')}</label>
                                    <input type="text" class="form-control" id="field-lienhe">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_soluong')}</label>
                                    <input type="number" class="form-control" id="field-soluong">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_mapo')}</label>
                                    <input type="text" class="form-control" id="field-mapo">
                                </div>
                            </div>
                            
                            <!-- Mã bản vẽ -->
                            <div class="section-header drawing-section">
                                <h6 class="section-title">${t('drawing_codes')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label">${t('form_mabave_chinh')}</label>
                                    <input type="text" class="form-control" id="field-mabave_chinh">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('form_mabave')}</label>
                                    <input type="text" class="form-control" id="field-mabave">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('form_mabavkythuat')}</label>
                                    <input type="text" class="form-control" id="field-mabavkythuat">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('form_mame')}</label>
                                    <input type="text" class="form-control" id="field-mame">
                                </div>
                            </div>
                            
                            <!-- Thông tin kỹ thuật -->
                            <div class="section-header">
                                <h6 class="section-title">${t('technical_info')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">${t('form_loaisanpham')}</label>
                                    <select class="form-select" id="field-loaisanpham">
                                        <option value="">${t('select_loaisanpham')}</option>
                                        <option value="SJT散件图">SJT - ${t('loaisanpham_sjt')}</option>
                                        <option value="WLJ物料架">WLJ - ${t('loaisanpham_wlj')}</option>
                                        <option value="ZZC周转车">ZZC - ${t('loaisanpham_zzc')}</option>
                                        <option value="GZT工作台">GZT - ${t('loaisanpham_gzt')}</option>
                                        <option value="WCP无尘棚">WCP - ${t('loaisanpham_wcp')}</option>
                                        <option value="LSX流水线">LSX - ${t('loaisanpham_lsx')}</option>
                                        <option value="ZWJ转弯机">ZWJ - ${t('loaisanpham_zwj')}</option>
                                        <option value="GZL改造类">GZL - ${t('loaisanpham_gzl')}</option>
                                        <option value="BSX倍速线">BSX - ${t('loaisanpham_bsx')}</option>
                                        <option value="WLL围栏类">WLL - ${t('loaisanpham_wll')}</option>
                                        <option value="GTX滚筒线">GTX - ${t('loaisanpham_gtx')}</option>
                                        <option value="ZHT展会图">ZHT - ${t('loaisanpham_zht')}</option>
                                        <option value="LHX老化线">LHX - ${t('loaisanpham_lhx')}</option>
                                    </select>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_kysu')}</label>
                                    <input type="text" class="form-control" id="field-kysu">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_tinhtrang')}</label>
                                    <input type="text" class="form-control" id="field-tinhtrang">
                                </div>
                            </div>
                            
                            <!-- Thời gian & Độ khẩn -->
                            <div class="section-header">
                                <h6 class="section-title">${t('time_urgency')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">${t('form_capbach')}</label>
                                    <select class="form-select" id="field-capbach">
                                        <option value="normal">${t('urgency_normal_option')}</option>
                                        <option value="urgent">${t('urgency_urgent_option')}</option>
                                        <option value="very_urgent">${t('urgency_very_urgent_option')}</option>
                                    </select>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_tg_mongmuon')}</label>
                                    <input type="datetime-local" class="form-control" id="field-tg-mongmuon">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_tg_hoanthanh')}</label>
                                    <input type="datetime-local" class="form-control" id="field-tg-hoanthanh">
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-primary" id="btn-save-project">${t('save')}</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- View Detail Modal -->
        <div class="modal fade" id="view-modal-project" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title"><i class="bi bi-eye"></i> ${t('view_project_title')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="view-content-project">
                        <!-- Content will be loaded here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('close')}</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Confirm Delete Modal -->
        <div class="modal fade" id="confirm-delete-modal-project" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-exclamation-triangle"></i> <span data-i18n="confirm_delete">${t('confirm_delete')}</span></h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><span data-i18n="confirm_delete_message">${t('confirm_delete_message', { count: 0 })}</span></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-danger" id="btn-confirm-delete-project">${t('delete')}</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup Projects event listeners
 */
function setupProjectsEvents() {
    // Add button
    $('#btn-add-project').click(function() {
        showProjectModal();
    });
    
    // Edit button
    $('#btn-edit-project').click(function() {
        if (ProjectsState.selectedIds.length === 1) {
            editProject(ProjectsState.selectedIds[0]);
        }
    });
    
    // Delete button
    $('#btn-delete-project').click(function() {
        if (ProjectsState.selectedIds.length > 0) {
            showDeleteConfirmModal();
        }
    });
    
    // Refresh button
    $('#btn-refresh-project').click(function() {
        loadProjects();
    });
    
    // Column toggle button
    $('#btn-toggle-columns').click(function() {
        toggleColumnSelector();
    });
    
    // Close column selector
    $('#btn-close-column-selector').click(function() {
        $('#column-selector').hide();
    });
    
    // Reset columns
    $('#btn-reset-columns').click(function() {
        resetColumnVisibility();
    });
    
    // Apply columns
    $('#btn-apply-columns').click(function() {
        applyColumnVisibility();
        $('#column-selector').hide();
    });
    
    // Export Excel button
    $('#btn-export-excel-project').click(function(e) {
        e.preventDefault();
        exportToExcel();
    });
    
    // Export CSV button
    $('#btn-export-csv-project').click(function(e) {
        e.preventDefault();
        exportToCSV();
    });
    
    // Filter: Status
    $('#filter-status').change(function() {
        ProjectsState.filterStatus = $(this).val();
        ProjectsState.currentPage = 1;
        loadProjects();
    });
    
    // Filter: Urgency
    $('#filter-urgency').change(function() {
        ProjectsState.filterUrgency = $(this).val();
        ProjectsState.currentPage = 1;
        loadProjects();
    });
    
    // Search input
    $('#search-input-project').on('input', debounce(function() {
        ProjectsState.searchText = $(this).val();
        ProjectsState.currentPage = 1;
        loadProjects();
    }, 500));
    
    // Clear search
    $('#btn-clear-search').click(function() {
        $('#search-input-project').val('');
        ProjectsState.searchText = '';
        ProjectsState.currentPage = 1;
        loadProjects();
    });
    
    // Page size change
    $('#page-size-project').change(function() {
        ProjectsState.pageSize = parseInt($(this).val());
        ProjectsState.currentPage = 1;
        loadProjects();
    });
    
    // Jump to page
    $('#btn-jump-to-page').click(function() {
        const page = parseInt($('#jump-to-page').val());
        if (page >= 1 && page <= ProjectsState.totalPages) {
            ProjectsState.currentPage = page;
            loadProjects();
        } else {
            showToast(t('error'), t('validation_invalid_page', { max: ProjectsState.totalPages }), 'warning');
        }
    });
    
    // Enter key for jump to page
    $('#jump-to-page').keypress(function(e) {
        if (e.which === 13) {
            $('#btn-jump-to-page').click();
        }
    });
    
    // Save button
    $('#btn-save-project').click(function() {
        saveProject();
    });
    
    // Confirm delete button
    $('#btn-confirm-delete-project').click(function() {
        deleteSelectedProjects();
    });
    
    // Close column selector when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('#column-selector, #btn-toggle-columns').length) {
            $('#column-selector').hide();
        }
    });
    
    // Initialize column selector
    initColumnSelector();
}

/**
 * Setup language change listener for Projects module
 */
function setupProjectsLanguageListener() {
    window.addEventListener('languageChanged', function(e) {
        console.log('[Projects] Language changed:', e.detail.language);
        // Update all dynamic text in the module
        updateProjectsI18n();
    });
}

/**
 * Update all i18n text in Projects module
 */
function updateProjectsI18n() {
    // Update filter options
    updateProjectsFilterOptions();
    
    // Update column selector
    initColumnSelector();
    
    // Update page info
    updateToolbarState();
    
    // Update modal titles
    const modalTitle = $('#modal-title-project');
    if (modalTitle.length) {
        const isEdit = $('#tracking-id').val();
        modalTitle.text(isEdit ? t('edit_project_title') : t('add_project_title'));
    }
    
    // Update view modal title
    const viewModalTitle = $('#view-modal-project .modal-title');
    if (viewModalTitle.length) {
        viewModalTitle.html('<i class="bi bi-eye"></i> ' + t('view_project_title'));
    }
    
    // Update urgency badge labels
    renderProjectsTable();
    
    // Update toolbar buttons
    updateToolbarButtonsI18n();
    
    // Update quick action dropdown
    updateQuickActionsI18n();
    
    // Update delete modal
    updateDeleteModalI18n();
}

/**
 * Update toolbar buttons with i18n
 */
function updateToolbarButtonsI18n() {
    // Add button
    const btnAdd = $('#btn-add-project');
    if (btnAdd.length) {
        btnAdd.html('<i class="bi bi-plus-circle"></i> ' + t('add'));
        btnAdd.attr('title', t('add_project'));
    }
    
    // Edit button
    const btnEdit = $('#btn-edit-project');
    if (btnEdit.length) {
        btnEdit.html('<i class="bi bi-pencil"></i> ' + t('edit'));
        btnEdit.attr('title', t('edit_project'));
    }
    
    // Delete button
    const btnDelete = $('#btn-delete-project');
    if (btnDelete.length) {
        btnDelete.html('<i class="bi bi-trash"></i> ' + t('delete'));
        btnDelete.attr('title', t('delete_project'));
    }
    
    // Refresh button
    const btnRefresh = $('#btn-refresh-project');
    if (btnRefresh.length) {
        btnRefresh.attr('title', t('refresh_projects'));
    }
    
    // Toggle columns button
    const btnColumns = $('#btn-toggle-columns');
    if (btnColumns.length) {
        btnColumns.html('<i class="bi bi-layout-columns"></i> <span class="d-none d-md-inline">' + t('btn_toggle_columns') + '</span>');
        btnColumns.attr('title', t('toggle_columns'));
    }
    
    // Export button text
    const exportBtn = $('#projects-container .dropdown-toggle');
    if (exportBtn.length) {
        exportBtn.html('<i class="bi bi-download"></i> ' + t('export'));
    }
    
    // Search input placeholder
    const searchInput = $('#search-input-project');
    if (searchInput.length) {
        searchInput.attr('placeholder', t('search_placeholder'));
    }
}

/**
 * Update quick actions dropdown with i18n
 */
function updateQuickActionsI18n() {
    // This will be called when rendering the table
    // The labels are already set in renderProjectsTable
}

/**
 * Update delete modal with i18n
 */
function updateDeleteModalI18n() {
    const deleteModal = $('#confirm-delete-modal-project');
    if (deleteModal.length) {
        deleteModal.find('.modal-title').html('<i class="bi bi-exclamation-triangle"></i> ' + t('confirm_delete'));
    }
}

/**
 * Update filter options with i18n
 */
function updateProjectsFilterOptions() {
    // Status filter
    const statusFilter = $('#filter-status');
    if (statusFilter.length) {
        statusFilter.find('option').eq(0).text(t('all_status'));
        statusFilter.find('option').eq(1).text(t('status_pending'));
        statusFilter.find('option').eq(2).text(t('status_in_progress'));
        statusFilter.find('option').eq(3).text(t('status_completed'));
    }
    
    // Urgency filter
    const urgencyFilter = $('#filter-urgency');
    if (urgencyFilter.length) {
        urgencyFilter.find('option').eq(0).text(t('all_urgency'));
        urgencyFilter.find('option').eq(1).text(t('urgency_normal'));
        urgencyFilter.find('option').eq(2).text(t('urgency_urgent'));
        urgencyFilter.find('option').eq(3).text(t('urgency_very_urgent'));
    }
    
    // Page size options
    const pageSizeSelect = $('#page-size-project');
    if (pageSizeSelect.length) {
        const currentVal = pageSizeSelect.val();
        pageSizeSelect.find('option').each(function(i) {
            const val = [10, 25, 50, 100][i];
            if (val) {
                $(this).text(val + ' ' + t('per_page'));
            }
        });
        pageSizeSelect.val(currentVal);
    }
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Load projects data
 */
async function loadProjects() {
    console.log('[Projects] Loading projects...');
    
    const tbody = $('#projects-table-body');
    tbody.html(createLoadingState(22));
    
    ProjectsState.isLoading = true;
    updateToolbarState();
    
    try {
        let result;
        
        if (ProjectsState.searchText) {
            result = await api.searchProjects(
                ProjectsState.searchText,
                [],
                ProjectsState.currentPage,
                ProjectsState.pageSize
            );
        } else {
            result = await api.getProjects({
                page: ProjectsState.currentPage,
                limit: ProjectsState.pageSize
            });
        }
        
        if (result && result.data) {
            ProjectsState.projects = result.data || [];
            ProjectsState.totalRecords = result.total || 0;
            ProjectsState.totalPages = Math.ceil(ProjectsState.totalRecords / ProjectsState.pageSize) || 1;
            
            renderProjectsTable();
            updatePagination();
        } else {
            ProjectsState.projects = [];
            ProjectsState.totalRecords = 0;
            ProjectsState.totalPages = 1;
            tbody.html(createEmptyState(t('no_data_projects'), 22));
        }
    } catch (error) {
        console.error('[Projects] Load error:', error);
        tbody.html(createErrorState(t('load_error_projects') + ': ' + error.message, 22));
    } finally {
        ProjectsState.isLoading = false;
        updateToolbarState();
    }
}

/**
 * Render projects table
 */
function renderProjectsTable() {
    const tbody = $('#projects-table-body');
    
    if (ProjectsState.projects.length === 0) {
        tbody.html(createEmptyState(t('no_data_projects'), 23));
        return;
    }
    
    let html = '';
    const colKeys = [
        'stt', 'tracking_id', 'ngay', 'khachhang', 'nhanvienkd', 
        'tensanpham', 'quycach', 'lienhe', 'soluong', 'mapo', 'mabave', 
        'mabavkythuat', 'mame', 'loaisanpham', 'kysu', 'tinhtrang', 'dokhan', 
        'tg_mongmuon', 'tg_hoanthanh', 'trangthai', 'nguoinhan', 'actions'
    ];
    
    // Map key to data field
    const keyToField = {
        'stt': 'STT',
        'tracking_id': 'Tracking ID',
        'ngay': 'Ngày',
        'khachhang': 'Khách hàng',
        'nhanvienkd': 'Nhân viên KD',
        'tensanpham': 'Tên sản phẩm',
        'quycach': 'Quy cách',
        'lienhe': 'Người liên hệ (KH)',
        'soluong': 'Số lượng',
        'mapo': 'Mã PO',
        'mabavkythuat': 'Mã bản vẽ KT',
        'mabave': 'Mã bản vẽ',
        'mame': 'Mã mẹ',
        'loaisanpham': 'Loại sản phẩm',
        'kysu': 'Kỹ sư',
        'tinhtrang': 'Tình trạng',
        'dokhan': 'Độ khẩn',
        'tg_mongmuon': 'TG mong muốn',
        'tg_hoanthanh': 'TG hoàn thành',
        'trangthai': 'Trạng thái',
        'nguoinhan': 'Người nhận'
    };

    const getProjectValue = (project, keys, fallback = '') => {
        for (const key of keys) {
            const value = project[key];
            if (value === undefined || value === null) continue;
            if (typeof value === 'string' && value.trim() === '') continue;
            return value;
        }
        return fallback;
    };

    const getStatusText = (rawStatus) => {
        const status = String(rawStatus || '').toLowerCase().trim();
        const isZh = window.currentLanguage === 'zh';
        if (status === 'yes' || status === 'pending') {
            return isZh ? '待接收' : 'Chờ nhận';
        }
        if (status === 'no' || status === 'accepted') {
            return isZh ? '已接收' : 'Đã nhận';
        }
        return rawStatus || '-';
    };

    const getPendingReceiverText = () => {
        return window.currentLanguage === 'zh' ? '未接收' : 'Chưa nhận';
    };

    const getProjectStatusBadge = (rawStatus) => {
        const status = String(rawStatus || '').toLowerCase().trim();
        if (status === 'yes' || status === 'pending') {
            return `<span class="badge bg-danger-subtle text-danger-emphasis">Chờ nhận</span>`;
        }
        if (status === 'no' || status === 'accepted') {
            return `<span class="badge bg-success-subtle text-success-emphasis">Đã nhận</span>`;
        }
        return `<span class="badge bg-secondary-subtle text-secondary-emphasis">${escapeHtml(String(rawStatus || '-'))}</span>`;
    };
    
     ProjectsState.projects.forEach((project, index) => {
          const rowNum = (ProjectsState.currentPage - 1) * ProjectsState.pageSize + index + 1;
          const trackingId = getProjectValue(project, ['Tracking ID', 'tracking_id'], '-');
          const ngay = getProjectValue(project, ['Ngày', 'Created_Date'], '');
          const khachHang = getProjectValue(project, ['Khách hàng', 'khach_hang'], '-');
          const nhanVienKd = getProjectValue(project, ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], '-');
          const tenSanPham = getProjectValue(project, ['Tên sản phẩm', 'ten_san_pham'], '-');
          const quyCach = getProjectValue(project, ['Quy cách', 'quy_cach'], '-');
          const lienHe = getProjectValue(project, ['Người liên hệ (KH)', 'Người liên hệ\n(KH)', 'nguoi_lien_he_kh'], '-');
          const soLuong = getProjectValue(project, ['Số lượng', 'so_luong'], '-');
          const maPo = getProjectValue(project, ['Mã PO', 'ma_po'], '-');
          const maBanVe = getProjectValue(project, ['Mã bản vẽ', 'ma_ban_ve'], '-');
          const maBanVeKt = getProjectValue(project, ['Mã bản vẽ kỹ thuật (sau khi đặt hàng)', 'Mã bản vẽ kỹ thuật', 'ma_ban_ve_ky_thuat'], '-');
          const maMe = getProjectValue(project, ['Mã mẹ', 'Mã mẹ ', 'Mã thành phẩm (Mã mẹ)', 'ma_me'], '-');
          const loaiSanPham = getProjectValue(project, ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], '-');
          const kySu = getProjectValue(project, ['Nhân viên thiết kế', 'Kỹ sư', 'Kỹ sư thiết kế', 'nhan_vien_thiet_ke'], '-');
          const tinhTrang = getProjectValue(project, ['Tình trạng hoàn thành dự án', 'Tình trạng', 'tinh_trang_hoan_thanh'], '-');
          const doKhan = getProjectValue(project, ['Tính cấp bách', 'Mức độ khẩn cấp', 'Độ khẩn', 'urgency_level'], '');
          const tgMongMuon = getProjectValue(project, ['Thời gian mong muốn có bản vẽ', 'TG mong muốn', 'thoi_gian_mong_muon_ban_ve'], '');
          const tgHoanThanh = getProjectValue(project, ['Thời gian hoàn thành kế hoạch', 'TG hoàn thành', 'thoi_gian_hoan_thanh_ke_hoach'], '');
          const pendingStatus = getProjectValue(project, ['is_pending', 'Trạng thái chờ'], '');
          const nguoiNhan = getProjectValue(project, ['accepted_by', 'Người nhận', 'accepted_by'], '');
          
          html += `<tr data-id="${trackingId}">`;
         
         // Column: STT
         if (ProjectsState.visibleColumns.stt) {
             html += `<td>${rowNum}</td>`;
         }
         
          // Column: Tracking ID
          if (ProjectsState.visibleColumns.tracking_id) {
              html += `<td><a href="#" class="view-link view-project" data-id="${trackingId}">${trackingId || '-'}</a></td>`;
          }
         
          // Column: Ngày
          if (ProjectsState.visibleColumns.ngay) {
              html += `<td>${formatDate(ngay) || '-'}</td>`;
          }
         
          // Column: Khách hàng
          if (ProjectsState.visibleColumns.khachhang) {
              html += `<td>${escapeHtml(String(khachHang))}</td>`;
          }
         
          // Column: Nhân viên KD
          if (ProjectsState.visibleColumns.nhanvienkd) {
              html += `<td>${escapeHtml(String(nhanVienKd))}</td>`;
          }
         
          // Column: Tên sản phẩm
          if (ProjectsState.visibleColumns.tensanpham) {
              html += `<td>${escapeHtml(String(tenSanPham))}</td>`;
          }
         
          // Column: Quy cách
          if (ProjectsState.visibleColumns.quycach) {
              html += `<td>${escapeHtml(String(quyCach))}</td>`;
          }
         
          // Column: Người liên hệ (KH)
          if (ProjectsState.visibleColumns.lienhe) {
              html += `<td>${escapeHtml(String(lienHe))}</td>`;
          }
         
          // Column: Số lượng
          if (ProjectsState.visibleColumns.soluong) {
              html += `<td>${soLuong}</td>`;
          }
         
          // Column: Mã PO
          if (ProjectsState.visibleColumns.mapo) {
              html += `<td>${escapeHtml(String(maPo))}</td>`;
          }
         
          // Column: Mã bản vẽ KT
          if (ProjectsState.visibleColumns.mabavkythuat) {
              html += `<td>${escapeHtml(String(maBanVeKt))}</td>`;
          }
         
          // Column: Mã bản vẽ
          if (ProjectsState.visibleColumns.mabave) {
              html += `<td>${escapeHtml(String(maBanVe))}</td>`;
          }
         
          // Column: Mã mẹ
          if (ProjectsState.visibleColumns.mame) {
              html += `<td>${escapeHtml(String(maMe))}</td>`;
          }
         
          // Column: Loại sản phẩm
          if (ProjectsState.visibleColumns.loaisanpham) {
              html += `<td>${escapeHtml(String(loaiSanPham))}</td>`;
          }
         
          // Column: Độ khẩn
          if (ProjectsState.visibleColumns.dokhan) {
              html += `<td>${getUrgencyBadge(doKhan)}</td>`;
          }
         
          // Column: Tình trạng
          if (ProjectsState.visibleColumns.tinhtrang) {
              html += `<td>${escapeHtml(String(tinhTrang))}</td>`;
          }
         
          // Column: Kỹ sư
          if (ProjectsState.visibleColumns.kysu) {
              html += `<td>${escapeHtml(String(kySu))}</td>`;
          }
         
          // Column: TG mong muốn
          if (ProjectsState.visibleColumns.tg_mongmuon) {
              html += `<td>${formatDateTime(tgMongMuon) || '-'}</td>`;
          }
         
          // Column: TG hoàn thành
          if (ProjectsState.visibleColumns.tg_hoanthanh) {
              html += `<td>${formatDateTime(tgHoanThanh) || '-'}</td>`;
          }
         
          // Column: Trạng thái
          if (ProjectsState.visibleColumns.trangthai) {
              html += `<td>${getProjectStatusBadge(pendingStatus)}</td>`;
          }
         
          // Column: Người nhận
          if (ProjectsState.visibleColumns.nguoinhan) {
              html += `<td>${escapeHtml(String(nguoiNhan || getPendingReceiverText()))}</td>`;
          }
         
         // Column: Actions (Quick actions menu)
         html += `<td>
             <div class="dropdown">
                 <button class="btn btn-sm btn-light p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                     <i class="bi bi-three-dots-vertical"></i>
                 </button>
                 <ul class="dropdown-menu dropdown-menu-end">
                     <li><a class="dropdown-item quick-view" href="#" data-id="${trackingId}">
                         <i class="bi bi-eye text-info"></i> ${t('quick_view')}
                     </a></li>
                     <li><a class="dropdown-item quick-edit" href="#" data-id="${trackingId}">
                         <i class="bi bi-pencil text-warning"></i> ${t('quick_edit')}
                     </a></li>
                     <li><hr class="dropdown-divider"></li>
                     <li><a class="dropdown-item quick-delete text-danger" href="#" data-id="${trackingId}">
                         <i class="bi bi-trash"></i> ${t('quick_delete')}
                     </a></li>
                 </ul>
             </div>
         </td>`;
         
         html += '</tr>';
     });
    
    tbody.html(html);
    
    // Setup row click handlers
    setupRowHandlers();
}

/**
 * Setup row event handlers
 */
function setupRowHandlers() {
    // View link
    $('.view-project').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        viewProject(id);
    });
    
    // Row click for selection (single select)
    $('#projects-table-body tr').click(function(e) {
        if (!$(e.target).closest('.dropdown').length) {
            const id = $(this).data('id');
            ProjectsState.selectedIds = [id];
            
            // Update row styling
            $('#projects-table-body tr').removeClass('table-primary');
            $(this).addClass('table-primary');
            
            updateToolbarState();
        }
    });
    
    // Quick action handlers
    setupQuickActionHandlers();
}

/**
 * Update selected IDs
 */
function updateSelectedIds() {
    ProjectsState.selectedIds = [];
    
    $('#projects-table-body tr').each(function() {
        const checkbox = $(this).find('input[type="checkbox"]');
        if (checkbox.is(':checked')) {
            ProjectsState.selectedIds.push($(this).data('id'));
        }
    });
    
    // Update row styling
    $('#projects-table-body tr').removeClass('table-primary');
    ProjectsState.selectedIds.forEach(id => {
        $(`#projects-table-body tr[data-id="${id}"]`).addClass('table-primary');
    });
    
    updateToolbarState();
    
    // Update select all checkbox
    const allChecked = ProjectsState.selectedIds.length === ProjectsState.projects.length;
    $('#select-all-projects').prop('checked', allChecked);
}

/**
 * Update toolbar button states
 */
function updateToolbarState() {
    const count = ProjectsState.selectedIds.length;
    
    $('#btn-edit-project').prop('disabled', count !== 1);
    $('#btn-delete-project').prop('disabled', count === 0);
    
    const start = (ProjectsState.currentPage - 1) * ProjectsState.pageSize + 1;
    const end = Math.min(ProjectsState.currentPage * ProjectsState.pageSize, ProjectsState.totalRecords);
    
    $('#page-info-project').text(
        ProjectsState.totalRecords > 0 
        ? t('page_info', { start: start, end: end, total: ProjectsState.totalRecords })
        : t('page_info', { start: 0, end: 0, total: 0 })
    );
}

/**
 * Update pagination
 */
function updatePagination() {
    const pagination = $('#pagination-project');
    
    if (ProjectsState.totalPages <= 1) {
        pagination.html('');
        return;
    }
    
    pagination.html(createPagination(ProjectsState.currentPage, ProjectsState.totalPages));
    
    // Add click handlers
    $('.page-link').click(function(e) {
        e.preventDefault();
        const page = parseInt($(this).data('page'));
        if (page >= 1 && page <= ProjectsState.totalPages) {
            ProjectsState.currentPage = page;
            loadProjects();
        }
    });
}

// ============================================
// CRUD OPERATIONS
// ============================================

/**
 * Show project modal for add
 */
function showProjectModal() {
    $('#project-form')[0].reset();
    $('#tracking-id').val('');
    $('#modal-title-project').text(t('add_project_title'));
    
    // Clear previous validation states
    $('.is-valid, .is-invalid').removeClass('is-valid is-invalid');
    $('.invalid-feedback').remove();
    
    // Set default date
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $('#field-ngay').val(now.toISOString().slice(0, 16));
    
    // Auto-fill current logged in user's name as sales person
    const currentUserStr = localStorage.getItem('current_user');
    if (currentUserStr) {
        try {
            const currentUser = JSON.parse(currentUserStr);
            // Get the full name of the current user
            const fullName = currentUser.full_name || currentUser.username || '';
            if (fullName) {
                $('#field-nhanvienkd').val(fullName);
            }
        } catch (e) {
            console.error('Error parsing current user:', e);
        }
    }
    
    // Populate customer dropdown
    populateCustomerDropdown();
    
    // Setup real-time validation
    setupRealTimeValidation();
    
    const modalElement = document.getElementById('project-modal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    
    // Update form labels with i18n
    updateProjectFormLabels();
    
    modal.show();
}

/**
 * Setup real-time validation for form fields
 * UX Improvement: Validate fields as user types
 */
function setupRealTimeValidation() {
    // Required fields to validate on blur
    const requiredFields = [
        { id: '#field-khachhang', name: 'Khách hàng' },
        { id: '#field-tensanpham', name: 'Tên sản phẩm' },
        { id: '#field-lienhe', name: 'Người liên hệ' }
    ];
    
    requiredFields.forEach(field => {
        const $input = $(field.id);
        if ($input.length) {
            $input.off('blur.realvalidation').on('blur.realvalidation', function() {
                validateFieldOnBlur($(this), field.name);
            });
            
            // Also validate on keyup for better UX
            $input.off('keyup.realvalidation').on('keyup.realvalidation', function() {
                if ($(this).val().trim()) {
                    $(this).removeClass('is-invalid').addClass('is-valid');
                    $(this).next('.invalid-feedback').remove();
                }
            });
        }
    });

    const $customerSelect = $('#field-khachhang-select');
    if ($customerSelect.length) {
        $customerSelect.off('change.realvalidation').on('change.realvalidation', function() {
            const selectedValue = ($(this).val() || '').trim();
            if (selectedValue) {
                $('#field-khachhang').val(selectedValue);
                clearFieldError($('#field-khachhang'));
                $('#field-khachhang').addClass('is-valid');
            }
        });
    }

    const $customerInput = $('#field-khachhang');
    if ($customerInput.length) {
        $customerInput.off('input.customerSync').on('input.customerSync', function() {
            const typedValue = ($(this).val() || '').trim();
            const $select = $('#field-khachhang-select');
            const matchedOption = $select.find('option').filter(function() {
                return ($(this).val() || '').trim() === typedValue;
            }).first();
            $select.val(matchedOption.length > 0 ? typedValue : '');
        });
    }
    
    // Number field validation
    const $quantity = $('#field-soluong');
    if ($quantity.length) {
        $quantity.off('blur.realvalidation').on('blur.realvalidation', function() {
            const value = $(this).val().trim();
            if (value && isNaN(value)) {
                showFieldError($(this), 'Số lượng phải là số');
            } else {
                clearFieldError($(this));
            }
        });
    }
}

/**
 * Validate a single field on blur
 */
function validateFieldOnBlur($input, fieldName) {
    const value = $input.val().trim();
    
    if (!value) {
        showFieldError($input, `${fieldName} là trường bắt buộc`);
        return false;
    } else {
        clearFieldError($input);
        $input.addClass('is-valid');
        return true;
    }
}

/**
 * Show field error
 */
function showFieldError($input, message) {
    clearFieldError($input);
    $input.removeClass('is-valid').addClass('is-invalid');
    $input.after(`<div class="invalid-feedback" style="display: block; color: #BA1A1A; font-size: 12px;">${message}</div>`);
}

/**
 * Clear field error
 */
function clearFieldError($input) {
    $input.removeClass('is-invalid is-valid');
    $input.next('.invalid-feedback').remove();
}

/**
 * Load customers from API and populate dropdown
 */
async function loadCustomers() {
    try {
        const result = await api.getCustomers();
        if (result.success && result.data) {
            ProjectsState.customers = result.data;
            return result.data;
        }
        ProjectsState.customers = [];
        return [];
    } catch (error) {
        console.error('[Projects] Error loading customers:', error);
        ProjectsState.customers = [];
        return [];
    }
}

/**
 * Populate customer dropdown with customers data
 */
function populateCustomerDropdown() {
    // If no customers loaded yet, load them first
    if (ProjectsState.customers.length === 0) {
        return loadCustomers().then(customers => {
            addCustomerOptions(customers);
        });
    }
    addCustomerOptions(ProjectsState.customers);
    return Promise.resolve();
}

/**
 * Add customer options to dropdown
 */
function addCustomerOptions(customers) {
    const customerSelect = $('#field-khachhang-select');
    const input = $('#field-khachhang');
    const currentValue = (input.val() || '').trim();
    customerSelect.empty();
    customerSelect.append(
        $('<option></option>')
            .val('')
            .text(t('select_customer'))
    );

    const normalized = Array.isArray(customers)
        ? customers
            .map(customer => (customer && customer.name ? String(customer.name).trim() : ''))
            .filter(Boolean)
        : [];

    // Fallback: nếu bảng customers rỗng, lấy danh sách từ dữ liệu projects đã có.
    if (normalized.length === 0 && Array.isArray(ProjectsState.projects)) {
        ProjectsState.projects.forEach(project => {
            const name = String(
                project['Khách hàng']
                || project['khach_hang']
                || project['khachhang']
                || ''
            ).trim();
            if (name) normalized.push(name);
        });
    }

    const uniqueNames = [...new Set(normalized)].sort((a, b) => a.localeCompare(b, 'vi'));

    uniqueNames.forEach(name => {
        customerSelect.append($('<option></option>').val(name).text(name));
    });

    if (currentValue) {
        const matched = uniqueNames.includes(currentValue);
        customerSelect.val(matched ? currentValue : '');
        input.val(currentValue);
    }

    input.attr('placeholder', uniqueNames.length > 0 ? 'Hoặc nhập khách hàng mới' : 'Nhập khách hàng');
}

/**
 * Update project form labels with i18n
 */
function updateProjectFormLabels() {
    // Section headers
    $('#project-form .section-title').eq(0).text(t('basic_info'));
    $('#project-form .section-title').eq(1).text(t('product_info'));
    $('#project-form .section-title').eq(2).text(t('drawing_codes'));
    $('#project-form .section-title').eq(3).text(t('technical_info'));
    $('#project-form .section-title').eq(4).text(t('time_urgency'));
    
    // Labels
    $('#project-form label').eq(0).html(t('form_ngay_khoitao'));
    $('#project-form label').eq(1).html(t('form_khachhang_required'));
    $('#project-form label').eq(2).html(t('form_nhanvienkd'));
    $('#project-form label').eq(3).html(t('form_tensanpham_required'));
    $('#project-form label').eq(4).html(t('form_quycach'));
    $('#project-form label').eq(5).html(t('form_lienhe_kh'));
    $('#project-form label').eq(6).html(t('form_soluong'));
    $('#project-form label').eq(7).html(t('form_mapo'));
    $('#project-form label').eq(8).html(t('form_loaisanpham'));
    $('#project-form label').eq(9).html(t('form_kysu'));
    $('#project-form label').eq(10).html(t('form_tinhtrang'));
    $('#project-form label').eq(11).html(t('form_capbach'));
    $('#project-form label').eq(12).html(t('form_tg_mongmuon'));
    $('#project-form label').eq(13).html(t('form_tg_hoanthanh'));

    // Customer controls
    const customerSelect = $('#field-khachhang-select');
    if (customerSelect.length) {
        customerSelect.find('option').first().text(t('select_customer'));
    }
    $('#field-khachhang').attr('placeholder', 'Hoặc nhập khách hàng mới');
    
    // Urgency options
    const urgencySelect = $('#field-capbach');
    if (urgencySelect.length) {
        urgencySelect.find('option').eq(0).text(t('urgency_normal_option'));
        urgencySelect.find('option').eq(1).text(t('urgency_urgent_option'));
        urgencySelect.find('option').eq(2).text(t('urgency_very_urgent_option'));
    }
    
    // Modal buttons
    $('#project-modal .btn-secondary').eq(0).text(t('cancel'));
    $('#project-modal .btn-primary').text(t('save'));
}

/**
 * Edit project
 * @param {string} id - Tracking ID
 */
async function editProject(id) {
    try {
        const result = await api.getProject(id);
        
        if (result) {
            $('#tracking-id').val(id);
            $('#modal-title-project').text(t('edit_project_title'));
            
            // Fill form fields manually - using database keys with fallback to old labels
            // Thông tin cơ bản
            $('#field-ngay').val(result['Created_Date'] || result['Ngày'] || result['Ngày khởi tạo'] || '');
            $('#field-nhanvienkd').val(result['nhan_vien_kinh_doanh'] || result['Nhân viên KD'] || result['Nhân viên kinh doanh'] || '');
            
            // Populate customer options first
            await populateCustomerDropdown();
            const customerName = (result['khach_hang'] || result['Khách hàng'] || '').trim();
            $('#field-khachhang').val(customerName);
            const hasOption = $('#field-khachhang-select option').filter(function() {
                return ($(this).val() || '').trim() === customerName;
            }).length > 0;
            $('#field-khachhang-select').val(hasOption ? customerName : '');
            
            // Thông tin sản phẩm
            $('#field-tensanpham').val(result['ten_san_pham'] || result['Tên sản phẩm'] || '');
            $('#field-quycach').val(result['quy_cach'] || result['Quy cách'] || '');
            $('#field-lienhe').val(result['nguoi_lien_he_kh'] || result['Người liên hệ (KH)'] || result['Người liên hệ\n(KH)'] || '');
            $('#field-soluong').val(result['so_luong'] || result['Số lượng'] || '');
            $('#field-mapo').val(result['ma_po'] || result['Mã PO'] || '');
            $('#field-mabave_chinh').val(result['ma_ban_ve'] || result['Mã bản vẽ chính'] || result['Mã bản vẽ'] || '');
            $('#field-mabave').val(result['Mã bản vẽ'] || result['ma_ban_ve'] || '');
            $('#field-mabavkythuat').val(
                result['ma_ban_ve_ky_thuat']
                || result['Mã bản vẽ kỹ thuật (sau khi đặt hàng)']
                || result['Mã bản vẽ kỹ thuật']
                || ''
            );
            $('#field-mame').val(result['ma_me'] || result['Mã mẹ'] || result['Mã mẹ '] || result['Mã thành phẩm (Mã mẹ)'] || '');
            
            // Thông tin kỹ thuật
            $('#field-loaisanpham').val(result['loai_san_pham'] || result['Loại sản phẩm'] || result['Hạng mục'] || '');
            $('#field-kysu').val(result['nhan_vien_thiet_ke'] || result['Nhân viên thiết kế'] || result['Kỹ sư thiết kế'] || result['Kỹ sư'] || '');
            $('#field-tinhtrang').val(result['tinh_trang_hoan_thanh'] || result['Tình trạng hoàn thành dự án'] || result['Tình trạng'] || '');
            
            // Thời gian & Độ khẩn
            $('#field-capbach').val(result['urgency_level'] || result['Độ khẩn'] || result['Tính cấp bách'] || result['Mức độ khẩn cấp'] || 'normal');
            $('#field-tg-mongmuon').val(result['thoi_gian_mong_muon_ban_ve'] || result['Thời gian mong muốn có bản vẽ'] || result['TG mong muốn'] || '');
            $('#field-tg-hoanthanh').val(result['thoi_gian_hoan_thanh_ke_hoach'] || result['Thời gian hoàn thành kế hoạch'] || result['TG hoàn thành'] || '');
            
            // Update form labels with i18n
            updateProjectFormLabels();
            
            const modal = new bootstrap.Modal('#project-modal');
            modal.show();
        }
    } catch (error) {
        console.error('[Projects] Edit error:', error);
        showToast(t('error'), t('load_error_projects'), 'error');
    }
}

/**
 * View project details
 * @param {string} id - Tracking ID
 */
async function viewProject(id) {
    try {
        const result = await api.getProject(id);
        
        if (result) {
            // Update modal title
            $('#view-modal-project .modal-title').html('<i class="bi bi-eye"></i> ' + t('view_project_title'));
            
            const displayData = {};
            
            // Map technical/duplicate keys to preferred display keys
            const preferredKeys = {
                // Prefer Vietnamese labels over technical keys
                'Ngày khởi tạo': 'Ngày',
                'Nhân viên kinh doanh': 'Nhân viên KD',
                'Người liên hệ\n(KH)': 'Người liên hệ (KH)',
                'Mã bản vẽ phương án (mã trước khi đặt hàng)': 'Mã bản vẽ',
                'Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)': 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)',
                'Mã thành phẩm (Mã mẹ)': 'Mã mẹ',
                'Mã mẹ ': 'Mã mẹ',
                'Hạng mục': 'Loại sản phẩm',
                'Kỹ sư thiết kế': 'Nhân viên thiết kế',
                // Prefer user-friendly keys for status fields
                'Mức độ khẩn cấp': 'Tính cấp bách',
                'urgency_level': 'Tính cấp bách',
                'Trạng thái chờ': 'is_pending',
                'Người nhận': 'accepted_by',
                'Thời gian nhận': 'accepted_at',
                'User ID': 'user_id',
                'desired_solution_time': 'Thời gian hoàn thành kế hoạch'
            };
            
            for (const [key, value] of Object.entries(result)) {
                if (value !== undefined && value !== null && value !== '') {
                    // Nếu key là key kỹ thuật/đồ thị và có key người dùng cuối thì bỏ qua
                    if (preferredKeys[key] && result[preferredKeys[key]] !== undefined) {
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
            
            $('#view-content-project').html(html);
            
            const modal = new bootstrap.Modal('#view-modal-project');
            modal.show();
        }
    } catch (error) {
        console.error('[Projects] View error:', error);
        showToast(t('error'), t('load_error_projects'), 'error');
    }
}
/**
 * Save project - Create or Update
 */
async function saveProject() {
    const trackingId = $('#tracking-id').val();
    const isEditMode = !!trackingId;
    
    // Clear previous validation
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').remove();
    
    // Validation - Kiểm tra các trường bắt buộc
    const selectedCustomer = ($('#field-khachhang-select').val() || '').trim();
    const typedCustomer = ($('#field-khachhang').val() || '').trim();
    const khachhang = typedCustomer || selectedCustomer;
    const tensanpham = $('#field-tensanpham').val().trim();
    const lienhe = $('#field-lienhe').val().trim();
    let hasError = false;
    
    if (!khachhang) {
        showFieldError($('#field-khachhang'), 'Khách hàng là trường bắt buộc');
        hasError = true;
    }
    
    if (!tensanpham) {
        showFieldError($('#field-tensanpham'), 'Tên sản phẩm là trường bắt buộc');
        hasError = true;
    }
    
    if (!lienhe) {
        showFieldError($('#field-lienhe'), 'Người liên hệ là trường bắt buộc');
        hasError = true;
    }
    
    // Validate quantity if provided
    const quantity = $('#field-soluong').val().trim();
    if (quantity && isNaN(quantity)) {
        showFieldError($('#field-soluong'), 'Số lượng phải là số');
        hasError = true;
    }
    
    if (hasError) {
        // Scroll to first error
        const firstError = $('.is-invalid').first();
        if (firstError.length) {
            firstError[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
        return;
    }
    
    // Collect form data using database keys
    const formData = {
        'Created_Date': $('#field-ngay').val(),
        'khach_hang': khachhang,
        'nhan_vien_kinh_doanh': $('#field-nhanvienkd').val().trim(),
        'ten_san_pham': tensanpham,
        'quy_cach': $('#field-quycach').val().trim(),
        'nguoi_lien_he_kh': $('#field-lienhe').val().trim(),
        'so_luong': $('#field-soluong').val(),
        'ma_po': $('#field-mapo').val().trim(),
        'ma_ban_ve': ($('#field-mabave').val() || $('#field-mabave_chinh').val() || '').trim(),
        'ma_ban_ve_ky_thuat': $('#field-mabavkythuat').val().trim(),
        'ma_me': $('#field-mame').val().trim(),
        'loai_san_pham': $('#field-loaisanpham').val().trim(),
        'nhan_vien_thiet_ke': $('#field-kysu').val().trim(),
        'tinh_trang_hoan_thanh': $('#field-tinhtrang').val().trim(),
        'urgency_level': $('#field-capbach').val(),
        'thoi_gian_mong_muon_ban_ve': $('#field-tg-mongmuon').val(),
        'thoi_gian_hoan_thanh_ke_hoach': $('#field-tg-hoanthanh').val(),
        // Legacy keys để tương thích backend add_record hiện tại
        'Ngày': $('#field-ngay').val(),
        'Khách hàng': khachhang,
        'Nhân viên KD': $('#field-nhanvienkd').val().trim(),
        'Tên sản phẩm': tensanpham,
        'Quy cách': $('#field-quycach').val().trim(),
        'Người liên hệ (KH)': $('#field-lienhe').val().trim(),
        'Số lượng': $('#field-soluong').val(),
        'Mã PO': $('#field-mapo').val().trim(),
        'Mã bản vẽ': ($('#field-mabave').val() || $('#field-mabave_chinh').val() || '').trim(),
        'Mã bản vẽ kỹ thuật (sau khi đặt hàng)': $('#field-mabavkythuat').val().trim(),
        'Mã mẹ': $('#field-mame').val().trim(),
        'Loại sản phẩm': $('#field-loaisanpham').val().trim(),
        'Kỹ sư': $('#field-kysu').val().trim(),
        'Tình trạng': $('#field-tinhtrang').val().trim(),
        'Tính cấp bách': $('#field-capbach').val(),
        'TG mong muốn': $('#field-tg-mongmuon').val(),
        'TG hoàn thành': $('#field-tg-hoanthanh').val()
    };
    
    // Remove empty values (but keep 0 for numeric fields if needed)
    Object.keys(formData).forEach(key => {
        const value = formData[key];
        if (value === '' || value === null || value === undefined) {
            delete formData[key];
        }
    });
    
    // Add tracking ID if editing
    if (trackingId) {
        formData['tracking_id'] = trackingId;
    }
    
    showLoading(t('saving'));
    
    try {
        let result;
        
        if (trackingId) {
            result = await api.updateProject(trackingId, formData);
        } else {
            result = await api.createProject(formData);
        }
        
        if (result.success) {
            showToast(t('success'), trackingId ? t('toast_project_updated') : t('toast_project_created'), 'success');
            
            // Hide modal
            bootstrap.Modal.getInstance('#project-modal').hide();
            
            // Reload data
            loadProjects();
        } else {
            throw new Error(result.error || t('error'));
        }
    } catch (error) {
        console.error('[Projects] Save error:', error);
        showToast(t('error'), error.message || t('error'), 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Show delete confirm modal
 */
function showDeleteConfirmModal() {
    $('#delete-count-project').text(ProjectsState.selectedIds.length);
    
    const modal = new bootstrap.Modal('#confirm-delete-modal-project');
    modal.show();
}

/**
 * Delete selected projects
 */
async function deleteSelectedProjects() {
    const ids = ProjectsState.selectedIds;
    
    showLoading(t('deleting'));
    
    try {
        const result = await api.deleteProjects(ids);
        
        if (result.success) {
            showToast(t('success'), t('toast_project_deleted', { count: ids.length }), 'success');
            
            // Hide modal
            bootstrap.Modal.getInstance('#confirm-delete-modal-project').hide();
            
            // Clear selection
            ProjectsState.selectedIds = [];
            
            // Reload data
            loadProjects();
        } else {
            throw new Error(result.error || t('error'));
        }
    } catch (error) {
        console.error('[Projects] Delete error:', error);
        showToast(t('error'), error.message || t('error'), 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// EXPORT
// ============================================

/**
 * Export to Excel
 */
function exportToExcel() {
    if (ProjectsState.projects.length === 0) {
        showToast(t('warning'), t('toast_no_data_export'), 'warning');
        return;
    }
    
    showLoading(t('exporting_data'));
    
    try {
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(ProjectsState.projects);
        XLSX.utils.book_append_sheet(wb, ws, t('projects_title'));
        XLSX.writeFile(wb, 'du_an_' + new Date().toISOString().slice(0, 10) + '.xlsx');
        
        showToast(t('success'), t('toast_export_success', { type: 'Excel' }), 'success');
    } catch (error) {
        console.error('[Projects] Export error:', error);
        showToast(t('error'), t('error'), 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Export to CSV
 */
function exportToCSV() {
    if (ProjectsState.projects.length === 0) {
        showToast(t('warning'), t('toast_no_data_export'), 'warning');
        return;
    }
    
    showLoading(t('exporting_data'));
    
    try {
        const headers = Object.keys(ProjectsState.projects[0]);
        let csv = headers.join(',') + '\n';
        
        ProjectsState.projects.forEach(row => {
            const values = headers.map(h => {
                const val = row[h] || '';
                return '"' + String(val).replace(/"/g, '""') + '"';
            });
            csv += values.join(',') + '\n';
        });
        
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'du_an_' + new Date().toISOString().slice(0, 10) + '.csv';
        link.click();
        
        showToast(t('success'), t('toast_export_success', { type: 'CSV' }), 'success');
    } catch (error) {
        console.error('[Projects] Export CSV error:', error);
        showToast(t('error'), t('error'), 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// HELPERS
// ============================================

/**
 * Get urgency badge HTML
 * @param {string} urgency - Độ khẩn
 * @returns {string}
 */
function getUrgencyBadge(urgency) {
    if (!urgency) return '-';
    
    const classes = {
        'normal': 'success',
        'urgent': 'warning',
        'very_urgent': 'danger'
    };
    
    const labels = {
        'normal': t('urgency_normal'),
        'urgent': t('urgency_urgent'),
        'very_urgent': t('urgency_very_urgent')
    };
    
    const cls = classes[urgency] || 'secondary';
    const label = labels[urgency] || urgency;
    
    return `<span class="badge bg-${cls}">${label}</span>`;
}

/**
 * Initialize column selector
 */
function initColumnSelector() {
    const body = $('#column-selector-body');
    let html = '';
    
    ProjectsState.columnsConfig.forEach(col => {
        const isVisible = ProjectsState.visibleColumns[col.key] !== false;
        html += `
            <div class="form-check">
                <input class="form-check-input column-checkbox" type="checkbox" 
                       value="${col.key}" id="col-${col.key}" ${isVisible ? 'checked' : ''}>
                <label class="form-check-label" for="col-${col.key}">${col.label}</label>
            </div>
        `;
    });
    
    body.html(html);
}

/**
 * Toggle column selector popup
 */
function toggleColumnSelector() {
    const selector = $('#column-selector');
    selector.toggle();
}

/**
 * Reset column visibility to default
 */
function resetColumnVisibility() {
    ProjectsState.columnsConfig.forEach(col => {
        ProjectsState.visibleColumns[col.key] = col.default;
    });
    
    // Update checkboxes
    $('.column-checkbox').each(function() {
        const key = $(this).val();
        const config = ProjectsState.columnsConfig.find(c => c.key === key);
        $(this).prop('checked', config ? config.default : true);
    });
    
    renderProjectsTable();
}

/**
 * Apply column visibility changes
 */
function applyColumnVisibility() {
    $('.column-checkbox').each(function() {
        const key = $(this).val();
        ProjectsState.visibleColumns[key] = $(this).is(':checked');
    });
    
    renderProjectsTable();
}

/**
 * Setup quick action handlers
 */
function setupQuickActionHandlers() {
    // Quick view
    $('.quick-view').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        viewProject(id);
    });
    
    // Quick edit
    $('.quick-edit').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        editProject(id);
    });
    
    // Quick delete
    $('.quick-delete').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        ProjectsState.selectedIds = [id];
        showDeleteConfirmModal();
    });
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initProjectsModule = initProjectsModule;
window.onProjectsTabInit = function() {
    // Called when projects tab is shown
    // Translate the content when tab is shown
    if (typeof translatePage === 'function') {
        translatePage();
    }
    
    if (!ProjectsState.isLoading && ProjectsState.projects.length === 0) {
        loadProjects();
    }
};
