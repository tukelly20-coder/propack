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
    virtualStart: 0,
    virtualEnd: 0,
    virtualScrollFrame: null,
    activeCell: null,
    editingCell: null,
    projectLocks: new Map(),
    lockCleanupTimer: null,
    realtimeStream: null,
    realtimeConnected: false,
    realtimeReloadTimer: null,
    onlineUsers: [],
    remoteCursors: new Map(),
    cursorPublishTimer: null,
    activeChangeLogContext: null,
    activeCommentContext: null,
    undoStack: [],
    columnFilters: {},
    activeFilterKey: null,
    searchDraft: '',
    columnWidths: {},
    columnResize: null,
    rangeSelection: null,
    selectedCells: [],
    columnOrder: [],
    rowHeight: 46,
    headerHeight: 54,
    rowHeightResize: null,
    headerHeightResize: null,
    // Column visibility
    visibleColumns: {
        'tracking_id': true,
        'ngay': true,
        'khachhang': true,
        'nhanvienkd': true,
        'tensanpham': true,
        'quycach': true,
        'yeucaukythuat': true,
        'lienhe': true,
        'soluong': true,
        'mapo': true,
        'dokhan': true,
        'tg_mongmuon': true,
        'trangthai': true,
        'nguoinhan': true,
        'tg_tiepnhan': true,
        'mabave': true,
        'mabavkythuat': true,
        'mame': true,
        'loaisanpham': true,
        'nhanvienthietke': true,
        'tinhtrang': true,
        'tg_hoanthanh': true,
        
    },
    // Available columns config
    columnsConfig: [
        { key: 'tracking_id', label: 'Tracking ID', default: true },
        { key: 'ngay', label: 'Ngày', default: true },
        { key: 'khachhang', label: 'Khách hàng', default: true },
        { key: 'nhanvienkd', label: 'Nhân viên KD', default: true },
        { key: 'tensanpham', label: 'Tên sản phẩm', default: true },
        { key: 'quycach', label: 'Quy cách', default: true },
        { key: 'yeucaukythuat', label: 'Yêu cầu kỹ thuật KH', default: true },
        { key: 'lienhe', label: 'Người liên hệ (KH)', default: true },
        { key: 'soluong', label: 'Số lượng', default: true },
        { key: 'mapo', label: 'Mã PO', default: true },
        { key: 'dokhan', label: 'Độ khẩn', default: true },
        { key: 'tg_mongmuon', label: 'TG mong muốn', default: true },
        { key: 'trangthai', label: 'Trạng thái', default: true },
        { key: 'nguoinhan', label: 'Người nhận', default: true },
        { key: 'tg_tiepnhan', label: 'TG tiếp nhận', default: true },
        { key: 'mabave', label: 'Mã bản vẽ', default: true },
        { key: 'mabavkythuat', label: 'Mã bản vẽ KT', default: true },
        { key: 'mame', label: 'Mã mẹ', default: true },
        { key: 'loaisanpham', label: 'Loại sản phẩm', default: true },
        { key: 'nhanvienthietke', label: 'Nhân viên thiết kế', default: true },
        { key: 'tinhtrang', label: 'Tình trạng', default: true },
        { key: 'tg_hoanthanh', label: 'TG hoàn thành', default: true },
    ]
};

const PROJECT_LAYOUT_STORAGE_PREFIX = 'projects_table_layout_v3';
const PROJECT_LAYOUT_PREFERENCE_KEY = 'projects_table_layout';
const PROJECT_FILTER_STORAGE_PREFIX = 'projects_table_filters_v1';
const PROJECT_FILTER_PREFERENCE_KEY = 'projects_table_filters';
const PROJECT_LOCK_CLEANUP_INTERVAL_MS = 1000;
const PROJECT_DEFAULT_ROW_HEIGHT = 46;
const PROJECT_MIN_ROW_HEIGHT = 30;
const PROJECT_MAX_ROW_HEIGHT = 120;
const PROJECT_DEFAULT_HEADER_HEIGHT = 54;
const PROJECT_MIN_HEADER_HEIGHT = 34;
const PROJECT_MAX_HEADER_HEIGHT = 180;
const PROJECT_VIRTUAL_OVERSCAN = 72;
const PROJECT_VIRTUAL_RENDER_CHUNK = 18;
const PROJECT_BOTTOM_BLANK_ROWS = 5;
const PROJECT_UNDO_LIMIT = 30;
const PROJECT_MIN_COLUMN_WIDTH = 58;

const PROJECT_SPREADSHEET_COLUMNS = [
    { key: 'tracking_id', label: 'STT', zhLabel: '序号', width: 88, readOnly: true, fields: ['Tracking ID', 'tracking_id'], className: 'col-stt' },
    { key: 'ngay', label: 'Ngày', zhLabel: '日期', width: 96, fields: ['Ngày', 'Created_Date'], updateKey: 'Ngày', type: 'date' },
    { key: 'khachhang', label: 'Khách hàng', zhLabel: '客户', width: 118, fields: ['Khách hàng', 'khach_hang'], updateKey: 'Khách hàng' },
    { key: 'nhanvienkd', label: 'Nhân viên kinh doanh', zhLabel: '业务员', width: 126, fields: ['Nhân viên KD', 'Nhân viên kinh doanh', 'nhan_vien_kinh_doanh'], updateKey: 'Nhân viên kinh doanh' },
    { key: 'tensanpham', label: 'Tên sản phẩm', zhLabel: '客户需求名称', width: 150, fields: ['Tên sản phẩm', 'ten_san_pham'], updateKey: 'Tên sản phẩm' },
    { key: 'quycach', label: 'Quy cách', zhLabel: '客户需求规格', width: 160, fields: ['Quy cách', 'quy_cach'], updateKey: 'Quy cách' },
    { key: 'yeucaukythuat', label: 'Yêu cầu kỹ thuật KH', zhLabel: '客户技术要求', width: 126, fields: ['客户技术要求', 'Yêu cầu kỹ thuật KH', 'khach_hang_yeu_cau_ky_thuat'], updateKey: '客户技术要求', type: 'longText', displayAsLink: true },
    { key: 'lienhe', label: 'Người liên hệ (KH)', zhLabel: '对接人', width: 114, fields: ['Người liên hệ (KH)', 'Người liên hệ\n(KH)', 'nguoi_lien_he_kh'], updateKey: 'Người liên hệ (KH)' },
    { key: 'soluong', label: 'Số lượng', zhLabel: '数量', width: 72, fields: ['Số lượng', 'so_luong'], updateKey: 'Số lượng', type: 'number', className: 'text-center' },
    { key: 'mapo', label: 'Mã PO', zhLabel: 'PO号', width: 112, fields: ['Mã PO', 'ma_po'], updateKey: 'Mã PO' },
    { key: 'dokhan', label: 'Tính cấp bách', zhLabel: '紧急程度', width: 112, fields: ['Tính cấp bách', 'Mức độ khẩn cấp', 'Độ khẩn', 'urgency_level'], updateKey: 'Tính cấp bách', type: 'select', optionsSource: 'urgency' },
    { key: 'tg_mongmuon', label: 'Thời gian mong muốn có bản vẽ', zhLabel: '期望出图时间', width: 146, fields: ['Thời gian mong muốn có bản vẽ', 'TG mong muốn', 'thoi_gian_mong_muon_ban_ve'], updateKey: 'Thời gian mong muốn có bản vẽ', type: 'datetime' },
    { key: 'trangthai', label: 'Trạng thái nhận', zhLabel: '接收状态', width: 108, fields: ['is_pending', 'Trạng thái chờ'], updateKey: 'is_pending', type: 'select', optionsSource: 'pendingStatus' },
    { key: 'nguoinhan', label: 'Người nhận', zhLabel: '接收人', width: 108, fields: ['accepted_by', 'Người nhận'], updateKey: 'accepted_by' },
    { key: 'tg_tiepnhan', label: 'Thời gian tiếp nhận phương án', zhLabel: '接收方案时间', width: 142, fields: ['Thời gian nhận', 'accepted_at'], updateKey: 'accepted_at', type: 'datetime' },
    { key: 'mabave', label: 'Mã bản vẽ phương án', zhLabel: '方案图号（下单前）', width: 146, fields: ['Mã bản vẽ phương án', 'Mã bản vẽ phương án (mã trước khi đặt hàng)', 'Mã bản vẽ', 'ma_ban_ve'], updateKey: 'Mã bản vẽ phương án (mã trước khi đặt hàng)' },
    { key: 'mabavkythuat', label: 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)', zhLabel: '工程图号（下单后）', width: 166, fields: ['Mã bản vẽ kỹ thuật (sau khi đặt hàng)', 'Mã bản vẽ kỹ thuật', 'ma_ban_ve_ky_thuat'], updateKey: 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)' },
    { key: 'mame', label: 'Mã mẹ', zhLabel: '母料号', width: 118, fields: ['Mã mẹ', 'Mã mẹ ', 'Mã thành phẩm (Mã mẹ)', 'ma_me'], updateKey: 'Mã mẹ' },
    { key: 'loaisanpham', label: 'Loại sản phẩm', zhLabel: '产品类型', width: 168, fields: ['Loại sản phẩm', 'Hạng mục', 'loai_san_pham'], updateKey: 'Loại sản phẩm', type: 'select', optionsSource: 'productTypes' },
    { key: 'nhanvienthietke', label: 'Nhân viên thiết kế', zhLabel: '设计者', width: 122, fields: ['Nhân viên thiết kế', 'Kỹ sư thiết kế', 'nhan_vien_thiet_ke'], updateKey: 'Nhân viên thiết kế', type: 'select', optionsSource: 'engineers' },
    { key: 'tinhtrang', label: 'Tình trạng hoàn thành dự án', zhLabel: '工程完成情况', width: 166, fields: ['Tình trạng hoàn thành dự án', 'Tình trạng', 'tinh_trang_hoan_thanh'], updateKey: 'Tình trạng hoàn thành dự án', type: 'select', optionsSource: 'completionStatus' },
    { key: 'tg_hoanthanh', label: 'Thời gian hoàn thành kế hoạch', zhLabel: '方案完成时间', width: 146, fields: ['Thời gian hoàn thành kế hoạch', 'TG hoàn thành', 'thoi_gian_hoan_thanh_ke_hoach'], updateKey: 'Thời gian hoàn thành kế hoạch', type: 'datetime' }
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

function getProjectsLanguage() {
    return typeof getCurrentLanguage === 'function' ? getCurrentLanguage() : (window.currentLanguage || 'vi');
}

function localizeMixedProjectLabel(label) {
    const text = String(label || '');
    const lang = getProjectsLanguage();
    if (!text) return '';

    if (text.includes(' / ')) {
        const parts = text.split(' / ');
        return lang === 'zh' ? (parts[1] || parts[0]).trim() : parts[0].trim();
    }

    const dashMatch = text.match(/^(.+?)\s*-\s*(.+)$/);
    if (dashMatch) {
        return lang === 'zh' ? dashMatch[1].trim() : dashMatch[2].trim();
    }

    return text.trim();
}

function getProjectOptionValue(option) {
    return typeof option === 'object' ? option.value : option;
}

function getProjectOptionLabel(option) {
    const label = typeof option === 'object' ? option.label : option;
    return localizeMixedProjectLabel(label);
}

function getDefaultProjectColumnOrder() {
    return PROJECT_SPREADSHEET_COLUMNS.map(column => column.key);
}

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
    
    loadProjectTableLayout();
    loadProjectFilterState();

    // Render the module content
    renderProjectsContent();
    applyProjectFilterControlsState();
    
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
    startProjectsRealtime();
    startProjectLockCleanup();
    syncProjectTableLayoutFromServer();
    syncProjectFilterStateFromServer();
}

/**
 * Render Projects module content
 */
