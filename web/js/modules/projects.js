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
    pageSize: 100000,
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
    quickAddDraft: {},
    quickAddStarted: false,
    quickAddPreviewId: null,
    autoScrollToBottomOnLoad: true,
    activeCell: null,
    editingCell: null,
    // Column visibility
    visibleColumns: {
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
        'nhanvienthietke': true,
        'tinhtrang': true,
        'dokhan': true,
        'tg_tiepnhan': true,
        'tg_mongmuon': true,
        'tg_hoanthanh': true,
        'trangthai': true,
        'nguoinhan': true
    },
    // Available columns config
    columnsConfig: [
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
        { key: 'loaisanpham', label: 'Loại sản phẩm', default: true },
        { key: 'nhanvienthietke', label: 'Nhân viên thiết kế', default: true },
        { key: 'dokhan', label: 'Độ khẩn', default: true },
        { key: 'tinhtrang', label: 'Tình trạng', default: true },
        { key: 'tg_tiepnhan', label: 'TG tiếp nhận', default: true },
        { key: 'tg_mongmuon', label: 'TG mong muốn', default: true },
        { key: 'tg_hoanthanh', label: 'TG hoàn thành', default: true },
        { key: 'trangthai', label: 'Trạng thái', default: true },
        { key: 'nguoinhan', label: 'Người nhận', default: true }
    ]
};

const PROJECT_VISIBLE_COLUMNS_STORAGE_KEY = 'projects_visible_columns_v2';

const PROJECT_SPREADSHEET_COLUMNS = [
    { key: 'tracking_id', label: 'STT', zhLabel: '序号', width: 88, readOnly: true, fields: ['Tracking ID', 'tracking_id'], className: 'col-stt' },
    { key: 'ngay', label: 'Ngày', zhLabel: '日期', width: 96, fields: ['Ngày', 'Created_Date'], updateKey: 'Ngày', type: 'date' },
    { key: 'khachhang', label: 'Khách hàng', zhLabel: '客户', width: 118, fields: ['Khách hàng', 'khach_hang'], updateKey: 'Khách hàng' },
    { key: 'nhanvienkd', label: 'Nhân viên kinh doanh', zhLabel: '业务员', width: 126, fields: ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], updateKey: 'Nhân viên kinh doanh' },
    { key: 'tensanpham', label: 'Tên sản phẩm', zhLabel: '客户需求名称', width: 150, fields: ['Tên sản phẩm', 'ten_san_pham'], updateKey: 'Tên sản phẩm' },
    { key: 'quycach', label: 'Quy cách', zhLabel: '客户需求规格', width: 160, fields: ['Quy cách', 'quy_cach'], updateKey: 'Quy cách' },
    { key: 'lienhe', label: 'Người liên hệ (KH)', zhLabel: '对接人', width: 114, fields: ['Người liên hệ (KH)', 'Người liên hệ\n(KH)', 'nguoi_lien_he_kh'], updateKey: 'Người liên hệ (KH)' },
    { key: 'soluong', label: 'Số lượng', zhLabel: '数量', width: 72, fields: ['Số lượng', 'so_luong'], updateKey: 'Số lượng', type: 'number', className: 'text-center' },
    { key: 'mapo', label: 'Mã PO', zhLabel: 'PO号', width: 112, fields: ['Mã PO', 'ma_po'], updateKey: 'Mã PO' },
    { key: 'mabave', label: 'Mã bản vẽ phương án', zhLabel: '方案图号（下单前）', width: 146, fields: ['Mã bản vẽ phương án', 'Mã bản vẽ phương án (mã trước khi đặt hàng)', 'Mã bản vẽ', 'ma_ban_ve'], updateKey: 'Mã bản vẽ phương án (mã trước khi đặt hàng)' },
    { key: 'mabavkythuat', label: 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)', zhLabel: '工程图号（下单后）', width: 166, fields: ['Mã bản vẽ kỹ thuật (sau khi đặt hàng)', 'Mã bản vẽ kỹ thuật', 'ma_ban_ve_ky_thuat'], updateKey: 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)' },
    { key: 'mame', label: 'Mã mẹ', zhLabel: '母料号', width: 118, fields: ['Mã mẹ', 'Mã mẹ ', 'Mã thành phẩm (Mã mẹ)', 'ma_me'], updateKey: 'Mã mẹ' },
    { key: 'loaisanpham', label: 'Loại sản phẩm', zhLabel: '产品类型', width: 168, fields: ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], updateKey: 'Loại sản phẩm', type: 'select', optionsSource: 'productTypes' },
    { key: 'nhanvienthietke', label: 'Nhân viên thiết kế', zhLabel: '设计者', width: 122, fields: ['Nhân viên thiết kế', 'Kỹ sư thiết kế', 'nhan_vien_thiet_ke'], updateKey: 'Nhân viên thiết kế', type: 'select', optionsSource: 'engineers' },
    { key: 'tinhtrang', label: 'Tình trạng hoàn thành dự án', zhLabel: '工程完成情况', width: 166, fields: ['Tình trạng hoàn thành dự án', 'Tình trạng', 'tinh_trang_hoan_thanh'], updateKey: 'Tình trạng hoàn thành dự án', type: 'select', optionsSource: 'completionStatus' },
    { key: 'dokhan', label: 'Tính cấp bách', zhLabel: '紧急程度', width: 112, fields: ['Tính cấp bách', 'Mức độ khẩn cấp', 'Độ khẩn', 'urgency_level'], updateKey: 'Tính cấp bách', type: 'select', optionsSource: 'urgency' },
    { key: 'tg_tiepnhan', label: 'Thời gian tiếp nhận phương án', zhLabel: '接收方案时间', width: 142, fields: ['Thời gian nhận', 'accepted_at'], updateKey: 'accepted_at', type: 'datetime' },
    { key: 'tg_mongmuon', label: 'Thời gian mong muốn có bản vẽ', zhLabel: '期望出图时间', width: 146, fields: ['Thời gian mong muốn có bản vẽ', 'TG mong muốn', 'thoi_gian_mong_muon_ban_ve'], updateKey: 'Thời gian mong muốn có bản vẽ', type: 'datetime' },
    { key: 'tg_hoanthanh', label: 'Thời gian hoàn thành kế hoạch', zhLabel: '方案完成时间', width: 146, fields: ['Thời gian hoàn thành kế hoạch', 'TG hoàn thành', 'thoi_gian_hoan_thanh_ke_hoach'], updateKey: 'Thời gian hoàn thành kế hoạch', type: 'datetime' },
    { key: 'trangthai', label: 'Trạng thái nhận', zhLabel: '接收状态', width: 108, fields: ['is_pending', 'Trạng thái chờ'], updateKey: 'is_pending', type: 'select', optionsSource: 'pendingStatus' },
    { key: 'nguoinhan', label: 'Người nhận', zhLabel: '接收人', width: 108, fields: ['accepted_by', 'Người nhận'], updateKey: 'accepted_by' }
];

