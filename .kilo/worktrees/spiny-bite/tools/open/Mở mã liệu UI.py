import sys
import os
import json
import importlib.util
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit, 
                               QLabel, QListWidget, QAbstractItemView, QSplitter,
                               QStatusBar, QProgressBar, QComboBox, QCompleter, QMenuBar, QMenu, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QStringListModel, QPoint
from PySide6.QtGui import QTextCursor, QKeySequence, QShortcut, QAction, QIcon

# Import updater module
try:
    import updater
except ImportError:
    updater = None

# ========================================================================
# 1. LOAD CORE MODULE SAFELY
# ========================================================================
core_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Mở mã liệu 打开链接VP.py")
spec = importlib.util.spec_from_file_location("material_core", core_path)
core = importlib.util.module_from_spec(spec)
sys.modules["material_core"] = core
spec.loader.exec_module(core)

# ========================================================================
# 2. LOG INTERCEPTOR
# ========================================================================
class SignalEmitter(QObject):
    log_emit = Signal(str)
    progress_update = Signal(int, str)  # progress percentage, status message

emitter = SignalEmitter()

original_safe_print = core.safe_print
def gui_safe_print(msg):
    # Phát signal thay vì in ra console (chạy an toàn ở mọi luồng)
    emitter.log_emit.emit(str(msg))

# Ghi đè hàm safe_print trong module gốc
core.safe_print = gui_safe_print

# ========================================================================
# 3. WORKER THREADS (KHÔNG LÀM ĐƠ GIAO DIỆN)
# ========================================================================
class LoadExcelWorker(QThread):
    finished = Signal()
    progress = Signal(int, str)
    
    def run(self):
        self.progress.emit(10, "Đang kết nối Excel...")
        core.safe_print("[SYSTEM] Bắt đầu tải dữ liệu Excel...")
        self.progress.emit(30, "Đang tải dữ liệu...")
        core.test_excel_connection()
        self.progress.emit(100, "Hoàn tất")
        self.finished.emit()

class SearchWorker(QThread):
    finished = Signal(dict)
    progress = Signal(int, str)
    
    def __init__(self, code):
        super().__init__()
        self.code = code
        
    def run(self):
        code = self.code
        self.progress.emit(10, f"Đang tìm: {code}")
        core.safe_print(f"\n" + "="*40 + f"\n>>> TÌM KIẾM MÃ: {code} <<<\n" + "="*40)
        
        # 1. Kiểm tra định dạng cEngineerFigNo
        if core.is_engineer_fig_no(code):
            self.progress.emit(20, "Nhận dạng Engineer Fig No...")
            core.safe_print(f"[INFO] Nhận diện định dạng Engineer Fig No: {code}")
            all_matches = core.find_cinvcode_from_excel(code, return_all=True)
            
            if not all_matches:
                core.safe_print(f"[ERROR] Không tìm thấy cInvCode cho cEngineerFigNo: {code}")
                self.finished.emit({"type": "error", "message": "Not found in Excel"})
                return
                
            if len(all_matches) == 1:
                # Chỉ có 1 kết quả -> tự chuyển sang cInvCode để truy vấn API
                cinv_code = all_matches[0]['cInvCode']
                core.safe_print(f"[OK] Đã tìm thấy 1 cInvCode: {cinv_code}")
                core.copy_to_clipboard(cinv_code)
                code = cinv_code
            else:
                # Có nhiều kết quả -> dừng luồng này và yêu cầu UI hiển thị list để chọn
                self.progress.emit(100, f"Tìm thấy {len(all_matches)} kết quả")
                self.finished.emit({"type": "multiple", "matches": all_matches, "original_code": self.code})
                return
                
        # 2. Truy vấn API với mã cInvCode
        self.progress.emit(40, "Đang gọi API...")
        core.safe_print(f"[API] Đang gọi server API...")
        urls = core.query_material(code)
        
        if urls:
            self.progress.emit(70, f"Đang xử lý {len(urls)} files...")
            urls_text = "\n".join(urls)
            core.copy_to_clipboard(urls_text)
            folder_count = core.open_all_folders(urls)
            core.safe_print(f"\n[OK] Đã mở {folder_count} thư mục chứa {len(urls)} file(s).")
            self.progress.emit(100, f"Hoàn tất: {len(urls)} files, {folder_count} folders")
            self.finished.emit({"type": "success", "urls": urls, "folder_count": folder_count})
        else:
            code_safe = code.replace('\\', '_').replace('/', '_') # Tránh lỗi path
            fallback_path = f"{core.FALLBACK_BASE_PATH}\\{code_safe}.jpg"
            if os.path.exists(fallback_path):
                self.progress.emit(80, "Sử dụng đường dẫn dự phòng...")
                core.safe_print(f"[INFO] Dùng đường dẫn dự phòng: {fallback_path}")
                core.copy_to_clipboard(fallback_path)
                core.open_folder_from_unc(fallback_path, open_file_directly=True)
                self.progress.emit(100, "Hoàn tất (file dự phòng)")
                self.finished.emit({"type": "success", "urls": [fallback_path]})
            else:
                core.safe_print(f"[ERROR] Không tìm thấy dữ liệu cho mã và không có file dự phòng.")
                self.progress.emit(100, "Không tìm thấy dữ liệu")
                self.finished.emit({"type": "error"})