function renderProjectsContent() {
    const container = document.getElementById('projects-container');
    
    container.innerHTML = `
        <div class="card mb-2 projects-toolbar-card">
            <div class="card-body py-2">
                <div class="projects-toolbar">
                    <div class="projects-toolbar-actions">
                        <button class="btn btn-sm btn-primary" type="button" id="btn-add-project" title="${t('add_project')}">
                            <i class="bi bi-plus-circle"></i><span>${t('add_project')}</span>
                        </button>
                        <button class="btn btn-sm btn-outline-primary" type="button" id="btn-undo-project" title="${t('undo')} (Ctrl+Z)" disabled>
                            <i class="bi bi-arrow-counterclockwise"></i><span>${t('undo')}</span>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" type="button" id="btn-toggle-columns" title="${t('btn_toggle_columns')}">
                            <i class="bi bi-layout-columns"></i><span>${t('btn_toggle_columns')}</span>
                        </button>
                    </div>
                    <div class="projects-toolbar-filters">
                        <select class="form-select form-select-sm" id="filter-status" title="${t('filter_status')}">
                            <option value="">${t('all_status')}</option>
                            <option value="pending">${t('status_pending')}</option>
                            <option value="in_progress">${t('status_in_progress')}</option>
                            <option value="completed">${t('status_completed')}</option>
                        </select>
                        <select class="form-select form-select-sm" id="filter-urgency" title="${t('filter_urgency')}">
                            <option value="">${t('all_urgency')}</option>
                            <option value="normal">${t('urgency_normal')}</option>
                            <option value="urgent">${t('urgency_urgent')}</option>
                            <option value="very_urgent">${t('urgency_very_urgent')}</option>
                        </select>
                        <div class="input-group input-group-sm projects-search">
                            <button class="btn btn-outline-secondary" type="button" id="btn-apply-search-project" title="Enter">
                                <i class="bi bi-search"></i>
                            </button>
                            <input type="text" class="form-control" id="search-input-project"
                                   value="${escapeHtml(ProjectsState.searchDraft || ProjectsState.searchText || '')}"
                                   placeholder="${t('search_projects') || 'Tìm kiếm...'}" title="Ctrl+F, Enter">
                            <button class="btn btn-outline-secondary" type="button" id="btn-clear-search" title="${t('clear_search')}">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                    </div>
                    <div class="projects-presence" id="projects-presence" title="Người đang online" tabindex="0">
                        <span class="projects-presence-dot"></span>
                        <span id="projects-presence-count">0</span>
                        <div class="projects-presence-popover" id="projects-presence-popover" role="tooltip"></div>
                    </div>
                    <span class="projects-filter-count" id="projects-filter-count"></span>
                </div>
            </div>
        </div>
        
        <!-- Column Visibility Dropdown (Hidden by default) -->
        <div class="column-selector-popup" id="column-selector" style="display: none;">
            <div class="column-selector-header">
                <div class="column-selector-title">
                    <span class="column-selector-title-icon"><i class="bi bi-layout-three-columns"></i></span>
                    <div>
                        <h6 class="mb-0" data-i18n="column_selector_title">${t('column_selector_title')}</h6>
                        <small data-i18n="column_selector_hint">${t('column_selector_hint') || 'Kéo để đổi vị trí cột'}</small>
                    </div>
                </div>
                <button type="button" class="btn-close" id="btn-close-column-selector" aria-label="Close"></button>
            </div>
            <div class="column-selector-body" id="column-selector-body">
                <!-- Generated by JS -->
            </div>
            <div class="column-selector-footer">
                <button class="btn btn-sm btn-outline-secondary" id="btn-reset-columns"><i class="bi bi-arrow-counterclockwise"></i> <span data-i18n="column_reset">${t('column_reset')}</span></button>
                <button class="btn btn-sm btn-primary" id="btn-apply-columns"><i class="bi bi-check2"></i> <span data-i18n="column_apply">${t('column_apply')}</span></button>
            </div>
        </div>

        <div class="project-filter-popup" id="project-column-filter" style="display: none;">
            <div class="project-filter-head">
                <strong id="project-filter-title">${t('column_filter_title')}</strong>
                <button type="button" class="btn-close" id="btn-close-project-filter"></button>
            </div>
            <div class="input-group input-group-sm project-filter-search">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" class="form-control" id="project-filter-search" placeholder="${t('search_in_column')}">
            </div>
            <div class="project-filter-tools">
                <button type="button" class="btn btn-sm btn-link" id="btn-project-filter-all">${t('select_all')}</button>
                <button type="button" class="btn btn-sm btn-link text-danger" id="btn-project-filter-clear">${t('clear_filter')}</button>
            </div>
            <div class="project-filter-values" id="project-filter-values"></div>
            <div class="project-filter-foot">
                <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-cancel-project-filter">${t('cancel')}</button>
                <button type="button" class="btn btn-sm btn-primary" id="btn-apply-project-filter">${t('save')}</button>
            </div>
        </div>

        <!-- Data Table -->
        <div class="card">
            <div class="card-body p-0">
                <div class="table-responsive" id="projects-table-wrap">
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
        <div id="project-row-context-menu" class="project-context-menu" style="position: fixed; display: none; z-index: 2200;" role="menu">
            <div class="project-context-head">
                <div class="project-context-icon"><i class="bi bi-grid-3x3-gap"></i></div>
                <div class="project-context-title-wrap">
                    <div class="project-context-title" data-menu-meta="title">${t('projects_title')}</div>
                    <div class="project-context-subtitle" data-menu-meta="subtitle">${t('context_choose_action')}</div>
                </div>
                <span class="project-context-badge" data-menu-meta="badge">Sheet</span>
            </div>
            <div class="project-context-section">
                <button type="button" class="project-context-item ctx-view"><span class="ctx-icon is-info"><i class="bi bi-eye"></i></span><span data-menu-label="view">${t('quick_view')}</span><kbd>Enter</kbd></button>
                <button type="button" class="project-context-item ctx-edit"><span class="ctx-icon is-warning"><i class="bi bi-pencil"></i></span><span data-menu-label="edit">${t('quick_edit')}</span><kbd>F2</kbd></button>
                <button type="button" class="project-context-item ctx-add"><span class="ctx-icon is-success"><i class="bi bi-plus-circle"></i></span><span data-menu-label="add">${t('add')}</span><kbd>+</kbd></button>
            </div>
            <div class="project-context-section">
                <button type="button" class="project-context-item ctx-copy-cell"><span class="ctx-icon"><i class="bi bi-copy"></i></span><span data-menu-label="copyCell">${t('copy_cell')}</span><kbd>Ctrl+C</kbd></button>
                <button type="button" class="project-context-item ctx-copy-row"><span class="ctx-icon"><i class="bi bi-table"></i></span><span data-menu-label="copyRow">${t('copy_row')}</span></button>
                <button type="button" class="project-context-item ctx-filter-value"><span class="ctx-icon"><i class="bi bi-funnel"></i></span><span data-menu-label="filterValue">${t('filter_this_value')}</span></button>
                <button type="button" class="project-context-item ctx-comments"><span class="ctx-icon is-primary"><i class="bi bi-chat-left-text"></i></span><span data-menu-label="comments">Bình luận</span></button>
                <button type="button" class="project-context-item ctx-change-log"><span class="ctx-icon is-info"><i class="bi bi-clock-history"></i></span><span data-menu-label="changeLog">Lịch sử chỉnh sửa</span></button>
                <button type="button" class="project-context-item ctx-material-docs"><span class="ctx-icon is-primary"><i class="bi bi-folder2-open"></i></span><span data-menu-label="materialDocs">Tài liệu mã liệu</span></button>
            </div>
            <div class="project-context-section">
                <button type="button" class="project-context-item ctx-refresh"><span class="ctx-icon"><i class="bi bi-arrow-clockwise"></i></span><span data-menu-label="refresh">${t('refresh')}</span></button>
                <button type="button" class="project-context-item ctx-columns"><span class="ctx-icon"><i class="bi bi-layout-columns"></i></span><span data-menu-label="columns">${t('btn_toggle_columns')}</span></button>
            </div>
            <div class="project-context-section">
                <button type="button" class="project-context-item ctx-export-excel"><span class="ctx-icon is-success"><i class="bi bi-file-earmark-excel"></i></span><span data-menu-label="exportExcel">${t('export_excel')}</span></button>
                <button type="button" class="project-context-item ctx-export-csv"><span class="ctx-icon is-primary"><i class="bi bi-file-earmark-text"></i></span><span data-menu-label="exportCsv">${t('export_csv')}</span></button>
            </div>
            <div class="project-context-section is-danger-section">
                <button type="button" class="project-context-item is-danger ctx-delete"><span class="ctx-icon is-danger"><i class="bi bi-trash"></i></span><span data-menu-label="delete">${t('quick_delete')}</span><kbd>Del</kbd></button>
            </div>
        </div>
        <div class="modal fade" id="project-material-docs-modal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="project-material-docs-title">Tài liệu mã liệu</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="project-material-docs-body">
                        <div class="text-muted">Đang tải...</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal fade" id="project-change-log-modal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="project-change-log-title">Lịch sử chỉnh sửa</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="project-change-log-body">
                        <div class="text-muted">Đang tải...</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal fade" id="project-comments-modal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="project-comments-title">Bình luận</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="project-comments-body" class="project-comments-body">
                            <div class="text-muted">Đang tải...</div>
                        </div>
                        <div class="project-comment-compose">
                            <textarea class="form-control" id="project-comment-input" rows="3" maxlength="1000" placeholder="Nhập bình luận..."></textarea>
                            <button type="button" class="btn btn-primary" id="btn-send-project-comment">
                                <i class="bi bi-send"></i><span>Gửi</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Add/Edit Modal -->
        <div class="modal fade project-modal-smart" id="project-modal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-xl modal-dialog-scrollable">
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
                            <div class="row g-3 project-form-grid project-form-vertical">
                                <div class="col-12">
                                    <label class="form-label">${t('form_ngay_khoitao')}</label>
                                    <input type="datetime-local" class="form-control" id="field-ngay">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_khachhang_required')}</label>
                                    <div class="row g-2 project-customer-field-stack">
                                        <div class="col-12">
                                            <select class="form-select" id="field-khachhang-select">
                                                <option value="">${t('select_customer')}</option>
                                            </select>
                                        </div>
                                        <div class="col-12">
                                            <input type="text" class="form-control" id="field-khachhang"
                                                   placeholder="${t('enter_customer_placeholder')}">
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
                            <div class="row g-3 project-form-grid project-form-vertical">
                                <div class="col-12">
                                    <label class="form-label">${t('form_tensanpham_required')}</label>
                                    <input type="text" class="form-control" id="field-tensanpham">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_quycach')}</label>
                                    <input type="text" class="form-control" id="field-quycach">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_khachhang_yeucau_kythuat')}</label>
                                    <textarea class="form-control" id="field-yeucaukythuat" rows="4" maxlength="1000"></textarea>
                                    <div class="form-text project-textarea-counter" id="field-yeucaukythuat-counter">0/1000</div>
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
                            <div class="row g-3 project-form-grid project-form-vertical">
                                <div class="col-12">
                                    <label class="form-label">${t('form_capbach')}</label>
                                    <select class="form-select" id="field-capbach">
                                        <option value="normal">${localizeMixedProjectLabel('正常 - Bình thường')}</option>
                                        <option value="urgent">${localizeMixedProjectLabel('紧急 - Khẩn cấp')}</option>
                                        <option value="very_urgent">${localizeMixedProjectLabel('非常紧急 - Rất khẩn cấp')}</option>
                                    </select>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">${t('form_tg_mongmuon')}</label>
                                    <div class="smart-deadline-field">
                                        <span class="smart-deadline-icon"><i class="bi bi-calendar-check"></i></span>
                                        <input type="datetime-local" class="form-control" id="field-tg-mongmuon" readonly>
                                    </div>
                                    <div class="form-text smart-deadline-note" id="smart-deadline-note">${t('deadline_normal_note')}</div>
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
        <div class="modal fade project-detail-modal" id="view-modal-project" tabindex="-1">
            <div class="modal-dialog modal-xl modal-dialog-scrollable">
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
    $(document).off('mousedown.projectSelectionClear').on('mousedown.projectSelectionClear', function(e) {
        if (!$(e.target).closest('#projects-table, .project-filter-popup, .modal').length) {
            ProjectsState.rangeSelection = null;
            ProjectsState.selectedCells = [];
            updateProjectSelection();
        }
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

    $('#btn-toggle-columns').click(function(e) {
        e.preventDefault();
        toggleColumnSelector();
    });

    $('#btn-add-project').click(function() {
        if (!canCurrentUserCreateProject()) {
            showToast(t('warning'), 'Bạn không có quyền tạo dự án.', 'warning');
            return;
        }
        showProjectModal();
    });

    $('#btn-undo-project').click(function() {
        undoLastProjectAction();
    });

    $('#btn-send-project-comment').click(function() {
        submitProjectComment();
    });

    $('#project-change-log-body')
        .off('click.projectRevert')
        .on('click.projectRevert', '.btn-revert-project-change', function() {
            const changeId = Number($(this).data('changeId'));
            if (changeId) revertProjectChange(changeId);
        });

    $('#project-material-docs-body')
        .off('click.projectMaterialFolder')
        .on('click.projectMaterialFolder', '.btn-open-material-folder', function() {
            const listUrl = String($(this).data('listUrl') || '');
            const folderName = String($(this).data('folderName') || '');
            if (listUrl) loadProjectMaterialFolder(listUrl, folderName);
        });

    $(document).off('change.projectDeadline').on('change.projectDeadline', '#field-ngay, #field-capbach', function() {
        updateProjectExpectedDrawingTime();
    });
    
    // Filter: Status
    $('#filter-status').change(function() {
        ProjectsState.filterStatus = $(this).val();
        ProjectsState.currentPage = 1;
        saveProjectFilterState();
        renderProjectsTablePreservingViewport();
    });
    
    // Filter: Urgency
    $('#filter-urgency').change(function() {
        ProjectsState.filterUrgency = $(this).val();
        ProjectsState.currentPage = 1;
        saveProjectFilterState();
        renderProjectsTablePreservingViewport();
    });
    
    // Search input
    $('#search-input-project').on('input', debounce(function(e) {
        ProjectsState.searchDraft = e?.target?.value || '';
        updateProjectSearchDirtyState();
        saveProjectFilterState();
    }, 180));

    $('#search-input-project').on('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyProjectSearchFromInput();
        }
    });

    $('#btn-apply-search-project').click(function() {
        applyProjectSearchFromInput();
    });
    
    // Clear search
    $('#btn-clear-search').click(function() {
        $('#search-input-project').val('');
        ProjectsState.searchDraft = '';
        ProjectsState.searchText = '';
        ProjectsState.currentPage = 1;
        saveProjectFilterState();
        updateProjectSearchDirtyState();
        renderProjectsTablePreservingViewport();
    });
    
    // Save button
    $('#btn-save-project').click(function() {
        saveProject();
    });
    
    // Confirm delete button
    $('#btn-confirm-delete-project').click(function() {
        deleteSelectedProjects();
    });

    $('#btn-close-project-filter, #btn-cancel-project-filter').click(function() {
        hideProjectColumnFilter();
    });

    $('#btn-project-filter-all').click(function() {
        $('#project-filter-values input[type="checkbox"]').prop('checked', true);
    });

    $('#btn-project-filter-clear').click(function() {
        const key = ProjectsState.activeFilterKey;
        if (key) {
            delete ProjectsState.columnFilters[key];
            hideProjectColumnFilter();
            saveProjectFilterState();
            renderProjectsTablePreservingViewport();
        }
    });

    $('#btn-apply-project-filter').click(function() {
        applyProjectColumnFilter();
    });

    $('#project-filter-search').on('input', function() {
        renderProjectFilterValues($(this).val());
    });

    $(window).off('resize.projectsFitTable').on('resize.projectsFitTable', debounce(function() {
        if (!$('#projects-container').is(':visible')) return;
        applyProjectTableWidths();
    }, 120));

    $(document).off('keydown.projectShortcuts').on('keydown.projectShortcuts', function(e) {
        const isSearch = (e.ctrlKey || e.metaKey) && String(e.key).toLowerCase() === 'f';
        if (isSearch && $('#projects-container').is(':visible')) {
            e.preventDefault();
            const searchInput = $('#search-input-project');
            searchInput.trigger('focus').trigger('select');
            return;
        }

        const isUndo = (e.ctrlKey || e.metaKey) && !e.shiftKey && String(e.key).toLowerCase() === 'z';
        if (!isUndo || !$('#projects-container').is(':visible')) return;
        if ($(e.target).is('input, textarea, select') || ProjectsState.editingCell) return;
        e.preventDefault();
        undoLastProjectAction();
    });
    
    // Close column selector when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('#column-selector, #btn-toggle-columns, #project-row-context-menu, #project-column-filter, .project-filter-trigger').length) {
            $('#column-selector').hide();
            hideProjectColumnFilter();
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
    $('#btn-add-project')
        .attr('title', t('add_project'))
        .find('span')
        .text(t('add_project'));

    $('#btn-toggle-columns')
        .attr('title', t('btn_toggle_columns'))
        .find('span')
        .text(t('btn_toggle_columns'));

    // Search input placeholder
    const searchInput = $('#search-input-project');
    if (searchInput.length) {
        searchInput.attr('placeholder', t('search_projects') || t('search_placeholder'));
    }

    $('#project-filter-title').text(t('column_filter_title'));
    $('#project-filter-search').attr('placeholder', t('search_in_column'));
    $('#btn-project-filter-all').text(t('select_all'));
    $('#btn-project-filter-clear').text(t('clear_filter'));

    updateProjectContextMenuI18n();
}

function applyProjectFilterControlsState() {
    $('#filter-status').val(ProjectsState.filterStatus || '');
    $('#filter-urgency').val(ProjectsState.filterUrgency || '');
    $('#search-input-project').val(ProjectsState.searchDraft || ProjectsState.searchText || '');
    updateProjectSearchDirtyState();
}

function updateProjectSearchDirtyState() {
    const draft = String(ProjectsState.searchDraft ?? '');
    const applied = String(ProjectsState.searchText ?? '');
    $('.projects-search').toggleClass('is-dirty', draft !== applied);
    $('#btn-apply-search-project').toggleClass('btn-primary', draft !== applied);
    $('#btn-apply-search-project').toggleClass('btn-outline-secondary', draft === applied);
}

function applyProjectSearchFromInput() {
    const value = $('#search-input-project').val() || '';
    ProjectsState.searchDraft = value;
    ProjectsState.searchText = value;
    ProjectsState.currentPage = 1;
    saveProjectFilterState();
    updateProjectSearchDirtyState();
    renderProjectsTablePreservingViewport();
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
async function loadProjects(options = {}) {
    console.log('[Projects] Loading projects...');
    const viewportSnapshot = options.preserveScroll ? (options.viewportSnapshot || captureProjectViewport()) : null;
    
    const tbody = $('#projects-table-body');
    renderProjectsSpreadsheetHeader();
    tbody.html(createLoadingState(getVisibleProjectColumns().length));
    
    ProjectsState.isLoading = true;
    updateToolbarState();
    
    try {
        const result = await api.getProjects({
            page: ProjectsState.currentPage,
            limit: ProjectsState.pageSize
        });
        
        if (result && result.data) {
            ProjectsState.projects = result.data || [];
            ProjectsState.totalRecords = result.total || 0;
            ProjectsState.totalPages = Math.ceil(ProjectsState.totalRecords / ProjectsState.pageSize) || 1;
            
            renderProjectsTable();
            if (viewportSnapshot) {
                restoreProjectViewport(viewportSnapshot);
            } else if (ProjectsState.autoScrollToBottomOnLoad) {
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

function getProjectsCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('current_user') || '{}') || {};
    } catch (error) {
        return {};
    }
}

function normalizeProjectRole(role) {
    const normalized = String(role || '').trim().toLowerCase();
    const aliases = {
        it: 'admin',
        administrator: 'admin',
        eng: 'engineer',
        'kỹ thuật': 'engineer',
        'ky thuat': 'engineer',
        'sản xuất': 'production',
        'san xuat': 'production',
        'kế hoạch': 'planner',
        'ke hoach': 'planner'
    };
    return aliases[normalized] || normalized;
}

function getProjectCurrentRole() {
    return normalizeProjectRole(getProjectsCurrentUser().role);
}

function canCurrentUserCreateProject() {
    return true;
}

function canCurrentUserDeleteProject() {
    return getProjectCurrentRole() === 'admin';
}

function canCurrentUserEditAnyProject() {
    return ['admin', 'planner', 'sales', 'engineer'].includes(getProjectCurrentRole());
}

function canCurrentUserEditProjectColumn(column) {
    if (!column || column.readOnly || !column.updateKey) return false;
    const role = getProjectCurrentRole();
    if (['admin', 'planner', 'sales', 'engineer'].includes(role)) return true;
    if (role === 'production') return column.key === 'tinhtrang';
    return false;
}

function getProjectsRealtimeUserId() {
    const user = getProjectsCurrentUser();
    return String(user.user_id || user.username || 'anonymous');
}

function getProjectLockKey(id, fieldName) {
    return `${String(id)}:${String(fieldName || '')}`;
}

function setProjectLocks(locks = []) {
    ProjectsState.projectLocks = new Map();
    locks.forEach(lock => {
        if (!lock) return;
        ProjectsState.projectLocks.set(getProjectLockKey(lock.tracking_id, lock.field_name), lock);
    });
    pruneExpiredProjectLocks();
    applyProjectLocksToRenderedCells();
}

function upsertProjectLock(lock) {
    if (!lock) return;
    ProjectsState.projectLocks.set(getProjectLockKey(lock.tracking_id, lock.field_name), lock);
    pruneExpiredProjectLocks();
    applyProjectLocksToRenderedCells();
}

function removeProjectLock(trackingId, fieldName) {
    ProjectsState.projectLocks.delete(getProjectLockKey(trackingId, normalizeProjectUpdateField(fieldName)));
    ProjectsState.projectLocks.delete(getProjectLockKey(trackingId, fieldName));
    applyProjectLocksToRenderedCells();
}

function getProjectCellLock($cell, column = null) {
    if (!$cell || !$cell.length || $cell.data('draft')) return null;
    const id = String($cell.data('id') || '');
    const updateKey = column?.updateKey || $cell.data('update-key') || '';
    const fieldName = normalizeProjectUpdateField(updateKey);
    return ProjectsState.projectLocks.get(getProjectLockKey(id, fieldName)) || null;
}

function getProjectLockExpiryTime(lock) {
    if (!lock || !lock.expires_at) return 0;
    const parsed = new Date(lock.expires_at);
    const time = parsed.getTime();
    return Number.isFinite(time) ? time : 0;
}

function pruneExpiredProjectLocks() {
    const now = Date.now();
    let changed = false;
    ProjectsState.projectLocks.forEach((lock, key) => {
        const expiresAt = getProjectLockExpiryTime(lock);
        if (expiresAt && expiresAt <= now) {
            ProjectsState.projectLocks.delete(key);
            changed = true;
        }
    });
    return changed;
}

function startProjectLockCleanup() {
    if (ProjectsState.lockCleanupTimer) return;
    ProjectsState.lockCleanupTimer = setInterval(() => {
        if (pruneExpiredProjectLocks()) {
            applyProjectLocksToRenderedCells();
        }
    }, PROJECT_LOCK_CLEANUP_INTERVAL_MS);
}

function isProjectCellLockedByOther($cell, column = null) {
    const lock = getProjectCellLock($cell, column);
    if (!lock) return false;
    return String(lock.locked_by || '') !== getProjectsRealtimeUserId();
}

function applyProjectLocksToRenderedCells() {
    pruneExpiredProjectLocks();
    $('#projects-table-body .project-sheet-cell').each(function() {
        const $cell = $(this);
        const column = getVisibleProjectColumns()[Number($cell.data('col'))];
        const lock = getProjectCellLock($cell, column);
        const lockedByOther = lock && String(lock.locked_by || '') !== getProjectsRealtimeUserId();
        $cell.toggleClass('locked-cell', !!lock);
        $cell.toggleClass('locked-by-other', !!lockedByOther);
        if (lock) {
            $cell.attr('title', `${lock.locked_by_name || lock.locked_by || ''} đang chỉnh sửa`);
        } else {
            $cell.removeAttr('title');
        }
    });
    applyProjectRemoteCursorsToRenderedCells();
}

function getProjectCursorKey(cursor) {
    return `${String(cursor.tracking_id || '')}:${String(cursor.field_name || '')}`;
}

function upsertProjectRemoteCursor(cursor) {
    if (!cursor || String(cursor.user_id || '') === getProjectsRealtimeUserId()) return;
    cursor.updated_at = Date.now();
    ProjectsState.remoteCursors.set(String(cursor.user_id || cursor.user_name || 'unknown'), cursor);
    applyProjectRemoteCursorsToRenderedCells();
}

function applyProjectRemoteCursorsToRenderedCells() {
    const now = Date.now();
    const ownUserId = getProjectsRealtimeUserId();
    const activeCursors = [];
    ProjectsState.remoteCursors.forEach((cursor, key) => {
        if (!cursor || cursor.user_id === ownUserId || now - Number(cursor.updated_at || 0) > 30000) {
            ProjectsState.remoteCursors.delete(key);
        } else {
            activeCursors.push(cursor);
        }
    });

    $('#projects-table-body .project-sheet-cell')
        .removeClass('remote-cursor-cell')
        .removeAttr('data-remote-user');

    activeCursors.forEach(cursor => {
        const $cell = $(`#projects-table-body .project-sheet-cell[data-id="${CSS.escape(String(cursor.tracking_id || ''))}"][data-update-key]`)
            .filter(function() {
                return normalizeProjectUpdateField($(this).data('update-key')) === String(cursor.field_name || '');
            })
            .first();
        if (!$cell.length) return;
        $cell.addClass('remote-cursor-cell');
        $cell.attr('data-remote-user', cursor.user_name || cursor.user_id || '');
    });
}