const PROJECT_SELECT_OPTIONS = {
    urgency: [
        { value: 'normal', label: '正常 - Bình thường' },
        { value: 'urgent', label: '紧急 - Khẩn cấp' },
        { value: 'very_urgent', label: '非常紧急 - Rất khẩn cấp' }
    ],
    pendingStatus: [
        { value: 'yes', label: 'Chờ nhận / 待接收' },
        { value: 'no', label: 'Đã nhận / 已接收' }
    ],
    completionStatus: [
        '待出图 - Đang vẽ',
        '方案已完成 - Đã ra BV',
        'BOM待建立- Đang làm BOM',
        'BOM已完成 -  BOM đã hoàn thành',
        'C类结案-Kết thúc vụ án loại C'
    ],
    productTypes: [
        'WLJ物料架 - Giá đựng vật liệu',
        'ZZC周转车 - xe trung chuyển',
        'GZT工作台 - bàn thao tác',
        'WCP无尘棚 - phòng sạch',
        'LSX流水线 - băng tải',
        'ZWJ转弯机 - bang tải chuyển hướng 90*: 180*',
        'GZL改造类 - sửa đổi',
        'SJT散件图 - bản vẽ tách chi tiết',
        'BSX倍速线 - Dây chuyền băng tải tự động',
        'WLL围栏类 - hàng rào',
        'GTX滚筒线 - băng tải con lăn'
    ],
    engineers: ['孟令宝', '邓氏乔贞', '阮文张', '阮克南', '黄庭字', '孙啸', '陈孟辉']
};

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize Projects module
 */
function initProjectsModule() {
    console.log('[Projects] Initializing...');
    
    if (window.history && 'scrollRestoration' in window.history) {
        window.history.scrollRestoration = 'manual';
    }
    
    loadProjectColumnVisibility();

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
                <!-- Row 1: Search & Filters -->
                <div class="row g-2 align-items-center mb-2">
                    <div class="col">
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
                <div class="table-responsive" id="projects-table-wrap" style="max-height: calc(100vh - 280px); overflow-y: auto;">
                    <table id="projects-table" class="table table-striped table-hover table-bordered mb-0" 
                           style="width: 100%; table-layout: fixed;">
                        <thead class="table-light">
                            <tr>
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
                                <th style="width: 140px;" data-i18n="col_tg_mongmuon">${t('col_tg_mongmuon')}</th>
                                <th style="width: 140px;" data-i18n="col_tg_hoanthanh">${t('col_tg_hoanthanh')}</th>
                                <th style="width: 100px;" data-i18n="col_trangthai">${t('col_trangthai')}</th>
                                <th style="width: 100px;" data-i18n="col_nguoinhan">${t('col_nguoinhan')}</th>
                            </tr>
                        </thead>
                        <tbody id="projects-table-body">
                            <!-- Data will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div id="project-row-context-menu" class="dropdown-menu" style="position: fixed; display: none; z-index: 2000;">
            <button type="button" class="dropdown-item ctx-add"><i class="bi bi-plus-circle text-success"></i> <span data-menu-label="add">${t('add')}</span></button>
            <button type="button" class="dropdown-item ctx-view"><i class="bi bi-eye text-info"></i> <span data-menu-label="view">${t('quick_view')}</span></button>
            <button type="button" class="dropdown-item ctx-edit"><i class="bi bi-pencil text-warning"></i> <span data-menu-label="edit">${t('quick_edit')}</span></button>
            <button type="button" class="dropdown-item text-danger ctx-delete"><i class="bi bi-trash"></i> <span data-menu-label="delete">${t('quick_delete')}</span></button>
            <div class="dropdown-divider"></div>
            <button type="button" class="dropdown-item ctx-refresh"><i class="bi bi-arrow-clockwise text-secondary"></i> <span data-menu-label="refresh">${t('refresh')}</span></button>
            <button type="button" class="dropdown-item ctx-columns"><i class="bi bi-layout-columns text-secondary"></i> <span data-menu-label="columns">${t('btn_toggle_columns')}</span></button>
            <div class="dropdown-divider"></div>
            <button type="button" class="dropdown-item ctx-export-excel"><i class="bi bi-file-earmark-excel text-success"></i> <span data-menu-label="exportExcel">${t('export_excel')}</span></button>
            <button type="button" class="dropdown-item ctx-export-csv"><i class="bi bi-file-earmark-text text-primary"></i> <span data-menu-label="exportCsv">${t('export_csv')}</span></button>
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
                            
                            <!-- Thời gian & Độ khẩn -->
                            <div class="section-header">
                                <h6 class="section-title">${t('time_urgency')}</h6>
                            </div>
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">${t('form_capbach')}</label>
                                    <select class="form-select" id="field-capbach">
                                        <option value="normal">正常 - Bình thường</option>
                                        <option value="urgent">紧急 - Khẩn cấp</option>
                                        <option value="very_urgent">非常紧急 - Rất khẩn cấp</option>
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
        if (!$(e.target).closest('#column-selector, #project-row-context-menu').length) {
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
    // Search input placeholder
    const searchInput = $('#search-input-project');
    if (searchInput.length) {
        searchInput.attr('placeholder', t('search_placeholder'));
    }

    updateProjectContextMenuI18n();
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
    renderProjectsSpreadsheetHeader();
    tbody.html(createLoadingState(getVisibleProjectColumns().length));
    
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
            if (ProjectsState.autoScrollToBottomOnLoad) {
                ensureProjectsInitialScrollToBottom();
            }
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

function scrollProjectsToBottom() {
    const wrap = document.querySelector('#projects-container .table-responsive');
    if (!wrap) return;
    wrap.scrollTop = wrap.scrollHeight;
}

function ensureProjectsInitialScrollToBottom(retries = 12) {
    if (!ProjectsState.autoScrollToBottomOnLoad) return;
    const container = document.getElementById('projects-container');
    const wrap = document.querySelector('#projects-container .table-responsive');
    if (container && wrap && container.offsetParent !== null && ProjectsState.projects.length > 0) {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                scrollProjectsToBottom();
                setTimeout(scrollProjectsToBottom, 80);
            });
        });
        ProjectsState.autoScrollToBottomOnLoad = false;
        return;
    }
    if (retries <= 0) return;
    setTimeout(() => ensureProjectsInitialScrollToBottom(retries - 1), 80);
}

/**
 * Render projects table
 */
