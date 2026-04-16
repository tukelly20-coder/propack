/**
 * AI Status System - Định nghĩa các trạng thái cho AI Chat
 * Dùng cho "Cách 2 - Hiển thị trạng thái thật"
 */

// ============================================
// STATUS CONSTANTS
// ============================================

/**
 * Các trạng thái của AI trong quá trình xử lý
 */
const AI_STATUS = {
    IDLE: "idle",                    // Không có gì đang chạy
    SENDING: "sending",              // Đang gửi request lên server
    THINKING: "thinking",            // AI đang suy nghĩ/phân tích câu hỏi
    CALLING_TOOL: "calling_tool",    // AI đang gọi API/tool bên ngoài
    PROCESSING: "processing",        // AI đang xử lý dữ liệu
    STREAMING: "streaming",          // AI đang stream nội dung trả lời
    DONE: "done",                    // Hoàn thành
    ERROR: "error"                   // Có lỗi xảy ra
};

// ============================================
// STATUS TO DISPLAY TEXT MAPPING
// ============================================

/**
 * Map trạng thái sang text hiển thị cho user
 * Sử dụng icon emoji để trực quan
 */
const STATUS_DISPLAY = {
    [AI_STATUS.IDLE]: "",
    [AI_STATUS.SENDING]: "📤 Đang gửi yêu cầu...",
    [AI_STATUS.THINKING]: "🧠 Đang suy nghĩ...",
    [AI_STATUS.CALLING_TOOL]: "🔧 Đang truy vấn dữ liệu...",
    [AI_STATUS.PROCESSING]: "⚙️ Đang xử lý...",
    [AI_STATUS.STREAMING]: "✍️ Đang trả lời...",
    [AI_STATUS.DONE]: "✅ Hoàn thành",
    [AI_STATUS.ERROR]: "❌ Có lỗi xảy ra"
};

// ============================================
// STATUS COLORS (for styling)
// ============================================

/**
 * Map trạng thái sang màu sắc (hex)
 */
const STATUS_COLORS = {
    [AI_STATUS.IDLE]: "#6c757d",
    [AI_STATUS.SENDING]: "#17a2b8",
    [AI_STATUS.THINKING]: "#6f42c1",
    [AI_STATUS.CALLING_TOOL]: "#fd7e14",
    [AI_STATUS.PROCESSING]: "#20c997",
    [AI_STATUS.STREAMING]: "#28a745",
    [AI_STATUS.DONE]: "#28a745",
    [AI_STATUS.ERROR]: "#dc3545"
};

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Lấy text hiển thị cho một trạng thái
 * @param {string} status - Trạng thái (từ AI_STATUS)
 * @returns {string} Text hiển thị
 */
function getStatusDisplay(status) {
    return STATUS_DISPLAY[status] || status;
}

/**
 * Lấy màu sắc cho một trạng thái
 * @param {string} status - Trạng thái (từ AI_STATUS)
 * @returns {string} Màu hex
 */
function getStatusColor(status) {
    return STATUS_COLORS[status] || "#6c757d";
}

/**
 * Kiểm tra xem trạng thái có phải là đang hoạt động không
 * @param {string} status - Trạng thái cần kiểm tra
 * @returns {boolean} True nếu đang hoạt động
 */
function isStatusActive(status) {
    return [AI_STATUS.SENDING, AI_STATUS.THINKING, AI_STATUS.CALLING_TOOL,
    AI_STATUS.PROCESSING, AI_STATUS.STREAMING].includes(status);
}

/**
 * Cập nhật thanh trạng thái global
 * @param {string} status - Trạng thái mới
 */
function updateGlobalStatusBar(status) {
    const bar = document.getElementById('ai-status-bar');
    if (!bar) return;

    const textEl = bar.querySelector('.ai-status-text');
    const iconEl = bar.querySelector('.ai-status-icon');

    if (status === 'idle' || status === AI_STATUS.IDLE || status === AI_STATUS.DONE) {
        // Ẩn thanh trạng thái
        bar.classList.remove('active');
        bar.classList.remove('error');
    } else if (status === 'error' || status === AI_STATUS.ERROR) {
        // Hiển thị lỗi
        bar.classList.add('active');
        bar.classList.add('error');
        if (textEl) textEl.textContent = getStatusDisplay(AI_STATUS.ERROR);
        if (iconEl) iconEl.style.display = 'none';
    } else {
        // Hiển thị trạng thái
        bar.classList.add('active');
        bar.classList.remove('error');
        if (textEl) textEl.textContent = getStatusDisplay(status);
        if (iconEl) iconEl.style.display = 'inline-block';
    }
}

// ============================================
// EXPORT TO WINDOW
// ============================================

// Export các biến và hàm để sử dụng ở các file khác
window.AI_STATUS = AI_STATUS;
window.STATUS_DISPLAY = STATUS_DISPLAY;
window.STATUS_COLORS = STATUS_COLORS;
window.getStatusDisplay = getStatusDisplay;
window.getStatusColor = getStatusColor;
window.isStatusActive = isStatusActive;
window.updateGlobalStatusBar = updateGlobalStatusBar;

console.log("[Status] AI Status system loaded");