function normalizeProjectUpdateField(fieldName) {
    const map = {
        'Ngày': 'Created_Date',
        'Khách hàng': 'khach_hang',
        'Nhân viên kinh doanh': 'nhan_vien_kinh_doanh',
        'Tên sản phẩm': 'ten_san_pham',
        'Quy cách': 'quy_cach',
        '客户技术要求': 'khach_hang_yeu_cau_ky_thuat',
        'Yêu cầu kỹ thuật KH': 'khach_hang_yeu_cau_ky_thuat',
        'Người liên hệ (KH)': 'nguoi_lien_he_kh',
        'Số lượng': 'so_luong',
        'Mã PO': 'ma_po',
        'Tính cấp bách': 'urgency_level',
        'is_pending': 'is_pending',
        'accepted_by': 'accepted_by',
        'accepted_at': 'accepted_at',
        'Mã bản vẽ phương án (mã trước khi đặt hàng)': 'ma_ban_ve',
        'Mã bản vẽ kỹ thuật (sau khi đặt hàng)': 'ma_ban_ve_ky_thuat',
        'Mã mẹ': 'ma_me',
        'Loại sản phẩm': 'loai_san_pham',
        'Nhân viên thiết kế': 'nhan_vien_thiet_ke',
        'Tình trạng hoàn thành dự án': 'tinh_trang_hoan_thanh',
        'Thời gian mong muốn có bản vẽ': 'thoi_gian_mong_muon_ban_ve',
        'Thời gian hoàn thành kế hoạch': 'thoi_gian_hoan_thanh_ke_hoach'
    };
    return map[fieldName] || fieldName;
}

function startProjectsRealtime() {
    if (ProjectsState.realtimeStream || typeof EventSource === 'undefined') return;
    const user = getProjectsCurrentUser();
    try {
        ProjectsState.realtimeStream = api.createProjectStream({
            user_id: user.user_id || '',
            username: user.username || '',
            user_name: user.full_name || user.display_name || user.username || ''
        });
    } catch (error) {
        console.warn('[Projects] Cannot open realtime stream:', error);
        return;
    }

    ProjectsState.realtimeStream.onopen = function() {
        ProjectsState.realtimeConnected = true;
    };
    ProjectsState.realtimeStream.onmessage = function(event) {
        handleProjectRealtimeEvent(event);
    };
    ProjectsState.realtimeStream.addEventListener('project', handleProjectRealtimeEvent);
    ProjectsState.realtimeStream.onerror = function() {
        ProjectsState.realtimeConnected = false;
    };
}

function handleProjectRealtimeEvent(event) {
    let payload;
    try {
        payload = JSON.parse(event.data || '{}');
    } catch (error) {
        return;
    }

    if (Array.isArray(payload.locks)) {
        setProjectLocks(payload.locks);
    }
    if (Array.isArray(payload.online_users)) {
        updateProjectsPresence(payload.online_users);
    }

    if (payload.type === 'cell_locked') {
        upsertProjectLock(payload.lock);
        return;
    }
    if (payload.type === 'cell_unlocked') {
        removeProjectLock(payload.tracking_id, payload.field_name);
        return;
    }
    if (payload.type === 'cursor') {
        upsertProjectRemoteCursor(payload.cursor);
        return;
    }
    if (payload.type === 'comment_added' || payload.type === 'comment_deleted') {
        refreshActiveProjectComments(payload);
        return;
    }
    if (payload.type === 'project_updated' && payload.record) {
        mergeRealtimeProjectRecord(payload.record);
        return;
    }
    if (payload.type === 'project_created') {
        if (!payload.record) {
            scheduleProjectsRealtimeReload();
            return;
        }
        mergeRealtimeProjectRecord(payload.record, { allowInsert: true });
        return;
    }
    if (payload.type === 'project_deleted') {
        removeRealtimeProjectRecord(payload.tracking_id);
    }
}

function updateProjectsPresence(users = []) {
    ProjectsState.onlineUsers = users;
    const count = users.length;
    const labels = users
        .map(user => user.full_name || user.user_name || user.username || user.user_id)
        .filter(Boolean);
    const label = labels.join(', ');
    $('#projects-presence-count').text(String(count));
    $('#projects-presence').attr('title', label ? `Online: ${label}` : 'Người đang online');
    renderProjectsPresencePopover(labels);
}

function renderProjectsPresencePopover(labels = []) {
    const popover = $('#projects-presence-popover');
    if (!popover.length) return;
    const items = labels.length
        ? labels.map(label => `<div class="projects-presence-user"><span class="projects-presence-user-dot"></span><span>${escapeHtml(label)}</span></div>`).join('')
        : `<div class="projects-presence-empty">${escapeHtml(t('no_online_users') || 'Chưa có người online')}</div>`;
    popover.html(`
        <div class="projects-presence-popover-title">${escapeHtml(t('online_users') || 'Đang online')}</div>
        <div class="projects-presence-list">${items}</div>
    `);
}

function mergeRealtimeProjectRecord(record, options = {}) {
    const id = getProjectId(record);
    if (!id) return;
    const oldDisplayIndex = getDisplayProjects().findIndex(project => getProjectId(project) === String(id));
    const index = ProjectsState.projects.findIndex(project => getProjectId(project) === String(id));
    let mergedRecord = record;
    if (index >= 0) {
        mergedRecord = { ...ProjectsState.projects[index], ...record };
        ProjectsState.projects[index] = mergedRecord;
    } else if (options.allowInsert) {
        ProjectsState.projects.push(record);
        ProjectsState.totalRecords = Math.max(ProjectsState.totalRecords || 0, ProjectsState.projects.length);
        renderProjectsVirtualRowsPreservingViewport();
        updateToolbarState();
        return;
    } else {
        scheduleProjectsRealtimeReload();
        return;
    }

    const newDisplayIndex = getDisplayProjects().findIndex(project => getProjectId(project) === String(id));
    if (oldDisplayIndex !== newDisplayIndex || newDisplayIndex < 0) {
        renderProjectsVirtualRowsPreservingViewport();
    } else {
        patchRenderedProjectRow(mergedRecord, newDisplayIndex);
    }
    updateToolbarState();
}

function scheduleProjectsRealtimeReload() {
    if (ProjectsState.realtimeReloadTimer) return;
    ProjectsState.realtimeReloadTimer = setTimeout(() => {
        ProjectsState.realtimeReloadTimer = null;
        loadProjects({ preserveScroll: true });
    }, 500);
}

function removeRealtimeProjectRecord(trackingId) {
    const id = String(trackingId || '');
    if (!id) return;
    const index = ProjectsState.projects.findIndex(project => getProjectId(project) === id);
    if (index < 0) return;
    ProjectsState.projects.splice(index, 1);
    ProjectsState.totalRecords = Math.max(0, (ProjectsState.totalRecords || 1) - 1);
    ProjectsState.selectedIds = ProjectsState.selectedIds.filter(selectedId => String(selectedId) !== id);
    renderProjectsVirtualRowsPreservingViewport();
    updateToolbarState();
}

function renderProjectsVirtualRowsPreservingViewport() {
    const viewportSnapshot = captureProjectViewport();
    renderProjectsVirtualRows({ force: true });
    restoreProjectViewport(viewportSnapshot);
}

function patchRenderedProjectRow(project, rowIndex) {
    const trackingId = getProjectId(project);
    const $row = $('#projects-table-body tr').filter(function() {
        return String($(this).data('id')) === String(trackingId);
    });
    if (!$row.length) return;

    const columns = getVisibleProjectColumns();
    columns.forEach((column, colIndex) => {
        const $cell = $row.find(`.project-sheet-cell[data-col="${colIndex}"]`);
        if (!$cell.length || $cell.data('draft') || $cell.data('blank')) return;
        if (ProjectsState.editingCell === $cell[0]) return;
        const rawValue = getProjectValue(project, column.fields, '');
        renderProjectCellDisplay($cell, column, rawValue);
        $cell.attr('data-row', rowIndex);
    });
    $row.attr('data-row-index', rowIndex);
    applyProjectLocksToRenderedCells();
}

function scrollProjectsToBottom() {
    const wrap = document.getElementById('projects-table-wrap');
    if (!wrap) return;
    const dataRows = getDisplayProjects().length + 1;
    const targetBottom = dataRows * getProjectRowHeight();
    wrap.scrollTop = Math.max(0, targetBottom - wrap.clientHeight + getProjectHeaderHeight());
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
    renderProjectsSpreadsheetHeader();
    renderProjectsVirtualRows({ force: true });
    setupProjectsVirtualScroll();
    setupSpreadsheetHandlers();
    updateToolbarState();
}

function renderProjectsTablePreservingViewport() {
    const viewportSnapshot = captureProjectViewport();
    renderProjectsTable();
    restoreProjectViewport(viewportSnapshot);
}

function captureProjectViewport() {
    const wrap = document.getElementById('projects-table-wrap');
    const activeCell = ProjectsState.activeCell ? { ...ProjectsState.activeCell } : null;
    return {
        scrollTop: wrap ? wrap.scrollTop : 0,
        scrollLeft: wrap ? wrap.scrollLeft : 0,
        activeCell
    };
}

function restoreProjectViewport(snapshot) {
    if (!snapshot) return;
    const restore = () => {
        const wrap = document.getElementById('projects-table-wrap');
        if (!wrap) return;
        wrap.scrollTop = snapshot.scrollTop || 0;
        wrap.scrollLeft = snapshot.scrollLeft || 0;
        renderProjectsVirtualRows();
        if (snapshot.activeCell) {
            requestAnimationFrame(() => {
                const $cell = $(`#projects-table-body .project-sheet-cell[data-row="${snapshot.activeCell.row}"][data-col="${snapshot.activeCell.col}"]`);
                if ($cell.length) activateProjectCell($cell);
            });
        }
    };
    requestAnimationFrame(() => {
        restore();
        setTimeout(restore, 80);
    });
}

function setupProjectsVirtualScroll() {
    const wrap = document.getElementById('projects-table-wrap');
    if (!wrap || wrap.dataset.virtualScrollReady === 'true') return;

    wrap.dataset.virtualScrollReady = 'true';
    wrap.addEventListener('scroll', () => {
        if (ProjectsState.virtualScrollFrame) return;
        ProjectsState.virtualScrollFrame = requestAnimationFrame(() => {
            ProjectsState.virtualScrollFrame = null;
            renderProjectsVirtualRows();
        });
    }, { passive: true });
}

function getProjectVirtualRange() {
    const wrap = document.getElementById('projects-table-wrap');
    const totalRows = getProjectVirtualTotalRows();
    const rowHeight = getProjectRowHeight();
    if (!wrap || totalRows <= 0) {
        return { start: 0, end: totalRows };
    }

    const visibleRows = Math.ceil(wrap.clientHeight / rowHeight);
    const firstVisibleRow = Math.max(0, Math.floor(wrap.scrollTop / rowHeight));
    const lastVisibleRow = Math.min(totalRows, firstVisibleRow + visibleRows);
    const rawStart = Math.max(0, firstVisibleRow - PROJECT_VIRTUAL_OVERSCAN);
    const rawEnd = Math.min(totalRows, lastVisibleRow + PROJECT_VIRTUAL_OVERSCAN);
    const start = Math.max(0, Math.floor(rawStart / PROJECT_VIRTUAL_RENDER_CHUNK) * PROJECT_VIRTUAL_RENDER_CHUNK);
    const end = Math.min(totalRows, Math.ceil(rawEnd / PROJECT_VIRTUAL_RENDER_CHUNK) * PROJECT_VIRTUAL_RENDER_CHUNK);
    return { start, end };
}