function renderProjectsTable() {
    const tbody = $('#projects-table-body');
    renderProjectsSpreadsheetHeader();
    let html = '';
    const columns = getVisibleProjectColumns();
    
    ProjectsState.projects.forEach((project, rowIndex) => {
        const trackingId = getProjectValue(project, ['Tracking ID', 'tracking_id'], '');
        html += `<tr data-id="${escapeHtml(String(trackingId))}" data-row-index="${rowIndex}">`;

        columns.forEach((column, colIndex) => {
            const rawValue = getProjectValue(project, column.fields, '');
            const displayValue = formatProjectCellValue(column, rawValue, rowIndex);
            const classes = [
                'project-sheet-cell',
                column.readOnly ? 'readonly' : 'editable',
                column.className || '',
                getProjectCellStateClass(column, rawValue)
            ].filter(Boolean).join(' ');
            html += `
                <td class="${classes}"
                    tabindex="0"
                    data-row="${rowIndex}"
                    data-col="${colIndex}"
                    data-key="${column.key}"
                    data-id="${escapeHtml(String(trackingId))}"
                    data-update-key="${escapeHtml(String(column.updateKey || ''))}"
                    data-raw-value="${escapeHtml(String(rawValue || ''))}">
                    ${displayValue}
                </td>
            `;
        });

        html += '</tr>';
    });

    html += renderQuickAddProjectRow(columns, ProjectsState.projects.length);
    
    tbody.html(html);
    
    setupSpreadsheetHandlers();
}

function renderQuickAddProjectRow(columns, rowIndex) {
    let html = `<tr class="project-quick-add-row${ProjectsState.quickAddStarted ? ' project-quick-add-started' : ''}" data-id="__new__" data-row-index="${rowIndex}" data-draft-row="true">`;

    if (!ProjectsState.quickAddStarted) {
        html += `
            <td class="project-sheet-cell quick-add-full-cell readonly"
                tabindex="0"
                colspan="${columns.length}"
                data-row="${rowIndex}"
                data-col="0"
                data-key="tracking_id"
                data-id="__new__"
                data-draft="true">
                ${renderQuickAddControl()}
            </td>
        `;
        html += '</tr>';
        return html;
    }

    columns.forEach((column, colIndex) => {
        const rawValue = getProjectDraftValue(column);
        const isReadonly = column.readOnly;
        const displayValue = isReadonly
            ? renderQuickAddControl()
            : formatProjectCellValue(column, rawValue, rowIndex);
        const classes = [
            'project-sheet-cell',
            'quick-add-cell',
            isReadonly ? 'readonly' : 'editable',
            column.className || '',
            getProjectCellStateClass(column, rawValue)
        ].filter(Boolean).join(' ');

        html += `
            <td class="${classes}"
                tabindex="0"
                data-row="${rowIndex}"
                data-col="${colIndex}"
                data-key="${column.key}"
                data-id="__new__"
                data-draft="true"
                data-update-key="${escapeHtml(String(column.updateKey || ''))}"
                data-raw-value="${escapeHtml(String(rawValue || ''))}">
                ${displayValue}
            </td>
        `;
    });

    html += '</tr>';
    return html;
}

function renderQuickAddControl() {
    if (!ProjectsState.quickAddStarted) {
        return `
            <button type="button" class="quick-add-start" title="${escapeHtml(t('quick_add_start_title'))}">
                <span class="quick-add-plus">+</span>
                <span class="quick-add-hint">${escapeHtml(t('quick_add_double_click'))}</span>
            </button>
        `;
    }

    return `
        <div class="quick-add-actions">
            <span class="quick-add-id">${escapeHtml(t('quick_add_new_id'))}: ${escapeHtml(String(ProjectsState.quickAddPreviewId || ''))}</span>
            <button type="button" class="btn btn-sm btn-success quick-add-save" title="${escapeHtml(t('quick_add_save_title'))}">
                <i class="bi bi-check-lg"></i>
                <span>${escapeHtml(t('save'))}</span>
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary quick-add-cancel" title="${escapeHtml(t('cancel'))}">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
    `;
}

function getVisibleProjectColumns() {
    return PROJECT_SPREADSHEET_COLUMNS.filter(column => ProjectsState.visibleColumns[column.key] !== false);
}

function renderProjectsSpreadsheetHeader() {
    const columns = getVisibleProjectColumns();
    const totalWidth = columns.reduce((sum, column) => sum + (column.width || 100), 0) || 1;
    const colgroup = columns
        .map(column => {
            const widthPercent = ((column.width || 100) / totalWidth) * 100;
            return `<col style="width: ${widthPercent.toFixed(4)}%;">`;
        })
        .join('');
    const header = columns
        .map(column => `
            <th class="project-sheet-header" title="${escapeHtml(column.label)} / ${escapeHtml(column.zhLabel || '')}">
                <span class="project-sheet-header-main">${escapeHtml(column.label)}</span>
                <span class="project-sheet-header-sub">${escapeHtml(column.zhLabel || '')}</span>
            </th>
        `)
        .join('');

    const table = $('#projects-table');
    table.find('colgroup').remove();
    table.toggleClass('project-many-columns', columns.length >= 18);
    table.prepend(`<colgroup>${colgroup}</colgroup>`);
    table.find('thead').html(`
        <tr class="project-sheet-header-row">${header}</tr>
    `);
}

function getProjectValue(project, keys, fallback = '') {
    for (const key of keys || []) {
        const value = project[key];
        if (value === undefined || value === null) continue;
        if (typeof value === 'string' && value.trim() === '') continue;
        return value;
    }
    return fallback;
}

function getProjectDraftValue(column) {
    if (!column) return '';
    if (ProjectsState.quickAddDraft[column.key] !== undefined) {
        return ProjectsState.quickAddDraft[column.key];
    }
    if (column.updateKey && ProjectsState.quickAddDraft[column.updateKey] !== undefined) {
        return ProjectsState.quickAddDraft[column.updateKey];
    }
    return '';
}

function setProjectDraftValue(column, value) {
    if (!column) return;
    ProjectsState.quickAddDraft[column.key] = value;
    if (column.updateKey) {
        ProjectsState.quickAddDraft[column.updateKey] = value;
    }
}

function getCurrentUserDisplayName() {
    const currentUserStr = localStorage.getItem('current_user');
    if (!currentUserStr) return '';
    try {
        const currentUser = JSON.parse(currentUserStr);
        return currentUser.full_name || currentUser.username || '';
    } catch (e) {
        console.error('Error parsing current user:', e);
        return '';
    }
}

function getProjectDraftFieldValue(...keys) {
    for (const key of keys) {
        const value = ProjectsState.quickAddDraft[key];
        if (value !== undefined && value !== null && String(value).trim() !== '') {
            return String(value).trim();
        }
    }
    return '';
}

