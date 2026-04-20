import sys
import json
import socket
import threading
import requests  # HTTP client
import urllib.request
import urllib.error
import time
import csv
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QDate, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut, QTextDocument, QPainter, QTextOption, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, 
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLineEdit, QLabel, QFileDialog, QMessageBox,
    QStatusBar, QToolBar, QMenu, QMenuBar, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QDateEdit, QGridLayout, QHeaderView, QCheckBox,
    QScrollArea, QFrame, QTabWidget, QItemDelegate, QStyleOptionViewItem, QProgressDialog
)

# Import language_manager - hỗ trợ cả chạy từ thư mục gốc và thư mục src/
try:
    from src.language_manager import language_manager, UI_TEXT
except ImportError:
    from language_manager import language_manager, UI_TEXT

# Import EditDialog - tách thành module riêng
try:
    from src.EditDialog import EditDialog
except ImportError:
    from EditDialog import EditDialog

# Import FilterbyValue - module lọc dữ liệu theo cột
try:
    from src.FilterbyValue import FilterByValueDialog
except ImportError:
    from FilterbyValue import FilterByValueDialog

# Import Toolbar - tách thành module riêng
try:
    from src.toolbar import Toolbar
except ImportError:
    from toolbar import Toolbar

# Import Setting module - tách column settings
try:
    from src.setting import ColumnSettingsDialog, ColumnSettingsManager
except ImportError:
    from setting import ColumnSettingsDialog, ColumnSettingsManager

# Import SearchDialog - module tìm kiếm nâng cao
try:
    from src.client_find import SearchDialog
except ImportError:
    from client_find import SearchDialog

# Import ViewDialog - module xem chi tiết bản ghi
try:
    from src.view_dialog import ViewDialog
except ImportError:
    from view_dialog import ViewDialog

# Import Models - TableModel, NumericSortProxyModel, safe_int, HorizontalScrollTableView
try:
    from src.models import TableModel, NumericSortProxyModel, safe_int, HorizontalScrollTableView
except ImportError:
    from models import TableModel, NumericSortProxyModel, safe_int, HorizontalScrollTableView

# Import New_Sales module - Dialog cho Sales tạo project mới
try:
    from src.New_Sales import NewSalesDialog
except ImportError:
    from New_Sales import NewSalesDialog

# Import New_Sales_Wizard - Multi-step wizard cho Sales (UX improvement)
try:
    from src.New_Sales_Wizard import NewSalesWizard
except ImportError:
    try:
        from New_Sales_Wizard import NewSalesWizard
    except ImportError:
        NewSalesWizard = None  # Fallback to old dialog

# Import NoticeTab module - Tab hiển thị thông báo
try:
    from src.NoticeTab import NoticeTab
except ImportError:
    from NoticeTab import NoticeTab

# Import Session Manager - lấy thông tin user và role
try:
    from src.session_manager import session_manager
except ImportError:
    from session_manager import session_manager

# Import LoginDialog - cho chức năng đăng xuất
try:
    from src.login_dialog import LoginDialog
except ImportError:
    from login_dialog import LoginDialog

# Import UserManagement module - quản lý users cho Admin
try:
    from src.UserManagement import UserManagement
except ImportError:
    from UserManagement import UserManagement


# ==================== Data Loader Thread (Async) ====================