class ProcessMultipleWorker(QThread):
    finished = Signal()
    progress = Signal(int, str)
    
    def __init__(self, cinv_codes, is_all=False):
        super().__init__()
        self.cinv_codes = cinv_codes
        self.is_all = is_all
        
    def run(self):
        total = len(self.cinv_codes)
        core.safe_print(f"\n[INFO] Đang xử lý {total} mã được chọn...")
        
        MAX_OPEN_LIMIT = 10
        codes_to_open = self.cinv_codes
        if len(codes_to_open) > MAX_OPEN_LIMIT:
            core.safe_print(f"[INFO] Giới hạn xử lý {MAX_OPEN_LIMIT} mã đầu tiên để tránh đầy màn hình.")
            codes_to_open = codes_to_open[:MAX_OPEN_LIMIT]
        
        processed = 0
        all_urls = []
        
        for i, cinv_code in enumerate(codes_to_open):
            self.progress.emit(int((i / len(codes_to_open)) * 80), f"Đang xử lý {i+1}/{len(codes_to_open)}...")
            urls = core.query_material(cinv_code)
            if urls:
                all_urls.extend(urls)
            processed += 1
        
        if all_urls:
            self.progress.emit(90, "Đang mở thư mục...")
            urls_text = "\n".join(all_urls)
            core.copy_to_clipboard(urls_text)
            folder_count = core.open_all_folders(all_urls)
            core.safe_print(f"\n[OK] Đã mở {folder_count} thư mục tổng cộng {len(all_urls)} file(s).")
            self.progress.emit(100, f"Hoàn tất: {len(all_urls)} files, {folder_count} folders")
        else:
            core.safe_print("[ERROR] Không tìm thấy file cho các mã đã chọn.")
            self.progress.emit(100, "Không tìm thấy file")
            
        self.finished.emit()