function getMissingQuickAddRequiredFields() {
    const missing = [];
    if (!getProjectDraftFieldValue('khachhang', 'Khách hàng')) missing.push('Khách hàng');
    if (!getProjectDraftFieldValue('tensanpham', 'Tên sản phẩm')) missing.push('Tên sản phẩm');
    if (!getProjectDraftFieldValue('lienhe', 'Người liên hệ (KH)')) missing.push('Người liên hệ');
    return missing;
}

function hasQuickAddDraftData() {
    return Object.values(ProjectsState.quickAddDraft).some(value => value !== undefined && value !== null && String(value).trim() !== '');
}

function getNextQuickAddPreviewId() {
    const ids = ProjectsState.projects
        .map(project => Number(getProjectValue(project, ['Tracking ID', 'tracking_id'], 0)))
        .filter(id => Number.isFinite(id));
    return (ids.length ? Math.max(...ids) : 0) + 1;
}

function getCurrentLocalDateTimeValue() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
}

function startQuickAddProject() {
    if (ProjectsState.quickAddStarted) return;

    ProjectsState.quickAddStarted = true;
    ProjectsState.quickAddPreviewId = getNextQuickAddPreviewId();
    ProjectsState.quickAddDraft = {
        ...ProjectsState.quickAddDraft,
        tracking_id: ProjectsState.quickAddPreviewId,
        'Tracking ID': ProjectsState.quickAddPreviewId,
        ngay: getProjectDraftFieldValue('ngay', 'Ngày') || getCurrentLocalDateTimeValue(),
        'Ngày': getProjectDraftFieldValue('ngay', 'Ngày') || getCurrentLocalDateTimeValue(),
        nhanvienkd: getProjectDraftFieldValue('nhanvienkd', 'Nhân viên kinh doanh') || getCurrentUserDisplayName(),
        'Nhân viên kinh doanh': getProjectDraftFieldValue('nhanvienkd', 'Nhân viên kinh doanh') || getCurrentUserDisplayName(),
        dokhan: getProjectDraftFieldValue('dokhan', 'Tính cấp bách') || 'normal',
        'Tính cấp bách': getProjectDraftFieldValue('dokhan', 'Tính cấp bách') || 'normal'
    };
    renderProjectsTable();

    const firstEditable = $('#projects-table-body .project-quick-add-row .project-sheet-cell.editable').first();
    if (firstEditable.length) {
        firstEditable.focus();
        activateProjectCell(firstEditable);
    }
}

function resetQuickAddProject() {
    ProjectsState.quickAddDraft = {};
    ProjectsState.quickAddStarted = false;
    ProjectsState.quickAddPreviewId = null;
    renderProjectsTable();
}

function buildQuickAddProjectPayload() {
    const defaultDate = getCurrentLocalDateTimeValue();

    const khachhang = getProjectDraftFieldValue('khachhang', 'Khách hàng');
    const tensanpham = getProjectDraftFieldValue('tensanpham', 'Tên sản phẩm');
    const lienhe = getProjectDraftFieldValue('lienhe', 'Người liên hệ (KH)');
    const nhanvienkd = getProjectDraftFieldValue('nhanvienkd', 'Nhân viên kinh doanh') || getCurrentUserDisplayName();
    const ngay = getProjectDraftFieldValue('ngay', 'Ngày') || defaultDate;

    const formData = {
        'Created_Date': ngay,
        'khach_hang': khachhang,
        'nhan_vien_kinh_doanh': nhanvienkd,
        'ten_san_pham': tensanpham,
        'quy_cach': getProjectDraftFieldValue('quycach', 'Quy cách'),
        'nguoi_lien_he_kh': lienhe,
        'so_luong': getProjectDraftFieldValue('soluong', 'Số lượng'),
        'ma_po': getProjectDraftFieldValue('mapo', 'Mã PO'),
        'ma_ban_ve': getProjectDraftFieldValue('mabave', 'Mã bản vẽ phương án (mã trước khi đặt hàng)'),
        'ma_ban_ve_ky_thuat': getProjectDraftFieldValue('mabavkythuat', 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)'),
        'ma_me': getProjectDraftFieldValue('mame', 'Mã mẹ'),
        'loai_san_pham': getProjectDraftFieldValue('loaisanpham', 'Loại sản phẩm'),
        'nhan_vien_thiet_ke': getProjectDraftFieldValue('nhanvienthietke', 'Nhân viên thiết kế'),
        'tinh_trang_hoan_thanh': getProjectDraftFieldValue('tinhtrang', 'Tình trạng hoàn thành dự án'),
        'urgency_level': getProjectDraftFieldValue('dokhan', 'Tính cấp bách') || 'normal',
        'thoi_gian_mong_muon_ban_ve': getProjectDraftFieldValue('tg_mongmuon', 'Thời gian mong muốn có bản vẽ'),
        'thoi_gian_hoan_thanh_ke_hoach': getProjectDraftFieldValue('tg_hoanthanh', 'Thời gian hoàn thành kế hoạch'),
        'Ngày': ngay,
        'Khách hàng': khachhang,
        'Nhân viên KD': nhanvienkd,
        'Tên sản phẩm': tensanpham,
        'Quy cách': getProjectDraftFieldValue('quycach', 'Quy cách'),
        'Người liên hệ (KH)': lienhe,
        'Số lượng': getProjectDraftFieldValue('soluong', 'Số lượng'),
        'Mã PO': getProjectDraftFieldValue('mapo', 'Mã PO'),
        'Mã bản vẽ phương án (mã trước khi đặt hàng)': getProjectDraftFieldValue('mabave', 'Mã bản vẽ phương án (mã trước khi đặt hàng)'),
        'Mã bản vẽ kỹ thuật (sau khi đặt hàng)': getProjectDraftFieldValue('mabavkythuat', 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)'),
        'Mã mẹ': getProjectDraftFieldValue('mame', 'Mã mẹ'),
        'Loại sản phẩm': getProjectDraftFieldValue('loaisanpham', 'Loại sản phẩm'),
        'Nhân viên thiết kế': getProjectDraftFieldValue('nhanvienthietke', 'Nhân viên thiết kế'),
        'Tình trạng hoàn thành dự án': getProjectDraftFieldValue('tinhtrang', 'Tình trạng hoàn thành dự án'),
        'Tính cấp bách': getProjectDraftFieldValue('dokhan', 'Tính cấp bách') || 'normal',
        'TG mong muốn': getProjectDraftFieldValue('tg_mongmuon', 'Thời gian mong muốn có bản vẽ'),
        'TG hoàn thành': getProjectDraftFieldValue('tg_hoanthanh', 'Thời gian hoàn thành kế hoạch')
    };

    Object.keys(formData).forEach(key => {
        const value = formData[key];
        if (value === '' || value === null || value === undefined) {
            delete formData[key];
        }
    });

    return formData;
}

