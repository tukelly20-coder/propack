/**
 * Mở mã liệu Web App - JavaScript
 * Xử lý giao diện và gọi API backend
 */

// ========================================================================
// State
// ========================================================================

const state = {
    history: [],
    cachedMatches: [],
    isSearching: false
};

// ========================================================================
// DOM Elements
// ========================================================================

const elements = {
    // Search
    txtCode: document.getElementById('txt-code'),
    btnSearch: document.getElementById('btn-search'),
    btnClearInput: document.getElementById('btn-clear-input'),
    historyCombo: document.getElementById('history-combo'),
    historyChips: document.getElementById('history-chips'),
    btnClearHistory: document.getElementById('btn-clear-history'),
    
    // Matches
    resultsInfo: document.getElementById('results-info'),
    listMatches: document.getElementById('list-matches'),
    resultCount: document.getElementById('result-count'),
    btnOpenSelected: document.getElementById('btn-open-selected'),
    btnOpenAll: document.getElementById('btn-open-all'),
    
    // Status
    statusText: document.getElementById('status-text'),
    statusDot: document.getElementById('status-dot'),
    progressContainer: document.getElementById('progress-container'),
    progressBar: document.getElementById('progress-bar'),
    
    // Log
    txtLog: document.getElementById('txt-log'),
    btnCopyLog: document.getElementById('btn-copy-log'),
    btnClearLog: document.getElementById('btn-clear-log'),
    
    // Menu
    btnRefresh: document.getElementById('btn-refresh'),
    btnAbout: document.getElementById('btn-about'),
    
    // Loading
    loading: document.getElementById('loading'),
    
    // Modal
    copyModal: document.getElementById('copy-modal'),
    copyCount: document.getElementById('copy-count'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    
    // Toast
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

// ========================================================================
// Utility Functions
// ========================================================================

/**
 * Thêm log message vào panel
 */
function appendLog(message, type = 'info') {
    const now = new Date();
    const timestamp = now.toLocaleTimeString('vi-VN', { hour12: false });
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-message">${escapeHtml(message)}</span>
    `;
    elements.txtLog.appendChild(logEntry);
    elements.txtLog.scrollTop = elements.txtLog.scrollHeight;
}

/**
 * Escape HTML để tránh XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Cập nhật trạng thái
 */
function setStatus(message, loading = false) {
    elements.statusText.textContent = message;
    if (loading) {
        elements.statusDot.classList.add('loading');
    } else {
        elements.statusDot.classList.remove('loading');
    }
}

/**
 * Hiển thị/ẩn loading
 */
function setLoading(show) {
    if (show) {
        elements.loading.classList.remove('hidden');
    } else {
        elements.loading.classList.add('hidden');
    }
}

/**
 * Cập nhật progress bar
 */
function setProgress(percent) {
    if (percent > 0 && percent < 100) {
        elements.progressContainer.classList.remove('hidden');
        elements.progressBar.style.width = `${percent}%`;
    } else {
        elements.progressContainer.classList.add('hidden');
        elements.progressBar.style.width = '0%';
    }
}

/**
 * Bật/tắt giao diện tìm kiếm
 */
function setSearchEnabled(enabled) {
    elements.txtCode.disabled = !enabled;
    elements.btnSearch.disabled = !enabled;
    elements.listMatches.disabled = !enabled;
    elements.btnOpenSelected.disabled = !enabled;
    elements.btnOpenAll.disabled = !enabled;
}

// ========================================================================
// API Functions
// ========================================================================

/**
 * Gọi API kiểm tra trạng thái
 */
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'ready') {
            appendLog('[SYSTEM] Kết nối Excel OK', 'info');
            setStatus('Sẵn sàng');
        } else {
            appendLog(`[WARN] ${data.message}`, 'warning');
            setStatus('Lỗi kết nối');
        }
        return data;
    } catch (error) {
        appendLog(`[ERROR] Không thể kết nối server: ${error.message}`, 'error');
        setStatus('Lỗi kết nối');
        return null;
    }
}

/**
 * Gọi API tìm kiếm mã
 */
async function searchCode(code) {
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        appendLog(`[ERROR] Lỗi tìm kiếm: ${error.message}`, 'error');
        return { type: 'error', message: error.message };
    }
}

/**
 * Gọi API tìm kiếm nhiều mã
 */
async function searchMultiple(codes) {
    try {
        const response = await fetch('/api/search-multiple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        appendLog(`[ERROR] Lỗi tìm kiếm: ${error.message}`, 'error');
        return { type: 'error', message: error.message };
    }
}

/**
 * Lấy lịch sử tìm kiếm
 */
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        state.history = data.history || [];
        updateHistoryDropdown();
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

/**
 * Lưu lịch sử tìm kiếm
 */
async function saveHistory() {
    try {
        await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ history: state.history })
        });
    } catch (error) {
        console.error('Failed to save history:', error);
    }
}

// ========================================================================
// UI Functions
// ========================================================================

/**
 * Cập nhật dropdown và chips lịch sử
 */
function updateHistoryDropdown() {
    // Update dropdown
    elements.historyCombo.innerHTML = '<option value="">-- Chọn từ lịch sử --</option>';
    
    state.history.forEach(code => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = code;
        elements.historyCombo.appendChild(option);
    });
    
    // Update chips (show only last 5 items)
    elements.historyChips.innerHTML = '';
    state.history.slice(0, 5).forEach(code => {
        const chip = document.createElement('span');
        chip.className = 'history-chip';
        chip.innerHTML = `${escapeHtml(code)} <span class="chip-remove" data-code="${escapeHtml(code)}">&times;</span>`;
        chip.addEventListener('click', (e) => {
            if (e.target.classList.contains('chip-remove')) {
                removeFromHistory(e.target.dataset.code);
            } else {
                elements.txtCode.value = code;
                elements.txtCode.focus();
                elements.txtCode.select();
            }
        });
        elements.historyChips.appendChild(chip);
    });
    
    // Show/hide based on history
    if (state.history.length > 0) {
        elements.historyCombo.classList.remove('hidden');
    } else {
        elements.historyCombo.classList.add('hidden');
    }
    
    // Update datalist for autocomplete
    elements.txtCode.setAttribute('list', 'history-datalist');
    let datalist = document.getElementById('history-datalist');
    if (!datalist) {
        datalist = document.createElement('datalist');
        datalist.id = 'history-datalist';
        elements.txtCode.parentNode.appendChild(datalist);
    }
    datalist.innerHTML = state.history.map(h => `<option value="${escapeHtml(h)}">`).join('');
}

/**
 * Xóa một mã khỏi lịch sử
 */
function removeFromHistory(code) {
    state.history = state.history.filter(h => h !== code);
    updateHistoryDropdown();
    saveHistory();
    appendLog(`[SYSTEM] Đã xóa '${code}' khỏi lịch sử.`, 'info');
}

/**
 * Hiển thị kết quả tìm kiếm
 */
function showResults(result) {
    // Cập nhật badge count
    if (result.type === 'multiple') {
        elements.resultCount.textContent = result.matches ? result.matches.length : 0;
    } else {
        elements.resultCount.textContent = result.urls ? result.urls.length : 0;
    }
    
    if (result.type === 'multiple') {
        // Nhiều kết quả - hiển thị danh sách để chọn
        showMultipleMatches(result.matches);
    } else if (result.type === 'success') {
        // Thành công
        showSuccessResult(result);
    } else if (result.type === 'error') {
        // Lỗi
        showErrorResult(result.message);
    }
}

/**
 * Hiển thị nhiều kết quả
 */
function showMultipleMatches(matches) {
    state.cachedMatches = matches;
    elements.listMatches.innerHTML = '';
    
    // Nhóm theo cInvCode
    const uniqueCodes = {};
    matches.forEach(m => {
        const cinv = m.cInvCode;
        if (!uniqueCodes[cinv]) {
            uniqueCodes[cinv] = [];
        }
        uniqueCodes[cinv].push(m.cEngineerFigNo);
    });
    
    // Thêm vào list
    let index = 1;
    matches.forEach(m => {
        const option = document.createElement('option');
        option.value = index - 1;
        option.textContent = `${m.cEngineerFigNo} → ${m.cInvCode}`;
        elements.listMatches.appendChild(option);
        index++;
    });
    
    // Hiển thị thông tin
    const uniqueCount = Object.keys(uniqueCodes).length;
    const totalCount = matches.length;
    let infoHtml = `<i class="fas fa-folder-open"></i> Tổng: <strong>${totalCount}</strong> kết quả | Mã duy nhất: <strong>${uniqueCount}</strong>`;
    if (uniqueCount < totalCount) {
        infoHtml += ' | <i class="fas fa-exclamation-triangle"></i> Một số mã trùng lặp';
    }
    
    elements.resultsInfo.innerHTML = infoHtml;
    elements.resultsInfo.className = 'results-info';
    
    // Enable buttons
    elements.btnOpenSelected.disabled = false;
    elements.btnOpenAll.disabled = false;
    
    appendLog(`[INFO] Có ${totalCount} liên kết, vui lòng chọn mã muốn mở.`, 'info');
}

/**
 * Hiển thị kết quả thành công
 */
function showSuccessResult(result) {
    const urlCount = result.urls ? result.urls.length : 0;
    const folderCount = result.folder_count || 0;
    
    // Hiển thị thông tin kết quả
    if (urlCount > 0) {
        elements.resultsInfo.innerHTML = `<i class="fas fa-check-circle"></i> Tìm thấy: <strong>${urlCount}</strong> files trong <strong>${folderCount}</strong> folder(s)`;
        elements.resultsInfo.className = 'results-info success';
    } else {
        elements.resultsInfo.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Không tìm thấy files`;
        elements.resultsInfo.className = 'results-info warning';
    }
    
    // Clear matches list
    elements.listMatches.innerHTML = '';
    elements.resultCount.textContent = urlCount;
    
    // Disable buttons
    elements.btnOpenSelected.disabled = true;
    elements.btnOpenAll.disabled = true;
    
    // Copy URLs vào clipboard
    if (result.urls && result.urls.length > 0) {
        copyToClipboard(result.urls.join('\n'));
        showCopyModal(result.urls.length);
    }
    
    appendLog(`[OK] ${result.message}`, 'success');
}

/**
 * Hiển thị lỗi
 */
function showErrorResult(message) {
    elements.resultsInfo.innerHTML = `<i class="fas fa-times-circle"></i> ${escapeHtml(message)}`;
    elements.resultsInfo.className = 'results-info error';
    elements.listMatches.innerHTML = '';
    elements.resultCount.textContent = '0';
    
    // Disable buttons
    elements.btnOpenSelected.disabled = true;
    elements.btnOpenAll.disabled = true;
    
    appendLog(`[ERROR] ${message}`, 'error');
}

/**
 * Copy text vào clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    }
}

/**
 * Hiển thị modal thông báo đã copy
 */
function showCopyModal(count) {
    elements.copyCount.textContent = `Đã copy ${count} đường dẫn vào clipboard.`;
    elements.copyModal.classList.remove('hidden');
}

/**
 * Ẩn modal
 */
function hideModal() {
    elements.copyModal.classList.add('hidden');
}

// ========================================================================
// Event Handlers
// ========================================================================

/**
 * Xử lý tìm kiếm
 */
async function handleSearch() {
    const code = elements.txtCode.value.trim().replace(/["']/g, '');
    
    if (!code) {
        appendLog('[ERROR] Mã không được để trống!', 'error');
        elements.txtCode.focus();
        return;
    }
    
    // Thêm vào lịch sử
    if (!state.history.includes(code)) {
        state.history.unshift(code);
        state.history = state.history.slice(0, 20);
        updateHistoryDropdown();
        saveHistory();
    }
    
    // Bắt đầu tìm kiếm
    setSearchEnabled(false);
    setLoading(true);
    setProgress(30);
    setStatus(`Đang tìm: ${code}`, true);
    
    appendLog(`\n${'='.repeat(50)}\n>>> TÌM KIẾM MÃ: ${code} <<<\n${'='.repeat(50)}`, 'info');
    
    const result = await searchCode(code);
    
    setProgress(100);
    setLoading(false);
    setSearchEnabled(true);
    elements.txtCode.select();
    elements.txtCode.focus();
    
    showResults(result);
    setStatus(result.message || 'Hoàn tất', false);
}

/**
 * Xử lý mở các mã được chọn
 */
async function handleOpenSelected() {
    const selectedOptions = Array.from(elements.listMatches.selectedOptions);
    
    if (selectedOptions.length === 0) {
        appendLog('[WARN] Bạn chưa chọn mã nào. Hãy Ctrl+Click để chọn.', 'warning');
        return;
    }
    
    const selectedIndices = selectedOptions.map(opt => parseInt(opt.value));
    const codesToOpen = selectedIndices.map(i => state.cachedMatches[i].cInvCode);
    
    setSearchEnabled(false);
    setLoading(true);
    setProgress(0);
    appendLog(`[INFO] Đang xử lý ${codesToOpen.length} mã được chọn...`, 'info');
    
    const result = await searchMultiple(codesToOpen);
    
    setProgress(100);
    setLoading(false);
    setSearchEnabled(true);
    
    showResults(result);
}

/**
 * Xử lý mở tất cả
 */
async function handleOpenAll() {
    const codesToOpen = state.cachedMatches.map(m => m.cInvCode);
    
    if (codesToOpen.length === 0) {
        appendLog('[WARN] Không có mã nào để mở.', 'warning');
        return;
    }
    
    setSearchEnabled(false);
    setLoading(true);
    setProgress(0);
    appendLog(`[INFO] Đang xử lý ${codesToOpen.length} mã...`, 'info');
    
    const result = await searchMultiple(codesToOpen);
    
    setProgress(100);
    setLoading(false);
    setSearchEnabled(true);
    
    showResults(result);
}

// ========================================================================
// Keyboard Shortcuts
// ========================================================================

function setupKeyboardShortcuts() {
    // Enter để tìm kiếm
    elements.txtCode.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSearch();
        }
        // Escape để xóa input
        if (e.key === 'Escape') {
            elements.txtCode.value = '';
            elements.txtCode.focus();
        }
    });
    
    // Clear input button
    if (elements.btnClearInput) {
        elements.btnClearInput.addEventListener('click', () => {
            elements.txtCode.value = '';
            elements.txtCode.focus();
        });
    }
    
    // Ctrl+H để hiển thị/ẩn lịch sử
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'h') {
            e.preventDefault();
            toggleHistory();
        }
        // F5 để refresh
        if (e.key === 'F5') {
            e.preventDefault();
            checkStatus();
        }
        // Escape để đóng modal
        if (e.key === 'Escape') {
            hideModal();
        }
    });
}