# ========================================================================
# 4. GIAO DIỆN CHÍNH
# ========================================================================
# QSS = """
# QMainWindow, QWidget {
#     background-color: #1a1b26;
#     color: #a9b1d6;
#     font-family: 'Segoe UI', Arial, sans-serif;
# }
# QLineEdit {
#     background-color: #24283b;
#     border: 1px solid #414868;
#     border-radius: 6px;
#     padding: 10px;
#     font-size: 16px;
#     color: #c0caf5;
#     font-weight: bold;
# }
# QLineEdit:focus {
#     border: 1px solid #7aa2f7;
# }
# QPushButton {
#     background-color: #7aa2f7;
#     color: #15161e;
#     border: none;
#     border-radius: 6px;
#     padding: 10px 15px;
#     font-size: 14px;
#     font-weight: bold;
# }
# QPushButton:hover {
#     background-color: #8caaee;
# }
# QPushButton:pressed {
#     background-color: #2ac3de;
# }
# QPushButton:disabled {
#     background-color: #414868;
#     color: #737aa2;
# }
# QPushButton#secondaryBtn {
#     background-color: #bb9af7;
# }
# QPushButton#secondaryBtn:hover {
#     background-color: #c099ff;
# }
# QTextEdit {
#     background-color: #1f2335;
#     border: 1px solid #414868;
#     border-radius: 6px;
#     padding: 10px;
#     font-size: 14px;
#     font-family: 'Consolas', monospace;
#     color: #9ece6a;
# }
# QListWidget {
#     background-color: #24283b;
#     border: 1px solid #414868;
#     border-radius: 6px;
#     padding: 5px;
#     font-size: 14px;
# }
# QListWidget::item {
#     padding: 8px;
#     border-radius: 4px;
# }
# QListWidget::item:hover {
#     background-color: #414868;
# }
# QListWidget::item:selected {
#     background-color: #7aa2f7;
#     color: #15161e;
#     font-weight: bold;
# }
# QLabel {
#     font-size: 14px;
#     font-weight: bold;
#     color: #7dcfff;
# }
# QStatusBar {
#     background-color: #1f2335;
#     color: #a9b1d6;
#     border-top: 1px solid #414868;
# }
# QProgressBar {
#     background-color: #24283b;
#     border: 1px solid #414868;
#     border-radius: 4px;
#     text-align: center;
#     color: #c0caf5;
# }
# QProgressBar::chunk {
#     background-color: #7aa2f7;
#     border-radius: 4px;
# }
# QComboBox {
#     background-color: #24283b;
#     border: 1px solid #414868;
#     border-radius: 6px;
#     padding: 8px;
#     color: #c0caf5;
# }
# QComboBox::drop-down {
#     border: none;
# }
# QComboBox QAbstractItemView {
#     background-color: #24283b;
#     selection-background-color: #7aa2f7;
#     color: #c0caf5;
# }
# """

class MaterialQueryUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool mã liệu")
        self.resize(1400, 800)
        
        # Set window icon (favicon)
        if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
            # Chạy dưới dạng exe - lấy đường dẫn từ sys._MEIPASS
            icon_path = os.path.join(sys._MEIPASS, "favicon.ico")
        else:
            # Chạy dev mode hoặc fallback
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "favicon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print(f"[INFO] Window icon loaded from: {icon_path}")
        else:
            print(f"[WARNING] Icon not found at: {icon_path}")
        
        # self.setStyleSheet(QSS)
        
        # Setup menu bar for updater
        self.setup_menu_bar()
        
        # Search history
        self.search_history = []
        self.max_history = 20
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_settings.json")
        self.load_settings()
        
        # Setup central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter, 1)
        
        # --- LEFT PANEL: CONTROL ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)
        
        lbl_title = QLabel("CÔNG CỤ TRA CỨU MÃ LIỆU")
        lbl_title.setStyleSheet("font-size: 18px; color: #bb9af7;")
        left_layout.addWidget(lbl_title)
        
        # Search input with history dropdown
        search_layout = QVBoxLayout()
        search_layout.setSpacing(5)
        
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("Nhập Mã / Code (VD: PABC123-...)")
        self.txt_code.returnPressed.connect(self.on_search_clicked)
        search_layout.addWidget(self.txt_code)
        
        # History dropdown
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.history_combo.setMaxCount(self.max_history)
        self.history_combo.setMinimumHeight(30)
        self.history_combo.currentIndexChanged.connect(self.on_history_selected)
        self.history_combo.setVisible(False)
        search_layout.addWidget(self.history_combo)
        
        left_layout.addLayout(search_layout)
        
        # Search buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        self.btn_search = QPushButton("Tra cứu / Search")
        self.btn_search.clicked.connect(self.on_search_clicked)
        self.btn_search.setMinimumHeight(40)
        btn_row.addWidget(self.btn_search)
        
        # History toggle button
        self.btn_history = QPushButton("⌄")
        self.btn_history.setFixedWidth(40)
        self.btn_history.setToolTip("Hiển thị lịch sử tìm kiếm")
        self.btn_history.clicked.connect(self.toggle_history)
        btn_row.addWidget(self.btn_history)
        
        # Clear history button
        self.btn_clear_history = QPushButton("🗑")
        self.btn_clear_history.setFixedWidth(40)
        self.btn_clear_history.setToolTip("Xóa lịch sử tìm kiếm")
        self.btn_clear_history.setStyleSheet("background-color: #f7768e; color: #15161e;")
        self.btn_clear_history.clicked.connect(self.on_clear_history)
        btn_row.addWidget(self.btn_clear_history)
        
        left_layout.addLayout(btn_row)
        
        # Keyboard shortcuts hint
        hint_label = QLabel("Phím tắt: Enter = Tìm kiếm | ↑↓ = Lịch sử | Ctrl+H = Ẩn/Hiện lịch sử | Ctrl+C = Copy mã")
        hint_label.setStyleSheet("font-size: 11px; color: #737aa2;")
        left_layout.addWidget(hint_label)
        
        # Multiple matches section
        self.lbl_list = QLabel("Chọn các mã liên quan (Ctrl+Click):")
        self.lbl_list.setVisible(True)
        left_layout.addWidget(self.lbl_list)
        
        self.list_matches = QListWidget()
        self.list_matches.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_matches.setVisible(True)
        # Enable context menu for copy functionality
        self.list_matches.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_matches.customContextMenuRequested.connect(self.show_list_matches_context_menu)
        left_layout.addWidget(self.list_matches, stretch=1)
        
        # Results info panel
        self.lbl_results_info = QLabel("")
        self.lbl_results_info.setStyleSheet("font-size: 12px; color: #9ece6a; padding: 5px; background-color: #1f2335; border-radius: 4px;")
        self.lbl_results_info.setVisible(True)
        left_layout.addWidget(self.lbl_results_info)
        
        self.btn_open_selected = QPushButton("Open Selected")
        self.btn_open_selected.setObjectName("secondaryBtn")
        self.btn_open_selected.setVisible(True)
        self.btn_open_selected.clicked.connect(self.on_open_selected)
        left_layout.addWidget(self.btn_open_selected)
        
        self.btn_open_all = QPushButton("Open All Files")
        self.btn_open_all.setObjectName("secondaryBtn")
        self.btn_open_all.setVisible(True)
        self.btn_open_all.clicked.connect(self.on_open_all)
        left_layout.addWidget(self.btn_open_all)
        
        left_layout.addStretch(1)
        
        # --- RIGHT PANEL: LOGS ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        lbl_log = QLabel("NHẬT KÝ HỆ THỐNG / LOGS")
        right_layout.addWidget(lbl_log)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setLineWrapMode(QTextEdit.WidgetWidth)
        self.txt_log.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.txt_log.setContextMenuPolicy(Qt.CustomContextMenu)
        self.txt_log.customContextMenuRequested.connect(self.show_log_context_menu)
        right_layout.addWidget(self.txt_log)
        
        # Add to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([450, 950])
        
        # --- STATUS BAR ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_label = QLabel("Sẵn sàng")
        self.status_bar.addWidget(self.status_label)
        
        # Connect strictly to custom emitter
        emitter.log_emit.connect(self.append_log)
        emitter.progress_update.connect(self.update_progress)
        
        self.cached_matches = []
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Setup completer for search input
        self.completer = QCompleter()
        self.txt_code.setCompleter(self.completer)
        
        # Check post-update status
        self.check_post_update_status()
        
        # Start background load
        self.start_initialization()

    # ========================================================================
    # SETTINGS PERSISTENCE
    # ========================================================================
    def load_settings(self):
        """Đọc cài đặt và lịch sử tìm kiếm từ file JSON"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.search_history = data.get('search_history', [])[:self.max_history]
        except Exception:
            self.search_history = []

    def save_settings(self):
        """Lưu lịch sử tìm kiếm vào file JSON"""
        try:
            data = {'search_history': self.search_history}
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.append_log(f"[WARN] Không thể lưu cài đặt: {e}")

    def closeEvent(self, event):
        """Lưu settings khi đóng cửa sổ"""
        self.save_settings()
        event.accept()

    def setup_shortcuts(self):
        # Ctrl+H to toggle history
        self.shortcut_history = QShortcut(QKeySequence("Ctrl+H"), self)
        self.shortcut_history.activated.connect(self.toggle_history)
        
        # Ctrl+Enter to search
        self.shortcut_search = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_search.activated.connect(self.on_search_clicked)
        
        # Ctrl+C to copy selected codes in list_matches
        self.shortcut_copy = QShortcut(QKeySequence("Ctrl+C"), self.list_matches)
        self.shortcut_copy.activated.connect(self.copy_selected_cinv_codes)
        
        # Escape to close history dropdown
        self.shortcut_escape = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_escape.activated.connect(self.hide_history)

    def toggle_history(self):
        if self.history_combo.isVisible():
            self.hide_history()
        else:
            self.show_history()

    def show_history(self):
        if self.search_history:
            self.history_combo.clear()
            self.history_combo.addItems(self.search_history)
            self.history_combo.setVisible(True)
            self.history_combo.showPopup()

    def on_clear_history(self):
        """Xóa toàn bộ lịch sử tìm kiếm"""
        self.search_history = []
        self.history_combo.clear()
        self.history_combo.setVisible(False)
        self.completer.setModel(QStringListModel([]))
        self.save_settings()
        self.append_log("[SYSTEM] Đã xóa lịch sử tìm kiếm.")

    def hide_history(self):
        self.history_combo.setVisible(False)

    def on_history_selected(self, index):
        if index >= 0 and index < len(self.search_history):
            code = self.search_history[index]
            self.txt_code.setText(code)
            self.history_combo.setVisible(False)
            self.txt_code.setFocus()
            self.txt_code.selectAll()

    def add_to_history(self, code):
        # Remove if already exists
        if code in self.search_history:
            self.search_history.remove(code)
        
        # Add to beginning
        self.search_history.insert(0, code)
        
        # Limit history size
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[:self.max_history]
        
        # Update completer
        self.completer.setModel(QStringListModel(self.search_history))

    def show_log_context_menu(self, pos: QPoint):
        """Hiển thị context menu khi click phải vào log"""
        menu = QMenu(self)
        copy_selection_action = QAction("📋 Copy dòng đã chọn", self)
        copy_selection_action.triggered.connect(self.txt_log.copy)
        copy_selection_action.setEnabled(self.txt_log.textCursor().hasSelection())
        
        copy_all_action = QAction("📄 Copy toàn bộ log", self)
        copy_all_action.triggered.connect(lambda: QApplication.clipboard().setText(self.txt_log.toPlainText()))
        
        clear_log_action = QAction("🗑 Xóa log", self)
        clear_log_action.triggered.connect(self.txt_log.clear)
        
        menu.addAction(copy_selection_action)
        menu.addAction(copy_all_action)
        menu.addSeparator()
        menu.addAction(clear_log_action)
        menu.exec(self.txt_log.mapToGlobal(pos))

    def show_list_matches_context_menu(self, pos: QPoint):
        """Hiển thị context menu khi click phải vào list_matches"""
        selected_items = self.list_matches.selectedItems()
        has_selection = len(selected_items) > 0
        has_items = self.list_matches.count() > 0
        
        menu = QMenu(self)
        
        # Copy selected cInvCodes
        copy_selected_action = QAction("Copy mã đã chọn", self)
        copy_selected_action.triggered.connect(self.copy_selected_cinv_codes)
        copy_selected_action.setEnabled(has_selection)
        
        # Copy all cInvCodes
        copy_all_action = QAction("Copy all", self)
        copy_all_action.triggered.connect(self.copy_all_cinv_codes)
        copy_all_action.setEnabled(has_items)
        
        # Copy selected rows as text
        copy_rows_action = QAction("Copy dòng", self)
        copy_rows_action.triggered.connect(self.copy_selected_rows)
        copy_rows_action.setEnabled(has_selection)
        
        menu.addAction(copy_selected_action)
        menu.addAction(copy_all_action)
        menu.addSeparator()
        menu.addAction(copy_rows_action)
        
        menu.exec(self.list_matches.mapToGlobal(pos))

    def copy_selected_cinv_codes(self):
        """Copy các cInvCode đã chọn vào clipboard"""
        selected_items = self.list_matches.selectedItems()
        if not selected_items:
            self.append_log("[WARN] Vui lòng chọn mã trước khi copy!")
            return
        
        selected_indices = [self.list_matches.row(item) for item in selected_items]
        codes = [self.cached_matches[i]['cInvCode'] for i in selected_indices]
        codes_text = "\n".join(codes)
        
        QApplication.clipboard().setText(codes_text)
        self.append_log(f"[SYSTEM] Đã copy {len(codes)} mã: {codes_text}")

    def copy_all_cinv_codes(self):
        """Copy tất cả cInvCode vào clipboard"""
        if not self.cached_matches:
            self.append_log("[WARN] Không có mã nào để copy!")
            return
        
        codes = [m['cInvCode'] for m in self.cached_matches]
        codes_text = "\n".join(codes)
        
        QApplication.clipboard().setText(codes_text)
        self.append_log(f"[SYSTEM] Đã copy {len(codes)} mã: {codes_text}")

    def copy_selected_rows(self):
        """Copy các dòng đã chọn (nguyên text hiển thị)"""
        selected_items = self.list_matches.selectedItems()
        if not selected_items:
            self.append_log("[WARN] Vui lòng chọn dòng trước khi copy!")
            return
        
        rows_text = "\n".join(item.text() for item in selected_items)
        QApplication.clipboard().setText(rows_text)
        self.append_log(f"[SYSTEM] Đã copy {len(selected_items)} dòng")

    def append_log(self, text):
        self.txt_log.append(text)
        cursor = self.txt_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.txt_log.setTextCursor(cursor)
        
    def update_progress(self, value, message):
        if value > 0 and value < 100:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
            self.status_label.setText(message)
        elif value >= 100:
            self.progress_bar.setVisible(False)
            self.status_label.setText(message if message else "Hoàn tất")
        
    def set_gui_enabled(self, enabled):
        self.txt_code.setEnabled(enabled)
        self.btn_search.setEnabled(enabled)
        self.list_matches.setEnabled(enabled)
        self.btn_open_selected.setEnabled(enabled)
        self.btn_open_all.setEnabled(enabled)

    def check_post_update_status(self):
        """Kiểm tra xem app vừa được update xong hay là bị lỗi rollback để thông báo"""
        if updater is None: return
        
        state = updater.get_update_state()
        if not state: return
        
        status = state.get("status")
        msg = state.get("message", "")
        
        if status == "Success":
            # Xóa backup dir nếu thành công để dọn dẹp không gian
            backup_dir = state.get("backup_dir", "")
            if backup_dir and os.path.exists(backup_dir):
                import shutil
                try:
                    shutil.rmtree(backup_dir)
                    self.append_log(f"\n[UPDATER] Đã dọn dẹp thư mục backup cũ thành công.")
                except Exception as e:
                    self.append_log(f"\n[UPDATER] Không thể dọn dẹp thư mục backup cũ: {e}")
                    
            QMessageBox.information(self, "Cập nhật thành công", "Ứng dụng đã được cập nhật lên phiên bản mới nhất thành công!")
            self.append_log("[UPDATER] Cập nhật thành công từ file trạng thái state.")
            
        elif status == "Failed":
             QMessageBox.warning(self, "Cập nhật thất bại", f"Quá trình cập nhật gặp sự cố sao chép file và đã tự động khôi phục bản cũ (Rollback).\nChi tiết: {msg}")
             self.append_log(f"\n[UPDATER] Cập nhật thất bại (Rollback). Lỗi: {msg}")
             
        updater.clear_update_state()

    def start_initialization(self):
        self.set_gui_enabled(False)
        self.txt_code.setText("Đang khởi tạo...")
        self.status_label.setText("Đang khởi tạo...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.init_worker = LoadExcelWorker()
        self.init_worker.progress.connect(self.update_progress)
        self.init_worker.finished.connect(self.on_init_finished)
        self.init_worker.start()
        
    def on_init_finished(self):
        self.set_gui_enabled(True)
        self.txt_code.clear()
        self.txt_code.setFocus()
        self.progress_bar.setVisible(False)
        self.status_label.setText("Sẵn sàng")
        self.append_log("[SYSTEM] Hệ thống sẵn sàng.")

    def hide_multiple_selection(self):
        self.lbl_list.setVisible(False)
        self.list_matches.setVisible(False)
        self.btn_open_selected.setVisible(False)
        self.btn_open_all.setVisible(False)
        self.lbl_results_info.setVisible(False)

    def show_multiple_selection(self, matches):
        self.cached_matches = matches
        self.list_matches.clear()
        
        # Group matches by cInvCode
        unique_codes = {}
        for m in matches:
            cinv = m['cInvCode']
            if cinv not in unique_codes:
                unique_codes[cinv] = []
            unique_codes[cinv].append(m['cEngineerFigNo'])
        
        # Add to list with count info
        for i, m in enumerate(matches, 1):
            eng_fig = m['cEngineerFigNo']
            cinv = m['cInvCode']
            self.list_matches.addItem(f"{i}. {eng_fig}  →  {cinv}")
            
        # Show results info
        unique_count = len(unique_codes)
        total_count = len(matches)
        info_text = f"📁 Tổng: {total_count} kết quả | 🔑 Mã duy nhất: {unique_count}"
        if unique_count > total_count:
            info_text += " | ⚠️ Một số mã trùng lặp"
        self.lbl_results_info.setText(info_text)
        self.lbl_results_info.setVisible(True)
            
        self.lbl_list.setVisible(True)
        self.list_matches.setVisible(True)
        self.btn_open_selected.setVisible(True)
        self.btn_open_all.setVisible(True)
        
        self.append_log(f"\n[INFO] Có {len(matches)} liên kết, vui lòng chọn file muốn mở bên trái.")

    def on_search_clicked(self):
        code = self.txt_code.text().strip().strip('"').strip("'")
        if not code:
            self.append_log("[ERROR] Mã không được để trống!")
            return
        
        # Add to history
        self.add_to_history(code)
        self.hide_history()
             
        self.set_gui_enabled(False)
        
        self.search_worker = SearchWorker(code)
        self.search_worker.progress.connect(self.update_progress)
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.start()

    def on_search_finished(self, result):
        self.set_gui_enabled(True)
        self.txt_code.selectAll()
        self.txt_code.setFocus()
        
        if result.get("type") == "multiple":
            self.show_multiple_selection(result["matches"])
        elif result.get("type") == "success":
            urls = result.get("urls", [])
            folder_count = result.get("folder_count", 0)
            # Show multiple selection widgets (even if empty)
            self.lbl_list.setVisible(True)
            self.list_matches.setVisible(True)
            self.btn_open_selected.setVisible(True)
            self.btn_open_all.setVisible(True)
            self.list_matches.clear()
            if urls:
                # Show detailed results info
                info_text = f"✅ Tìm thấy: {len(urls)} files trong {folder_count} folder(s)"
                self.lbl_results_info.setText(info_text)
                self.lbl_results_info.setStyleSheet("font-size: 12px; color: #9ece6a; padding: 5px; background-color: #1f2335; border-radius: 4px;")
                self.lbl_results_info.setVisible(True)
            else:
                self.lbl_results_info.setText("⚠️ Không tìm thấy files")
                self.lbl_results_info.setStyleSheet("font-size: 12px; color: #f7768e; padding: 5px; background-color: #1f2335; border-radius: 4px;")
                self.lbl_results_info.setVisible(True)
        elif result.get("type") == "error":
            # Show multiple selection widgets (even if empty)
            self.lbl_list.setVisible(True)
            self.list_matches.setVisible(True)
            self.btn_open_selected.setVisible(True)
            self.btn_open_all.setVisible(True)
            self.list_matches.clear()
            self.lbl_results_info.setText("❌ Không tìm thấy dữ liệu")
            self.lbl_results_info.setStyleSheet("font-size: 12px; color: #f7768e; padding: 5px; background-color: #1f2335; border-radius: 4px;")
            self.lbl_results_info.setVisible(True)

    def on_open_selected(self):
        selected_items = self.list_matches.selectedItems()
        if not selected_items:
            self.append_log("[WARN] Bạn chưa chọn file nào. Hãy Ctrl+Click để chọn.")
            return
            
        selected_indices = [self.list_matches.row(item) for item in selected_items]
        codes_to_open = [self.cached_matches[i]['cInvCode'] for i in selected_indices]
        
        self.set_gui_enabled(False)
        self.multi_worker = ProcessMultipleWorker(codes_to_open, False)
        self.multi_worker.progress.connect(self.update_progress)
        self.multi_worker.finished.connect(self.on_multi_finished)
        self.multi_worker.start()

    def on_open_all(self):
        codes_to_open = [m['cInvCode'] for m in self.cached_matches]
        self.set_gui_enabled(False)
        self.multi_worker = ProcessMultipleWorker(codes_to_open, True)
        self.multi_worker.progress.connect(self.update_progress)
        self.multi_worker.finished.connect(self.on_multi_finished)
        self.multi_worker.start()

    def on_multi_finished(self):
        self.set_gui_enabled(True)

    # ========================================================================
    # MENU BAR - UPDATER
    # ========================================================================
    def setup_menu_bar(self):
        """Thiết lập menu bar với tùy chọn kiểm tra cập nhật"""
        menubar = self.menuBar()
        
        # Menu Trợ giúp
        help_menu = menubar.addMenu("Trợ giúp")
        
        # Kiểm tra cập nhật
        check_update_action = help_menu.addAction("Kiểm tra cập nhật...")
        check_update_action.triggered.connect(self.on_check_update)
        
        # Thông tin phiên bản
        about_action = help_menu.addAction("Thông tin phiên bản")
        about_action.triggered.connect(self.on_show_about)

    def on_check_update(self):
        """Xử lý khi người dùng bấm Kiểm tra cập nhật"""
        if updater is None:
            QMessageBox.warning(self, "Lỗi", "Module cập nhật không khả dụng!")
            return
        
        # Kiểm tra cập nhật
        self.append_log("[UPDATER] Đang kiểm tra cập nhật...")
        result = updater.check_for_updates()
        
        # Kiểm tra lỗi kết nối
        if result.get('error'):
            error_msg = result['error']
            self.append_log(f"[UPDATER] Lỗi: {error_msg}")
            QMessageBox.warning(self, "Lỗi kết nối", 
                f"Không thể kiểm tra cập nhật:\n\n{error_msg}\n\n"
                f"Vui lòng kiểm tra:\n"
                f"1. Đường dẫn mạng có thể truy cập được\n"
                f"2. File cập nhật đã được đặt trên network share")
            return
        
        # Kiểm tra có cập nhật không
        if not result.get('has_update'):
            QMessageBox.information(self, "Cập nhật", 
                f"Bạn đang sử dụng phiên bản mới nhất ({updater.load_local_version()})")
            self.append_log("[UPDATER] Không có cập nhật mới")
            return
        
        # Có cập nhật mới
        update_info = result.get('update_info')
        version = update_info.get('version', '?')
        changelog = update_info.get('changelog', 'Không có thông tin')
        
        msg = f"Phiên bản mới: v{version}\n\nThay đổi:\n{changelog}\n\nBạn có muốn cập nhật không?"
        reply = QMessageBox.question(self, "Có cập nhật mới!", msg, 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.perform_update(update_info)

    def perform_update(self, update_info):
        """Thực hiện cập nhật"""
        try:
            self.append_log("[UPDATER] Đang tải cập nhật...")
            
            def progress_callback(percent, status=""):
                self.append_log(f"[UPDATER] {percent}% - {status}")
            
            success = updater.perform_update(update_info, progress_callback)
            
            if success:
                QMessageBox.information(self, "Thành công", 
                    "Cập nhật hoàn tất! Ứng dụng sẽ khởi động lại...")
                updater.restart_application()
            else:
                QMessageBox.warning(self, "Lỗi", "Cập nhật thất bại!")
                self.append_log("[UPDATER] Cập nhật thất bại")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật: {str(e)}")
            self.append_log(f"[UPDATER] Lỗi: {str(e)}")

    def on_show_about(self):
        """Hiển thị thông tin phiên bản"""
        version = updater.load_local_version() if updater else "Unknown"
        QMessageBox.about(self, "Thông tin phiên bản", 
            f"Mở mã liệu UI\nPhiên bản: {version}\n\n© 2026")

if __name__ == "__main__":
    # PySide6 hỗ trợ HiDPI mặc định, không cần cấu hình thêm

    app = QApplication(sys.argv)
    
    # Set application icon (CHO TASKBAR)
    if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, "favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"[INFO] App icon loaded from: {icon_path}")
    else:
        print(f"[WARNING] Icon not found at: {icon_path}")
    
    window = MaterialQueryUI()
    window.show()
    sys.exit(app.exec())