function formatProjectCellValue(column, rawValue, rowIndex) {
    if (column.key === 'tracking_id') {
        const value = rawValue || rowIndex + 1;
        return `<a href="#" class="view-link view-project" data-id="${escapeHtml(String(rawValue))}">${escapeHtml(String(value))}</a>`;
    }
    if (column.key === 'trangthai') {
        return renderPendingStatus(rawValue);
    }
    if (column.key === 'dokhan') {
        return renderUrgencyCell(rawValue);
    }
    const text = rawValue === undefined || rawValue === null || rawValue === '' ? '' : String(rawValue);
    return escapeHtml(text);
}

function renderPendingStatus(rawStatus) {
    const status = String(rawStatus || '').toLowerCase().trim();
    if (status === 'yes' || status === 'pending') {
        return '<span class="project-sheet-pill status-pending">Chờ nhận / 待接收</span>';
    }
    if (status === 'no' || status === 'accepted') {
        return '<span class="project-sheet-pill status-accepted">Đã nhận / 已接收</span>';
    }
    return escapeHtml(String(rawStatus || ''));
}

function normalizeProjectUrgency(rawUrgency) {
    const value = String(rawUrgency || '').trim();
    const normalized = value.toLowerCase();

    if (!value) {
        return { value: '', label: '' };
    }
    if (normalized === 'very_urgent' || normalized.includes('very') || value.includes('非常')) {
        return { value: 'very_urgent', label: '非常紧急 - Rất khẩn cấp' };
    }
    if (normalized === 'urgent' || value.includes('紧急')) {
        return { value: 'urgent', label: '紧急 - Khẩn cấp' };
    }
    if (normalized === 'normal' || value.includes('正常')) {
        return { value: 'normal', label: '正常 - Bình thường' };
    }

    return { value: value, label: value };
}

function renderUrgencyCell(rawUrgency) {
    const urgency = normalizeProjectUrgency(rawUrgency);
    let cls = 'urgency-normal';
    if (urgency.value === 'very_urgent') {
        cls = 'urgency-very-urgent';
    } else if (urgency.value === 'urgent') {
        cls = 'urgency-urgent';
    }
    return urgency.label ? `<span class="project-sheet-pill ${cls}">${escapeHtml(urgency.label)}</span>` : '';
}

function getProjectCellStateClass(column, rawValue) {
    if (column.key === 'dokhan') {
        const urgency = normalizeProjectUrgency(rawValue);
        if (urgency.value === 'very_urgent') return 'cell-very-urgent';
        if (urgency.value === 'urgent') return 'cell-urgent';
        if (urgency.value || urgency.label) return 'cell-normal';
    }
    if (column.key === 'trangthai') {
        const value = String(rawValue || '').toLowerCase();
        if (value === 'yes' || value === 'pending') return 'cell-pending';
        if (value === 'no' || value === 'accepted') return 'cell-accepted';
    }
    return '';
}

/**
 * Setup row event handlers
 */
function setupRowHandlers() {
    setupSpreadsheetHandlers();
}

function setupSpreadsheetHandlers() {
    const tbody = $('#projects-table-body');

    tbody.off('click.projectSheet').on('click.projectSheet', '.project-sheet-cell', function(e) {
        if ($(e.target).closest('.view-project, input, select, textarea, button').length) return;
        activateProjectCell($(this));
    });

    tbody.off('focus.projectSheet').on('focus.projectSheet', '.project-sheet-cell', function() {
        activateProjectCell($(this));
    });

    tbody.off('dblclick.projectSheet').on('dblclick.projectSheet', '.project-sheet-cell.editable', function() {
        beginProjectCellEdit($(this));
    });

    tbody.off('dblclick.quickAddStart').on('dblclick.quickAddStart', '.quick-add-start, .project-quick-add-row .project-sheet-cell.readonly', function(e) {
        e.preventDefault();
        e.stopPropagation();
        startQuickAddProject();
    });

    tbody.off('click.quickAddSave').on('click.quickAddSave', '.quick-add-save', function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveQuickAddProject();
    });

    tbody.off('click.quickAddCancel').on('click.quickAddCancel', '.quick-add-cancel', function(e) {
        e.preventDefault();
        e.stopPropagation();
        resetQuickAddProject();
    });

    tbody.off('keydown.projectSheet').on('keydown.projectSheet', '.project-sheet-cell', function(e) {
        handleProjectCellKeydown(e, $(this));
    });

    tbody.off('paste.projectSheet').on('paste.projectSheet', '.project-sheet-cell', function(e) {
        handleProjectCellPaste(e, $(this));
    });

    tbody.off('copy.projectSheet').on('copy.projectSheet', '.project-sheet-cell', function(e) {
        const value = $(this).attr('data-raw-value') || $(this).text().trim();
        e.originalEvent.clipboardData.setData('text/plain', value);
        e.preventDefault();
    });

    tbody.off('click.viewProject').on('click.viewProject', '.view-project', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        viewProject(id);
    });

    tbody.off('contextmenu.projectCtx').on('contextmenu.projectCtx', 'tr', function(e) {
        if ($(this).data('draft-row')) return;
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        selectProjectRow(id, $(this));
        showProjectContextMenu(e.clientX, e.clientY, id);
    });

    $('#projects-table-wrap').off('contextmenu.projectCtxBlank').on('contextmenu.projectCtxBlank', function(e) {
        if ($(e.target).closest('#projects-table-body tr').length) return;
        e.preventDefault();
        showProjectContextMenu(e.clientX, e.clientY, null);
    });

    setupProjectContextMenuHandlers();
}

function activateProjectCell($cell) {
    if (!$cell || !$cell.length) return;
    const id = $cell.data('id');
    ProjectsState.activeCell = {
        row: Number($cell.data('row')),
        col: Number($cell.data('col'))
    };
    selectProjectRow(id, $cell.closest('tr'));
    $('#projects-table-body .project-sheet-cell').removeClass('active-cell');
    $cell.addClass('active-cell');
}

function selectProjectRow(id, $row) {
    ProjectsState.selectedIds = id === '__new__' || id === undefined || id === null ? [] : [id];
    $('#projects-table-body tr').removeClass('table-primary selected-row');
    $row.addClass('table-primary selected-row');
    updateToolbarState();
}