// ========================================================================
// Toggle Functions
// ========================================================================

function toggleHistory() {
    if (elements.historyCombo.classList.contains('hidden')) {
        if (state.history.length > 0) {
            elements.historyCombo.classList.remove('hidden');
            elements.historyCombo.focus();
        }
    } else {
        elements.historyCombo.classList.add('hidden');
    }
}

function clearHistory() {
    state.history = [];
    updateHistoryDropdown();
    saveHistory();
    appendLog('[SYSTEM] Đã xóa lịch sử tìm kiếm.', 'info');
    showToast('Đã xóa lịch sử', 'success');
}

/**
 * Hiển thị toast notification
 */
function showToast(message, type = 'info') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type} hidden`;
    
    // Show
    setTimeout(() => {
        elements.toast.classList.remove('hidden');
    }, 10);
    
    // Auto hide
    setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

// ========================================================================
// Initialization
// ========================================================================

function init() {
    // Setup event listeners
    elements.btnSearch.addEventListener('click', handleSearch);
    elements.btnClearHistory.addEventListener('click', clearHistory);
    elements.btnOpenSelected.addEventListener('click', handleOpenSelected);
    elements.btnOpenAll.addEventListener('click', handleOpenAll);
    elements.btnRefresh.addEventListener('click', () => {
        checkStatus();
        showToast('Đã làm mới trạng thái', 'success');
    });
    elements.btnCopyLog.addEventListener('click', () => {
        copyToClipboard(elements.txtLog.textContent);
        showToast('Đã copy log', 'success');
    });
    elements.btnClearLog.addEventListener('click', () => {
        elements.txtLog.innerHTML = '<div class="log-entry log-info"><span class="log-time">--:--:--</span><span class="log-message">Đã xóa log</span></div>';
    });
    elements.btnCloseModal.addEventListener('click', hideModal);
    
    // Close modal on backdrop click
    elements.copyModal.addEventListener('click', (e) => {
        if (e.target === elements.copyModal) {
            hideModal();
        }
    });
    
    // History selection
    elements.historyCombo.addEventListener('change', (e) => {
        const code = e.target.value;
        if (code) {
            elements.txtCode.value = code;
            elements.historyCombo.classList.add('hidden');
            elements.txtCode.focus();
            elements.txtCode.select();
        }
    });
    
    // About button
    elements.btnAbout.addEventListener('click', () => {
        alert('Mở mã liệu Web\nPhiên bản: 1.0.0\n\n© 2026\n\nLưu ý: Do hạn chế của trình duyệt, chức năng mở Windows Explorer sẽ copy đường dẫn vào clipboard để bạn tự dán.');
    });
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Load initial data
    appendLog('[SYSTEM] Đang khởi tạo...', 'info');
    checkStatus();
    loadHistory();
    appendLog('[SYSTEM] Hệ thống sẵn sàng. Nhập mã để tìm kiếm.', 'info');
    
    // Focus vào ô tìm kiếm
    elements.txtCode.focus();
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', init);