class DataLoader(QThread):
    """Thread để load dữ li liệu từ server mà không block UI"""
    data_loaded = Signal(list)
    error_occurred = Signal(str)
    progress_updated = Signal(int, str)  # progress percentage, message
    
    def __init__(self, db_client, parent=None):
        super().__init__(parent)
        self.db_client = db_client
        self._is_cancelled = False
        # Get UI texts
        try:
            from src.language_manager import language_manager
            self.texts = language_manager.get_all_ui_texts()
        except:
            self.texts = {
                'loading_data': 'Đang tải dữ liệu...',
                'processing_data': 'Đang xử lý dữ liệu...',
                'complete': 'Hoàn thành',
                'loading': 'Đang tải dữ liệu từ server...',
                'cancel': 'Hủy',
                'wait': 'Vui lòng chờ',
                'error': 'Lỗi',
                'load_error': 'Không thể tải dữ liệu từ server'
            }
    
    def run(self):
        """Load data trong background thread"""
        try:
            self.progress_updated.emit(10, self.texts.get('loading_data', 'Đang tải dữ liệu...'))
            
            # Load data từ server
            data = self.db_client.get_all_data()
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(90, self.texts.get('processing_data', 'Đang xử lý dữ liệu...'))
            
            if data is None:
                self.error_occurred.emit("Server không phản hồi")
                return
            
            self.progress_updated.emit(100, self.texts.get('complete', 'Hoàn thành'))
            self.data_loaded.emit(data if data else [])
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Hủy việc load data"""
        self._is_cancelled = True


class DataSearcher(QThread):
    """Thread để tìm kiếm dữ liệu mà không block UI"""
    search_finished = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, db_client, search_text, columns=None, parent=None):
        super().__init__(parent)
        self.db_client = db_client
        self.search_text = search_text
        self.columns = columns or []
    
    def run(self):
        """Tìm kiếm dữ liệu trong background thread"""
        try:
            results = self.db_client.search_data(self.search_text, self.columns)
            self.search_finished.emit(results if results else [])
        except Exception as e:
            self.error_occurred.emit(str(e))


# ==================== DBClient for Server Communication ====================

class DBClient(QObject):
    """Client để giao tiếp với server.py cho DB operations"""
    
    data_updated = Signal()  # Signal khi data được cập nhật từ server
    
    def __init__(self, host='localhost', port=8001, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 1  # seconds
    
    def connect(self):
        """Kết nối đến server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.reconnect_attempts = 0
            print(f"DBClient: Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"DBClient: Failed to connect to server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Ngắt kết nối từ server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
    
    def send_request(self, request, timeout=30.0):
        """
        Gửi request và nhận response qua HTTP API (server.py)
        Fallback to TCP socket if HTTP fails
        """
        # Thử HTTP trước
        try:
            url = f"http://{self.host}:{self.port}/api/socket"
            headers = {'Content-Type': 'application/json'}
            
            request_json = json.dumps(request, ensure_ascii=False)
            print(f"[DBClient] HTTP POST to {url}")
            
            # Sử dụng urllib thay vì requests (không cần dependencies)
            data = request_json.encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                print(f"[DBClient] HTTP Response: {len(response_data)} bytes")
                
                # Thử parse JSON
                try:
                    result = json.loads(response_data)
                    return result
                except json.JSONDecodeError:
                    # Response là string thuần (như "PONG", code, etc.)
                    return response_data
                    
        except urllib.error.URLError as e:
            print(f"[DBClient] HTTP failed: {e}, falling back to TCP socket")
        except Exception as e:
            print(f"[DBClient] HTTP error: {e}, falling back to TCP socket")
        
        # Fallback to TCP socket
        client_socket = None
        try:
            # Tạo socket mới cho mỗi request - tránh connection reuse issues
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(timeout)
            client_socket.connect((self.host, self.port))
            
            print(f"[DBClient] TCP Connected for request: {request.get('request', 'unknown')}")
            
            # Gửi request
            request_json = json.dumps(request, ensure_ascii=False)
            client_socket.sendall(request_json.encode('utf-8'))
            print(f"[DBClient] TCP Sent request: {len(request_json)} bytes")
            
            # Nhận response - nhận toàn bộ dữ liệu
            response_data = b''
            
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    # Server đóng connection
                    print(f"[DBClient] TCP Server closed connection, received {len(response_data)} bytes total")
                    break
                response_data += chunk
                
                # Thử parse JSON ngay lập tức
                try:
                    response_str = response_data.decode('utf-8')
                    response = json.loads(response_str)
                    print(f"[DBClient] TCP Parse success: {len(response_data)} bytes")
                    return response
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # Dữ liệu chưa đủ, tiếp tục nhận
                    continue
            
            # Parse những gì đã nhận được
            if response_data:
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    return response
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    print(f"[DBClient] TCP Parse error: {e}, data length: {len(response_data)}")
            
            return None
        
        except socket.timeout:
            print(f"[DBClient] TCP Timeout after {timeout}s")
            return None
        except ConnectionAbortedError as e:
            print(f"[DBClient] TCP Connection aborted: {e}")
            return None
        except Exception as e:
            print(f"[DBClient] TCP Request error: {e}")
            return None
        finally:
            # Luôn đóng socket sau request - đảm bảo connection lifecycle rõ ràng
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
    
    def get_all_data(self):
        """Lấy tất cả dữ liệu từ server"""
        request = {"request": "GET_DB_ALL"}
        response = self.send_request(request)
        return response if response else []
    
    def get_paged_data(self, page=1, limit=50, sort_by="Tracking ID", sort_order="desc"):
        """Lấy dữ liệu phân trang"""
        request = {
            "request": "GET_DB_PAGED",
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        response = self.send_request(request)
        return response if response else {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 1}
    
    def add_record(self, record):
        """Thêm bản ghi mới"""
        request = {
            "request": "ADD_DB_RECORD",
            "record": record
        }
        response = self.send_request(request)
        return response
    
    def update_record(self, tracking_id, data):
        """Cập nhật bản ghi"""
        request = {
            "request": "UPDATE_DB_RECORD",
            "tracking_id": tracking_id,
            "data": data
        }
        response = self.send_request(request)
        return response
    
    def delete_records(self, tracking_ids, user_role=None):
        """Xóa các bản ghi"""
        request = {
            "request": "DELETE_DB_RECORDS",
            "tracking_ids": tracking_ids,
            "user_role": user_role  # Gửi role để server kiểm tra quyền
        }
        response = self.send_request(request)
        return response
    
    def search_data(self, search_text, columns=None):
        """Tìm kiếm dữ liệu"""
        request = {
            "request": "SEARCH_DB_DATA",
            "search_text": search_text,
            "columns": columns or []
        }
        response = self.send_request(request)
        return response if response else []
    
    def filter_data(self, filters):
        """Lọc dữ liệu theo column filters"""
        request = {
            "request": "FILTER_DB_DATA",
            "filters": filters
        }
        response = self.send_request(request)
        return response if response else []
    
    def reindex_tracking_id(self):
        """Đánh lại Tracking ID"""
        request = {"request": "REINDEX_DB"}
        response = self.send_request(request)
        return response
    
    def ping(self):
        """Kiểm tra kết nối server"""
        request = {"request": "PING"}
        response = self.send_request(request, timeout=3.0)
        return response == "PONG" if response else False


class WrappedHeaderView(QHeaderView):
    """Custom header view với word wrap tự động"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._min_height = 40  # Chiều cao tối thiểu
        
        # Style cho header
        self.setStyleSheet(
            "QHeaderView::section {"
            "    background-color: #E8E8E8;"
            "    color: black;"
            "    font-weight: bold;"
            "    font-size: 12px;"
            "    padding-left: 4px;"
            "    padding-right: 4px;"
            "    padding-top: 4px;"
            "    padding-bottom: 4px;"
            "    border: 1px solid #A0A0A0;"
            "}"
        )
    
    def paintSection(self, painter, rect, logical_index):
        """Vẽ section với word wrap"""
        if not self.model() or logical_index < 0:
            return
        
        text = self.model().headerData(logical_index, self.orientation(), Qt.ItemDataRole.DisplayRole)
        if not text:
            return
        
        # Vẽ background
        painter.save()
        
        # Vẽ background đơn giản
        painter.fillRect(rect, Qt.GlobalColor.lightGray)
        
        # Vẽ border
        pen = painter.pen()
        pen.setColor(Qt.GlobalColor.gray)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        
        # Tính toán vùng vẽ text (trừ padding)
        text_rect = rect.adjusted(4, 4, -4, -4)
        
        # Vẽ text với word wrap và căn giữa
        painter.setFont(self.font())
        painter.setPen(Qt.GlobalColor.black)
        
        # Sử dụng QTextDocument để wrap text
        doc = QTextDocument()
        doc.setHtml(str(text))
        doc.setTextWidth(text_rect.width())
        doc.setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignCenter))
        
        painter.translate(text_rect.topLeft())
        doc.drawContents(painter)
        painter.restore()
    
    def sizeHint(self):
        """Tính toán size hint với chiều cao động"""
        hint = super().sizeHint()
        
        # Tính chiều cao dựa trên text dài nhất
        if self.model():
            max_height = self._min_height
            for i in range(self.count()):
                text = self.model().headerData(i, self.orientation(), Qt.ItemDataRole.DisplayRole)
                if text:
                    width = self.sectionSize(i)
                    height = self._calculateWrappedHeight(str(text), width)
                    max_height = max(max_height, height)
            
            hint.setHeight(max_height)
        
        return hint
    
    def _calculateWrappedHeight(self, text, width):
        """Tính chiều cao sau khi wrap"""
        doc = QTextDocument()
        doc.setHtml(str(text))
        doc.setTextWidth(width - 8)  # Trừ padding
        return int(doc.size().height()) + 8  # Thêm padding


# ==================== Color Delegates for Status and Urgency ====================

class StatusColorDelegate(QItemDelegate):
    """Delegate hiển thị status với màu sắc nhất quán NoticeTab"""
    
    # Status colors - nhất quán với NoticeTab
    STATUS_COLORS = {
        # Tiếng Việt
        "Chờ duyệt": QColor("#FFFFC8"),  # Vàng nhạt
        "Đang chờ": QColor("#FFFFC8"),
        "Chờ xử lý": QColor("#FFFFC8"),
        "Đã nhận": QColor("#C8FFC8"),   # Xanh lá nhạt
        "Đang làm": QColor("#C8E0FF"),  # Xanh dương nhạt
        "Hoàn thành": QColor("#90EE90"), # Xanh lá đậm
        "Quá hạn": QColor("#FFC8C8"),   # Đỏ nhạt
        # Tiếng Trung
        "待审批": QColor("#FFFFC8"),
        "等待": QColor("#FFFFC8"),
        "已接收": QColor("#C8FFC8"),
        "进行中": QColor("#C8E0FF"),
        "已完成": QColor("#90EE90"),
        "逾期": QColor("#FFC8C8"),
        # English
        "Pending": QColor("#FFFFC8"),
        "In Progress": QColor("#C8E0FF"),
        "Completed": QColor("#90EE90"),
        "Overdue": QColor("#FFC8C8"),
        "Accepted": QColor("#C8FFC8"),
    }
    
    def paint(self, painter, option, index):
        # Lấy giá trị status
        value = index.model().data(index, Qt.DisplayRole)
        
        # Set màu nền nếu có trong mapping
        if value and str(value) in self.STATUS_COLORS:
            option.backgroundBrush = QBrush(self.STATUS_COLORS[str(value)])
        
        super().paint(painter, option, index)


class UrgencyColorDelegate(QItemDelegate):
    """Delegate hiển thị urgency với màu sắc nhất quán NoticeTab"""
    
    # Urgency colors - nhất quán với NoticeTab
    URGENCY_COLORS = {
        # Tiếng Việt
        "Rất khẩn": QColor("#FFC8C8"),    # Đỏ nhạt
        "Khẩn": QColor("#FFFFC8"),         # Vàng nhạt
        "Bình thường": QColor("#C8FFC8"),  # Xanh lá nhạt
        # Tiếng Trung
        "紧急": QColor("#FFC8C8"),   
        "加急": QColor("#FFFFC8"),
        "一般": QColor("#C8FFC8"),
        # English & Database values
        "very_urgent": QColor("#FFC8C8"),
        "urgent": QColor("#FFFFC8"),
        "normal": QColor("#C8FFC8"),
        "Very Urgent": QColor("#FFC8C8"),
        "Urgent": QColor("#FFFFC8"),
        "Normal": QColor("#C8FFC8"),
    }
    
    def paint(self, painter, option, index):
        # Lấy giá trị urgency
        value = index.model().data(index, Qt.DisplayRole)
        
        # Set màu nền nếu có trong mapping
        if value and str(value) in self.URGENCY_COLORS:
            option.backgroundBrush = QBrush(self.URGENCY_COLORS[str(value)])
        
        super().paint(painter, option, index)


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self, server_ip: str = "localhost"):
        super().__init__()
        
        # Get UI texts for current language
        self.texts = language_manager.get_all_ui_texts()
        
        # Biến dữ liệu
        self.data = []
        self.filtered_data = []
        self.current_page = 1
        self.items_per_page = 50
        
        # DB Client for server communication
        self.db_client = DBClient(host=server_ip, port=8001, parent=self)
        
        # Loading state
        self.is_loading = False
        self.data_loader = None
        self.progress_dialog = None
        
        # Filter theo từng cột
        self.column_filters = {}
        
        # Cấu hình cột hiển thị - sử dụng ColumnSettingsManager
        self.column_settings_file = 'column_settings.json'
        self.settings_manager = ColumnSettingsManager(self.column_settings_file)
        
        # Load window state từ settings trước khi setGeometry
        window_state = self.settings_manager.load_window_state()
        if window_state:
            # Khôi phục vị trí và kích thước
            # Sử dụng move/resize để đảm bảo vị trí chính xác
            x = window_state.get('x', 100)
            y = window_state.get('y', 100)
            width = window_state.get('width', 1400)
            height = window_state.get('height', 800)
            self.move(x, y)
            self.resize(width, height)
            
            # Khôi phục trạng thái maximized (lưu để áp dụng sau khi show)
            self._restored_maximized = window_state.get('is_maximized', False)
        else:
            # Sử dụng default
            self.move(100, 100)
            self.resize(1400, 800)
            self._restored_maximized = False
        
        self.setWindowTitle(self.texts["window_title"])
        
        self.visible_columns = self.settings_manager.load_column_settings()
        
        # Đảm bảo cột "Tính cấp bách" luôn ẩn (chỉ dùng "Mức độ khẩn cấp")
        if self.visible_columns is None:
            self.visible_columns = {}
        # Ẩn cột "Tính cấp bách" mặc định (cả Tiếng Việt và Tiếng Trung)
        self.visible_columns["Tính cấp bách"] = False
        self.visible_columns["紧急程度"] = False
        
        # Cấu hình page size
        self.page_size = self.settings_manager.load_page_size()
        self.items_per_page = self.page_size
        
        # Load dữ liệu (DBClient sẽ tự tạo connection trong send_request)
        self.load_data()
        
        # Setup giao diện
        self.setup_ui()
        
        # Hiển thị dữ liệu
        self.display_data()
        
        # Áp dụng maximized state nếu cần
        # Điều này đảm bảo hoạt động cả khi chạy standalone và khi mở từ client.py
        if self._restored_maximized:
            print("[DEBUG] Applying maximized state in __init__")
            self.setWindowState(Qt.WindowMaximized)
    
    def load_data(self):
        """Đọc dữ liệu từ server (async với QThread) - Không block UI"""
        # Nếu đang load rồi thì bỏ qua
        if self.is_loading:
            print("Đang tải dữ liệu, bỏ qua request...")
            return
        
        self.is_loading = True
        
        # Tạo và hiển thị progress dialog
        self.progress_dialog = QProgressDialog(
            self.texts.get('loading', 'Đang tải dữ liệu từ server...'),
            self.texts.get('cancel', 'Hủy'),
            0, 100, self
        )
        self.progress_dialog.setWindowTitle(self.texts.get('wait', 'Vui lòng chờ'))
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.canceled.connect(self.cancel_loading)
        self.progress_dialog.show()
        
        # Tạo data loader thread
        self.data_loader = DataLoader(self.db_client)
        self.data_loader.progress_updated.connect(self.update_loading_progress)
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.error_occurred.connect(self.on_load_error)
        self.data_loader.finished.connect(self.on_loader_finished)
        self.data_loader.start()
    
    def update_loading_progress(self, value, message):
        """Cập nhật progress dialog"""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(message)
    
    def on_data_loaded(self, data):
        """Xử lý khi data được load xong"""
        self.data = data if data else []
        self.filtered_data = self.data.copy()
        print(self.texts["msg_load_success"].format(len(self.data)))
    
    def on_load_error(self, error_message):
        """Xử lý khi load data lỗi"""
        print(f"Lỗi khi tải dữ liệu: {error_message}")
        QMessageBox.critical(self, self.texts.get('error', 'Lỗi'), 
            f"{self.texts.get('load_error', 'Không thể tải dữ liệu từ server')}: {error_message}")
        self.data = []
        self.filtered_data = []
    
    def on_loader_finished(self):
        """Xử lý khi loader thread kết thúc"""
        self.is_loading = False
        
        # Đóng progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Hiển thị dữ liệu
        self.display_data()
    
    def cancel_loading(self):
        """Hủy việc load data"""
        if self.data_loader and self.data_loader.isRunning():
            self.data_loader.cancel()
            self.data_loader.wait(1000)
        self.is_loading = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
    
    def load_column_settings(self):
        """Đọc cấu hình cột từ file (sử dụng manager)"""
        result = self.settings_manager.load_column_settings()
        return result if result else None
    
    def save_column_settings(self, visible_columns):
        """Lưu cấu hình cột vào file (giữ lại page_size)"""
        self.settings_manager.save_column_settings(visible_columns, self.items_per_page)
    
    def load_page_size(self):
        """Đọc page_size từ file cấu hình (sử dụng manager)"""
        return self.settings_manager.load_page_size()
    
    def load_column_widths(self):
        """Đọc chiều rộng cột từ file cấu hình (sử dụng manager)"""
        return self.settings_manager.load_column_widths()
    
    def save_column_widths(self, column_widths):
        """Lưu chiều rộng cột vào file cấu hình (sử dụng manager)"""
        self.settings_manager.save_column_widths(column_widths)
    
    def on_column_resized(self, logical_index, old_size, new_size):
        """Xử lý khi user thay đổi chiều rộng cột - lưu theo tên cột"""
        # Chỉ lưu khi có model với headers
        if not hasattr(self, 'model') or not hasattr(self.model, '_headers'):
            return
        
        # Lưu tất cả chiều rộng hiện tại theo tên cột
        column_widths_by_name = {}
        for col, header_name in enumerate(self.model._headers):
            if col < self.model.columnCount():
                column_widths_by_name[header_name] = self.table_view.columnWidth(col)
        
        self.save_column_widths(column_widths_by_name)
    
    def save_current_column_widths(self):
        """Lưu tất cả chiều rộng cột hiện tại (theo tên cột)"""
        if not hasattr(self, 'model') or not hasattr(self.model, '_headers'):
            return
        
        column_widths_by_name = {}
        for col, header_name in enumerate(self.model._headers):
            if col < self.model.columnCount():
                column_widths_by_name[header_name] = self.table_view.columnWidth(col)
        
        self.save_column_widths(column_widths_by_name)
    
    def restore_column_widths(self):
        """Khôi phục chiều rộng cột từ settings (theo tên cột)"""
        saved_widths = self.load_column_widths()  # { "column_name": width }
        
        # Kiểm tra nếu là format cũ (theo index) thì bỏ qua
        if not saved_widths or all(k.isdigit() for k in saved_widths.keys()):
            return
        
        # Restore theo tên cột - map từ display_headers sang width
        if not hasattr(self, 'model') or not hasattr(self.model, '_headers'):
            return
        
        for col, header_name in enumerate(self.model._headers):
            if header_name in saved_widths:
                self.table_view.setColumnWidth(col, saved_widths[header_name])
    
    def save_page_size(self):
        """Lưu page_size vào file cấu hình (sử dụng manager)"""
        self.settings_manager.save_page_size(self.items_per_page)
    
    def open_column_settings(self):
        """Mở dialog cài đặt cột với khả năng sắp xếp"""
        column_order = self.settings_manager.load_column_order()
        dialog = ColumnSettingsDialog(self, self.visible_columns, column_order)
        if dialog.exec() == QDialog.Accepted:
            self.visible_columns, column_order = dialog.get_column_settings()
            self.settings_manager.save_column_settings(
                self.visible_columns, 
                self.items_per_page,
                column_order
            )
            self.display_data()
    
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Menu bar
        self.create_menu_bar()
        
        # Toolbar - sử dụng module riêng (chuyển thành context menu)
        self.toolbar = Toolbar(self, self.texts)
        
        # ========== TAB WIDGET ==========
        self.tab_widget = QTabWidget()
        
        # Tab 1: Project Table
        project_tab = QWidget()
        project_layout = QVBoxLayout(project_tab)
        
        # Table - tạo table_view TRƯỚC KHI sử dụng
        self.table_view = HorizontalScrollTableView()
        self.table_view.setSortingEnabled(False)  # Tắt sorting cho table view
        self.table_view.doubleClicked.connect(self.view_record)
        
        # ===== UI/UX: Row Hover Effects, Selection, Alternating Colors =====
        # Style nhất quán với NoticeTab
        self.table_view.setStyleSheet("""
            QTableView {
                gridline-color: #ddd;
                alternate-background-color: #f9f9f9;
                background-color: white;
            }
            QTableView::item:hover {
                background-color: #E3F2FD;
            }
            QTableView::item:selected {
                background-color: #1976D2;
                color: white;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 5px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        self.table_view.setAlternatingRowColors(True)
        
        # Tạo delegates cho Status và Urgency columns
        self.status_delegate = StatusColorDelegate(self.table_view)
        self.urgency_delegate = UrgencyColorDelegate(self.table_view)
        
        # Hiển thị số dòng (row numbers) ở phía bên trái - giống Excel
        self.table_view.verticalHeader().show()
        # Thiết lập độ rộng cho row header
        self.table_view.verticalHeader().setDefaultSectionSize(25)
        self.table_view.verticalHeader().setMinimumWidth(50)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        # Căn giữa số dòng (giống Excel)
        self.table_view.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        # Style cho row header
        self.table_view.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                font-weight: bold;
            }
        """)
        
        # Sử dụng WrappedHeaderView với word wrap tự động cho column header
        wrapped_header = WrappedHeaderView(Qt.Orientation.Horizontal, self.table_view)
        self.table_view.setHorizontalHeader(wrapped_header)
        
        # Căn lề trái cho header của bảng
        wrapped_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Lưu chiều rộng cột khi thay đổi
        header = self.table_view.horizontalHeader()
        header.sectionResized.connect(self.on_column_resized)
        
        # Thiết lập context menu policy cho table_view
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.toolbar.show_context_menu)
        
        # Tạo context menu sau khi table_view đã tồn tại
        self.toolbar.create_context_menu(self.table_view)
        self.toolbar.table_view = self.table_view
        
        # Tạo ABC header (A, B, C...) phía trên table
        # self.abc_header_widget = self.create_abc_header()
        # project_layout.addWidget(self.abc_header_widget)

        project_layout.addWidget(self.table_view)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel(self.texts["search_label"])
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.texts["search_placeholder"])
        self.search_input.textChanged.connect(self.search_data)
        
        search_btn = QPushButton(self.texts["search_btn"])
        search_btn.clicked.connect(self.search_data)
        
        clear_btn = QPushButton(self.texts["refresh_btn"])
        clear_btn.clicked.connect(self.refresh_data)
        
        # Nút Tìm kiếm nâng cao (mở SearchDialog)
        advanced_search_btn = QPushButton(self.texts.get("search_advanced_btn", "Tìm kiếm nâng cao"))
        advanced_search_btn.clicked.connect(self.open_advanced_search)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        search_layout.addWidget(advanced_search_btn)
        project_layout.addLayout(search_layout)
        
        # Pagination
        self.create_pagination(project_layout)
        
        # Thêm Tab Project vào TabWidget
        self.tab_widget.addTab(project_tab, "📋 Dự án / 项目")
        
        # Tab 2: Notice Tab (hiển thị cho tất cả các role để xem thông báo)
        self.notice_tab = None
        
        
        # Hiển thị tab cho tất cả các role (sales, engineer, admin, IT, Pur)
        if session_manager.is_sales() or session_manager.is_engineer() or session_manager.is_admin() or session_manager.is_it() or session_manager.is_pur():
            # print("[NoticeTab] Tạo NoticeTab cho user")
            self.notice_tab = NoticeTab(self, server_ip=self.db_client.host)
            self.notice_tab.data_updated.connect(self.on_notice_updated)
            self.tab_widget.addTab(self.notice_tab, "🔔 Thông báo")
            
            # Update badge after a delay to ensure data is loaded
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, self.update_notice_badge)
        # else:
        #     print(f"[NoticeTab] User role '{user_role}' không được hiển thị tab Thông báo")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Thiết lập phím tắt F5 cho table_view (đảm bảo hoạt động khi table có focus)
        shortcut_f5 = QShortcut(QKeySequence("F5"), self.table_view)
        shortcut_f5.activated.connect(self.refresh_data)
        
        # Thiết lập phím tắt Ctrl+F cho tìm kiếm nâng cao
        shortcut_ctrl_f = QShortcut(QKeySequence("Ctrl+F"), self.table_view)
        shortcut_ctrl_f.activated.connect(self.open_advanced_search)
        
        # Thiết lập filter headers
        self.setup_filter_headers()
    
    def on_notice_updated(self):
        """Xử lý khi có cập nhật từ Notice Tab"""
        # Reload data để cập nhật table
        self.load_data()
        self.display_data()
        # Cập nhật badge
        self.update_notice_badge()
    
    def update_notice_badge(self):
        """Cập nhật số lượng trên tab Thông báo"""
        if not self.notice_tab:
            return
        
        # Lấy số lượng pending
        count = self.notice_tab.get_pending_count_sync()
        
        # Tìm index của notice tab
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.notice_tab:
                if count > 0:
                    self.tab_widget.setTabText(i, f"🔔 Thông báo ({count})")
                else:
                    self.tab_widget.setTabText(i, "🔔 Thông báo")
                break
    
    # def create_abc_header(self):
    #     """Tạo header row hiển thị A, B, C... (giống Excel)"""
    #     abc_header = QWidget()
    #     abc_header.setFixedHeight(25)
        
    #     # Lấy display_headers hiện tại - BAO GỒM METADATA
    #     all_headers = language_manager.get_all_headers()
        
    #     # Đảm bảo cột "Tính cấp bách" luôn ẩn (chỉ dùng "Mức độ khẩn cấp")
    #     visible_columns = dict(self.visible_columns) if self.visible_columns else {}
    #     visible_columns["Tính cấp bách"] = False
    #     visible_columns["紧急程度"] = False
        
    #     display_headers = [h for h in all_headers if visible_columns.get(h, True)]
        
    #     # Tạo layout với spacer đầu tiên cho row header
    #     layout = QHBoxLayout(abc_header)
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(0)
        
    #     # Spacer cho row header (bên trái)
    #     spacer = QWidget()
    #     spacer.setFixedWidth(self.table_view.verticalHeader().width())
    #     layout.addWidget(spacer)
        
    #     # Thêm labels cho A, B, C...
    #     for i in range(len(display_headers)):
    #         label = QLabel(TableModel.number_to_letters(i))
    #         label.setAlignment(Qt.AlignCenter)
    #         label.setStyleSheet("""
    #             background-color: #f0f0f0;
    #             font-weight: bold;
    #             font-size: 11px;
    #             border: 1px solid #ccc;
    #         """)
    #         layout.addWidget(label)
        
    #     return abc_header
    
    # def refresh_abc_header(self):
    #     """Cập nhật ABC header (A, B, C...) khi columns thay đổi"""
    #     if hasattr(self, 'abc_header_widget') and self.abc_header_widget:
    #         try:
    #             self.abc_header_widget.hide()
    #             self.layout().removeWidget(self.abc_header_widget)
    #             self.abc_header_widget.deleteLater()
    #             self.abc_header_widget = None
    #         except Exception as e:
    #             print(f"Error removing ABC header: {e}")
    
    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # Menu File
        file_menu = menubar.addMenu(self.texts["menu_file"])
        
        # Đã loại bỏ Save - dữ liệu tự động lưu khi thêm/sửa/xóa
        
        file_menu.addSeparator()
        
        export_excel_action = QAction(self.texts["action_export_excel"], self)
        export_excel_action.triggered.connect(self.export_excel)
        file_menu.addAction(export_excel_action)
        
        export_csv_action = QAction(self.texts["action_export_csv"], self)
        export_csv_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_csv_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.texts["action_exit"], self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        file_menu.addSeparator()
        
        # Thêm action Đăng xuất
        logout_action = QAction("Đăng xuất / 退出", self)
        logout_action.triggered.connect(self.on_logout)
        file_menu.addAction(logout_action)
        
        # Menu Edit
        edit_menu = menubar.addMenu(self.texts["menu_edit"])
        
        add_action = QAction(self.texts["action_add"], self)
        add_action.setShortcut(self.texts["action_add_shortcut"])
        add_action.triggered.connect(self.add_record)
        edit_menu.addAction(add_action)
        
        edit_action = QAction(self.texts["action_edit"], self)
        edit_action.setShortcut(self.texts["action_edit_shortcut"])
        edit_action.triggered.connect(self.edit_record)
        edit_menu.addAction(edit_action)
        
        delete_action = QAction(self.texts["action_delete"], self)
        delete_action.setShortcut(self.texts["action_delete_shortcut"])
        delete_action.triggered.connect(self.delete_records)
        # Chỉ hiển thị menu Delete cho Admin
        if session_manager.can_delete_project():
            edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        refresh_action = QAction(self.texts["action_refresh"], self)
        refresh_action.triggered.connect(self.refresh_data)
        edit_menu.addAction(refresh_action)
        
        # Menu Column Settings
        columns_menu = menubar.addMenu(self.texts["menu_columns"])
        
        column_settings_action = QAction(self.texts["action_column_settings"], self)
        column_settings_action.triggered.connect(self.open_column_settings)
        columns_menu.addAction(column_settings_action)
        
        # Menu Filter
        filter_menu = menubar.addMenu(self.texts.get("menu_filter", "Lọc dữ liệu"))
        
        filter_help_action = QAction(self.texts.get("action_filter_help", "Hướng dẫn lọc..."), self)
        filter_help_action.triggered.connect(self.show_filter_dialog)
        filter_menu.addAction(filter_help_action)
        
        clear_filter_action = QAction(self.texts.get("action_clear_filter", "Xóa tất cả bộ lọc"), self)
        clear_filter_action.triggered.connect(self.clear_all_filters)
        filter_menu.addAction(clear_filter_action)
        
        # Menu Admin (chỉ cho admin và IT)
        # # DEBUG: Log role information
        # print(f"[DEBUG MENU] session_manager.is_admin() = {session_manager.is_admin()}")
        # print(f"[DEBUG MENU] session_manager.get_user_role() = {session_manager.get_user_role()}")
        # print(f"[DEBUG MENU] session_manager.get_user_role() == 'IT' = {session_manager.get_user_role() == 'IT'}")
        
        if session_manager.is_admin() or session_manager.get_user_role() == 'IT':
            admin_menu = menubar.addMenu("👤 Quản trị / 管理")
            
            user_management_action = QAction("Quản lý người dùng / 用户管理", self)
            user_management_action.triggered.connect(self.open_user_management)
            admin_menu.addAction(user_management_action)
        
        # Menu Help
        help_menu = menubar.addMenu(self.texts["menu_help"])
        
        about_action = QAction(self.texts["action_about"], self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_pagination(self, layout):
        """Tạo phân trang"""
        pagination_layout = QHBoxLayout()
        
        # Label trang
        self.page_label = QLabel(self.texts["page_label"])
        pagination_layout.addWidget(self.page_label)
        
        # Spinbox trang hiện tại
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self.change_page)
        pagination_layout.addWidget(self.page_spinbox)
        
        # Label tổng số trang
        self.total_pages_label = QLabel("/ 1")
        pagination_layout.addWidget(self.total_pages_label)
        
        # Nút Previous
        prev_btn = QPushButton("<")
        prev_btn.clicked.connect(self.previous_page)
        pagination_layout.addWidget(prev_btn)
        
        # Nút Next
        next_btn = QPushButton(">")
        next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(next_btn)
        
        # Label tổng số bản ghi
        self.total_records_label = QLabel(self.texts["total_records"].format(0))
        pagination_layout.addWidget(self.total_records_label)
        
        # Thêm separator
        pagination_layout.addSpacing(20)
        
        # Label số dòng mỗi trang
        page_size_label = QLabel(self.texts["page_size_label"])
        pagination_layout.addWidget(page_size_label)
        
        # Spinbox chọn số dòng mỗi trang
        self.page_size_spinbox = QSpinBox()
        self.page_size_spinbox.setMinimum(10)
        self.page_size_spinbox.setMaximum(99999)
        self.page_size_spinbox.setValue(self.items_per_page)
        self.page_size_spinbox.valueChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_spinbox)
        
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
    
    def display_data(self):
        """Hiển thị dữ liệu lên bảng"""
        # Headers cho hiển thị theo ngôn ngữ - LẤY TẤT CẢ BAO GỒM METADATA
        all_headers = language_manager.get_all_headers()
        current_lang = language_manager.get_language()
        
        # Đảm bảo cột "Tính cấp bách" luôn ẩn (chỉ dùng "Mức độ khẩn cấp")
        visible_columns = dict(self.visible_columns) if self.visible_columns else {}
        visible_columns["Tính cấp bách"] = False
        visible_columns["紧急程度"] = False
        
        # Lấy thứ tự cột từ settings nếu có
        saved_column_order = self.settings_manager.load_column_order()
        
        # Kiểm tra xem column_order có hợp lệ với ngôn ngữ hiện tại không
        # Nếu column_order chứa headers của ngôn ngữ khác, bỏ qua và dùng mặc định
        use_saved_order = False
        if saved_column_order:
            # Đếm số headers trong column_order mà khớp với headers hiện tại
            matching_headers = [h for h in saved_column_order if h in all_headers]
            # Nếu > 50% headers khớp, sử dụng saved order
            if len(matching_headers) > len(saved_column_order) * 0.5:
                use_saved_order = True
            else:
                print(f"[WARNING] Column order ({len(saved_column_order)} items) doesn't match current language '{current_lang}'. Using default order.")
        
        if use_saved_order and saved_column_order:
            # Sắp xếp headers theo thứ tự đã lưu
            order_dict = {h: i for i, h in enumerate(saved_column_order)}
            display_headers = sorted(all_headers, key=lambda h: order_dict.get(h, len(order_dict)))
            # Chỉ hiển thị các cột visible
            display_headers = [h for h in display_headers if visible_columns.get(h, True)]
        else:
            # Sử dụng thứ tự mặc định và lọc theo visible
            display_headers = [h for h in all_headers if visible_columns.get(h, True)]
        
        # Mapping từ display header sang actual key trong DB.json - BAO GỒM METADATA
        key_mapping = language_manager.get_all_keys()
        
        # Sắp xếp filtered_data theo Tracking ID giảm dần (số) TRƯỚC KHI phân trang
        sorted_data = sorted(self.filtered_data, key=lambda x: safe_int(x.get("Tracking ID")), reverse=True)
        
        # Tính toán phân trang
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(sorted_data))
        page_data = sorted_data[start_idx:end_idx]
        
        # Lưu page_data để dùng trong get_selected_rows()
        self.page_data = page_data
        
        # Create model với key_mapping
        self.model = TableModel(page_data, display_headers, key_mapping)
        
        # Create custom proxy model với numeric sort cho STT
        self.proxy_model = NumericSortProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.set_key_mapping(key_mapping)
        
        # Set model to table
        self.table_view.setModel(self.proxy_model)
        
        # ===== UI/UX: Apply Color Delegates for Status and Urgency =====
        # Tìm cột Status và Urgency để áp dụng delegates
        status_columns = ["Trạng thái", "状态", "Status"]
        urgency_columns = ["Mức độ khẩn cấp", "紧急程度", "Urgency Level"]
        
        for col, header in enumerate(display_headers):
            if header in status_columns:
                self.table_view.setItemDelegateForColumn(col, self.status_delegate)
            elif header in urgency_columns:
                self.table_view.setItemDelegateForColumn(col, self.urgency_delegate)
        
        # Resize header để tính toán chiều cao đúng với wrapped text
        self.table_view.horizontalHeader().resizeSections(QHeaderView.ResizeMode.Interactive)
        
        # Hiển thị tất cả các cột trong model (model chỉ có các cột visible)
        for col in range(len(display_headers)):
            self.table_view.showColumn(col)
        
        # Hiển thị tất cả các cột trong model (model chỉ có các cột visible)
        for col in range(len(display_headers)):
            self.table_view.showColumn(col)
        
        # Áp dụng chiều rộng cột đã lưu (dùng QTimer để đảm bảo UI đã vẽ xong)
        QTimer.singleShot(100, self.restore_column_widths)
        
        # # Cập nhật ABC header (A, B, C...) khi columns thay đổi
        # QTimer.singleShot(110, self.refresh_abc_header)
        
        # Update pagination
        total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
        self.page_spinbox.setMaximum(total_pages)
        self.page_spinbox.setValue(self.current_page)
        self.total_pages_label.setText(f"/ {total_pages}")
        self.total_records_label.setText(self.texts["total_records"].format(len(self.filtered_data)))
        
        # Update status
        self.status_bar.showMessage(self.texts["page_info"].format(self.current_page, total_pages, len(page_data)))
    
    def search_data(self):
        """Tìm kiếm dữ liệu"""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            self.filtered_data = self.data.copy()
        else:
            self.filtered_data = []
            for item in self.data:
                # Tìm kiếm trong tất cả các trường
                found = False
                for key, value in item.items():
                    if value and search_text in str(value).lower():
                        found = True
                        break
                if found:
                    self.filtered_data.append(item)
        
        self.current_page = 1
        self.display_data()
    
    def open_advanced_search(self):
        """Mở dialog tìm kiếm nâng cao từ client_find"""
        # Lấy headers và key_mapping - BAO GỒM METADATA
        key_mapping = language_manager.get_all_keys()
        
        # Mở SearchDialog với search_type="DB_DATA" để tìm trong DB.json
        dialog = SearchDialog(
            parent=self,
            server_ip='localhost',
            history_data=self.data,
            headers=key_mapping,
            search_type="DB_DATA"
        )
        
        if dialog.exec() == QDialog.Accepted:
            results = dialog.get_search_results()
            if results:
                self.filtered_data = results
                self.current_page = 1
                self.display_data()
                self.status_bar.showMessage(
                    f"Đã tìm thấy: {len(results)} kết quả", 3000
                )
    
    def clear_search(self):
        """Xóa tìm kiếm và hiển thị tất cả dữ liệu (giữ nguyên cho tương thích)"""
        self.search_input.clear()
        self.filtered_data = self.data.copy()
        self.current_page = 1
        self.display_data()
    
    def refresh_data(self):
        """Làm mới dữ liệu: Tải lại từ server và hiển thị"""
        # Kiểm tra nếu đang load dữ liệu
        if self.is_loading:
            self.status_bar.showMessage(self.texts.get('msg_loading', 'Đang tải dữ liệu, vui lòng chờ...'), 3000)
            return
        
        self.load_data()  # Tải lại từ server - now async
        self.search_input.clear()  # Xóa search input
        self.column_filters = {}  # Xóa tất cả filters
        self.current_page = 1  # Reset về trang 1
        # display_data sẽ được gọi trong on_loader_finished khi load xong
    
    def change_page(self, page):
        """Thay đổi trang"""
        total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
        if 1 <= page <= total_pages:
            self.current_page = page
            self.display_data()
    
    def change_page_size(self, size):
        """Thay đổi số dòng mỗi trang"""
        self.items_per_page = size
        self.current_page = 1  # Quay về trang 1
        self.save_page_size()  # Lưu cấu hình
        self.display_data()  # Hiển thị lại dữ liệu
    
    def previous_page(self):
        """Trang trước"""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_data()
    
    def next_page(self):
        """Trang sau"""
        total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.display_data()
    
    def export_excel(self):
        """Xuất dữ liệu ra Excel"""
        try:
            # Sử dụng pandas nếu có, nếu không thì xuất CSV
            try:
                import pandas as pd
                
                # Chuyển đổi dữ liệu thành DataFrame
                df = pd.DataFrame(self.filtered_data)
                
                # Lưu file
                file_path, _ = QFileDialog.getSaveFileName(
                    self, self.texts["action_export_excel"], "", "Excel Files (*.xlsx);;All Files (*)"
                )
                
                if file_path:
                    df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Thành công", self.texts["msg_save_success"])
            except ImportError:
                # Nếu không có pandas, xuất CSV thay thế
                self.export_csv()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", self.texts["error_export_excel"].format(str(e)))
    
    def export_csv(self):
        """Xuất dữ liệu ra CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, self.texts["action_export_csv"], "", "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                # Headers cho hiển thị theo ngôn ngữ - BAO GỒM METADATA
                display_headers = language_manager.get_all_headers()
                
                # Mapping từ display header sang actual key trong DB.json - BAO GỒM METADATA
                key_mapping = language_manager.get_all_keys()
                
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(display_headers)
                    
                    for item in self.filtered_data:
                        row = []
                        for display_header in display_headers:
                            actual_key = key_mapping.get(display_header, display_header)
                            row.append(item.get(actual_key, ""))
                        writer.writerow(row)
                
                QMessageBox.information(self, "Thành công", self.texts["msg_save_success"])
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", self.texts["error_export_csv"].format(str(e)))
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        QMessageBox.about(self, self.texts["about_title"], self.texts["about_text"])
    
    # ========== CRUD METHODS ==========
    
    def get_selected_rows(self):
        """Lấy danh sách các dòng được chọn"""
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            return []
        
        # Lấy các row index từ proxy model (map về source model)
        rows = set()
        for index in selected_indexes:
            rows.add(self.proxy_model.mapToSource(index).row())
        
        # Lấy dữ liệu trực tiếp từ page_data (đã được sắp xếp và phân trang đúng)
        selected_records = []
        for row in sorted(rows):
            if row < len(self.page_data):
                selected_records.append({
                    'data': self.page_data[row]
                })
        
        return selected_records
    
    def edit_record(self):
        """Chỉnh sửa bản ghi được chọn"""
        selected = self.get_selected_rows()
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", self.texts["msg_select_record"])
            return
        
        if len(selected) > 1:
            QMessageBox.warning(self, "Cảnh báo", self.texts["msg_select_one_record"])
            return
        
        record = selected[0]['data']
        tracking_id = record.get("Tracking ID")
        
        dialog = EditDialog(self, record, is_new=False)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            
            # Gửi cập nhật lên server
            response = self.db_client.update_record(tracking_id, new_data)
            if response and response.get("success"):
                # Reload data từ server
                self.load_data()
                self.display_data()
                QMessageBox.information(self, "Thành công", self.texts["msg_edit_success"])
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể cập nhật trên server")
    
    def update_record(self, old_record, new_data):
        """Cập nhật bản ghi (dùng bởi ViewDialog)"""
        tracking_id = old_record.get("Tracking ID")
        
        # Gửi cập nhật lên server
        response = self.db_client.update_record(tracking_id, new_data)
        if response and response.get("success"):
            # Reload data từ server
            self.load_data()
            self.display_data()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể cập nhật trên server")
    
    def view_record(self):
        """Xem chi tiết bản ghi (double-click)"""
        selected = self.get_selected_rows()
        if not selected:
            return
        
        if len(selected) > 1:
            QMessageBox.warning(self, "Cảnh báo", self.texts["msg_select_one_record"])
            return
        
        record = selected[0]['data']
        
        dialog = ViewDialog(self, record)
        dialog.exec()
    
    def add_record(self):
        """Thêm bản ghi mới - Hiển thị dialog phù hợp với role"""
        # Kiểm tra role của user
        if session_manager.is_sales():
            # Sales: Sử dụng NewSalesWizard (UX improvement - multi-step)
            if NewSalesWizard is not None:
                print("[LOG] User is sales, opening NewSalesWizard (Multi-step)")
                dialog = NewSalesWizard(self, self.db_client.host)
                if dialog.exec() == QDialog.Accepted:
                    # Wizard đã tự lưu vào DB
                    # reload data để cập nhật bảng
                    self.load_data()
                    # Hiển thị trang cuối cùng
                    total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
                    self.current_page = total_pages
                    self.display_data()
            else:
                # Fallback to old dialog
                print("[LOG] User is sales, opening NewSalesDialog")
                dialog = NewSalesDialog(self, self.db_client.host)
                if dialog.exec() == QDialog.Accepted:
                    # NewSalesDialog đã tự lưu vào DB qua ADD_SALES_RECORD
                    # Và đã hiển thị thông báo thành công trong NewSalesDialog
                    # Chỉ cần reload data để cập nhật bảng
                    self.load_data()
                    # Hiển thị trang cuối cùng
                    total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
                    self.current_page = total_pages
                    self.display_data()
        else:
            # Non-sales users: Sử dụng EditDialog
            print("[LOG] User is NOT sales, opening EditDialog")
            dialog = EditDialog(self, None, is_new=True)
            if dialog.exec() == QDialog.Accepted:
                new_data = dialog.get_data()
                
                # Gửi thêm mới lên server
                response = self.db_client.add_record(new_data)
                if response and response.get("success"):
                    # Reload data từ server
                    self.load_data()
                    # Hiển thị trang cuối cùng
                    total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
                    self.current_page = total_pages
                    self.display_data()
                    QMessageBox.information(self, "Thành công", self.texts["msg_add_success"])
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể thêm bản ghi trên server")
    
    def open_user_management(self):
        """Mở cửa sổ quản lý người dùng"""
        # Log khi nhấn vào Quản lý người dùng
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = session_manager.get_current_user() or "Unknown"
        user_role = session_manager.get_user_role() or "Unknown"
        user_ip = getattr(self.db_client, 'host', 'localhost')
        
        print(f"[USER_MGMT_LOG] [{timestamp}] User '{username}' (Role: {user_role}) accessed User Management from IP: {user_ip}")
        
        # Tạo dialog để chứa UserManagement widget
        from PySide6.QtWidgets import QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle("👥 Quản lý người dùng / 用户管理")
        dialog.setMinimumSize(1200, 700)
        
        # Tạo UserManagement widget và thêm vào dialog
        user_mgmt = UserManagement(self, server_ip=self.db_client.host)
        
        # Layout cho dialog
        layout = QVBoxLayout(dialog)
        layout.addWidget(user_mgmt)
        dialog.setLayout(layout)
        
        # Hiển thị dialog dạng modal
        dialog.exec()
    
    def delete_records(self):
        """Xóa các bản ghi được chọn - Chỉ Admin mới có quyền"""
        # DEBUG: Log chi tiết về session và user_role
        print(f"[DEBUG DELETE] Bắt đầu delete_records()")
        print(f"[DEBUG DELETE] can_delete_project() = {session_manager.can_delete_project()}")
        
        # Kiểm tra quyền admin
        if not session_manager.can_delete_project():
            print(f"[DEBUG DELETE] User không có quyền xóa")
            QMessageBox.warning(
                self, 
                "Cảnh báo / 警告", 
                "Bạn không có quyền xóa dự án.\nChỉ Admin mới được phép thực hiện thao tác này.\n\n您没有权限删除项目。只有管理员才能执行此操作。"
            )
            return
        
        selected = self.get_selected_rows()
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", self.texts["msg_select_delete"])
            return
        
        # Hiển thị xác nhận
        count = len(selected)
        reply = QMessageBox.question(
            self, 
            self.texts["dialog_confirm_delete"], 
            self.texts["dialog_confirm_delete_msg"].format(count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            tracking_ids = [sel['data'].get("Tracking ID") for sel in selected]
            
            # DEBUG: Log chi tiết về user_role và tracking_ids
            user_role = session_manager.get_user_role()
            print(f"[DEBUG DELETE] user_role = {user_role}")
            print(f"[DEBUG DELETE] tracking_ids = {tracking_ids}")
            
            # Gửi xóa lên server với user_role
            response = self.db_client.delete_records(tracking_ids, user_role)
            
            # DEBUG: Log response từ server
            print(f"[DEBUG DELETE] response = {response}")
            
            if response and response.get("success"):
                # Reload data từ server
                self.load_data()
                # Điều chỉnh trang nếu cần
                total_pages = (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page
                if self.current_page > total_pages:
                    self.current_page = max(1, total_pages)
                self.display_data()
                QMessageBox.information(self, "Thành công", self.texts["msg_delete_success"].format(count))
            else:
                error_msg = response.get("error", "Không thể xóa trên server") if response else "Không thể xóa trên server"
                print(f"[DEBUG DELETE] Lỗi: {error_msg}")
                QMessageBox.critical(self, "Lỗi", error_msg)
    
    def update_window_title(self):
        """Cập nhật tiêu đề cửa sổ"""
        self.setWindowTitle(self.texts["window_title"])
    
    def has_unsaved_changes(self):
        """Kiểm tra thay đổi"""
        return True
    
    def closeEvent(self, event):
        """Xử lý sự kiện đóng cửa sổ - lưu chiều rộng cột và window state trước khi đóng"""
        # Debug logging
        print(f"[DEBUG] closeEvent called - isMaximized: {self.isMaximized()}")
        
        # Hủy loading nếu đang tải
        if self.is_loading:
            self.cancel_loading()
        
        # Lưu chiều rộng cột hiện tại
        self.save_current_column_widths()
        
        # Lưu window state - chỉ lưu x, y, width, height khi KHÔNG maximized
        # Sử dụng geometry() để lấy vị trí chính xác của content area
        if self.isMaximized():
            # Nếu đang maximized, chỉ lưu is_maximized=True
            window_state = {
                'x': 100,
                'y': 100,
                'width': 1400,
                'height': 800,
                'is_maximized': True
            }
        else:
            # Lưu x, y từ frameGeometry (bao gồm title bar)
            # Lưu width, height từ geometry (chỉ content area)
            # Điều này đảm bảo lưu/khôi phục nhất quán
            frame_geo = self.frameGeometry()
            content_geo = self.geometry()
            window_state = {
                'x': frame_geo.x(),
                'y': frame_geo.y(),
                'width': content_geo.width(),
                'height': content_geo.height(),
                'is_maximized': False
            }
        
        print(f"[DEBUG] Saving window state: {window_state}")
        self.settings_manager.save_window_state(window_state)
        
        # Disconnect từ server
        self.db_client.disconnect()
        event.accept()
    
    def on_logout(self):
        """Xử lý đăng xuất - đóng cửa sổ hiện tại và hiện dialog đăng nhập lại"""
        print("[Project_Tracking] Người dùng yêu cầu đăng xuất")
        
        # Hiển thị dialog xác nhận đăng xuất
        reply = QMessageBox.question(
            self, 
            "Đăng xuất / 退出", 
            "Bạn có chắc muốn đăng xuất?\n您确定要退出吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Lưu window state trước khi đóng
            self.save_current_column_widths()
            if self.isMaximized():
                window_state = {
                    'x': 100,
                    'y': 100,
                    'width': 1400,
                    'height': 800,
                    'is_maximized': True
                }
            else:
                frame_geo = self.frameGeometry()
                content_geo = self.geometry()
                window_state = {
                    'x': frame_geo.x(),
                    'y': frame_geo.y(),
                    'width': content_geo.width(),
                    'height': content_geo.height(),
                    'is_maximized': False
                }
            self.settings_manager.save_window_state(window_state)
            
            # Đóng cửa sổ hiện tại
            self.close()
            
            # Hiển thị dialog đăng nhập
            print("[Project_Tracking] Hiển thị dialog đăng nhập")
            login_dialog = LoginDialog()
            if login_dialog.exec() == QDialog.Accepted:
                # Đăng nhập thành công, mở lại Project_Tracking
                from src.Project_Tracking import MainWindow as PTMainWindow
                server_ip = session_manager.get_server_ip() or "localhost"
                new_window = PTMainWindow(server_ip=server_ip)
                new_window.show()
            else:
                # Hủy đăng nhập, thoát app
                print("[Project_Tracking] Đã hủy đăng nhập, thoát app")
                import sys
                sys.exit(0)
    
    # ========== FILTER METHODS ==========
    
    def setup_filter_headers(self):
        """Thiết lập clickable header để mở filter dialog"""
        header = self.table_view.horizontalHeader()
        header.sectionClicked.connect(self.on_header_clicked)
    
    def on_header_clicked(self, column):
        """Xử lý khi click vào header cột - mở filter dialog"""
        # Kiểm tra xem model đã được setup chưa
        if not hasattr(self, 'model') or not hasattr(self.model, '_headers'):
            return
        
        # Kiểm tra column có hợp lệ không
        if column < 0 or column >= len(self.model._headers):
            return
        
        # Lấy column name và key
        display_header = self.model._headers[column]
        column_key = self.model._key_mapping.get(display_header, display_header)
        
        # Lấy tất cả giá trị unique của cột từ filtered_data
        values = set()
        for item in self.filtered_data:
            value = item.get(column_key, "")
            if value:
                values.add(str(value))
        
        # Lấy giá trị đã lọc trước đó
        checked_values = {v: True for v in values}
        if column_key in self.column_filters:
            checked_values = {v: (v in self.column_filters[column_key]) for v in values}
        
        # Mở dialog filter
        dialog = FilterByValueDialog(
            self, 
            column_name=display_header,
            column_key=column_key,
            values=values,
            checked_values=checked_values
        )
        
        if dialog.exec() == QDialog.Accepted:
            selected = dialog.get_selected_values()
            
            if selected:
                # Lưu filter cho cột này
                self.column_filters[column_key] = selected
            else:
                # Nếu không chọn gì, xóa filter cho cột này
                if column_key in self.column_filters:
                    del self.column_filters[column_key]
            
            # Áp dụng filter
            self.apply_column_filters()
    
    def apply_column_filters(self):
        """Áp dụng filter theo từng cột"""
        # Nếu không có filter nào, hiển thị filtered_data ban đầu (có thể đã có search)
        if not self.column_filters:
            self.display_data()
            return
        
        # Lấy search text hiện tại
        search_text = self.search_input.text().lower().strip()
        
        # Lọc dữ liệu từ data gốc
        filtered = []
        for item in self.data:
            # Kiểm tra search trước
            if search_text:
                found = False
                for key, value in item.items():
                    if value and search_text in str(value).lower():
                        found = True
                        break
                if not found:
                    continue
            
            # Kiểm tra column filters
            match = True
            for column_key, selected_values in self.column_filters.items():
                item_value = str(item.get(column_key, ""))
                if item_value not in selected_values:
                    match = False
                    break
            
            if match:
                filtered.append(item)
        
        self.filtered_data = filtered
        self.current_page = 1
        self.display_data()
    
    def clear_column_filter(self, column_key):
        """Xóa filter của một cột cụ thể"""
        if column_key in self.column_filters:
            del self.column_filters[column_key]
            self.apply_column_filters()
    
    def clear_all_filters(self):
        """Xóa tất cả filter theo cột"""
        self.column_filters = {}
        self.apply_column_filters()
    
    def show_filter_dialog(self):
        """Hiển thị dialog chọn cột để lọc (alternative cách mở filter)"""
        # Hiển thị thông báo hướng dẫn user click vào header
        QMessageBox.information(
            self, 
            self.texts.get("filter_dialog_title", "Hướng dẫn lọc dữ liệu"),
            self.texts.get("filter_dialog_message", 
                "Để lọc dữ liệu theo cột, hãy CLICK VÀO TÊN CỘT (header) trên bảng.\n\n"
                "Một hộp thoại sẽ hiện ra cho phép bạn chọn các giá trị muốn hiển thị."
            )
        )
    
    def get_cell_value_from_position(self, pos):
        """Lấy (column_key, value) từ vị trí click chuột"""
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return None, None
        
        col = index.column()
        display_header = self.model._headers[col]
        column_key = self.model._key_mapping.get(display_header, display_header)
        
        row = index.row()
        if row < len(self.page_data):
            value = self.page_data[row].get(column_key, "")
            return column_key, str(value) if value else None
        return None, None
    
    def filter_by_cell_value(self, column_key, value):
        """Lọc dữ liệu theo giá trị cụ thể của một cột"""
        if not value:
            return
        self.column_filters[column_key] = [value]
        self.apply_column_filters()
        self.status_bar.showMessage(f"Đã lọc: {column_key} = {value}", 3000)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    restored_max = getattr(window, '_restored_maximized', 'NOT_SET')
    print(f"[DEBUG] main() - _restored_maximized = {restored_max}")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