function handleProjectCellKeydown(e, $cell) {
    if (ProjectsState.editingCell) return;

    const key = e.key;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(key)) {
        e.preventDefault();
        if (key === 'Enter') {
            beginProjectCellEdit($cell);
            return;
        }
        moveProjectCellFocus($cell, key === 'Tab' ? (e.shiftKey ? 'ArrowLeft' : 'ArrowRight') : key);
        return;
    }

    if (key === 'F2') {
        e.preventDefault();
        beginProjectCellEdit($cell);
        return;
    }

    if ((key === 'Backspace' || key === 'Delete') && $cell.hasClass('editable')) {
        e.preventDefault();
        saveProjectCell($cell, '');
        return;
    }

    if (key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && $cell.hasClass('editable')) {
        e.preventDefault();
        beginProjectCellEdit($cell, key);
    }
}

function moveProjectCellFocus($cell, direction) {
    const row = Number($cell.data('row'));
    const col = Number($cell.data('col'));
    let nextRow = row;
    let nextCol = col;

    if (direction === 'ArrowUp') nextRow -= 1;
    if (direction === 'ArrowDown') nextRow += 1;
    if (direction === 'ArrowLeft') nextCol -= 1;
    if (direction === 'ArrowRight') nextCol += 1;

    const $next = $(`#projects-table-body .project-sheet-cell[data-row="${nextRow}"][data-col="${nextCol}"]`);
    if ($next.length) {
        $next.focus();
        activateProjectCell($next);
    }
}

function beginProjectCellEdit($cell, seedValue = null) {
    if (!$cell.hasClass('editable') || ProjectsState.editingCell) return;
    if ($cell.data('draft') && !ProjectsState.quickAddStarted) {
        showToast(t('info'), t('quick_add_double_click'), 'info');
        return;
    }

    const column = getVisibleProjectColumns()[Number($cell.data('col'))];
    if (!column || column.readOnly || !column.updateKey) return;

    const originalValue = $cell.attr('data-raw-value') || '';
    const editValue = seedValue !== null ? seedValue : originalValue;
    ProjectsState.editingCell = $cell[0];
    $cell.addClass('editing-cell');

    const finish = async (commit, value) => {
        if (ProjectsState.editingCell !== $cell[0]) return;
        ProjectsState.editingCell = null;
        $cell.removeClass('editing-cell');
        if (commit) {
            await saveProjectCell($cell, value);
        } else {
            renderProjectCellDisplay($cell, column, originalValue);
        }
        $cell.focus();
    };

    if (column.type === 'select') {
        const options = getProjectColumnOptions(column, originalValue);
        const selectHtml = options.map(option => {
            const value = typeof option === 'object' ? option.value : option;
            const label = typeof option === 'object' ? option.label : option;
            return `<option value="${escapeHtml(String(value))}" ${String(value) === String(originalValue) ? 'selected' : ''}>${escapeHtml(String(label))}</option>`;
        }).join('');
        $cell.html(`<select class="project-cell-editor form-select form-select-sm">${selectHtml}</select>`);
        const $select = $cell.find('select');
        $select.focus();
        $select.on('change blur', function() {
            finish(true, $(this).val());
        });
        $select.on('keydown', function(e) {
            if (e.key === 'Escape') {
                e.preventDefault();
                finish(false);
            }
            if (e.key === 'Enter') {
                e.preventDefault();
                finish(true, $(this).val());
            }
        });
        return;
    }

    const inputType = column.type === 'number' ? 'number' : 'text';
    $cell.html(`<input class="project-cell-editor form-control form-control-sm" type="${inputType}" value="${escapeHtml(String(editValue))}">`);
    const $input = $cell.find('input');
    $input.focus();
    $input[0].select();
    $input.on('blur', function() {
        finish(true, $(this).val());
    });
    $input.on('keydown', function(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            finish(false);
        }
        if (e.key === 'Enter') {
            e.preventDefault();
            finish(true, $(this).val());
        }
        if (e.key === 'Tab') {
            e.preventDefault();
            const value = $(this).val();
            finish(true, value).then(() => moveProjectCellFocus($cell, e.shiftKey ? 'ArrowLeft' : 'ArrowRight'));
        }
    });
}

function getProjectColumnOptions(column, currentValue) {
    const base = PROJECT_SELECT_OPTIONS[column.optionsSource] || [];
    const values = [...base];
    const hasCurrentValue = values.some(option => String(typeof option === 'object' ? option.value : option) === String(currentValue));
    const normalizedUrgency = column.optionsSource === 'urgency' ? normalizeProjectUrgency(currentValue) : null;
    if (normalizedUrgency?.value && !values.some(option => String(typeof option === 'object' ? option.value : option) === normalizedUrgency.value)) {
        values.unshift({ value: normalizedUrgency.value, label: normalizedUrgency.label });
    } else if (currentValue && !hasCurrentValue && column.optionsSource !== 'urgency') {
        values.unshift(currentValue);
    }
    return values;
}

async function handleProjectCellPaste(e, $cell) {
    if (!$cell.hasClass('editable')) return;
    const text = e.originalEvent.clipboardData.getData('text/plain');
    if (!text) return;
    e.preventDefault();

    const rows = text.replace(/\r/g, '').split('\n').filter((row, index, all) => row.length > 0 || index < all.length - 1);
    const matrix = rows.map(row => row.split('\t'));
    await applyProjectPasteMatrix($cell, matrix);
}

async function applyProjectPasteMatrix($startCell, matrix) {
    const columns = getVisibleProjectColumns();
    const startRow = Number($startCell.data('row'));
    const startCol = Number($startCell.data('col'));
    const updatesById = new Map();
    const touchedCells = [];

    matrix.forEach((rowValues, rowOffset) => {
        rowValues.forEach((value, colOffset) => {
            const row = startRow + rowOffset;
            const col = startCol + colOffset;
            const column = columns[col];
            const $target = $(`#projects-table-body .project-sheet-cell[data-row="${row}"][data-col="${col}"]`);
            if (!$target.length || !column || column.readOnly || !column.updateKey) return;
            if ($target.data('draft')) return;
            const id = String($target.data('id'));
            if (!updatesById.has(id)) updatesById.set(id, {});
            updatesById.get(id)[column.updateKey] = value;
            touchedCells.push({ $cell: $target, column, value, row });
        });
    });

    if (updatesById.size === 0) return;
    touchedCells.forEach(({ $cell }) => $cell.addClass('saving-cell'));

    try {
        for (const [id, payload] of updatesById.entries()) {
            const result = await api.updateProject(id, payload);
            if (!result || !result.success) {
                throw new Error(result?.error || t('error'));
            }
            const rowIndex = ProjectsState.projects.findIndex(project => String(getProjectValue(project, ['Tracking ID', 'tracking_id'], '')) === String(id));
            if (rowIndex >= 0) {
                Object.assign(ProjectsState.projects[rowIndex], payload);
            }
        }
        touchedCells.forEach(({ $cell, column, value }) => {
            $cell.removeClass('saving-cell error-cell');
            renderProjectCellDisplay($cell, column, value);
        });
    } catch (error) {
        touchedCells.forEach(({ $cell }) => $cell.removeClass('saving-cell').addClass('error-cell'));
        console.error('[Projects] Paste update error:', error);
        showToast(t('error'), error.message || t('error'), 'error');
    }
}

