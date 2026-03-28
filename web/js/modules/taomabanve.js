/**
 * Create Code Module (Tạo Mã Bản Vẽ)
 * Extracted from taomabanve.html
 */

// ============================================
// STATE
// ============================================

const TaoMaBanVeState = {
    codeHistory: [],
    currentPage: 1,
    pageSize: 20,
    totalRecords: 0,
    totalPages: 1,
    isLoading: false,
    currentLang: localStorage.getItem('language') || 'vi'
};

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize Create Code module
 */
function initTaomabanveModule() {
    console.log('[TaoMaBanVe] Initializing...');
    
    // Render the module content
    renderTaomabanveContent();
    
    // Setup event listeners
    setupTaomabanveEvents();
    
    // Auto-fill user info
    autoFillUserInfo();
    autoSelectLastCategory();
    
    // Translate category dropdown options
    translateCategoryDropdown();
    
    // Load code history
    loadCodeHistory();
}

/**
 * Render Create Code module content
 */
function renderTaomabanveContent() {
    const container = document.getElementById('taomabanve-container');
    
    container.innerHTML = `
        <div class="row g-3">
            <!-- Language Selector - Top Right -->
            <div class="col-12">
                <div class="d-flex justify-content-end">
                    <div class="btn-group" role="group" aria-label="Language selector">
                        <button type="button" class="btn btn-outline-primary btn-sm lang-btn" data-lang="vi" id="lang-vi">VI</button>
                        <button type="button" class="btn btn-outline-primary btn-sm lang-btn" data-lang="zh" id="lang-zh">中文</button>
                    </div>
                </div>
            </div>
            
            <!-- Create Code Section - Left Column -->
            <div class="col-lg-4 col-md-5">
                <div class="card h-100">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-plus-circle"></i> <span data-i18n="create_code">Tạo Mã Bản Vẽ</span></h5>
                    </div>
                    <div class="card-body">
                        <!-- Create Code Form -->
                        <form id="create-code-form" class="needs-validation" novalidate>
                            <div class="row g-3">
                                <!-- Tên người xin mã -->
                                <div class="col-12">
                                    <div class="form-floating">
                                        <input type="text" class="form-control" id="code-name" required maxlength="100" 
                                               placeholder="Nhập tên người xin mã" data-i18n-placeholder="placeholder_name">
                                        <label for="code-name"><span data-i18n="requester_name">Tên người xin mã</span> <span class="text-danger">*</span></label>
                                        <div class="invalid-feedback" id="code-name-error"></div>
                                        <div class="form-text text-end"><span id="code-name-count">0</span>/100 <span data-i18n="chars">ký tự</span></div>
                                    </div>
                                </div>
                                
                                <!-- Mã nhân viên -->
                                <div class="col-12">
                                    <div class="form-floating">
                                        <input type="text" class="form-control" id="employee-code" required maxlength="3" 
                                               placeholder="3 chữ số" inputmode="numeric" data-i18n-placeholder="three_digits">
                                        <label for="employee-code"><span data-i18n="employee_code">Mã nhân viên công trình</span> <span class="text-danger">*</span> <small class="text-muted">(<span data-i18n="three_digits">3 chữ số</span>)</small></label>
                                        <div class="invalid-feedback" id="employee-code-error"></div>
                                    </div>
                                    <div class="form-text">
                                        <i class="bi bi-info-circle me-1"></i><span data-i18n="employee_code_hint">Nhập ID nhân viên công trình 3 chữ số (vd: 001, 002, 003)</span>
                                    </div>
                                </div>
                                
                                <!-- Hạng mục -->
                                <div class="col-12">
                                    <div class="form-floating">
                                        <select class="form-select" id="code-category" required>
                                            <option value="" selected>-- Chọn hạng mục --</option>
                                            <option value="SJT">SJT散件图 - Bản vẽ tách chi tiết</option>
                                            <option value="WLJ">WLJ物料架 - Giá đựng vật liệu</option>
                                            <option value="ZZC">ZZC周转车 - Xe trung chuyển</option>
                                            <option value="GZT">GZT工作台 - Bàn thao tác</option>
                                            <option value="WCP">WCP无尘棚 - Phòng sạch</option>
                                            <option value="LSX">LSX流水线 - Băng tải</option>
                                            <option value="ZWJ">ZWJ转弯机 - Băng tải chuyển hướng 90,180</option>
                                            <option value="GZL">GZL改造类 - Cải tạo</option>
                                            <option value="BSX">BSX倍速线 - Băng chuyền xích</option>
                                            <option value="WLL">WLL围栏类 - Hàng rào</option>
                                            <option value="GTX">GTX滚筒线 - Băng chuyền con lăn</option>
                                            <option value="ZHT">ZHT展会图 - Bản vẽ mặt bằng</option>
                                            <option value="LHX">LHX老化线 - Băng chuyền lão hóa</option>
                                        </select>
                                        <label for="code-category"><span data-i18n="category">Hạng mục</span> <span class="text-danger">*</span></label>
                                        <div class="invalid-feedback" id="code-category-error"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <button type="submit" class="btn btn-primary btn-lg w-100" id="btn-create-code-submit">
                                    <i class="bi bi-plus-circle me-2"></i><span data-i18n="create_btn">Tạo Mã</span>
                                </button>
                            </div>
                        </form>
                        
                        <!-- Result Display -->
                        <div class="mt-3" id="generated-code-container" style="display: none;">
                            <div class="input-group">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- History Section - Right Column -->
            <div class="col-lg-8 col-md-7">
                <div class="card h-100">
                    <div class="card-header bg-secondary text-white">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="mb-0"><i class="bi bi-history"></i> <span data-i18n="history">Lịch Sử Tạo Mã</span></h5>
                            <div>
                                <button class="btn btn-sm btn-light" id="btn-refresh-history">
                                    <i class="bi bi-arrow-clockwise"></i> <span data-i18n="refresh">Làm mới</span>
                                </button>
                                <button class="btn btn-sm btn-success" id="btn-export-history">
                                    <i class="bi bi-file-earmark-excel"></i> <span data-i18n="export_excel">Xuất Excel</span>
                                </button>
                            </div>
                        </div>
                    </div>
                    <!-- Stats Row - Compact Inline -->
                    <div class="px-3 py-1" id="code-history-stats" style="border-bottom: 1px solid #dee2e6;">
                        <div class="d-flex flex-wrap gap-2 align-items-center">
                            <div class="d-flex align-items-center">
                                <span class="fw-bold text-primary me-1" id="stat-total-code">0</span>
                                <span class="text-muted small" data-i18n="total">Tổng</span>
                            </div>
                            <div class="vr"></div>
                            <div class="d-flex align-items-center">
                                <span class="fw-bold text-success me-1" id="stat-today-code">0</span>
                                <span class="text-muted small" data-i18n="today">Hôm nay</span>
                            </div>
                            <div class="vr"></div>
                            <div class="d-flex align-items-center">
                                <span class="fw-bold text-primary me-1" id="stat-week-code">0</span>
                                <span class="text-muted small" data-i18n="week">Tuần</span>
                            </div>
                            <div class="vr"></div>
                            <div class="d-flex align-items-center">
                                <span class="fw-bold text-info small" id="stat-latest-code">-</span>
                                <span class="text-muted small ms-1" data-i18n="latest">Mới nhất</span>
                            </div>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive" style="max-height: 350px; overflow-y: auto;">
                            <table class="table table-striped table-hover table-bordered mb-0" id="code-history-table">
                                <thead class="table-light sticky-top">
                                    <tr>
                                        <th data-i18n="stt">STT</th>
                                        <th data-i18n="name">Tên</th>
                                        <th data-i18n="employee_code_th">Mã nhân viên</th>
                                        <th data-i18n="category_th">Hạng mục</th>
                                        <th data-i18n="drawing_code">Mã bản vẽ</th>
                                        <th data-i18n="mother_code">Mã mẹ</th>
                                        <th data-i18n="time">Thời gian</th>
                                        <th data-i18n="action">Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody id="code-history-table-body">
                                    <!-- Data will be loaded here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <!-- Pagination for History -->
                    <div class="card-footer py-2">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <span id="code-history-page-info" data-i18n="page_info">Hiển thị 0 bản ghi</span>
                            </div>
                            <div class="col-auto">
                                <select class="form-select form-select-sm" id="code-history-page-size" style="width: auto;">
                                    <option value="10">10 / <span data-i18n="per_page">trang</span></option>
                                    <option value="20" selected>20 / <span data-i18n="per_page">trang</span></option>
                                    <option value="50">50 / <span data-i18n="per_page">trang</span></option>
                                    <option value="100">100 / <span data-i18n="per_page">trang</span></option>
                                </select>
                            </div>
                            <div class="col-auto ms-auto">
                                <nav>
                                    <ul class="pagination mb-0" id="code-history-pagination">
                                        <!-- Pagination will be generated here -->
                                    </ul>
                                </nav>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Translate all newly rendered content
    if (window.translatePage) {
        window.translatePage();
    }
}

/**
 * Setup Create Code event listeners
 */
function setupTaomabanveEvents() {
    // Language selector buttons
    $(document).on('click', '.lang-btn', function() {
        const lang = $(this).data('lang');
        // Gọi hàm xử lý trong module này (sẽ gọi hàm toàn cục)
        if (window.handleTaomabanveLanguageChange) {
            window.handleTaomabanveLanguageChange(lang);
        }
    });
    
    // Create code form submit
    $('#create-code-form').submit(handleCreateCode);
    
    // Refresh history button
    $('#btn-refresh-history').click(function() {
        loadCodeHistory();
    });
    
    // Export history button
    $('#btn-export-history').click(function() {
        exportCodeHistory();
    });
    
    // Page size change
    $('#code-history-page-size').change(function() {
        TaoMaBanVeState.pageSize = parseInt($(this).val());
        TaoMaBanVeState.currentPage = 1;
        loadCodeHistory();
    });
    
    // Character counter for name field
    $('#code-name').on('input', function() {
        const length = $(this).val().length;
        $('#code-name-count').text(length);
        
        if (length > 80) {
            $('#code-name-count').addClass('text-warning');
        } else if (length >= 100) {
            $('#code-name-count').removeClass('text-warning').addClass('text-danger');
        } else {
            $('#code-name-count').removeClass('text-warning text-danger');
        }
    });
    
    // Employee code input validation
    $('#employee-code').on('input', function() {
        let value = $(this).val();
        value = value.replace(/\D/g, '');
        if (value.length > 3) {
            value = value.substring(0, 3);
        }
        $(this).val(value);
        
        if (value.length === 3 && value !== '000') {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else if (value.length > 0) {
            $(this).removeClass('is-valid is-invalid');
        }
    });
    
    // Category selection feedback
    $('#code-category').on('change', function() {
        if ($(this).val()) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else {
            $(this).removeClass('is-valid');
        }
    });
}

// ============================================
// AUTO FILL
// ============================================

/**
 * Auto-fill user info from localStorage
 */
function autoFillUserInfo() {
    try {
        const userStr = localStorage.getItem('current_user');
        if (userStr) {
            const user = JSON.parse(userStr);
            
            const nameField = $('#code-name');
            if (user.full_name) {
                nameField.val(user.full_name);
            } else if (user.username) {
                nameField.val(user.username);
            }
            
            $('#code-name-count').text(nameField.val().length);
            
            const empCodeField = $('#employee-code');
            if (user.employee_id) {
                let empCode = user.employee_id.toString();
                empCode = empCode.padStart(3, '0').slice(-3);
                empCodeField.val(empCode);
            }
        }
    } catch (error) {
        console.error('[TaoMaBanVe] AutoFill error:', error);
    }
}

/**
 * Auto-select last used category
 */
function autoSelectLastCategory() {
    try {
        const lastCategory = localStorage.getItem('last_category');
        if (lastCategory) {
            const categorySelect = $('#code-category');
            if (categorySelect.find(`option[value="${lastCategory}"]`).length > 0) {
                categorySelect.val(lastCategory);
            }
        }
    } catch (error) {
        console.error('[TaoMaBanVe] AutoSelect error:', error);
    }
}

/**
 * Save last used category
 * @param {string} category - Category code
 */
function saveLastCategory(category) {
    try {
        if (category) {
            localStorage.setItem('last_category', category);
        }
    } catch (error) {
        console.error('[TaoMaBanVe] SaveLastCategory error:', error);
    }
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Load code history
 */
async function loadCodeHistory() {
    console.log('[TaoMaBanVe] Loading code history...');
    
    const tbody = $('#code-history-table-body');
    tbody.html('<tr><td colspan="8" class="text-center py-3"><div class="spinner-border spinner-border-sm" role="status"></div> ' + t_taomabanve('loading') + '</td></tr>');
    
    TaoMaBanVeState.isLoading = true;
    
    try {
        const result = await api.getCodeHistory(1, 999999);
        
        if (result && result.data && Array.isArray(result.data)) {
            TaoMaBanVeState.codeHistory = result.data;
            TaoMaBanVeState.totalRecords = result.total || 0;
            
            // Load parent codes for all history items
            TaoMaBanVeState.codeHistory = await loadParentCodesForHistory(TaoMaBanVeState.codeHistory);
            
            calculateAndDisplayStats(result.data);
            renderCodeHistoryTable();
            
            // Hide pagination since we loaded all data
            $('#code-history-pagination').closest('.col-auto').hide();
            $('#code-history-page-size').closest('.col-auto').hide();
        } else {
            TaoMaBanVeState.codeHistory = [];
            tbody.html(createEmptyState(t_taomabanve('no_history'), 8));
        }
    } catch (error) {
        console.error('[TaoMaBanVe] Load error:', error);
        tbody.html(createErrorState(t_taomabanve('load_history_error') + error.message, 8));
    } finally {
        TaoMaBanVeState.isLoading = false;
    }
}

/**
 * Render code history table
 */
function renderCodeHistoryTable() {
    const tbody = $('#code-history-table-body');
    
    if (TaoMaBanVeState.codeHistory.length === 0) {
        tbody.html(createEmptyState(t_taomabanve('no_history'), 8));
        $('#code-history-page-info').text(t_taomabanve('page_info', { start: 0, end: 0, total: 0 }));
        return;
    }
    
    // Calculate pagination values
    const start = (TaoMaBanVeState.currentPage - 1) * TaoMaBanVeState.pageSize + 1;
    const end = Math.min(TaoMaBanVeState.currentPage * TaoMaBanVeState.pageSize, TaoMaBanVeState.totalRecords);
    const pageInfoText = t_taomabanve('page_info', { start: start, end: end, total: TaoMaBanVeState.totalRecords });
    $('#code-history-page-info').text(pageInfoText);
    
    let html = '';
    
    TaoMaBanVeState.codeHistory.forEach((item, index) => {
        // Get translated category name
        const categoryDisplay = getCategoryDisplayName(item.category);
        
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${escapeHtml(item.name || '')}</td>
                <td>${escapeHtml(item.employee || '')}</td>
                <td>${escapeHtml(categoryDisplay)}</td>
                <td><code class="code-value">${escapeHtml(item.code || '')}</code></td>
                <td>${item.parent_code ? '<code class="parent-code text-success">' + escapeHtml(item.parent_code) + '</code>' : '<span class="text-muted">-</span>'}</td>
                <td>${formatDateTime(item.time)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary btn-copy-history me-1" data-code="${escapeHtml(item.code || '')}" title="Copy">
                        <i class="bi bi-clipboard"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger btn-delete-history" data-code="${escapeHtml(item.code || '')}" title="Xóa">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.html(html);
    
    // Add click handlers
    $('.btn-copy-history').click(function() {
        const code = $(this).data('code');
        navigator.clipboard.writeText(code).then(() => {
            showToast(t_taomabanve('toast_success'), t_taomabanve('toast_code_copy'), 'success');
        });
    });
    
    $('.btn-delete-history').click(function() {
        const code = $(this).data('code');
        handleDeleteCodeHistory(code);
    });
}

/**
 * Calculate and display statistics
 * @param {Array} data - Code history data
 */
function calculateAndDisplayStats(data) {
    if (!data || data.length === 0) {
        $('#stat-total-code').text('0');
        $('#stat-today-code').text('0');
        $('#stat-week-code').text('0');
        $('#stat-latest-code').text('-');
        return;
    }
    
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    // Get start of week (Monday)
    const dayOfWeek = now.getDay();
    const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() + mondayOffset);
    weekStart.setHours(0, 0, 0, 0);
    
    let todayCount = 0;
    let weekCount = 0;
    let latestCode = null;
    let latestTimestamp = null;
    
    data.forEach(item => {
        if (!item.time) return;
        
        const itemDate = new Date(item.time);
        const itemDateOnly = new Date(itemDate.getFullYear(), itemDate.getMonth(), itemDate.getDate());
        
        if (itemDateOnly.getTime() === today.getTime()) {
            todayCount++;
        }
        
        if (itemDate >= weekStart) {
            weekCount++;
        }
        
        if (!latestTimestamp || itemDate > latestTimestamp) {
            latestTimestamp = itemDate;
            latestCode = item.code;
        }
    });
    
    $('#stat-total-code').text(data.length);
    $('#stat-today-code').text(todayCount);
    $('#stat-week-code').text(weekCount);
    
    if (latestCode) {
        $('#stat-latest-code').text(getRelativeTime(latestTimestamp, TaoMaBanVeState.currentLang));
    } else {
        $('#stat-latest-code').text('-');
    }
}

// ============================================
// ACTIONS
// ============================================

/**
 * Handle create code form submission
 */
async function handleCreateCode(e) {
    e.preventDefault();
    
    const name = $('#code-name').val().trim();
    const employeeCode = $('#employee-code').val();
    const category = $('#code-category').val();
    
    // Validate
    if (!employeeCode || employeeCode.length !== 3) {
        $('#employee-code').addClass('is-invalid');
        showToast(t_taomabanve('toast_error'), t_taomabanve('validation_employee_3digits'), 'error');
        return;
    }
    
    if (employeeCode === '000') {
        $('#employee-code').addClass('is-invalid');
        showToast(t_taomabanve('toast_error'), t_taomabanve('validation_employee_not_zero'), 'error');
        return;
    }
    
    if (!name) {
        showToast(t_taomabanve('toast_error'), t_taomabanve('validation_name_required'), 'error');
        return;
    }
    
    if (!category) {
        showToast(t_taomabanve('toast_error'), t_taomabanve('validation_category_required'), 'error');
        return;
    }
    
    // Disable submit button
    const submitBtn = $('#btn-create-code-submit');
    const originalBtnText = submitBtn.html();
    submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>' + t_taomabanve('creating_code'));
    
    showLoading(t_taomabanve('creating'));
    
    try {
        // Save last used category
        saveLastCategory(category);
        
        const result = await api.createCode(name, category, employeeCode);
        
        if (result.success && result.code) {
            $('#generated-code').text(result.code);
            $('#generated-code-container').removeClass('d-none');
            $('#generated-code-container').show();
            
            // Copy to clipboard automatically
            try {
                await navigator.clipboard.writeText(result.code);
                showToast(t_taomabanve('toast_success'), t_taomabanve('toast_code_created') + result.code, 'success');
            } catch (clipErr) {
                showToast(t_taomabanve('toast_success'), t_taomabanve('toast_code_created') + result.code, 'success');
            }
            
            $('#generated-code-container').hide();
            
            // Reload history
            setTimeout(async () => {
                await loadCodeHistory();
            }, 500);
        } else {
            throw new Error(result.error || 'Có lỗi xảy ra khi tạo mã');
        }
    } catch (error) {
        console.error('[TaoMaBanVe] Create error:', error);
        showToast(t_taomabanve('toast_error'), error.message || 'Không thể tạo mã. Vui lòng thử lại.', 'error');
    } finally {
        submitBtn.prop('disabled', false).html(originalBtnText);
        hideLoading();
    }
}

/**
 * Handle delete code history
 * @param {string} code - Code to delete
 */
async function handleDeleteCodeHistory(code) {
    if (!code) return;
    
    const password = prompt(t_taomabanve('delete_code_confirm').replace('{code}', code));
    
    if (!password) return;
    
    if (password.trim() !== 'kelly') {
        showToast(t_taomabanve('toast_error'), t_taomabanve('delete_code_wrong_password'), 'error');
        return;
    }
    
    showLoading(t_taomabanve('deleting_code'));
    
    try {
        const result = await api.deleteCodeHistory(code, password);
        
        if (result.success) {
            showToast(t_taomabanve('toast_success'), t_taomabanve('toast_code_deleted').replace('{code}', code), 'success');
            await loadCodeHistory();
        } else {
            throw new Error(result.error || 'Có lỗi xảy ra khi xóa');
        }
    } catch (error) {
        console.error('[TaoMaBanVe] Delete error:', error);
        showToast(t_taomabanve('toast_error'), error.message || 'Không thể xóa mã', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Export code history to Excel
 */
async function exportCodeHistory() {
    showLoading(t_taomabanve('exporting_data'));
    
    try {
        const result = await api.exportCodeHistory();
        
        if (!result.data || result.data.length === 0) {
            showToast(t_taomabanve('toast_warning'), t_taomabanve('toast_no_data_export'), 'warning');
            return;
        }
        
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(result.data);
        XLSX.utils.book_append_sheet(wb, ws, t_taomabanve('excel_sheet_name'));
        XLSX.writeFile(wb, t_taomabanve('excel_filename_prefix') + new Date().toISOString().slice(0, 10) + '.xlsx');
        
        showToast(t_taomabanve('toast_success'), t_taomabanve('toast_export_success').replace('{type}', 'Excel'), 'success');
    } catch (error) {
        console.error('[TaoMaBanVe] Export error:', error);
        showToast(t_taomabanve('toast_error'), 'Không thể xuất Excel: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// MULTILANGUAGE SUPPORT
// ============================================

// Use global translation function from i18n.js
function t_taomabanve(key, params) {
    let translation = key;
    
    if (window.t) {
        translation = window.t(key, params);
    } else {
        // Fallback to localStorage language if window.t not available
        const lang = localStorage.getItem('language') || 'vi';
        const translations = {
            'vi': {
                'page_info': 'Hiển thị {start} - {end} của {total} bản ghi',
                'no_history': 'Chưa có lịch sử tạo mã',
                'loading': 'Đang tải...',
                'load_history_error': 'Lỗi tải lịch sử: '
            },
            'zh': {
                'page_info': '显示 {start} - {end}，共 {total} 条',
                'no_history': '暂无创建记录',
                'loading': '加载中...',
                'load_history_error': '加载历史记录错误: '
            }
        };
        
        const langData = translations[lang] || translations['vi'];
        translation = langData[key] || key;
    }
    
    // Replace placeholders if params provided
    if (params && typeof params === 'object') {
        Object.keys(params).forEach(param => {
            translation = translation.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
        });
    }
    
    return translation;
}

// Change language handler for this module
function handleTaomabanveLanguageChange(lang) {
    console.log('[TaoMaBanVe] handleTaomabanveLanguageChange called with:', lang);
    
    // Gọi hàm toàn cục để đổi ngôn ngữ (quan trọng!)
    if (window.changeLanguage) {
        window.changeLanguage(lang);
    }
    
    // Cập nhật state cục bộ
    TaoMaBanVeState.currentLang = lang;
    
    // Cập nhật giao diện nút ngôn ngữ
    setTimeout(() => {
        const container = document.getElementById('taomabanve-container');
        if (container) {
            container.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active', 'btn-primary');
                btn.classList.add('btn-outline-primary');
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active', 'btn-primary');
                    btn.classList.remove('btn-outline-primary');
                }
            });
        }
    }, 50);
    
    // Translate category dropdown options
    translateCategoryDropdown();
    
    // Cập nhật lại các thống kê với ngôn ngữ mới
    calculateAndDisplayStats(TaoMaBanVeState.codeHistory);
}

// Lắng nghe sự kiện thay đổi ngôn ngữ từ header chính
window.addEventListener('languageChanged', function(e) {
    const lang = e.detail?.language || localStorage.getItem('language') || 'vi';
    TaoMaBanVeState.currentLang = lang;
    
    // Cập nhật trạng thái nút ngôn ngữ (chỉ trong container taomabanve)
    setTimeout(() => {
        const container = document.getElementById('taomabanve-container');
        if (container) {
            container.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active', 'btn-primary');
                btn.classList.add('btn-outline-primary');
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active', 'btn-primary');
                    btn.classList.remove('btn-outline-primary');
                }
            });
        }
    }, 50);
    
    // Dịch lại trang
    if (window.translatePage) {
        window.translatePage();
    }
    
    // Translate category dropdown options
    translateCategoryDropdown();
    
    // Cập nhật lại các thống kê
    calculateAndDisplayStats(TaoMaBanVeState.codeHistory);
});

// Get relative time string - sử dụng hàm dịch toàn cục
function getRelativeTime_taomabanve(date) {
    if (!date) return '-';
    
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) {
        return seconds + ' ' + t_taomabanve('seconds_ago');
    } else if (minutes < 60) {
        return minutes + ' ' + t_taomabanve('minutes_ago');
    } else if (hours < 24) {
        return hours + ' ' + t_taomabanve('hours_ago');
    } else if (days === 1) {
        return t_taomabanve('yesterday');
    } else if (days < 7) {
        return days + ' ' + t_taomabanve('days_ago');
    } else {
        return date.toLocaleDateString(TaoMaBanVeState.currentLang === 'zh' ? 'zh-CN' : 'vi-VN');
    }
}

// Get category display name with bilingual format (always shows Code + Chinese - Vietnamese)
function getCategoryDisplayName(categoryCode) {
    if (!categoryCode) return '';
    
    // Bilingual category names - always show in this format
    const CATEGORIES_BILINGUAL = {
        'SJT': 'SJT散件图 - Bản vẽ tách chi tiết',
        'WLJ': 'WLJ物料架 - Giá đựng vật liệu',
        'ZZC': 'ZZC周转车 - Xe trung chuyển',
        'GZT': 'GZT工作台 - Bàn thao tác',
        'WCP': 'WCP无尘棚 - Phòng sạch',
        'LSX': 'LSX流水线 - Băng tải',
        'ZWJ': 'ZWJ转弯机 - Băng tải chuyển hướng 90,180',
        'GZL': 'GZL改造类 - Cải tạo',
        'BSX': 'BSX倍速线 - Băng chuyền xích',
        'WLL': 'WLL围栏类 - Hàng rào',
        'GTX': 'GTX滚筒线 - Băng chuyền con lăn',
        'ZHT': 'ZHT展会图 - Bản vẽ mặt bằng',
        'LHX': 'LHX老化线 - Băng chuyền lão hóa'
    };
    
    return CATEGORIES_BILINGUAL[categoryCode] || categoryCode;
}

// Translate category dropdown options - No longer needed since we use bilingual format
function translateCategoryDropdown() {
    // Categories are now displayed in bilingual format (Code + Chinese - Vietnamese)
    // No translation needed - content is hardcoded and fixed
    console.log('[TaoMaBanVe] translateCategoryDropdown called (no action needed - bilingual format)');
}

// Search parent code from API
async function searchParentCode(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/codes/search-parent?code=${encodeURIComponent(code)}`);
        const result = await response.json();
        
        if (result.success && result.parent_code) {
            return result.parent_code;
        }
        return null;
    } catch (error) {
        console.error('[TaoMaBanVe] Search parent code error:', error);
        return null;
    }
}