function renderProjectsVirtualRows(options = {}) {
    const tbody = $('#projects-table-body');
    let html = '';
    const columns = getVisibleProjectColumns();
    const displayProjects = getDisplayProjects();
    const totalRows = getProjectVirtualTotalRows(displayProjects.length);
    const { start, end } = getProjectVirtualRange();
    if (!options.force && start === ProjectsState.virtualStart && end === ProjectsState.virtualEnd && tbody.children().length > 0) {
        return;
    }
    ProjectsState.virtualStart = start;
    ProjectsState.virtualEnd = end;
    const rowHeight = getProjectRowHeight();

    if (start > 0) {
        html += renderProjectSpacerRow(columns.length, start * rowHeight, 'top');
    }
    
    for (let rowIndex = start; rowIndex < end; rowIndex += 1) {
        if (rowIndex === displayProjects.length) {
            html += renderQuickAddProjectRow(columns, rowIndex);
            continue;
        }

        const project = displayProjects[rowIndex];
        if (!project) {
            html += renderProjectBlankRow(columns, rowIndex);
            continue;
        }
        const trackingId = getProjectValue(project, ['Tracking ID', 'tracking_id'], '');
        html += `<tr data-id="${escapeHtml(String(trackingId))}" data-row-index="${rowIndex}">`;

        columns.forEach((column, colIndex) => {
            const rawValue = getProjectValue(project, column.fields, '');
            const displayValue = formatProjectCellValue(column, rawValue, rowIndex);
            const canEdit = canCurrentUserEditProjectColumn(column);
            const selectionClasses = getSelectionRangeClasses(rowIndex, colIndex);
            const classes = [
                'project-sheet-cell',
                canEdit ? 'editable' : 'readonly',
                column.className || '',
                getProjectCellStateClass(column, rawValue),
                selectionClasses
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
                    ${wrapProjectCellContent(displayValue)}
                    ${colIndex === 0 ? '<span class="project-row-height-resizer" title="Kéo để đổi chiều cao hàng"></span>' : ''}
                </td>
            `;
        });

        html += '</tr>';
    }

    if (end < totalRows) {
        html += renderProjectSpacerRow(columns.length, (totalRows - end) * rowHeight, 'bottom');
    }
    
    tbody.html(html);
    applyProjectLocksToRenderedCells();
}

function getProjectBottomBlankRowCount() {
    return PROJECT_BOTTOM_BLANK_ROWS;
}

function getProjectVirtualTotalRows(displayCount = getDisplayProjects().length) {
    return displayCount + 1 + getProjectBottomBlankRowCount();
}

function renderProjectSpacerRow(colspan, height, position) {
    return `
        <tr class="project-virtual-spacer project-virtual-spacer-${position}" aria-hidden="true">
            <td colspan="${colspan}" style="height: ${height}px; padding: 0; border: 0;"></td>
        </tr>
    `;
}

function renderProjectBlankRow(columns, rowIndex) {
    let html = `<tr class="project-blank-row" data-row-index="${rowIndex}" data-blank-row="true" aria-hidden="true">`;
    columns.forEach((column, colIndex) => {
        html += `
            <td class="project-sheet-cell project-blank-cell readonly ${column.className || ''}"
                data-row="${rowIndex}"
                data-col="${colIndex}"
                data-key="${escapeHtml(column.key)}"
                data-id=""
                data-blank="true"
                data-raw-value="">
                ${wrapProjectCellContent('')}
            </td>
        `;
    });
    html += '</tr>';
    return html;
}

function wrapProjectCellContent(content) {
    return `<div class="project-cell-content">${content}</div>`;
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
                ${wrapProjectCellContent(renderQuickAddControl())}
                <span class="project-row-height-resizer" title="Kéo để đổi chiều cao hàng"></span>
            </td>
        `;
        html += '</tr>';
        return html;
    }

    columns.forEach((column, colIndex) => {
        const rawValue = getProjectDraftValue(column);
        const isReadonly = column.readOnly || !canCurrentUserCreateProject();
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
                ${wrapProjectCellContent(displayValue)}
                ${colIndex === 0 ? '<span class="project-row-height-resizer" title="Kéo để đổi chiều cao hàng"></span>' : ''}
            </td>
        `;
    });

    html += '</tr>';
    return html;
}

function renderQuickAddControl() {
    if (!ProjectsState.quickAddStarted) {
        if (!canCurrentUserCreateProject()) {
            return `<span class="quick-add-readonly">Chỉ xem</span>`;
        }
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

function getProjectOrderedColumns() {
    const byKey = new Map(PROJECT_SPREADSHEET_COLUMNS.map(column => [column.key, column]));
    const savedOrder = Array.isArray(ProjectsState.columnOrder) ? ProjectsState.columnOrder : [];
    const orderedKeys = savedOrder.filter(key => byKey.has(key));
    getDefaultProjectColumnOrder().forEach(key => {
        if (!orderedKeys.includes(key)) orderedKeys.push(key);
    });
    return orderedKeys.map(key => byKey.get(key)).filter(Boolean);
}

function getVisibleProjectColumns() {
    return getProjectOrderedColumns().filter(column => ProjectsState.visibleColumns[column.key] !== false);
}

function getProjectColumnWidth(column) {
    const savedWidth = Number(ProjectsState.columnWidths[column.key]);
    const baseWidth = Number(column.width || 100);
    return Math.max(PROJECT_MIN_COLUMN_WIDTH, Number.isFinite(savedWidth) && savedWidth > 0 ? savedWidth : baseWidth);
}

function clampProjectNumber(value, min, max, fallback) {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) return fallback;
    return Math.max(min, Math.min(max, Math.round(numericValue)));
}

function getProjectRowHeight() {
    return clampProjectNumber(ProjectsState.rowHeight, PROJECT_MIN_ROW_HEIGHT, PROJECT_MAX_ROW_HEIGHT, PROJECT_DEFAULT_ROW_HEIGHT);
}

function getProjectHeaderHeight() {
    return clampProjectNumber(ProjectsState.headerHeight, PROJECT_MIN_HEADER_HEIGHT, PROJECT_MAX_HEADER_HEIGHT, PROJECT_DEFAULT_HEADER_HEIGHT);
}

function getFittedProjectColumnWidths(columns) {
    const baseWidths = columns.map(column => getProjectColumnWidth(column));
    const baseTotal = baseWidths.reduce((sum, width) => sum + width, 0);
    const wrap = document.getElementById('projects-table-wrap');
    const availableWidth = Math.max(0, (wrap ? wrap.clientWidth : 0) - 2);
    if (!availableWidth || baseTotal >= availableWidth || baseTotal <= 0) {
        return baseWidths;
    }

    const extra = availableWidth - baseTotal;
    const rawWidths = baseWidths.map(width => width + (extra * width / baseTotal));
    const fittedWidths = rawWidths.map(width => Math.max(PROJECT_MIN_COLUMN_WIDTH, Math.floor(width)));
    let remainder = availableWidth - fittedWidths.reduce((sum, width) => sum + width, 0);
    let index = 0;
    while (remainder > 0 && fittedWidths.length > 0) {
        fittedWidths[index % fittedWidths.length] += 1;
        remainder -= 1;
        index += 1;
    }
    return fittedWidths;
}

function getProjectTableWidths(columns = getVisibleProjectColumns()) {
    const columnWidths = getFittedProjectColumnWidths(columns);
    const totalWidth = columnWidths.reduce((sum, width) => sum + width, 0) || 1;
    return { columnWidths, totalWidth };
}

function getProjectColumnHeaderLabel(column) {
    const lang = getProjectsLanguage();
    if (lang === 'zh') return column.zhLabel || column.label || column.key;
    return column.label || column.zhLabel || column.key;
}

function renderProjectsSpreadsheetHeader() {
    const columns = getVisibleProjectColumns();
    const { columnWidths, totalWidth } = getProjectTableWidths(columns);
    const headerHeight = getProjectHeaderHeight();
    const colgroup = columns
        .map((column, index) => `<col data-key="${escapeHtml(column.key)}" style="width: ${columnWidths[index]}px;">`)
        .join('');
    const header = columns
        .map((column, index) => `
            <th class="project-sheet-header" data-key="${escapeHtml(column.key)}" data-col-index="${index}" style="width: ${columnWidths[index]}px; height: ${headerHeight}px;" title="${escapeHtml(column.label)} / ${escapeHtml(column.zhLabel || '')}">
                <button type="button" class="project-filter-trigger${ProjectsState.columnFilters[column.key] ? ' active' : ''}" data-key="${escapeHtml(column.key)}" title="Lọc ${escapeHtml(getProjectColumnHeaderLabel(column))}">
                    <span class="project-sheet-header-main">${escapeHtml(getProjectColumnHeaderLabel(column))}</span>
                    <i class="bi bi-funnel${ProjectsState.columnFilters[column.key] ? '-fill' : ''}"></i>
                </button>
                <span class="project-column-resizer" data-key="${escapeHtml(column.key)}" data-col-index="${index}" title="Kéo để đổi độ rộng cột"></span>
                <span class="project-header-height-resizer" title="Kéo để đổi chiều cao header"></span>
            </th>
        `)
        .join('');

    const table = $('#projects-table');
    table.find('colgroup').remove();
    table.toggleClass('project-many-columns', columns.length >= 18);
    table.prepend(`<colgroup>${colgroup}</colgroup>`);
    table.css({
        width: `${totalWidth}px`,
        minWidth: '100%',
        '--project-row-height': `${getProjectRowHeight()}px`,
        '--project-header-height': `${headerHeight}px`
    });
    table.find('thead').html(`
        <tr class="project-sheet-header-row">${header}</tr>
    `);

    table.find('.project-filter-trigger').off('click.projectColumnFilter').on('click.projectColumnFilter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        showProjectColumnFilter($(this).data('key'), this);
    });
    setupProjectColumnResizeHandlers();
    setupProjectTableHeightResizeHandlers();
}

function setupProjectColumnResizeHandlers() {
    const table = $('#projects-table');
    table.find('.project-column-resizer')
        .off('mousedown.projectColumnResize')
        .on('mousedown.projectColumnResize', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const key = String($(this).data('key'));
            const colIndex = Number($(this).data('col-index'));
            const width = $(this).closest('th')[0]?.getBoundingClientRect().width
                || getProjectColumnWidth(PROJECT_SPREADSHEET_COLUMNS.find(column => column.key === key) || {});
            ProjectsState.columnResize = {
                key,
                colIndex,
                startX: e.clientX,
                startWidth: width
            };
            $('body').addClass('project-column-resizing');
        });

    $(document)
        .off('mousemove.projectColumnResize')
        .on('mousemove.projectColumnResize', function(e) {
            if (!ProjectsState.columnResize) return;
            e.preventDefault();
            const resize = ProjectsState.columnResize;
            const nextWidth = Math.max(PROJECT_MIN_COLUMN_WIDTH, resize.startWidth + e.clientX - resize.startX);
            applyProjectColumnWidth(resize.key, resize.colIndex, nextWidth);
        })
        .off('mouseup.projectColumnResize')
        .on('mouseup.projectColumnResize', function() {
            if (!ProjectsState.columnResize) return;
            ProjectsState.columnResize = null;
            $('body').removeClass('project-column-resizing');
            saveProjectTableLayout();
        });
}

function applyProjectColumnWidth(key, colIndex, width) {
    const nextWidth = Math.round(Math.max(PROJECT_MIN_COLUMN_WIDTH, width));
    ProjectsState.columnWidths[key] = nextWidth;
    applyProjectTableWidths();
}

function applyProjectTableWidths() {
    const columns = getVisibleProjectColumns();
    const { columnWidths, totalWidth } = getProjectTableWidths(columns);

    const table = $('#projects-table');
    columns.forEach((column, index) => {
        const width = columnWidths[index];
        table.find(`col[data-key="${cssEscapeProjectKey(column.key)}"]`).css('width', `${width}px`);
        table.find(`th.project-sheet-header[data-key="${cssEscapeProjectKey(column.key)}"]`).css('width', `${width}px`);
    });
    table.css({
        width: `${totalWidth}px`,
        minWidth: '100%',
        '--project-row-height': `${getProjectRowHeight()}px`,
        '--project-header-height': `${getProjectHeaderHeight()}px`
    });
}

function setupProjectTableHeightResizeHandlers() {
    const table = $('#projects-table');

    table.find('.project-header-height-resizer')
        .off('mousedown.projectHeaderHeightResize')
        .on('mousedown.projectHeaderHeightResize', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ProjectsState.headerHeightResize = {
                startY: e.clientY,
                startHeight: getProjectHeaderHeight()
            };
            $('body').addClass('project-row-height-resizing');
        });

    $('#projects-table-body')
        .off('mousedown.projectRowHeightResize')
        .on('mousedown.projectRowHeightResize', '.project-row-height-resizer', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ProjectsState.rowHeightResize = {
                startY: e.clientY,
                startHeight: getProjectRowHeight()
            };
            $('body').addClass('project-row-height-resizing');
        });

    $(document)
        .off('mousemove.projectTableHeightResize')
        .on('mousemove.projectTableHeightResize', function(e) {
            if (ProjectsState.headerHeightResize) {
                e.preventDefault();
                const resize = ProjectsState.headerHeightResize;
                setProjectHeaderHeight(resize.startHeight + e.clientY - resize.startY);
                return;
            }

            if (ProjectsState.rowHeightResize) {
                e.preventDefault();
                const resize = ProjectsState.rowHeightResize;
                setProjectRowHeight(resize.startHeight + e.clientY - resize.startY);
            }
        })
        .off('mouseup.projectTableHeightResize')
        .on('mouseup.projectTableHeightResize', function() {
            if (!ProjectsState.headerHeightResize && !ProjectsState.rowHeightResize) return;
            ProjectsState.headerHeightResize = null;
            ProjectsState.rowHeightResize = null;
            $('body').removeClass('project-row-height-resizing');
            saveProjectTableLayout();
        });
}

function setProjectHeaderHeight(height) {
    ProjectsState.headerHeight = clampProjectNumber(height, PROJECT_MIN_HEADER_HEIGHT, PROJECT_MAX_HEADER_HEIGHT, PROJECT_DEFAULT_HEADER_HEIGHT);
    $('#projects-table th.project-sheet-header').css('height', `${ProjectsState.headerHeight}px`);
}

function setProjectRowHeight(height) {
    const oldHeight = getProjectRowHeight();
    ProjectsState.rowHeight = clampProjectNumber(height, PROJECT_MIN_ROW_HEIGHT, PROJECT_MAX_ROW_HEIGHT, PROJECT_DEFAULT_ROW_HEIGHT);
    const newHeight = getProjectRowHeight();
    if (oldHeight === newHeight) return;

    const wrap = document.getElementById('projects-table-wrap');
    const anchorRow = wrap ? Math.floor(wrap.scrollTop / oldHeight) : 0;
    if (wrap) {
        wrap.scrollTop = anchorRow * newHeight;
    }
    renderProjectsVirtualRows({ force: true });
}

function cssEscapeProjectKey(value) {
    if (window.CSS && typeof window.CSS.escape === 'function') {
        return window.CSS.escape(String(value));
    }
    return String(value).replace(/["\\]/g, '\\$&');
}

function normalizeProjectFilterText(value) {
    return String(value ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
}

function stripProjectHtml(value) {
    const element = document.createElement('div');
    element.innerHTML = String(value ?? '');
    return element.textContent || element.innerText || '';
}

function getProjectRenderedFilterLabel(project, column, rowIndex = 0) {
    if (!column) return t('empty_value');
    const rawValue = getProjectValue(project, column.fields, '');
    const isEmpty = rawValue === undefined || rawValue === null || String(rawValue).trim() === '';
    if (isEmpty) return t('empty_value');

    if (column.key === 'ngay') return formatProjectMonthCell(rawValue);
    if (column.key === 'tg_tiepnhan') return formatProjectDateOnlyCell(rawValue);
    if (column.key === 'trangthai') return stripProjectHtml(renderPendingStatus(rawValue)).trim() || String(rawValue);
    if (column.key === 'dokhan') return normalizeProjectUrgency(rawValue).label || String(rawValue);
    if (column.key === 'yeucaukythuat') return t('click_to_view');
    if (column.key === 'tracking_id') return String(rawValue || rowIndex + 1);
    return stripProjectHtml(formatProjectCellValue(column, rawValue, rowIndex)).trim();
}

function getProjectRenderedFilterValue(project, column, rowIndex = 0) {
    return normalizeProjectFilterText(getProjectRenderedFilterLabel(project, column, rowIndex));
}

function getProjectSearchTokens(searchText) {
    return normalizeProjectFilterText(searchText).split(/\s+/).filter(Boolean);
}

function getProjectSearchHaystack(project) {
    const visibleColumns = getVisibleProjectColumns();
    const visibleValues = visibleColumns.map(column => getProjectRenderedFilterLabel(project, column));
    return normalizeProjectFilterText(visibleValues.join(' '));
}

function matchProjectSearch(project) {
    const tokens = getProjectSearchTokens(ProjectsState.searchText);
    if (tokens.length === 0) return true;
    const haystack = getProjectSearchHaystack(project);
    return tokens.every(token => haystack.includes(token));
}

function getProjectId(project) {
    return String(getProjectValue(project, ['Tracking ID', 'tracking_id'], ''));
}

function getDisplayProjects() {
    return ProjectsState.projects.filter(project => {
        if (!matchProjectSearch(project)) return false;
        if (!matchProjectQuickFilters(project)) return false;

        return Object.entries(ProjectsState.columnFilters).every(([key, selectedValues]) => {
            if (!Array.isArray(selectedValues) || selectedValues.length === 0) return true;
            const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === key);
            if (!column) return true;
            return selectedValues.includes(getProjectRenderedFilterValue(project, column));
        });
    });
}

function matchProjectQuickFilters(project) {
    if (ProjectsState.filterUrgency) {
        const urgency = normalizeProjectUrgency(getProjectValue(project, ['urgency_level', 'Tính cấp bách', 'Độ khẩn'], ''));
        if (urgency.value !== ProjectsState.filterUrgency) return false;
    }

    if (ProjectsState.filterStatus) {
        const pending = String(getProjectValue(project, ['is_pending', 'Trạng thái chờ'], '')).toLowerCase();
        const completion = normalizeProjectFilterText(getProjectValue(project, ['tinh_trang_hoan_thanh', 'Tình trạng hoàn thành dự án', 'Tình trạng'], ''));
        if (ProjectsState.filterStatus === 'pending' && !(pending === 'yes' || pending === 'pending')) return false;
        if (ProjectsState.filterStatus === 'completed' && !completion.includes('hoan thanh') && !completion.includes('完成')) return false;
        if (ProjectsState.filterStatus === 'in_progress' && (pending === 'yes' || pending === 'pending' || completion.includes('hoan thanh') || completion.includes('完成'))) return false;
    }

    return true;
}

function focusFirstProjectSearchResult() {
    if (!ProjectsState.searchText) return;
    const displayProjects = getDisplayProjects();
    if (displayProjects.length === 0) return;
    const wrap = document.getElementById('projects-table-wrap');
    if (!wrap) return;
    wrap.scrollTop = 0;
    renderProjectsVirtualRows({ force: true });
    requestAnimationFrame(() => {
        const firstCell = $('#projects-table-body .project-sheet-cell[data-row="0"][data-col="0"]');
        if (firstCell.length) {
            firstCell.trigger('focus');
        }
    });
}

function matchProjectColumnFilters(project, excludedKey = '') {
    return Object.entries(ProjectsState.columnFilters).every(([key, selectedValues]) => {
        if (key === excludedKey) return true;
        if (!Array.isArray(selectedValues) || selectedValues.length === 0) return true;
        const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === key);
        if (!column) return true;
        return selectedValues.includes(getProjectRenderedFilterValue(project, column));
    });
}

function getProjectColumnFilterOptions(columnKey) {
    const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === columnKey);
    if (!column) return [];
    const values = new Map();
    ProjectsState.projects.forEach((project, rowIndex) => {
        if (!matchProjectSearch(project)) return;
        if (!matchProjectQuickFilters(project)) return;
        if (!matchProjectColumnFilters(project, columnKey)) return;
        const label = getProjectRenderedFilterLabel(project, column, rowIndex);
        const normalized = normalizeProjectFilterText(label);
        if (!values.has(normalized)) values.set(normalized, label);
    });
    return [...values.entries()]
        .map(([value, label]) => ({ value, label }))
        .sort((a, b) => a.label.localeCompare(b.label, 'vi'));
}

function showProjectColumnFilter(columnKey, anchor) {
    const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === columnKey);
    if (!column) return;
    ProjectsState.activeFilterKey = columnKey;
    $('#project-filter-title').text(t('filter_column_title', { column: getProjectColumnDisplayName(column) }));
    $('#project-filter-search').val('');
    renderProjectFilterValues('');

    const popup = $('#project-column-filter');
    popup.css({ display: 'block', left: 0, top: 0 });
    const rect = anchor.getBoundingClientRect();
    const width = popup.outerWidth();
    const height = popup.outerHeight();
    const left = Math.min(rect.left, window.innerWidth - width - 8);
    const top = Math.min(rect.bottom + 6, window.innerHeight - height - 8);
    popup.css({ left: `${Math.max(8, left)}px`, top: `${Math.max(8, top)}px` });
}

function renderProjectFilterValues(searchText = '') {
    const key = ProjectsState.activeFilterKey;
    const options = getProjectColumnFilterOptions(key);
    const selected = ProjectsState.columnFilters[key] || options.map(option => option.value);
    const needle = normalizeProjectFilterText(searchText);
    const visibleOptions = options.filter(option => !needle || normalizeProjectFilterText(option.label).includes(needle));
    const html = visibleOptions.map(option => `
        <label class="project-filter-value">
            <input type="checkbox" value="${escapeHtml(option.value)}" data-visible="true" ${selected.includes(option.value) ? 'checked' : ''}>
            <span class="project-filter-label-text">${escapeHtml(option.label)}</span>
            <button type="button" class="btn btn-sm btn-filter-only" data-value="${escapeHtml(option.value)}">${t('filter_only_this')}</button>
        </label>
    `).join('');
    $('#project-filter-values').html(html || `<div class="project-filter-empty">${escapeHtml(t('no_filter_values'))}</div>`);
    
    // Setup filter only button handler
    $('.btn-filter-only').off('click').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const value = $(this).data('value');
        applyProjectColumnFilterOnly(value);
    });
}

function applyProjectColumnFilterOnly(value) {
    const key = ProjectsState.activeFilterKey;
    if (!key) return;
    
    // Set column filter to only contain this value
    ProjectsState.columnFilters[key] = [String(value)];
    
    hideProjectColumnFilter();
    saveProjectFilterState();
    renderProjectsTablePreservingViewport();
}

function applyProjectColumnFilter() {
    const key = ProjectsState.activeFilterKey;
    if (!key) return;
    const allOptions = getProjectColumnFilterOptions(key);
    const previousValues = ProjectsState.columnFilters[key] || allOptions.map(option => option.value);
    const visibleValues = $('#project-filter-values input[type="checkbox"]')
        .map(function() { return $(this).val(); })
        .get();
    const checkedVisibleValues = $('#project-filter-values input[type="checkbox"]:checked')
        .map(function() { return $(this).val(); })
        .get();
    const visibleSet = new Set(visibleValues);
    const checkedVisibleSet = new Set(checkedVisibleValues);
    const checkedValues = allOptions
        .map(option => option.value)
        .filter(value => visibleSet.has(value) ? checkedVisibleSet.has(value) : previousValues.includes(value));
    const allVisible = checkedValues.length === allOptions.length;
    if (allVisible) {
        delete ProjectsState.columnFilters[key];
    } else {
        ProjectsState.columnFilters[key] = checkedValues;
    }
    hideProjectColumnFilter();
    saveProjectFilterState();
    renderProjectsTablePreservingViewport();
}

function hideProjectColumnFilter() {
    $('#project-column-filter').hide();
    ProjectsState.activeFilterKey = null;
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

function getProjectDeadlineDays(urgency) {
    if (urgency === 'very_urgent') return 0;
    if (urgency === 'urgent') return 2;
    return 3;
}

function parseProjectLocalDateTime(value) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
}

function formatProjectLocalDateTimeInput(date) {
    const pad = value => String(value).padStart(2, '0');
    return [
        date.getFullYear(),
        pad(date.getMonth() + 1),
        pad(date.getDate())
    ].join('-') + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function addProjectWorkingDays(startDate, days) {
    const result = new Date(startDate);
    let added = 0;
    while (added < days) {
        result.setDate(result.getDate() + 1);
        if (result.getDay() !== 0) {
            added += 1;
        }
    }
    return result;
}

function updateProjectExpectedDrawingTime() {
    const createdAt = parseProjectLocalDateTime($('#field-ngay').val());
    const urgency = $('#field-capbach').val() || 'normal';
    const days = getProjectDeadlineDays(urgency);
    const deadline = addProjectWorkingDays(createdAt, days);
    $('#field-tg-mongmuon').val(formatProjectLocalDateTimeInput(deadline));
    $('#smart-deadline-note').text(t(`deadline_${urgency}_note`));
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
        'khach_hang_yeu_cau_ky_thuat': getProjectDraftFieldValue('yeucaukythuat', '客户技术要求'),
        'nguoi_lien_he_kh': lienhe,
        'so_luong': getProjectDraftFieldValue('soluong', 'Số lượng') || '1',
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
        '客户技术要求': getProjectDraftFieldValue('yeucaukythuat', '客户技术要求'),
        'Người liên hệ (KH)': lienhe,
        'Số lượng': getProjectDraftFieldValue('soluong', 'Số lượng') || '1',
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
    if (column.key === 'ngay') {
        return escapeHtml(formatProjectMonthCell(rawValue));
    }
    if (column.key === 'tg_tiepnhan') {
        return escapeHtml(formatProjectDateOnlyCell(rawValue));
    }
    if (column.key === 'trangthai') {
        return renderPendingStatus(rawValue);
    }
    if (column.key === 'dokhan') {
        return renderUrgencyCell(rawValue);
    }
    if (column.key === 'yeucaukythuat') {
        const text = rawValue === undefined || rawValue === null ? '' : String(rawValue).trim();
        if (!text) return '';
        const project = getDisplayProjects()[rowIndex];
        const id = project ? getProjectId(project) : '';
        return `<a href="#" class="view-link view-project" data-id="${escapeHtml(String(id))}">${escapeHtml(t('click_to_view'))}</a>`;
    }
    const text = rawValue === undefined || rawValue === null || rawValue === '' ? '' : String(rawValue);
    return escapeHtml(text);
}

function formatProjectMonthCell(rawValue) {
    if (rawValue === undefined || rawValue === null || rawValue === '') return '';
    const text = String(rawValue).trim();
    const match = text.match(/^\d{4}[-/](\d{1,2})[-/]\d{1,2}/);
    if (match) {
        return `${Number(match[1])}月`;
    }

    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime())) {
        return `${parsed.getMonth() + 1}月`;
    }

    return text;
}

function formatProjectDateOnlyCell(rawValue) {
    if (rawValue === undefined || rawValue === null || rawValue === '') return '';
    const text = String(rawValue).trim();
    const match = text.match(/^(\d{4}[-/]\d{1,2}[-/]\d{1,2})/);
    if (match) {
        return match[1].replace(/\//g, '-');
    }

    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime())) {
        const year = parsed.getFullYear();
        const month = String(parsed.getMonth() + 1).padStart(2, '0');
        const day = String(parsed.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    return text;
}

function renderPendingStatus(rawStatus) {
    const status = String(rawStatus || '').toLowerCase().trim();
    if (status === 'yes' || status === 'pending') {
        return `<span class="project-sheet-pill status-pending">${escapeHtml(localizeMixedProjectLabel('Chờ nhận / 待接收'))}</span>`;
    }
    if (status === 'no' || status === 'accepted') {
        return `<span class="project-sheet-pill status-accepted">${escapeHtml(localizeMixedProjectLabel('Đã nhận / 已接收'))}</span>`;
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
        return { value: 'very_urgent', label: localizeMixedProjectLabel('非常紧急 - Rất khẩn cấp') };
    }
    if (normalized === 'urgent' || value.includes('紧急')) {
        return { value: 'urgent', label: localizeMixedProjectLabel('紧急 - Khẩn cấp') };
    }
    if (normalized === 'normal' || value.includes('正常')) {
        return { value: 'normal', label: localizeMixedProjectLabel('正常 - Bình thường') };
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

    tbody.off('mousedown.projectSelection').on('mousedown.projectSelection', '.project-sheet-cell', function(e) {
        if ($(this).data('blank')) return;
        handleProjectCellMouseDown(e, $(this));
    });

    tbody.off('mouseenter.projectSelection').on('mouseenter.projectSelection', '.project-sheet-cell', function(e) {
        if ($(this).data('blank')) return;
        handleProjectCellMouseEnter(e, $(this));
    });

    tbody.off('click.projectSheet').on('click.projectSheet', '.project-sheet-cell', function(e) {
        if ($(e.target).closest('.view-project, input, select, textarea, button').length) return;
        if ($(this).data('blank')) return;
        activateProjectCell($(this));
    });

    tbody.off('focus.projectSheet').on('focus.projectSheet', '.project-sheet-cell', function() {
        if ($(this).data('blank')) return;
        activateProjectCell($(this));
    });

    tbody.off('dblclick.projectSheet').on('dblclick.projectSheet', '.project-sheet-cell.editable', function() {
        beginProjectCellEdit($(this));
    });

    tbody.off('dblclick.quickAddStart').on('dblclick.quickAddStart', '.quick-add-start, .project-quick-add-row .project-sheet-cell.readonly', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!canCurrentUserCreateProject()) {
            showToast(t('warning'), 'Bạn không có quyền tạo dự án.', 'warning');
            return;
        }
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
        if ($(this).data('draft-row') || $(this).data('blank-row')) return;
        e.preventDefault();
        e.stopPropagation();
        const id = $(this).data('id');
        const $cell = $(e.target).closest('.project-sheet-cell');
        selectProjectRow(id, $(this));
        if ($cell.length) activateProjectCell($cell);
        showProjectContextMenu(e.clientX, e.clientY, id, $cell);
    });

    $('#projects-table-wrap').off('contextmenu.projectCtxBlank').on('contextmenu.projectCtxBlank', function(e) {
        if ($(e.target).closest('#projects-table-body tr').length) return;
        e.preventDefault();
        showProjectContextMenu(e.clientX, e.clientY, null, null);
    });

    setupProjectContextMenuHandlers();
}

function handleProjectCellMouseDown(e, $cell) {
    if ($(e.target).closest('.view-project, input, select, textarea, button, .project-row-height-resizer').length) return;
    if (e.button !== 0) return;

    const row = Number($cell.data('row'));
    const col = Number($cell.data('col'));
    const key = $cell.data('key');

    ProjectsState.rangeSelection = {
        startRow: row,
        startCol: col,
        startKey: key,
        endRow: row,
        endCol: col,
        isSelecting: true
    };

    if (!e.ctrlKey && !e.metaKey) {
        ProjectsState.selectedCells = [];
    }

    updateProjectSelection();
    $(document).off('mouseup.projectSelection').on('mouseup.projectSelection', handleProjectCellMouseUp);
}

function handleProjectCellMouseEnter(e, $cell) {
    const range = ProjectsState.rangeSelection;
    if (!range || !range.isSelecting) return;

    const row = Number($cell.data('row'));
    const col = Number($cell.data('col'));

    if (range.endRow === row && range.endCol === col) return;

    range.endRow = row;
    range.endCol = col;

    updateProjectSelection();
}

function handleProjectCellMouseUp() {
    const range = ProjectsState.rangeSelection;
    if (range) {
        range.isSelecting = false;
        finalizeProjectSelection();
    }
    $(document).off('mouseup.projectSelection');
}

function updateProjectSelection() {
    const range = ProjectsState.rangeSelection;
    const $tbody = $('#projects-table-body');
    
    if (!range) {
        $tbody.find('.project-sheet-cell').removeClass('selected-cell selection-start-cell');
        return;
    }

    $tbody.find('.project-sheet-cell').each(function() {
        const $this = $(this);
        const r = Number($this.data('row'));
        const c = Number($this.data('col'));
        const classes = getSelectionRangeClasses(r, c);
        $this.toggleClass('selected-cell', classes.includes('selected-cell'));
        $this.toggleClass('selection-start-cell', classes.includes('selection-start-cell'));
    });
}

function getSelectionRangeClasses(row, col) {
    const range = ProjectsState.rangeSelection;
    if (!range) return '';

    const minRow = Math.min(range.startRow, range.endRow);
    const maxRow = Math.max(range.startRow, range.endRow);
    const minCol = Math.min(range.startCol, range.endCol);
    const maxCol = Math.max(range.startCol, range.endCol);

    const classes = [];
    if (row >= minRow && row <= maxRow && col >= minCol && col <= maxCol) {
        classes.push('selected-cell');
        if (row === range.startRow && col === range.startCol) {
            classes.push('selection-start-cell');
        }
    }
    return classes.join(' ');
}

function finalizeProjectSelection() {
    const range = ProjectsState.rangeSelection;
    if (!range) return;

    const minRow = Math.min(range.startRow, range.endRow);
    const maxRow = Math.max(range.startRow, range.endRow);
    const minCol = Math.min(range.startCol, range.endCol);
    const maxCol = Math.max(range.startCol, range.endCol);

    const columns = getVisibleProjectColumns();
    const displayProjects = getDisplayProjects();
    const selected = [];

    for (let r = minRow; r <= maxRow; r++) {
        const project = displayProjects[r];
        if (!project) continue;
        for (let c = minCol; c <= maxCol; c++) {
            const column = columns[c];
            if (!column) continue;
            selected.push({
                rowIndex: r,
                colIndex: c,
                columnKey: column.key,
                value: getProjectValue(project, column.fields, ''),
                id: getProjectId(project)
            });
        }
    }
    ProjectsState.selectedCells = selected;
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
    publishProjectCursor($cell);
}

function publishProjectCursor($cell) {
    if (!$cell || !$cell.length || $cell.data('draft') || $cell.data('blank')) return;
    const id = String($cell.data('id') || '');
    if (!id || id === '__new__') return;
    const column = getVisibleProjectColumns()[Number($cell.data('col'))];
    if (!column) return;
    clearTimeout(ProjectsState.cursorPublishTimer);
    ProjectsState.cursorPublishTimer = setTimeout(() => {
        api.updateProjectCursor({
            tracking_id: id,
            field_name: column.updateKey || column.fields?.[0] || column.key,
            field_label: getProjectColumnDisplayName(column),
            row: Number($cell.data('row')),
            column: Number($cell.data('col'))
        }).catch(error => console.warn('[Projects] Cursor publish failed:', error));
    }, 120);
}

function selectProjectRow(id, $row) {
    ProjectsState.selectedIds = id === '__new__' || id === undefined || id === null || id === '' ? [] : [id];
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
        if (isProjectCellLockedByOther($cell)) {
            showToast(t('warning'), 'Ô này đang được người khác chỉnh sửa', 'warning');
            return;
        }
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
    const columns = getVisibleProjectColumns();
    const maxRow = getDisplayProjects().length;
    let nextRow = row;
    let nextCol = col;

    if (direction === 'ArrowUp') nextRow -= 1;
    if (direction === 'ArrowDown') nextRow += 1;
    if (direction === 'ArrowLeft') nextCol -= 1;
    if (direction === 'ArrowRight') nextCol += 1;
    if (nextRow < 0 || nextRow > maxRow || nextCol < 0 || nextCol >= columns.length) return;

    focusProjectCell(nextRow, nextCol);
}

function focusProjectCell(row, col) {
    const wrap = document.getElementById('projects-table-wrap');
    if (!wrap) return;

    const rowHeight = getProjectRowHeight();
    const targetTop = row * rowHeight;
    const targetBottom = targetTop + rowHeight;
    if (targetTop < wrap.scrollTop) {
        wrap.scrollTop = targetTop;
    } else if (targetBottom > wrap.scrollTop + wrap.clientHeight) {
        wrap.scrollTop = targetBottom - wrap.clientHeight;
    }

    renderProjectsVirtualRows();
    requestAnimationFrame(() => {
        const $next = $(`#projects-table-body .project-sheet-cell[data-row="${row}"][data-col="${col}"]`);
        if ($next.length) {
            $next.focus();
            activateProjectCell($next);
        }
    });
}

async function beginProjectCellEdit($cell, seedValue = null) {
    if (!$cell.hasClass('editable') || ProjectsState.editingCell) return;
    if ($cell.data('draft') && !ProjectsState.quickAddStarted) {
        showToast(t('info'), t('quick_add_double_click'), 'info');
        return;
    }

    const column = getVisibleProjectColumns()[Number($cell.data('col'))];
    if (!column || column.readOnly || !column.updateKey) return;
    if (isProjectCellLockedByOther($cell, column)) {
        showToast(t('warning'), 'Ô này đang được người khác chỉnh sửa', 'warning');
        return;
    }
    if (!$cell.data('draft')) {
        try {
            const lockResult = await api.lockProjectCell(String($cell.data('id')), column.updateKey);
            if (!lockResult || !lockResult.success) {
                throw new Error(lockResult?.error || 'Không thể khóa ô để chỉnh sửa');
            }
            upsertProjectLock(lockResult.lock);
        } catch (error) {
            showToast(t('warning'), error.message || 'Ô này đang được người khác chỉnh sửa', 'warning');
            return;
        }
    }

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
            if (!$cell.data('draft')) {
                api.unlockProjectCell(String($cell.data('id')), column.updateKey).catch(() => {});
            }
            renderProjectCellDisplay($cell, column, originalValue);
        }
        $cell.focus();
    };

    if (column.type === 'select') {
        const options = getProjectColumnOptions(column, originalValue);
        const selectHtml = options.map(option => {
            const value = getProjectOptionValue(option);
            const label = getProjectOptionLabel(option);
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
    const hasCurrentValue = values.some(option => String(getProjectOptionValue(option)) === String(currentValue));
    const normalizedUrgency = column.optionsSource === 'urgency' ? normalizeProjectUrgency(currentValue) : null;
    if (normalizedUrgency?.value && !values.some(option => String(getProjectOptionValue(option)) === normalizedUrgency.value)) {
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
    const displayProjects = getDisplayProjects();
    const startRow = Number($startCell.data('row'));
    const startCol = Number($startCell.data('col'));
    const updatesById = new Map();
    const touchedCells = [];

    matrix.forEach((rowValues, rowOffset) => {
        rowValues.forEach((value, colOffset) => {
            const row = startRow + rowOffset;
            const col = startCol + colOffset;
            const column = columns[col];
            const project = displayProjects[row];
            if (!column || column.readOnly || !column.updateKey || !project) return;
            const id = String(getProjectValue(project, ['Tracking ID', 'tracking_id'], ''));
            if (!id) return;
            const $target = $(`#projects-table-body .project-sheet-cell[data-row="${row}"][data-col="${col}"]`);
            if (!updatesById.has(id)) updatesById.set(id, {});
            updatesById.get(id)[column.updateKey] = value;
            touchedCells.push({ $cell: $target, column, value, row, id, oldValue: getProjectValue(project, column.fields, '') });
        });
    });

    if (updatesById.size === 0) return;
    touchedCells.forEach(({ $cell }) => $cell.length && $cell.addClass('saving-cell'));

    try {
        for (const [id, payload] of updatesById.entries()) {
            const project = ProjectsState.projects.find(item => getProjectId(item) === String(id));
            const result = await api.updateProject(id, { ...payload, version: project?.version || 1 });
            if (!result || !result.success) {
                throw new Error(result?.error || t('error'));
            }
            const rowIndex = ProjectsState.projects.findIndex(project => String(getProjectValue(project, ['Tracking ID', 'tracking_id'], '')) === String(id));
            if (rowIndex >= 0) {
                Object.assign(ProjectsState.projects[rowIndex], result.record || payload);
            }
        }
        pushProjectUndo({
            type: 'bulk-update',
            label: t('undo_paste_data'),
            updates: touchedCells.map(({ id, column, oldValue, value }) => ({
                id,
                key: column.updateKey,
                columnKey: column.key,
                oldValue,
                newValue: value
            }))
        });
        touchedCells.forEach(({ $cell, column, value }) => {
            if (!$cell.length) return;
            $cell.removeClass('saving-cell error-cell');
            renderProjectCellDisplay($cell, column, value);
        });
    } catch (error) {
        touchedCells.forEach(({ $cell }) => $cell.length && $cell.removeClass('saving-cell').addClass('error-cell'));
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
        const project = getProjectContextRow(id);
        const payload = { [column.updateKey]: value, version: project?.version || 1 };
        const result = await api.updateProject(id, payload);
        if (!result || !result.success) {
            throw new Error(result?.error || t('error'));
        }

        if (result.record) {
            mergeRealtimeProjectRecord(result.record);
        } else {
            updateProjectRowDataById(id, column, value);
        }
        pushProjectUndo({
            type: 'cell',
            label: t('undo_edit_cell'),
            id,
            key: column.updateKey,
            columnKey: column.key,
            oldValue,
            newValue: value
        });
        renderProjectCellDisplay($cell, column, value);
        $cell.removeClass('saving-cell');
        removeProjectLock(id, column.updateKey);
    } catch (error) {
        console.error('[Projects] Cell update error:', error);
        $cell.removeClass('saving-cell').addClass('error-cell');
        renderProjectCellDisplay($cell, column, oldValue);
        showToast(t('error'), error.message || t('error'), 'error');
        api.unlockProjectCell(id, column.updateKey).catch(() => {});
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
    const viewportSnapshot = captureProjectViewport();

    try {
        const result = await api.createProject(buildQuickAddProjectPayload());
        if (!result || !result.success) {
            throw new Error(result?.error || t('error'));
        }

        ProjectsState.quickAddDraft = {};
        ProjectsState.quickAddStarted = false;
        ProjectsState.quickAddPreviewId = null;
        showToast(t('success'), t('toast_project_created'), 'success');
        await loadProjects({ preserveScroll: true, viewportSnapshot });
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

function updateProjectRowDataById(id, column, value) {
    const project = ProjectsState.projects.find(item => getProjectId(item) === String(id));
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
    $cell.html(wrapProjectCellContent(formatProjectCellValue(column, rawValue, Number($cell.data('row')))));
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
    const undo = ProjectsState.undoStack[ProjectsState.undoStack.length - 1];
    $('#btn-undo-project')
        .prop('disabled', !undo || ProjectsState.isLoading)
        .attr('title', undo ? `${undo.label || t('undo')} (Ctrl+Z)` : `${t('undo')} (Ctrl+Z)`)
        .find('span')
        .text(t('undo'));
    $('#btn-add-project')
        .prop('disabled', !canCurrentUserCreateProject())
        .toggleClass('disabled', !canCurrentUserCreateProject());

    const displayCount = getDisplayProjects().length;
    const activeColumnFilters = Object.keys(ProjectsState.columnFilters).length;
    const hasQuickFilters = !!ProjectsState.filterStatus || !!ProjectsState.filterUrgency;
    const hasSearch = !!String(ProjectsState.searchText || '').trim();
    const countText = activeColumnFilters || hasQuickFilters || hasSearch
        ? t('rows_count_filtered', { display: displayCount, total: ProjectsState.projects.length })
        : t('rows_count', { count: ProjectsState.projects.length });
    $('#projects-filter-count').text(countText);
}

function pushProjectUndo(entry) {
    ProjectsState.undoStack.push(entry);
    if (ProjectsState.undoStack.length > PROJECT_UNDO_LIMIT) {
        ProjectsState.undoStack.shift();
    }
    updateToolbarState();
}

async function undoLastProjectAction() {
    if (ProjectsState.isLoading || ProjectsState.undoStack.length === 0) return;
    const action = ProjectsState.undoStack.pop();
    const viewportSnapshot = captureProjectViewport();
    updateToolbarState();
    showLoading(action.label || t('undo'));

    try {
        if (action.type === 'cell') {
            await undoProjectCellAction(action);
        } else if (action.type === 'bulk-update') {
            await undoProjectBulkUpdate(action);
        } else if (action.type === 'delete') {
            await undoProjectDelete(action);
        }
        showToast(t('success'), t('undo_success'), 'success');
        await loadProjects({ preserveScroll: true });
        restoreProjectViewport(viewportSnapshot);
    } catch (error) {
        ProjectsState.undoStack.push(action);
        console.error('[Projects] Undo error:', error);
        showToast(t('error'), error.message || t('error'), 'error');
    } finally {
        hideLoading();
        updateToolbarState();
    }
}

async function undoProjectCellAction(action) {
    const result = await api.updateProject(action.id, { [action.key]: action.oldValue });
    if (!result || !result.success) {
        throw new Error(result?.error || t('error'));
    }
}

async function undoProjectBulkUpdate(action) {
    const payloads = new Map();
    action.updates.forEach(update => {
        if (!payloads.has(update.id)) payloads.set(update.id, {});
        payloads.get(update.id)[update.key] = update.oldValue;
    });
    for (const [id, payload] of payloads.entries()) {
        const result = await api.updateProject(id, payload);
        if (!result || !result.success) {
            throw new Error(result?.error || t('error'));
        }
    }
}

async function undoProjectDelete(action) {
    const result = await api.restoreProjects(action.records || []);
    if (!result || !result.success) {
        throw new Error(result?.error || t('error'));
    }
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
    $('#field-soluong').val('1');
    updateTechnicalRequirementCounter();
    
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
    updateProjectExpectedDrawingTime();
    
    modal.show();
}

/**
 * Setup real-time validation for form fields
 * UX Improvement: Validate fields as user types
 */
function setupRealTimeValidation() {
    // Required fields to validate on blur
    const requiredFields = [
        { id: '#field-khachhang', messageKey: 'validation_khachhang_required' },
        { id: '#field-tensanpham', messageKey: 'validation_tensanpham_required' }
    ];
    
    requiredFields.forEach(field => {
        const $input = $(field.id);
        if ($input.length) {
            $input.off('blur.realvalidation').on('blur.realvalidation', function() {
                if (field.id === '#field-khachhang') {
                    validateCustomerField();
                } else {
                    validateFieldOnBlur($(this), field.messageKey);
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
                showFieldError($(this), t('validation_quantity_number'));
            } else {
                clearFieldError($(this));
            }
        });
    }

    $('#field-yeucaukythuat')
        .off('input.techRequirementCounter')
        .on('input.techRequirementCounter', updateTechnicalRequirementCounter);
    updateTechnicalRequirementCounter();
}

function updateTechnicalRequirementCounter() {
    const value = $('#field-yeucaukythuat').val() || '';
    $('#field-yeucaukythuat-counter').text(`${value.length}/1000`);
}

/**
 * Validate a single field on blur
 */
function validateFieldOnBlur($input, messageKey) {
    const value = $input.val().trim();
    
    if (!value) {
        showFieldError($input, t(messageKey));
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
        showFieldError($customerInput, t('validation_khachhang_required'));
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
    $input.after(`<div class="invalid-feedback" style="display: block; color: #BA1A1A; font-size: 12px;">${escapeHtml(message)}</div>`);
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

    input.attr('placeholder', uniqueNames.length > 0 ? t('new_customer_placeholder') : t('enter_customer_placeholder'));
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
    $('#project-form label').eq(5).html(t('form_khachhang_yeucau_kythuat'));
    $('#project-form label').eq(6).html(t('form_lienhe_kh'));
    $('#project-form label').eq(7).html(t('form_soluong'));
    $('#project-form label').eq(8).html(t('form_mapo'));
    $('#project-form label').eq(9).html(t('form_capbach'));
    $('#project-form label').eq(10).html(t('form_tg_mongmuon'));

    // Customer controls
    const customerSelect = $('#field-khachhang-select');
    if (customerSelect.length) {
        customerSelect.find('option').first().text(t('select_customer'));
    }
    $('#field-khachhang').attr('placeholder', t('new_customer_placeholder'));
    
    // Urgency options
    const urgencySelect = $('#field-capbach');
    if (urgencySelect.length) {
        urgencySelect.find('option').eq(0).text(localizeMixedProjectLabel('正常 - Bình thường'));
        urgencySelect.find('option').eq(1).text(localizeMixedProjectLabel('紧急 - Khẩn cấp'));
        urgencySelect.find('option').eq(2).text(localizeMixedProjectLabel('非常紧急 - Rất khẩn cấp'));
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
            $('#field-yeucaukythuat').val(result['khach_hang_yeu_cau_ky_thuat'] || result['客户技术要求'] || result['Yêu cầu kỹ thuật KH'] || '');
            updateTechnicalRequirementCounter();
            $('#field-lienhe').val(result['nguoi_lien_he_kh'] || result['Người liên hệ (KH)'] || result['Người liên hệ\n(KH)'] || '');
            $('#field-soluong').val(result['so_luong'] || result['Số lượng'] || '1');
            $('#field-mapo').val(result['ma_po'] || result['Mã PO'] || '');
            // Thời gian & Độ khẩn
            $('#field-capbach').val(result['urgency_level'] || result['Độ khẩn'] || result['Tính cấp bách'] || result['Mức độ khẩn cấp'] || 'normal');
            $('#field-tg-mongmuon').val(result['thoi_gian_mong_muon_ban_ve'] || result['Thời gian mong muốn có bản vẽ'] || result['TG mong muốn'] || '');
            
            // Update form labels with i18n
            updateProjectFormLabels();
            if (!$('#field-tg-mongmuon').val()) {
                updateProjectExpectedDrawingTime();
            } else {
                $('#smart-deadline-note').text(t(`deadline_${$('#field-capbach').val() || 'normal'}_note`));
            }
            
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
            $('#view-content-project').html(buildProjectDetailView(result));
            
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
    if (isEditMode && !canCurrentUserEditAnyProject()) {
        showToast(t('warning'), 'Bạn không có quyền chỉnh sửa toàn bộ dự án.', 'warning');
        return;
    }
    if (!isEditMode && !canCurrentUserCreateProject()) {
        showToast(t('warning'), 'Bạn không có quyền tạo dự án.', 'warning');
        return;
    }
    
    // Clear previous validation
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').remove();
    
    // Validation - Kiểm tra các trường bắt buộc
    const khachhang = getCustomerFieldValue();
    const tensanpham = $('#field-tensanpham').val().trim();
    let hasError = false;
    
    if (!validateCustomerField()) {
        hasError = true;
    }
    
    if (!tensanpham) {
        showFieldError($('#field-tensanpham'), t('validation_tensanpham_required'));
        hasError = true;
    }
    
    // Validate quantity if provided
    const quantity = $('#field-soluong').val().trim();
    if (quantity && isNaN(quantity)) {
        showFieldError($('#field-soluong'), t('validation_quantity_number'));
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
        'khach_hang_yeu_cau_ky_thuat': $('#field-yeucaukythuat').val().trim().slice(0, 1000),
        'nguoi_lien_he_kh': $('#field-lienhe').val().trim(),
        'so_luong': $('#field-soluong').val() || '1',
        'ma_po': $('#field-mapo').val().trim(),
        'urgency_level': $('#field-capbach').val(),
        'thoi_gian_mong_muon_ban_ve': $('#field-tg-mongmuon').val(),
        // Legacy keys để tương thích backend add_record hiện tại
        'Ngày': $('#field-ngay').val(),
        'Khách hàng': khachhang,
        'Nhân viên KD': $('#field-nhanvienkd').val().trim(),
        'Tên sản phẩm': tensanpham,
        'Quy cách': $('#field-quycach').val().trim(),
        '客户技术要求': $('#field-yeucaukythuat').val().trim().slice(0, 1000),
        'Người liên hệ (KH)': $('#field-lienhe').val().trim(),
        'Số lượng': $('#field-soluong').val() || '1',
        'Mã PO': $('#field-mapo').val().trim(),
        'Tính cấp bách': $('#field-capbach').val(),
        'TG mong muốn': $('#field-tg-mongmuon').val()
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
        const existingProject = ProjectsState.projects.find(project => getProjectId(project) === String(trackingId));
        formData.version = existingProject?.version || 1;
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
            loadProjects({ preserveScroll: !trackingId });
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
    if (!canCurrentUserDeleteProject()) {
        showToast(t('warning'), 'Bạn không có quyền xóa dự án.', 'warning');
        return;
    }
    $('#delete-count-project').text(ProjectsState.selectedIds.length);
    
    const modal = new bootstrap.Modal('#confirm-delete-modal-project');
    modal.show();
}

/**
 * Delete selected projects
 */
async function deleteSelectedProjects() {
    if (!canCurrentUserDeleteProject()) {
        showToast(t('warning'), 'Bạn không có quyền xóa dự án.', 'warning');
        return;
    }
    const ids = [...ProjectsState.selectedIds];
    const idSet = new Set(ids.map(id => String(id)));
    const deletedRecords = ProjectsState.projects
        .filter(project => idSet.has(getProjectId(project)))
        .map(project => ({ ...project }));
    
    showLoading(t('deleting'));
    
    try {
        const result = await api.deleteProjects(ids);
        
        if (result.success) {
            showToast(t('success'), t('toast_project_deleted', { count: ids.length }), 'success');
            if (deletedRecords.length > 0) {
                pushProjectUndo({
                    type: 'delete',
                    label: t('undo_delete_rows', { count: deletedRecords.length }),
                    records: deletedRecords
                });
            }
            
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
    const orderedColumns = getProjectOrderedColumns();
    const visibleCount = orderedColumns.filter(col => ProjectsState.visibleColumns[col.key] !== false).length;
    const html = `
        <div class="column-selector-summary">
            <div>
                <strong>${escapeHtml(t('column_selector_title') || 'Chọn cột hiển thị')}</strong>
                <span>${escapeHtml(t('column_selector_hint') || 'Kéo để đổi vị trí cột')}</span>
            </div>
            <span class="column-selector-count">${visibleCount}/${orderedColumns.length}</span>
        </div>
        <div class="column-selector-list" id="column-selector-list">
            ${orderedColumns.map(column => renderColumnSelectorItem(column)).join('')}
        </div>
    `;
    body.html(html);
    setupColumnSelectorDragHandlers();
    updateColumnSelectorSummary();
}

function renderColumnSelectorItem(column) {
    const isVisible = ProjectsState.visibleColumns[column.key] !== false;
    const lang = getProjectCurrentLanguage();
    const primary = getProjectColumnDisplayName(column);
    const secondary = lang === 'zh'
        ? column.label
        : (column.zhLabel || '');
    return `
        <div class="column-selector-item" draggable="true" data-key="${escapeHtml(column.key)}">
            <span class="column-drag-handle" title="${escapeHtml(t('column_drag_hint') || 'Kéo để sắp xếp')}"><i class="bi bi-grip-vertical"></i></span>
            <input class="form-check-input column-checkbox" type="checkbox"
                   value="${escapeHtml(column.key)}" id="col-${escapeHtml(column.key)}" ${isVisible ? 'checked' : ''}>
            <label class="column-selector-label" for="col-${escapeHtml(column.key)}">
                <span class="column-selector-name">${escapeHtml(primary)}</span>
                ${secondary ? `<span class="column-selector-sub">${escapeHtml(secondary)}</span>` : ''}
            </label>
            <span class="column-selector-pin">${escapeHtml(column.zhLabel || column.label)}</span>
        </div>
    `;
}

function getProjectColumnDisplayName(column) {
    if (!column) return '';
    return getProjectCurrentLanguage() === 'zh'
        ? (column.zhLabel || column.label || column.key)
        : (column.label || column.zhLabel || column.key);
}

function getProjectCurrentLanguage() {
    return typeof getCurrentLanguage === 'function'
        ? getCurrentLanguage()
        : (window.currentLanguage || 'vi');
}

function setupColumnSelectorDragHandlers() {
    const list = document.getElementById('column-selector-list');
    if (!list) return;

    list.querySelectorAll('.column-selector-item').forEach(item => {
        item.addEventListener('dragstart', function(e) {
            this.classList.add('is-dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.dataset.key || '');
        });
        item.addEventListener('dragend', function() {
            this.classList.remove('is-dragging');
            updateColumnSelectorSummary();
        });
    });

    list.addEventListener('dragover', function(e) {
        e.preventDefault();
        const dragging = list.querySelector('.column-selector-item.is-dragging');
        if (!dragging) return;
        const afterElement = getColumnDragAfterElement(list, e.clientY);
        if (!afterElement) {
            list.appendChild(dragging);
        } else if (afterElement !== dragging) {
            list.insertBefore(dragging, afterElement);
        }
    });

    list.addEventListener('change', function(e) {
        if (!e.target.classList.contains('column-checkbox')) return;
        updateColumnSelectorSummary();
    });
}

function getColumnDragAfterElement(container, y) {
    const items = [...container.querySelectorAll('.column-selector-item:not(.is-dragging)')];
    return items.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset, element: child };
        }
        return closest;
    }, { offset: Number.NEGATIVE_INFINITY, element: null }).element;
}

function updateColumnSelectorSummary() {
    const total = $('#column-selector-list .column-selector-item').length;
    const visible = $('#column-selector-list .column-checkbox:checked').length;
    $('.column-selector-count').text(`${visible}/${total}`);
}

function getProjectLayoutStorageKey() {
    let userKey = 'anonymous';
    try {
        const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}');
        userKey = currentUser.id || currentUser.user_id || currentUser.username || currentUser.full_name || userKey;
    } catch (error) {
        userKey = 'anonymous';
    }
    return `${PROJECT_LAYOUT_STORAGE_PREFIX}:${String(userKey).trim() || 'anonymous'}`;
}

function getProjectTableLayoutPayload() {
    return {
        visibleColumns: { ...ProjectsState.visibleColumns },
        columnOrder: [...ProjectsState.columnOrder],
        columnWidths: { ...ProjectsState.columnWidths },
        rowHeight: getProjectRowHeight(),
        headerHeight: getProjectHeaderHeight()
    };
}

function applyProjectTableLayoutPayload(parsed) {
    if (!parsed || typeof parsed !== 'object') return false;
    const visibleColumns = parsed.visibleColumns && typeof parsed.visibleColumns === 'object'
        ? parsed.visibleColumns
        : parsed;

    ProjectsState.columnsConfig.forEach(col => {
        if (typeof visibleColumns[col.key] === 'boolean') {
            ProjectsState.visibleColumns[col.key] = visibleColumns[col.key];
        }
    });

    const defaultOrder = getDefaultProjectColumnOrder();
    if (Array.isArray(parsed.columnOrder)) {
        ProjectsState.columnOrder = parsed.columnOrder
            .filter(key => defaultOrder.includes(key));
        defaultOrder.forEach(key => {
            if (!ProjectsState.columnOrder.includes(key)) ProjectsState.columnOrder.push(key);
        });
    } else {
        ProjectsState.columnOrder = defaultOrder;
    }

    if (parsed.columnWidths && typeof parsed.columnWidths === 'object') {
        ProjectsState.columnWidths = {};
        PROJECT_SPREADSHEET_COLUMNS.forEach(column => {
            const width = Number(parsed.columnWidths[column.key]);
            if (Number.isFinite(width) && width >= PROJECT_MIN_COLUMN_WIDTH) {
                ProjectsState.columnWidths[column.key] = Math.round(width);
            }
        });
    }

    ProjectsState.rowHeight = clampProjectNumber(parsed.rowHeight, PROJECT_MIN_ROW_HEIGHT, PROJECT_MAX_ROW_HEIGHT, PROJECT_DEFAULT_ROW_HEIGHT);
    const savedHeaderHeight = Number(parsed.headerHeight);
    ProjectsState.headerHeight = savedHeaderHeight === 84
        ? PROJECT_DEFAULT_HEADER_HEIGHT
        : clampProjectNumber(savedHeaderHeight, PROJECT_MIN_HEADER_HEIGHT, PROJECT_MAX_HEADER_HEIGHT, PROJECT_DEFAULT_HEADER_HEIGHT);
    return true;
}

function loadProjectTableLayout() {
    try {
        const storageKey = getProjectLayoutStorageKey();
        const saved = localStorage.getItem(storageKey)
            || (storageKey.endsWith(':anonymous') ? localStorage.getItem('projects_visible_columns_v2') : null);
        if (!saved) return;

        const parsed = JSON.parse(saved);
        applyProjectTableLayoutPayload(parsed);
    } catch (error) {
        console.warn('[Projects] Cannot load table layout:', error);
    }
}

function saveProjectTableLayout() {
    try {
        const payload = getProjectTableLayoutPayload();
        localStorage.setItem(getProjectLayoutStorageKey(), JSON.stringify(payload));
        saveProjectTableLayoutToServer(payload);
    } catch (error) {
        console.warn('[Projects] Cannot save table layout:', error);
    }
}

async function syncProjectTableLayoutFromServer() {
    if (!api?.getUserPreference || !localStorage.getItem('auth_token')) return;
    try {
        const result = await api.getUserPreference(PROJECT_LAYOUT_PREFERENCE_KEY);
        const layout = result?.value;
        if (!layout || typeof layout !== 'object') {
            saveProjectTableLayoutToServer(getProjectTableLayoutPayload());
            return;
        }
        const before = JSON.stringify(getProjectTableLayoutPayload());
        if (!applyProjectTableLayoutPayload(layout)) return;
        localStorage.setItem(getProjectLayoutStorageKey(), JSON.stringify(getProjectTableLayoutPayload()));
        if (JSON.stringify(getProjectTableLayoutPayload()) !== before) {
            initColumnSelector();
            renderProjectsTablePreservingViewport();
        }
    } catch (error) {
        console.warn('[Projects] Cannot sync table layout:', error);
    }
}

function saveProjectTableLayoutToServer(payload = getProjectTableLayoutPayload()) {
    if (!api?.setUserPreference || !localStorage.getItem('auth_token')) return;
    api.setUserPreference(PROJECT_LAYOUT_PREFERENCE_KEY, payload)
        .catch(error => console.warn('[Projects] Cannot persist table layout:', error));
}

function getProjectFilterStorageKey() {
    let userKey = 'anonymous';
    try {
        const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}');
        userKey = currentUser.id || currentUser.user_id || currentUser.username || currentUser.full_name || userKey;
    } catch (error) {
        userKey = 'anonymous';
    }
    return `${PROJECT_FILTER_STORAGE_PREFIX}:${String(userKey).trim() || 'anonymous'}`;
}

function getProjectFilterStatePayload() {
    return {
        filterStatus: ProjectsState.filterStatus || '',
        filterUrgency: ProjectsState.filterUrgency || '',
        searchText: ProjectsState.searchText || '',
        searchDraft: ProjectsState.searchDraft || ProjectsState.searchText || '',
        columnFilters: { ...ProjectsState.columnFilters }
    };
}

function applyProjectFilterStatePayload(parsed) {
    if (!parsed || typeof parsed !== 'object') return false;
    ProjectsState.filterStatus = typeof parsed.filterStatus === 'string' ? parsed.filterStatus : '';
    ProjectsState.filterUrgency = typeof parsed.filterUrgency === 'string' ? parsed.filterUrgency : '';
    ProjectsState.searchText = typeof parsed.searchText === 'string' ? parsed.searchText : '';
    ProjectsState.searchDraft = typeof parsed.searchDraft === 'string' ? parsed.searchDraft : ProjectsState.searchText;

    const validKeys = new Set(PROJECT_SPREADSHEET_COLUMNS.map(column => column.key));
    const nextFilters = {};
    if (parsed.columnFilters && typeof parsed.columnFilters === 'object') {
        Object.entries(parsed.columnFilters).forEach(([key, values]) => {
            if (!validKeys.has(key) || !Array.isArray(values)) return;
            const cleanedValues = values
                .map(value => normalizeProjectFilterText(value))
                .filter(Boolean);
            if (cleanedValues.length > 0) {
                nextFilters[key] = [...new Set(cleanedValues)];
            }
        });
    }
    ProjectsState.columnFilters = nextFilters;
    return true;
}

function loadProjectFilterState() {
    try {
        const saved = localStorage.getItem(getProjectFilterStorageKey());
        if (!saved) return;
        applyProjectFilterStatePayload(JSON.parse(saved));
    } catch (error) {
        console.warn('[Projects] Cannot load filters:', error);
    }
}

function saveProjectFilterState() {
    try {
        const payload = getProjectFilterStatePayload();
        localStorage.setItem(getProjectFilterStorageKey(), JSON.stringify(payload));
        saveProjectFilterStateToServer(payload);
    } catch (error) {
        console.warn('[Projects] Cannot save filters:', error);
    }
}

async function syncProjectFilterStateFromServer() {
    if (!api?.getUserPreference || !localStorage.getItem('auth_token')) return;
    try {
        const result = await api.getUserPreference(PROJECT_FILTER_PREFERENCE_KEY);
        const filters = result?.value;
        if (!filters || typeof filters !== 'object') {
            saveProjectFilterStateToServer(getProjectFilterStatePayload());
            return;
        }
        const before = JSON.stringify(getProjectFilterStatePayload());
        if (!applyProjectFilterStatePayload(filters)) return;
        localStorage.setItem(getProjectFilterStorageKey(), JSON.stringify(getProjectFilterStatePayload()));
        applyProjectFilterControlsState();
        if (JSON.stringify(getProjectFilterStatePayload()) !== before) {
            renderProjectsTablePreservingViewport();
        }
    } catch (error) {
        console.warn('[Projects] Cannot sync filters:', error);
    }
}

function saveProjectFilterStateToServer(payload = getProjectFilterStatePayload()) {
    if (!api?.setUserPreference || !localStorage.getItem('auth_token')) return;
    api.setUserPreference(PROJECT_FILTER_PREFERENCE_KEY, payload)
        .catch(error => console.warn('[Projects] Cannot persist filters:', error));
}

/**
 * Toggle column selector popup
 */
function toggleColumnSelector() {
    const selector = $('#column-selector');
    if (!selector.is(':visible')) {
        initColumnSelector();
    }
    selector.toggle();
}

/**
 * Reset column visibility to default
 */
function resetColumnVisibility() {
    ProjectsState.columnsConfig.forEach(col => {
        ProjectsState.visibleColumns[col.key] = col.default;
    });
    ProjectsState.columnOrder = getDefaultProjectColumnOrder();
    ProjectsState.columnWidths = {};
    ProjectsState.rowHeight = PROJECT_DEFAULT_ROW_HEIGHT;
    ProjectsState.headerHeight = PROJECT_DEFAULT_HEADER_HEIGHT;
    
    // Update checkboxes
    initColumnSelector();
    
    saveProjectTableLayout();
    renderProjectsTable();
}

/**
 * Apply column visibility changes
 */
function applyColumnVisibility() {
    ProjectsState.columnOrder = $('#column-selector-list .column-selector-item')
        .map(function() { return String($(this).data('key')); })
        .get()
        .filter(Boolean);
    $('.column-checkbox').each(function() {
        const key = $(this).val();
        ProjectsState.visibleColumns[key] = $(this).is(':checked');
    });
    
    saveProjectTableLayout();
    renderProjectsTable();
}

function hideProjectContextMenu() {
    $('#project-row-context-menu')
        .hide()
        .removeData('rowId')
        .removeData('cellMeta');
}

function showProjectContextMenu(x, y, rowId, $cell = null) {
    const menu = $('#project-row-context-menu');
    if (!menu.length) return;
    const hasRow = rowId !== undefined && rowId !== null && rowId !== '__new__';
    const cellMeta = getProjectContextCellMeta(rowId, $cell);
    const hasCellValue = !!(cellMeta && String(cellMeta.rawValue || '').trim());

    menu.data('rowId', rowId);
    menu.data('cellMeta', cellMeta);
    setProjectContextItemState(menu.find('.ctx-view, .ctx-copy-row'), hasRow);
    setProjectContextItemState(menu.find('.ctx-edit'), hasRow && canCurrentUserEditAnyProject());
    setProjectContextItemState(menu.find('.ctx-add'), canCurrentUserCreateProject());
    setProjectContextItemState(menu.find('.ctx-delete'), hasRow && canCurrentUserDeleteProject());
    setProjectContextItemState(menu.find('.ctx-comments'), hasRow);
    setProjectContextItemState(menu.find('.ctx-change-log'), hasRow);
    setProjectContextItemState(menu.find('.ctx-copy-cell'), !!cellMeta);
    setProjectContextItemState(menu.find('.ctx-filter-value'), !!cellMeta && hasCellValue);
    setProjectContextItemState(menu.find('.ctx-material-docs'), isProjectMaterialCodeCell(cellMeta));

    const rowLabel = hasRow ? `#${rowId}` : t('project_table');
    const columnLabel = cellMeta?.columnLabel || '';
    const valuePreview = hasCellValue ? String(cellMeta.rawValue).trim() : t('empty_cell');
    menu.find('[data-menu-meta="title"]').text(hasRow ? `${t('project_label')} ${rowLabel}` : t('project_table'));
    menu.find('[data-menu-meta="subtitle"]').text(columnLabel ? `${columnLabel}: ${valuePreview}` : t('no_row_selected'));
    menu.find('[data-menu-meta="badge"]').text(cellMeta?.columnZhLabel || (hasRow ? 'Row' : 'Sheet'));

    menu.css({ left: 0, top: 0, display: 'block', visibility: 'hidden' });
    const menuEl = menu[0];
    const menuWidth = menuEl.offsetWidth;
    const menuHeight = menuEl.offsetHeight;
    const left = Math.min(x, window.innerWidth - menuWidth - 8);
    const top = Math.min(y, window.innerHeight - menuHeight - 8);
    menu.css({ left: `${Math.max(8, left)}px`, top: `${Math.max(8, top)}px`, visibility: 'visible' });
}

function setProjectContextItemState($items, enabled) {
    $items.prop('disabled', !enabled).toggleClass('is-disabled', !enabled);
}

function getProjectContextCellMeta(rowId, $cell) {
    if (!$cell || !$cell.length) return null;
    const key = String($cell.data('key') || '');
    const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === key);
    return {
        rowId,
        key,
        columnLabel: getProjectColumnDisplayName(column) || key,
        columnZhLabel: column?.zhLabel || '',
        rawValue: localizeMixedProjectLabel($cell.attr('data-raw-value') || $cell.text().trim())
    };
}

function isProjectMaterialCodeCell(cellMeta) {
    if (!cellMeta) return false;
    const key = String(cellMeta.key || '');
    const value = String(cellMeta.rawValue || '').trim();
    if (!value) return false;
    return ['mabave', 'mabavkythuat', 'mame'].includes(key) || /^P[A-Z]{3,}/i.test(value) || /^10\d{6,}/.test(value);
}

function getProjectContextRow(rowId) {
    if (rowId === undefined || rowId === null || rowId === '__new__') return null;
    const target = String(rowId);
    return ProjectsState.projects.find(project => getProjectId(project) === target) || null;
}

function copyProjectContextText(text, successMessage) {
    const value = String(text ?? '');
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value)
            .then(() => showToast(t('success'), successMessage, 'success'))
            .catch(() => fallbackCopyProjectContextText(value, successMessage));
        return;
    }
    fallbackCopyProjectContextText(value, successMessage);
}

function fallbackCopyProjectContextText(text, successMessage) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
        document.execCommand('copy');
        showToast(t('success'), successMessage, 'success');
    } finally {
        textarea.remove();
    }
}

const PROJECT_DETAIL_SECTIONS = [
    { titleKey: 'basic_info', icon: 'bi-person-lines-fill', keys: ['tracking_id', 'ngay', 'khachhang', 'nhanvienkd', 'nguoinhan'] },
    { titleKey: 'product_info', icon: 'bi-box-seam', keys: ['tensanpham', 'quycach', 'yeucaukythuat', 'lienhe', 'soluong', 'mapo', 'loaisanpham'] },
    { titleKey: 'drawing_codes', icon: 'bi-file-earmark-code', keys: ['mabave', 'mabavkythuat', 'mame'] },
    { titleKey: 'time_urgency', icon: 'bi-clock-history', keys: ['dokhan', 'tg_mongmuon', 'tg_tiepnhan', 'tg_hoanthanh', 'trangthai', 'nhanvienthietke', 'tinhtrang'] }
];

function buildProjectDetailView(project) {
    const progress = getProjectDetailProgress(project);
    const summary = getProjectDetailSummary(project);
    const usedRawKeys = new Set();
    const sectionsHtml = PROJECT_DETAIL_SECTIONS
        .map(section => buildProjectDetailSection(project, section, usedRawKeys))
        .join('');
    const extraHtml = buildProjectDetailExtraSection(project, usedRawKeys);

    return `
        <div class="project-detail-view">
            <div class="project-detail-hero">
                <div>
                    <div class="project-detail-eyebrow">${escapeHtml(t('project_label'))}</div>
                    <div class="project-detail-title">${escapeHtml(summary.title)}</div>
                    <div class="project-detail-subtitle">${escapeHtml(summary.subtitle)}</div>
                </div>
                <div class="project-detail-badges">
                    ${summary.badges.map(badge => `<span class="project-detail-badge ${badge.className}">${escapeHtml(badge.text)}</span>`).join('')}
                </div>
            </div>

            <div class="project-progress-card">
                <div class="project-progress-head">
                    <strong>${escapeHtml(t('detail_progress'))}</strong>
                    <span>${progress.percent}%</span>
                </div>
                <div class="project-progress-bar" aria-label="${escapeHtml(t('detail_progress'))}">
                    <div class="project-progress-fill" style="width: ${progress.percent}%;"></div>
                </div>
                <div class="project-progress-steps">
                    ${progress.steps.map(step => `
                        <div class="project-progress-step ${step.active ? 'is-active' : ''} ${step.done ? 'is-done' : ''}">
                            <span class="project-progress-dot"><i class="bi ${step.icon}"></i></span>
                            <span>${escapeHtml(step.label)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="project-detail-sections">
                ${sectionsHtml}
                ${extraHtml}
            </div>
        </div>
    `;
}

function buildProjectDetailSection(project, section, usedRawKeys) {
    const rows = section.keys
        .map(key => PROJECT_SPREADSHEET_COLUMNS.find(column => column.key === key))
        .filter(Boolean)
        .map(column => getProjectDetailField(project, column, usedRawKeys));

    return `
        <section class="project-detail-card">
            <div class="project-detail-card-title"><i class="bi ${section.icon}"></i><span>${escapeHtml(t(section.titleKey))}</span></div>
            <div class="project-detail-grid">
                ${rows.map(row => renderProjectDetailField(row)).join('')}
            </div>
        </section>
    `;
}

function getProjectDetailField(project, column, usedRawKeys) {
    (column.fields || []).forEach(field => usedRawKeys.add(String(field)));
    if (column.updateKey) usedRawKeys.add(String(column.updateKey));
    usedRawKeys.add(column.key);

    const rawValue = getProjectValue(project, column.fields, '');
    return {
        label: getProjectColumnDisplayName(column),
        value: formatProjectDetailValue(column, rawValue),
        isEmpty: rawValue === undefined || rawValue === null || String(rawValue).trim() === ''
    };
}

function renderProjectDetailField(row) {
    return `
        <div class="project-detail-field ${row.isEmpty ? 'is-empty' : ''}">
            <div class="project-detail-label">${escapeHtml(row.label)}</div>
            <div class="project-detail-value">${escapeHtml(row.value)}</div>
        </div>
    `;
}

function formatProjectDetailValue(column, rawValue) {
    if (rawValue === undefined || rawValue === null || String(rawValue).trim() === '') {
        return t('detail_empty');
    }
    if (column.key === 'dokhan') {
        return normalizeProjectUrgency(rawValue).label || localizeMixedProjectLabel(rawValue);
    }
    if (column.key === 'trangthai') {
        return getProjectPendingStatusText(rawValue);
    }
    if (column.type === 'datetime' || column.key === 'ngay') {
        return formatProjectDetailDateTime(rawValue);
    }
    return localizeMixedProjectLabel(rawValue);
}

function getProjectPendingStatusText(rawStatus) {
    const status = String(rawStatus || '').toLowerCase().trim();
    if (status === 'yes' || status === 'pending') return t('status_pending');
    if (status === 'no' || status === 'accepted') return t('status_accepted');
    return localizeMixedProjectLabel(rawStatus);
}

function formatProjectDetailDateTime(rawValue) {
    const text = String(rawValue || '').trim();
    const parsed = new Date(text);
    if (Number.isNaN(parsed.getTime())) return text;
    const pad = value => String(value).padStart(2, '0');
    return `${pad(parsed.getDate())}/${pad(parsed.getMonth() + 1)}/${parsed.getFullYear()} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

function buildProjectDetailExtraSection(project, usedRawKeys) {
    const hiddenKeys = new Set(['id', 'password', 'token']);
    const extras = Object.entries(project || {})
        .filter(([key, value]) => value !== undefined && value !== null && String(value).trim() !== '')
        .filter(([key]) => !usedRawKeys.has(String(key)))
        .filter(([key]) => !hiddenKeys.has(String(key).toLowerCase()));

    if (extras.length === 0) return '';

    return `
        <section class="project-detail-card">
            <div class="project-detail-card-title"><i class="bi bi-database"></i><span>${escapeHtml(t('detail_extra_data'))}</span></div>
            <div class="project-detail-grid">
                ${extras.map(([key, value]) => renderProjectDetailField({
                    label: key,
                    value: localizeMixedProjectLabel(value),
                    isEmpty: false
                })).join('')}
            </div>
        </section>
    `;
}

function getProjectDetailSummary(project) {
    const id = getProjectValue(project, ['Tracking ID', 'tracking_id'], '');
    const product = getProjectValue(project, ['ten_san_pham', 'Tên sản phẩm'], '');
    const customer = getProjectValue(project, ['khach_hang', 'Khách hàng'], '');
    const urgency = normalizeProjectUrgency(getProjectValue(project, ['urgency_level', 'Tính cấp bách', 'Độ khẩn'], ''));
    const pendingText = getProjectPendingStatusText(getProjectValue(project, ['is_pending', 'Trạng thái chờ'], ''));
    const completion = localizeMixedProjectLabel(getProjectValue(project, ['tinh_trang_hoan_thanh', 'Tình trạng hoàn thành dự án', 'Tình trạng'], ''));

    return {
        title: id ? `#${id} ${product || t('view_project_title')}` : (product || t('view_project_title')),
        subtitle: customer || t('detail_empty'),
        badges: [
            { text: urgency.label || t('detail_empty'), className: `urgency-${urgency.value || 'normal'}` },
            { text: pendingText || t('detail_empty'), className: 'status' },
            { text: completion || t('detail_empty'), className: 'completion' }
        ]
    };
}

function getProjectDetailProgress(project) {
    const pending = String(getProjectValue(project, ['is_pending', 'Trạng thái chờ'], '')).toLowerCase().trim();
    const acceptedBy = getProjectValue(project, ['accepted_by', 'Người nhận'], '');
    const completionRaw = String(getProjectValue(project, ['tinh_trang_hoan_thanh', 'Tình trạng hoàn thành dự án', 'Tình trạng'], '') || '');
    const hasAccepted = pending === 'no' || pending === 'accepted' || !!acceptedBy;
    const hasInProgress = hasAccepted && !!completionRaw;
    const isCompleted = /完成|ho[aà]n th[aà]nh|done|completed/i.test(completionRaw);
    const percent = isCompleted ? 100 : hasInProgress ? 75 : hasAccepted ? 50 : 25;

    const steps = [
        { label: t('detail_stage_created'), icon: 'bi-flag', done: true, active: percent === 25 },
        { label: t('detail_stage_accepted'), icon: 'bi-person-check', done: percent >= 50, active: percent === 50 },
        { label: t('detail_stage_in_progress'), icon: 'bi-tools', done: percent >= 75, active: percent === 75 },
        { label: t('detail_stage_completed'), icon: 'bi-check2-circle', done: percent >= 100, active: percent === 100 }
    ];

    return { percent, steps };
}

function buildProjectRowClipboardText(project) {
    const columns = getVisibleProjectColumns().filter(column => !column.readOnly);
    return columns
        .map(column => getProjectValue(project, column.fields, ''))
        .join('\t');
}

function applyProjectContextFilter(cellMeta) {
    if (!cellMeta || !cellMeta.key) return;
    const column = PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === cellMeta.key);
    const project = ProjectsState.projects.find(item => getProjectId(item) === String(cellMeta.rowId || ''));
    const value = project && column
        ? getProjectRenderedFilterValue(project, column)
        : normalizeProjectFilterText(cellMeta.rawValue);
    if (!value) return;
    ProjectsState.columnFilters[cellMeta.key] = [value];
    hideProjectContextMenu();
    saveProjectFilterState();
    renderProjectsTablePreservingViewport();
    showToast(t('success'), t('filtered_column', { column: cellMeta.columnLabel }), 'success');
}

async function openProjectMaterialDocuments(cellMeta) {
    if (!isProjectMaterialCodeCell(cellMeta)) return;
    const code = String(cellMeta.rawValue || '').trim();
    const modalEl = document.getElementById('project-material-docs-modal');
    if (!modalEl) return;

    $('#project-material-docs-title').text(`Tài liệu mã liệu: ${code}`);
    $('#project-material-docs-body').html('<div class="text-muted">Đang tải...</div>');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    try {
        const result = await api.getMaterialDocuments(code);
        renderProjectMaterialDocuments(result);
    } catch (error) {
        $('#project-material-docs-body').html(`<div class="alert alert-warning mb-0">${escapeHtml(error.message || 'Không tìm thấy tài liệu')}</div>`);
    }
}

function getMaterialDocumentIcon(type) {
    if (type === 'pdf') return 'bi-file-earmark-pdf';
    if (type === 'drawing') return 'bi-file-earmark-image';
    if (type === 'bom') return 'bi-file-earmark-spreadsheet';
    if (type === 'cad') return 'bi-rulers';
    return 'bi-file-earmark';
}

function getMaterialDocumentTypeLabel(type) {
    const labels = {
        pdf: 'PDF',
        drawing: 'Bản vẽ',
        bom: 'BOM',
        cad: 'CAD',
        file: 'File'
    };
    return labels[type] || 'File';
}

function formatMaterialFileSize(size) {
    const bytes = Number(size || 0);
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function escapeProjectAttr(value) {
    return escapeHtml(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function renderMaterialErpInfo(erpInfo) {
    if (!erpInfo) return '';
    const rows = erpInfo.rows || [];
    if (!rows.length) {
        return `
            <div class="material-erp-panel">
                <div class="material-section-title"><i class="bi bi-database"></i><span>ERP</span></div>
                <div class="text-muted small">${escapeHtml(erpInfo.message || 'Không có thông tin ERP')}</div>
            </div>
        `;
    }

    return `
        <div class="material-erp-panel">
            <div class="material-section-title">
                <i class="bi bi-database"></i><span>ERP</span>
                ${erpInfo.source ? `<small>${escapeHtml(erpInfo.source)}</small>` : ''}
            </div>
            <div class="material-erp-list">
                ${rows.map(row => `
                    <div class="material-erp-item">
                        ${row.sheet ? `<div class="material-erp-sheet">${escapeHtml(row.sheet)}</div>` : ''}
                        <div class="material-erp-grid">
                            ${Object.entries(row.values || {}).map(([key, value]) => `
                                <div><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderMaterialFolders(folders) {
    if (!folders?.length) return '';
    return `
        <div class="material-folder-panel">
            <div class="material-section-title"><i class="bi bi-folder2-open"></i><span>Thư mục vật liệu</span></div>
            <div class="material-folder-list">
                ${folders.map(folder => `
                    <button type="button" class="material-folder-item btn-open-material-folder" data-list-url="${escapeProjectAttr(folder.list_url || '')}" data-folder-name="${escapeProjectAttr(folder.name || '')}" ${folder.exists ? '' : 'disabled'}>
                        <i class="bi bi-folder2-open"></i>
                        <span>${escapeHtml(folder.name || 'Thư mục')}</span>
                        <small>${Number(folder.file_count || 0)} file</small>
                    </button>
                `).join('')}
            </div>
            <div id="material-folder-browser" class="material-folder-browser"></div>
        </div>
    `;
}

function renderProjectMaterialDocuments(result) {
    const docs = result?.documents || [];
    if (!docs.length) {
        $('#project-material-docs-body').html(`<div class="alert alert-warning mb-0">${escapeHtml(result?.message || 'Không tìm thấy tài liệu')}</div>`);
        return;
    }

    const html = `
        <div class="material-doc-summary">
            <span>${escapeHtml(result.message || '')}</span>
            ${result.resolved_code && result.resolved_code !== result.code ? `<span>Mã mẹ: ${escapeHtml(result.resolved_code)}</span>` : ''}
        </div>
        ${renderMaterialErpInfo(result.erp_info)}
        ${renderMaterialFolders(result.folders || [])}
        <div class="material-doc-list">
            ${docs.map(doc => `
                <div class="material-doc-item ${doc.exists ? '' : 'is-missing'}">
                    <div class="material-doc-icon"><i class="bi ${getMaterialDocumentIcon(doc.type)}"></i></div>
                    <div class="material-doc-main">
                        <div class="material-doc-name">${escapeHtml(doc.name || '')}</div>
                        <div class="material-doc-meta">${escapeHtml(getMaterialDocumentTypeLabel(doc.type))}${doc.folder_name ? ` · ${escapeHtml(doc.folder_name)}` : ''}${doc.exists ? '' : ' · Server không truy cập được file'}</div>
                    </div>
                    <div class="material-doc-actions">
                        <a class="btn btn-sm btn-outline-primary ${doc.exists ? '' : 'disabled'}" href="${escapeHtml(doc.view_url || '#')}" target="_blank" rel="noopener">
                            <i class="bi bi-box-arrow-up-right"></i>
                        </a>
                        <a class="btn btn-sm btn-outline-secondary ${doc.exists ? '' : 'disabled'}" href="${escapeHtml(doc.download_url || '#')}">
                            <i class="bi bi-download"></i>
                        </a>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    $('#project-material-docs-body').html(html);
}

async function loadProjectMaterialFolder(listUrl, folderName = '') {
    const target = $('#material-folder-browser');
    if (!target.length) return;
    target.html('<div class="text-muted small">Đang tải thư mục...</div>');
    try {
        const result = await api.getMaterialFolder(listUrl);
        const entries = result.entries || [];
        if (!entries.length) {
            target.html(`<div class="alert alert-info mb-0">Thư mục ${escapeHtml(folderName || result.folder_name || '')} không có file hiển thị.</div>`);
            return;
        }
        const html = `
            <div class="material-folder-browser-head">
                <strong>${escapeHtml(result.folder_name || folderName || 'Thư mục')}</strong>
                <span>${entries.length}${result.truncated ? ` / ${Number(result.total || entries.length)}` : ''} mục</span>
            </div>
            <div class="material-folder-entry-list">
                ${entries.map(entry => `
                    <div class="material-folder-entry">
                        <i class="bi ${entry.is_dir ? 'bi-folder' : getMaterialDocumentIcon(entry.type)}"></i>
                        <div class="material-folder-entry-main">
                            <strong>${escapeHtml(entry.name || '')}</strong>
                            <span>${escapeHtml(getMaterialDocumentTypeLabel(entry.type))}${entry.size ? ` · ${escapeHtml(formatMaterialFileSize(entry.size))}` : ''}${entry.modified_at ? ` · ${escapeHtml(formatProjectChangeTime(entry.modified_at))}` : ''}</span>
                        </div>
                        <div class="material-doc-actions">
                            ${entry.is_dir ? `
                                <button type="button" class="btn btn-sm btn-outline-primary btn-open-material-folder" data-list-url="${escapeProjectAttr(entry.list_url || '')}" data-folder-name="${escapeProjectAttr(entry.name || '')}">
                                    <i class="bi bi-folder2-open"></i>
                                </button>
                            ` : `
                                <a class="btn btn-sm btn-outline-primary" href="${escapeHtml(entry.view_url || '#')}" target="_blank" rel="noopener">
                                    <i class="bi bi-box-arrow-up-right"></i>
                                </a>
                                <a class="btn btn-sm btn-outline-secondary" href="${escapeHtml(entry.download_url || '#')}">
                                    <i class="bi bi-download"></i>
                                </a>
                            `}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        target.html(html);
    } catch (error) {
        target.html(`<div class="alert alert-warning mb-0">${escapeHtml(error.message || 'Không tải được thư mục')}</div>`);
    }
}

function getProjectColumnByFieldName(fieldName) {
    const normalized = normalizeProjectUpdateField(fieldName);
    return PROJECT_SPREADSHEET_COLUMNS.find(column => normalizeProjectUpdateField(column.updateKey || column.fields?.[0] || column.key) === normalized) || null;
}

async function openProjectChangeLog(rowId, cellMeta = null) {
    if (!rowId || rowId === '__new__') return;
    const modalEl = document.getElementById('project-change-log-modal');
    if (!modalEl) return;

    const fieldName = cellMeta?.columnLabel || '';
    const column = cellMeta?.key ? PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === cellMeta.key) : null;
    ProjectsState.activeChangeLogContext = {
        trackingId: rowId,
        fieldName: column?.updateKey || '',
        fieldLabel: fieldName
    };
    $('#project-change-log-title').text(fieldName ? `Lịch sử chỉnh sửa: #${rowId} · ${fieldName}` : `Lịch sử chỉnh sửa: #${rowId}`);
    $('#project-change-log-body').html('<div class="text-muted">Đang tải...</div>');
    bootstrap.Modal.getOrCreateInstance(modalEl).show();

    try {
        const params = { limit: 100 };
        if (column?.updateKey) {
            params.field_name = column.updateKey;
        }
        const result = await api.getProjectChangeLogs(rowId, params);
        renderProjectChangeLog(result.logs || []);
    } catch (error) {
        $('#project-change-log-body').html(`<div class="alert alert-warning mb-0">${escapeHtml(error.message || 'Không tải được lịch sử')}</div>`);
    }
}

function formatProjectChangeTime(value) {
    if (!value) return '';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    const pad = n => String(n).padStart(2, '0');
    return `${pad(parsed.getDate())}/${pad(parsed.getMonth() + 1)}/${parsed.getFullYear()} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

function renderProjectChangeLog(logs) {
    if (!logs.length) {
        $('#project-change-log-body').html('<div class="alert alert-info mb-0">Chưa có lịch sử chỉnh sửa cho mục này.</div>');
        return;
    }

    const html = `
        <div class="project-change-log-list">
            ${logs.map(log => {
                const column = getProjectColumnByFieldName(log.field_name);
                const canRevert = column && canCurrentUserEditProjectColumn(column);
                return `
                <div class="project-change-log-item">
                    <div class="project-change-log-head">
                        <strong>${escapeHtml(log.changed_by_name || log.changed_by || 'Không rõ')}</strong>
                        <span>${escapeHtml(formatProjectChangeTime(log.changed_at))}</span>
                    </div>
                    <div class="project-change-log-field">${escapeHtml(log.field_name || '')}</div>
                    <div class="project-change-log-values">
                        <div><span>Từ</span><p>${escapeHtml(log.old_value || '') || '&nbsp;'}</p></div>
                        <i class="bi bi-arrow-right"></i>
                        <div><span>Sang</span><p>${escapeHtml(log.new_value || '') || '&nbsp;'}</p></div>
                    </div>
                    ${canRevert ? `
                        <div class="project-change-log-actions">
                            <button type="button" class="btn btn-sm btn-outline-secondary btn-revert-project-change" data-change-id="${Number(log.id) || 0}">
                                <i class="bi bi-arrow-counterclockwise"></i> Hoàn tác
                            </button>
                        </div>
                    ` : ''}
                </div>
            `; }).join('')}
        </div>
    `;
    $('#project-change-log-body').html(html);
}

async function reloadActiveProjectChangeLog() {
    const context = ProjectsState.activeChangeLogContext;
    if (!context) return;
    try {
        const params = { limit: 100 };
        if (context.fieldName) params.field_name = context.fieldName;
        const result = await api.getProjectChangeLogs(context.trackingId, params);
        renderProjectChangeLog(result.logs || []);
    } catch (error) {
        $('#project-change-log-body').html(`<div class="alert alert-warning mb-0">${escapeHtml(error.message || 'Không tải được lịch sử')}</div>`);
    }
}

async function revertProjectChange(changeId) {
    const context = ProjectsState.activeChangeLogContext;
    if (!context) return;
    const project = getProjectContextRow(context.trackingId);
    const payload = {
        version: project?.version || 1
    };
    const $button = $(`#project-change-log-body .btn-revert-project-change[data-change-id="${changeId}"]`);
    $button.prop('disabled', true).addClass('disabled');
    try {
        const result = await api.revertProjectChange(changeId, payload);
        if (result?.record) {
            mergeRealtimeProjectRecord(result.record);
        }
        await reloadActiveProjectChangeLog();
        showToast(t('success'), 'Đã hoàn tác thay đổi', 'success');
    } catch (error) {
        showToast(t('error'), error.message || 'Không hoàn tác được thay đổi', 'error');
    } finally {
        $button.prop('disabled', false).removeClass('disabled');
    }
}

async function openProjectComments(rowId, cellMeta = null) {
    if (!rowId || rowId === '__new__') return;
    const modalEl = document.getElementById('project-comments-modal');
    if (!modalEl) return;

    const column = cellMeta?.key ? PROJECT_SPREADSHEET_COLUMNS.find(col => col.key === cellMeta.key) : null;
    const fieldName = column?.updateKey || '';
    ProjectsState.activeCommentContext = {
        trackingId: rowId,
        fieldName,
        fieldLabel: cellMeta?.columnLabel || ''
    };
    $('#project-comments-title').text(fieldName ? `Bình luận: #${rowId} · ${cellMeta.columnLabel}` : `Bình luận: #${rowId}`);
    $('#project-comments-body').html('<div class="text-muted">Đang tải...</div>');
    $('#project-comment-input').val('');
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
    await loadProjectComments();
}

async function loadProjectComments() {
    const context = ProjectsState.activeCommentContext;
    if (!context) return;
    try {
        const params = {};
        if (context.fieldName) params.field_name = context.fieldName;
        const result = await api.getProjectComments(context.trackingId, params);
        renderProjectComments(result.comments || []);
    } catch (error) {
        $('#project-comments-body').html(`<div class="alert alert-warning mb-0">${escapeHtml(error.message || 'Không tải được bình luận')}</div>`);
    }
}

function renderProjectComments(comments) {
    if (!comments.length) {
        $('#project-comments-body').html('<div class="alert alert-info mb-0">Chưa có bình luận.</div>');
        return;
    }
    const html = `
        <div class="project-comment-list">
            ${comments.map(comment => `
                <div class="project-comment-item">
                    <div class="project-comment-head">
                        <strong>${escapeHtml(comment.created_by_name || comment.created_by || 'Không rõ')}</strong>
                        <span>${escapeHtml(formatProjectChangeTime(comment.created_at))}</span>
                    </div>
                    ${comment.field_name ? `<div class="project-comment-field">${escapeHtml(comment.field_name)}</div>` : ''}
                    <div class="project-comment-text">${escapeHtml(comment.comment_text || '')}</div>
                </div>
            `).join('')}
        </div>
    `;
    $('#project-comments-body').html(html);
}

async function submitProjectComment() {
    const context = ProjectsState.activeCommentContext;
    if (!context) return;
    const text = $('#project-comment-input').val().trim();
    if (!text) {
        showToast(t('warning'), 'Bình luận không được để trống', 'warning');
        return;
    }
    $('#btn-send-project-comment').prop('disabled', true);
    try {
        await api.addProjectComment(context.trackingId, {
            comment_text: text,
            field_name: context.fieldName || ''
        });
        $('#project-comment-input').val('');
        await loadProjectComments();
    } catch (error) {
        showToast(t('error'), error.message || 'Không gửi được bình luận', 'error');
    } finally {
        $('#btn-send-project-comment').prop('disabled', false);
    }
}

function refreshActiveProjectComments(payload) {
    const context = ProjectsState.activeCommentContext;
    if (!context) return;
    const affectedId = String(payload.tracking_id || payload.comment?.tracking_id || '');
    if (affectedId && affectedId === String(context.trackingId)) {
        loadProjectComments();
    }
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
    menu.on('click.ctxActions', '.ctx-copy-cell', function() {
        const cellMeta = menu.data('cellMeta');
        hideProjectContextMenu();
        if (!cellMeta) return;
        copyProjectContextText(cellMeta.rawValue || '', t('copied_cell'));
    });
    menu.on('click.ctxActions', '.ctx-copy-row', function() {
        const id = menu.data('rowId');
        const project = getProjectContextRow(id);
        hideProjectContextMenu();
        if (!project) return;
        copyProjectContextText(buildProjectRowClipboardText(project), t('copied_row'));
    });
    menu.on('click.ctxActions', '.ctx-filter-value', function() {
        const cellMeta = menu.data('cellMeta');
        applyProjectContextFilter(cellMeta);
    });
    menu.on('click.ctxActions', '.ctx-comments', function() {
        const id = menu.data('rowId');
        const cellMeta = menu.data('cellMeta');
        hideProjectContextMenu();
        openProjectComments(id, cellMeta);
    });
    menu.on('click.ctxActions', '.ctx-change-log', function() {
        const id = menu.data('rowId');
        const cellMeta = menu.data('cellMeta');
        hideProjectContextMenu();
        openProjectChangeLog(id, cellMeta);
    });
    menu.on('click.ctxActions', '.ctx-material-docs', function() {
        const cellMeta = menu.data('cellMeta');
        hideProjectContextMenu();
        openProjectMaterialDocuments(cellMeta);
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
    menu.find('[data-menu-label="copyCell"]').text(t('copy_cell'));
    menu.find('[data-menu-label="copyRow"]').text(t('copy_row'));
    menu.find('[data-menu-label="filterValue"]').text(t('filter_this_value'));
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