async function saveProjectCell($cell, value) {
    const column = getVisibleProjectColumns()[Number($cell.data('col'))];
    const id = String($cell.data('id'));
    const oldValue = $cell.attr('data-raw-value') || '';
    if ($cell.data('draft')) {
        await saveQuickAddProjectCell($cell, column, value);
        return;
    }
    if (!column || column.readOnly || !column.updateKey || value === oldValue) {
        if (column) renderProjectCellDisplay($cell, column, oldValue);
        return;
    }

    $cell.addClass('saving-cell').removeClass('error-cell');
    try {
        const payload = { [column.updateKey]: value };
        const result = await api.updateProject(id, payload);
        if (!result || !result.success) {
            throw new Error(result?.error || t('error'));
        }

        const rowIndex = Number($cell.data('row'));
        updateProjectRowData(rowIndex, column, value);
        renderProjectCellDisplay($cell, column, value);
        $cell.removeClass('saving-cell');
    } catch (error) {
        console.error('[Projects] Cell update error:', error);
        $cell.removeClass('saving-cell').addClass('error-cell');
        renderProjectCellDisplay($cell, column, oldValue);
        showToast(t('error'), error.message || t('error'), 'error');
    }
}

async function saveQuickAddProjectCell($cell, column, value) {
    if (!column || column.readOnly || !column.updateKey) return;
    if (!ProjectsState.quickAddStarted) {
        showToast(t('info'), t('quick_add_double_click'), 'info');
        renderProjectCellDisplay($cell, column, '');
        return;
    }

    setProjectDraftValue(column, value);
    renderProjectCellDisplay($cell, column, value);

    const missing = getMissingQuickAddRequiredFields();
    if (missing.length > 0) {
        $cell.closest('tr').addClass('project-quick-add-incomplete');
    } else {
        $cell.closest('tr').removeClass('project-quick-add-incomplete');
    }
}

async function saveQuickAddProject() {
    if (!ProjectsState.quickAddStarted) {
        startQuickAddProject();
        return;
    }

    if (!hasQuickAddDraftData()) return;

    const missing = getMissingQuickAddRequiredFields();
    if (missing.length > 0) {
        $('#projects-table-body .project-quick-add-row').addClass('project-quick-add-incomplete');
        showToast(t('warning'), t('quick_add_missing_fields').replace('{fields}', missing.join(', ')), 'warning');
        return;
    }

    const row = $('#projects-table-body .project-quick-add-row');
    row.removeClass('project-quick-add-incomplete').addClass('saving-cell');
    $('#projects-table-body .quick-add-cell').addClass('saving-cell').removeClass('error-cell');

    try {
        const result = await api.createProject(buildQuickAddProjectPayload());
        if (!result || !result.success) {
            throw new Error(result?.error || t('error'));
        }

        ProjectsState.quickAddDraft = {};
        ProjectsState.quickAddStarted = false;
        ProjectsState.quickAddPreviewId = null;
        showToast(t('success'), t('toast_project_created'), 'success');
        await loadProjects();
    } catch (error) {
        console.error('[Projects] Quick add error:', error);
        row.removeClass('saving-cell');
        $('#projects-table-body .quick-add-cell').removeClass('saving-cell').addClass('error-cell');
        showToast(t('error'), error.message || t('error'), 'error');
    }
}

function updateProjectRowData(rowIndex, column, value) {
    const project = ProjectsState.projects[rowIndex];
    if (!project) return;
    project[column.updateKey] = value;
    if (column.fields && column.fields[0]) {
        project[column.fields[0]] = value;
    }
}