// Load parent codes for all history items - ULTRA OPTIMIZED with batch API
async function loadParentCodesForHistory(historyData) {
    if (!historyData || historyData.length === 0) return historyData;
    
    const updatedData = [...historyData];
    const codesToSearch = [];
    
    // Collect codes that need parent lookup
    for (let i = 0; i < updatedData.length; i++) {
        const item = updatedData[i];
        // Only search for codes that start with category prefix (like PGZT, PWLL, etc.)
        // Skip codes that already look like cInvCode (start with '10')
        if (item.code && !item.parent_code && !item.code.startsWith('10')) {
            codesToSearch.push(item.code);
        }
    }
    
    if (codesToSearch.length === 0) return updatedData;
    
    try {
        const startTime = performance.now();
        let result = null;
        
        // Use POST for large batches (> 200 codes) to avoid URL length limits
        if (codesToSearch.length > 200) {
            const response = await fetch(
                `${API_BASE_URL}/codes/search-parent-batch-post`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ codes: codesToSearch })
                }
            );
            result = await response.json();
        } else {
            // Use GET for smaller batches
            const codesParam = codesToSearch.join(',');
            const response = await fetch(
                `${API_BASE_URL}/codes/search-parent-batch?codes=${encodeURIComponent(codesParam)}`
            );
            result = await response.json();
        }
        
        const elapsed = performance.now() - startTime;
        console.log(`[TaoMaBanVe] Batch parent lookup: ${codesToSearch.length} codes in ${elapsed.toFixed(0)}ms`);
        
        if (result.success && result.results) {
            // Apply results to data
            for (let i = 0; i < updatedData.length; i++) {
                const code = updatedData[i].code;
                if (code && result.results[code]) {
                    updatedData[i].parent_code = result.results[code];
                }
            }
        }
    } catch (error) {
        console.error('[TaoMaBanVe] Batch parent code lookup error:', error);
    }
    
    return updatedData;
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initTaomabanveModule = initTaomabanveModule;
window.onTaomabanveTabInit = function() {
    // Set initial language button state (chỉ trong container taomabanve)
    setTimeout(() => {
        const container = document.getElementById('taomabanve-container');
        if (container) {
            container.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active', 'btn-primary');
                btn.classList.add('btn-outline-primary');
                if (btn.dataset.lang === TaoMaBanVeState.currentLang) {
                    btn.classList.add('active', 'btn-primary');
                    btn.classList.remove('btn-outline-primary');
                }
            });
        }
    }, 100);
    
    if (!TaoMaBanVeState.isLoading && TaoMaBanVeState.codeHistory.length === 0) {
        loadCodeHistory();
    }
    
    // Ensure content is translated on tab init
    if (window.translatePage) {
        window.translatePage();
    }
};

// Export module function to global scope
window.handleTaomabanveLanguageChange = handleTaomabanveLanguageChange;