function renderProjectCellDisplay($cell, column, rawValue) {
    $cell.attr('data-raw-value', rawValue || '');
    $cell.removeClass('cell-normal cell-urgent cell-very-urgent cell-pending cell-accepted')
        .addClass(getProjectCellStateClass(column, rawValue));
    $cell.html(formatProjectCellValue(column, rawValue, Number($cell.data('row'))));
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

function updateToolbarState() {
    // Row-specific context menu actions are enabled when the menu opens.
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
                if (field.id === '#field-khachhang') {
                    validateCustomerField();
                } else {
                    validateFieldOnBlur($(this), field.name);
                }
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
            } else {
                validateCustomerField();
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

function getCustomerFieldValue() {
    const selectedCustomer = ($('#field-khachhang-select').val() || '').trim();
    const typedCustomer = ($('#field-khachhang').val() || '').trim();
    return typedCustomer || selectedCustomer;
}

function validateCustomerField() {
    const customerValue = getCustomerFieldValue();
    const $customerInput = $('#field-khachhang');
    if (!customerValue) {
        showFieldError($customerInput, 'Khách hàng là trường bắt buộc');
        return false;
    }
    clearFieldError($customerInput);
    $customerInput.addClass('is-valid');
    return true;
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
    $('#project-form .section-title').eq(2).text(t('time_urgency'));
    
    // Labels
    $('#project-form label').eq(0).html(t('form_ngay_khoitao'));
    $('#project-form label').eq(1).html(t('form_khachhang_required'));
    $('#project-form label').eq(2).html(t('form_nhanvienkd'));
    $('#project-form label').eq(3).html(t('form_tensanpham_required'));
    $('#project-form label').eq(4).html(t('form_quycach'));
    $('#project-form label').eq(5).html(t('form_lienhe_kh'));
    $('#project-form label').eq(6).html(t('form_soluong'));
    $('#project-form label').eq(7).html(t('form_mapo'));
    $('#project-form label').eq(8).html(t('form_capbach'));
    $('#project-form label').eq(9).html(t('form_tg_mongmuon'));
    $('#project-form label').eq(10).html(t('form_tg_hoanthanh'));

    // Customer controls
    const customerSelect = $('#field-khachhang-select');
    if (customerSelect.length) {
        customerSelect.find('option').first().text(t('select_customer'));
    }
    $('#field-khachhang').attr('placeholder', 'Hoặc nhập khách hàng mới');
    
    // Urgency options
    const urgencySelect = $('#field-capbach');
    if (urgencySelect.length) {
        urgencySelect.find('option').eq(0).text('正常 - Bình thường');
        urgencySelect.find('option').eq(1).text('紧急 - Khẩn cấp');
        urgencySelect.find('option').eq(2).text('非常紧急 - Rất khẩn cấp');
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
    const khachhang = getCustomerFieldValue();
    const tensanpham = $('#field-tensanpham').val().trim();
    const lienhe = $('#field-lienhe').val().trim();
    let hasError = false;
    
    if (!validateCustomerField()) {
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
        const columns = getVisibleProjectColumns();
        const data = [
            columns.map(column => column.label),
            columns.map(column => column.zhLabel || '')
        ];

        ProjectsState.projects.forEach((project, rowIndex) => {
            data.push(columns.map(column => {
                const value = getProjectValue(project, column.fields, '');
                if (column.key === 'tracking_id') return value || rowIndex + 1;
                return value;
            }));
        });

        const ws = XLSX.utils.aoa_to_sheet(data);
        ws['!cols'] = columns.map(column => ({ wch: Math.max(8, Math.round(column.width / 8)) }));
        XLSX.utils.book_append_sheet(wb, ws, '25年');
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
    const normalizedUrgency = normalizeProjectUrgency(urgency);
    
    const classes = {
        'normal': 'success',
        'urgent': 'warning',
        'very_urgent': 'danger'
    };

    const cls = classes[normalizedUrgency.value] || 'secondary';
    const label = normalizedUrgency.label || urgency;
    
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

function loadProjectColumnVisibility() {
    try {
        const saved = localStorage.getItem(PROJECT_VISIBLE_COLUMNS_STORAGE_KEY);
        if (!saved) return;

        const parsed = JSON.parse(saved);
        if (!parsed || typeof parsed !== 'object') return;

        ProjectsState.columnsConfig.forEach(col => {
            if (typeof parsed[col.key] === 'boolean') {
                ProjectsState.visibleColumns[col.key] = parsed[col.key];
            }
        });
    } catch (error) {
        console.warn('[Projects] Cannot load column visibility:', error);
    }
}

function saveProjectColumnVisibility() {
    try {
        localStorage.setItem(PROJECT_VISIBLE_COLUMNS_STORAGE_KEY, JSON.stringify(ProjectsState.visibleColumns));
    } catch (error) {
        console.warn('[Projects] Cannot save column visibility:', error);
    }
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
    
    saveProjectColumnVisibility();
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
    
    saveProjectColumnVisibility();
    renderProjectsTable();
}

function hideProjectContextMenu() {
    $('#project-row-context-menu').hide().removeData('rowId');
}

function showProjectContextMenu(x, y, rowId) {
    const menu = $('#project-row-context-menu');
    if (!menu.length) return;
    const hasRow = rowId !== undefined && rowId !== null && rowId !== '__new__';
    menu.data('rowId', rowId);
    menu.find('.ctx-view, .ctx-edit, .ctx-delete').prop('disabled', !hasRow).toggleClass('disabled', !hasRow);

    menu.css({ left: 0, top: 0, display: 'block' });
    const menuEl = menu[0];
    const menuWidth = menuEl.offsetWidth;
    const menuHeight = menuEl.offsetHeight;
    const left = Math.min(x, window.innerWidth - menuWidth - 8);
    const top = Math.min(y, window.innerHeight - menuHeight - 8);
    menu.css({ left: `${Math.max(8, left)}px`, top: `${Math.max(8, top)}px` });
}

function setupProjectContextMenuHandlers() {
    const menu = $('#project-row-context-menu');
    if (!menu.length) return;

    menu.off('click.ctxActions');
    menu.on('click.ctxActions', '.ctx-add', function() {
        hideProjectContextMenu();
        showProjectModal();
    });
    menu.on('click.ctxActions', '.ctx-view', function() {
        const id = menu.data('rowId');
        hideProjectContextMenu();
        if (id) viewProject(id);
    });
    menu.on('click.ctxActions', '.ctx-edit', function() {
        const id = menu.data('rowId');
        hideProjectContextMenu();
        if (id) editProject(id);
    });
    menu.on('click.ctxActions', '.ctx-delete', function() {
        const id = menu.data('rowId');
        hideProjectContextMenu();
        if (!id) return;
        ProjectsState.selectedIds = [id];
        showDeleteConfirmModal();
    });
    menu.on('click.ctxActions', '.ctx-refresh', function() {
        hideProjectContextMenu();
        ProjectsState.autoScrollToBottomOnLoad = true;
        loadProjects();
    });
    menu.on('click.ctxActions', '.ctx-columns', function(e) {
        const menuOffset = menu.offset();
        hideProjectContextMenu();
        toggleColumnSelector();
        const selector = $('#column-selector');
        if (selector.length && selector.is(':visible')) {
            const left = Math.min(e.clientX, window.innerWidth - selector.outerWidth() - 8);
            const top = Math.min(e.clientY, window.innerHeight - selector.outerHeight() - 8);
            selector.css({
                position: 'fixed',
                left: `${Math.max(8, left)}px`,
                right: 'auto',
                top: `${Math.max(8, top)}px`
            });
        } else if (menuOffset) {
            selector.css({ position: '', left: '', right: '', top: '' });
        }
    });
    menu.on('click.ctxActions', '.ctx-export-excel', function() {
        hideProjectContextMenu();
        exportToExcel();
    });
    menu.on('click.ctxActions', '.ctx-export-csv', function() {
        hideProjectContextMenu();
        exportToCSV();
    });

    $(document).off('click.projectCtxMenu').on('click.projectCtxMenu', function(e) {
        if (!$(e.target).closest('#project-row-context-menu').length) {
            hideProjectContextMenu();
        }
    });
    $(window).off('scroll.projectCtxMenu resize.projectCtxMenu').on('scroll.projectCtxMenu resize.projectCtxMenu', function() {
        hideProjectContextMenu();
    });
}

function updateProjectContextMenuI18n() {
    const menu = $('#project-row-context-menu');
    if (!menu.length) return;
    menu.find('[data-menu-label="add"]').text(t('add'));
    menu.find('[data-menu-label="view"]').text(t('quick_view'));
    menu.find('[data-menu-label="edit"]').text(t('quick_edit'));
    menu.find('[data-menu-label="delete"]').text(t('quick_delete'));
    menu.find('[data-menu-label="refresh"]').text(t('refresh'));
    menu.find('[data-menu-label="columns"]').text(t('btn_toggle_columns'));
    menu.find('[data-menu-label="exportExcel"]').text(t('export_excel'));
    menu.find('[data-menu-label="exportCsv"]').text(t('export_csv'));
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
    
    if (ProjectsState.autoScrollToBottomOnLoad) {
        ensureProjectsInitialScrollToBottom();
    }
};
