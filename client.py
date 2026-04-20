from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem, QSizePolicy, QInputDialog, QFileDialog, QMessageBox, QDialog, QMenuBar, QMenu
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QAction
import socket
import json
import sys
import subprocess
import logging
from datetime import datetime
import time
import random

# Import HorizontalScrollTableWidget for Shift+wheel horizontal scroll
from src.models import HorizontalScrollTableWidget

# Khởi tạo logger cho client
logger = logging.getLogger(__name__)
from src.about import AboutTab
from src.client_find import SearchDialog
from src.language_manager import CLIENT_TEXT, load_language
from src.Project_Tracking import MainWindow as ProjectTrackingMainWindow
from src.login_dialog import LoginDialog, LoginRequester
from src.session_manager import session_manager
from src.setting import SettingsTab

CATEGORIES = [
    "SJT散件图-SJT散件图-拆解详图",
    "WLJ物料架-WLJ物料架-物料架",
    "ZZC周转车-ZZC周转车-周转车",
    "GZT工作台-GZT工作台-工作台",
    "WCP无尘棚-WCP无尘棚-无尘棚",
    "LSX流水线-LSX流水线-流水线",
    "ZWJ转弯机-ZWJ转弯机-转弯机 90,180",
    "GZL改造类-GZL改造类-改造类",
    "BSX倍速线-BSX倍速线-倍速链",
    "WLL围栏类-WLL围栏类-围栏",
    "GTX滚筒线-GTX滚筒线-滚筒线",
    "ZHT展会图-ZHT展会图-展会图",
    "LHX老化线-LHX老化线-老化线"
]
#hàm yêu cầu tạo mã bản v?mới
class CodeRequester(QThread):
    code_received = Signal(str)

    def __init__(self, server_ip, name, category, employee):
        super().__init__()
        self.server_ip = server_ip
        self.name = name
        self.category = category
        self.employee = employee

    def run(self):
        try:
            socket.getaddrinfo(self.server_ip, 8001)
        except socket.gaierror:
            self.code_received.emit("Lỗi kết nối")
            return
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, 8001))
            request = {
                "request": "REQUEST_CODE",
                "name": self.name,
                "category": self.category,
                "employee": self.employee
            }
            client_socket.send(json.dumps(request).encode('utf-8'))
            code = client_socket.recv(1024).decode('utf-8')
            client_socket.close()
            self.code_received.emit(code)
        except Exception as e:
            print(f"Lỗi kết nối trong CodeRequester: {e}")
            self.code_received.emit("Lỗi kết nối")

#Yêu cầu lịch s?t?server
class HistoryRequester(QThread):
    history_received = Signal(list)

    def __init__(self, server_ip, page=1):
        super().__init__()
        self.server_ip = server_ip
        self.page = page
        self.limit = 100
        self.offset = 0

    def run(self):
        try:
            socket.getaddrinfo(self.server_ip, 8001)
        except socket.gaierror:
            self.history_received.emit([])
            return
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1)
            client_socket.connect((self.server_ip, 8001))
            request = {"request": "GET_HISTORY", "limit": self.limit, "offset": self.offset, "page": self.page}
            client_socket.send(json.dumps(request).encode('utf-8'))
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            data = data.decode('utf-8')
            print(f"[DEBUG] HistoryRequester - Received data length: {len(data)}, data preview: {data[:100] if data else 'empty'}")
            if not data.strip():
                history = []
            else:
                history = json.loads(data)
            client_socket.close()
            self.history_received.emit(history)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSONDecodeError in HistoryRequester: {e}")
            self.history_received.emit([])
        except Exception as e:
            print(f"[DEBUG] Exception in HistoryRequester: {e}")
            self.history_received.emit([])

#Yêu cầu lịch s?toàn b?cho export
class ExportHistoryRequester(QThread):
    history_received = Signal(list)

    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip

    def run(self):
        try:
            socket.getaddrinfo(self.server_ip, 8001)
        except socket.gaierror:
            self.history_received.emit([])
            return
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1)
            client_socket.connect((self.server_ip, 8001))
            request = {"request": "GET_HISTORY", "limit": None}
            client_socket.send(json.dumps(request).encode('utf-8'))
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            data = data.decode('utf-8')
            print(f"[DEBUG] ExportHistoryRequester - Received data length: {len(data)}, data preview: {data[:100] if data else 'empty'}")
            if not data.strip():
                history = []
            else:
                history = json.loads(data)
            client_socket.close()
            self.history_received.emit(history)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSONDecodeError in ExportHistoryRequester: {e}")
            self.history_received.emit([])
        except Exception as e:
            print(f"[DEBUG] Exception in ExportHistoryRequester: {e}")
            self.history_received.emit([])

# Tìm kiếm lịch s?t?server
class SearchHistoryRequester(QThread):
    search_results = Signal(list)

    def __init__(self, server_ip, search_text, columns):
        super().__init__()
        self.server_ip = server_ip
        self.search_text = search_text
        self.columns = columns

    def run(self):
        try:
            socket.getaddrinfo(self.server_ip, 8001)
        except socket.gaierror:
            self.search_results.emit([])
            return
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # Tăng timeout cho search
            client_socket.connect((self.server_ip, 8001))
            request = {
                "request": "SEARCH_HISTORY",
                "search_text": self.search_text,
                "columns": self.columns
            }
            client_socket.send(json.dumps(request).encode('utf-8'))
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            data = data.decode('utf-8')
            print(f"[DEBUG] SearchHistoryRequester - Received data length: {len(data)}, data preview: {data[:100] if data else 'empty'}")
            if not data.strip():
                results = []
            else:
                results = json.loads(data)
            client_socket.close()
            self.search_results.emit(results)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSONDecodeError in SearchHistoryRequester: {e}")
            self.search_results.emit([])
        except Exception as e:
            print(f"[DEBUG] Exception in SearchHistoryRequester: {e}")
            self.search_results.emit([])

#kiểm tra kết nối đến server
class ConnectionChecker(QThread):
    connection_status = Signal(str)

    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip

    def run(self):
        print(f"ConnectionChecker started for {self.server_ip}")
        if not self.server_ip:
            print("No server IP, emitting disconnected")
            self.connection_status.emit('disconnected')
            return
        try:
            socket.getaddrinfo(self.server_ip, 8001, socket.AF_INET, socket.SOCK_STREAM)
        except socket.gaierror as e:
            print(f"Invalid server IP: {self.server_ip}, {e}")
            self.connection_status.emit('disconnected')
            return
        try:
            print(f"Creating socket to {self.server_ip}:8001")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1)
            print("Connecting...")
            client_socket.connect((self.server_ip, 8001))
            print("Connected, sending PING")
            request = {"request": "PING"}
            client_socket.send(json.dumps(request).encode('utf-8'))
            print("Sent PING, receiving...")
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Received: {response}")
            client_socket.close()
            if response == "PONG":
                print("PONG received, connected")
                self.connection_status.emit('connected')
            else:
                print(f"Unexpected response: {response}, disconnected")
                self.connection_status.emit('disconnected')
        except Exception as e:
            print(f"Lỗi kết nối trong ConnectionChecker: {e}")
            self.connection_status.emit('disconnected')
        print("ConnectionChecker finished")

# Biến toàn cục đ?gi?tham chiếu đến MainWindow đang chạy
_main_window_instance = None

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tạo Mã Bản Vẽ")
        self.resize(800, 600)
        self.tabs = QTabWidget()
        self.current_language = load_language()
        self.current_state = 'DISCONNECTED'
        self.retry_interval = 5
        self.max_retry_interval = 60
        layout = QVBoxLayout()
        self.connection_label = QLabel(CLIENT_TEXT[self.current_language]['connecting'])
        layout.addWidget(self.connection_label)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Project Tracking window reference (singleton)
        self.project_tracking_window = None
        
        # Get server IP from session
        self.server_ip = session_manager.get_server_ip() or ""
        
        # Tab 1: Tạo Mã Bản V?
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        self.name_label = QLabel("Tên người xin mã:")
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab1_layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(100)
        self.name_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_last_name()
        tab1_layout.addWidget(self.name_input)
        self.employee_label = QLabel("Mã nhân viên:")
        self.employee_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab1_layout.addWidget(self.employee_label)
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("Nhập mã nhân viên")
        self.employee_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_last_employee()
        tab1_layout.addWidget(self.employee_input)
        self.category_label = QLabel("Hạng mục:")
        self.category_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab1_layout.addWidget(self.category_label)
        self.category_combo = QComboBox()
        for cat in CATEGORIES:
            code = cat[:3]
            self.category_combo.addItem(cat, code)
        self.category_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab1_layout.addWidget(self.category_combo)
        self.load_last_category()
        self.button = QPushButton("Tạo Mã")
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.clicked.connect(self.request_code)
        tab1_layout.addWidget(self.button)
        self.result_label = QLabel("Mã s?hiển th??đây")
        self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab1_layout.addWidget(self.result_label)
        tab1.setLayout(tab1_layout)
        self.tabs.addTab(tab1, "Tạo Mã")

        # Tab 2: Lịch S?
        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        self.history_table = HorizontalScrollTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Tên", "Mã nhân viên", "Hạng mục", "Mã", "Thời gian"])
        tab2_layout.addWidget(self.history_table)
        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Trước")
        self.prev_button.clicked.connect(self.prev_page)
        self.page_label = QLabel("Trang 1")
        self.next_button = QPushButton("Sau")
        self.next_button.clicked.connect(self.next_page)
        self.delete_button = QPushButton("Xóa")
        self.delete_button.clicked.connect(self.delete_history)
        self.export_button = QPushButton("Xuất XLS")
        self.export_button.clicked.connect(self.export_xls)
        self.refresh_button = QPushButton("Làm mới")
        self.refresh_button.clicked.connect(self.request_history)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.delete_button)
        pagination_layout.addWidget(self.export_button)
        pagination_layout.addWidget(self.refresh_button)
        tab2_layout.addLayout(pagination_layout)
        tab2.setLayout(tab2_layout)
        self.tabs.addTab(tab2, "Lịch Sử")
        self.history_page = 0
        self.history_data = []
        self.history_headers = {"name": "Tên", "employee": "Mã nhân viên", "category": "Hạng mục", "code": "Mã", "time": "Thời gian"}
        self.last_refresh = 0
        self.search_mode = False

        # Tab 3: Ngôn ng?
        tab3 = QWidget()
        tab3_layout = QVBoxLayout()
        tab3_layout.setAlignment(Qt.AlignTop)
        self.language_label = QLabel("Chọn ngôn ng?")
        tab3_layout.addWidget(self.language_label)
        self.language_combo = QComboBox()
        self.language_combo.addItem("Tiếng Việt", 'vi')
        self.language_combo.addItem("Tiếng Trung", 'zh')
        tab3_layout.addWidget(self.language_combo)
        self.apply_button = QPushButton("Áp dụng")
        self.apply_button.clicked.connect(self.apply_language)
        tab3_layout.addWidget(self.apply_button)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab3_layout.addWidget(spacer)
        tab3.setLayout(tab3_layout)
        self.tabs.addTab(tab3, "Ngôn ngữ")

        # Tab 4: Tool Đồng b?hóa
        tab4 = QWidget()
        tab4_layout = QVBoxLayout()
        tab4_layout.addWidget(QLabel("Nội dung tool đồng b?hóa"))
        # Ô 1 điền From.txt
        from_layout = QHBoxLayout()
        self.tab4_input_from = QLineEdit()
        self.tab4_input_from.setPlaceholderText("Nhập link From")
        self.browse_from_button = QPushButton("Browse")
        self.browse_from_button.clicked.connect(self.browse_from_directory)
        from_layout.addWidget(self.tab4_input_from)
        from_layout.addWidget(self.browse_from_button)
        tab4_layout.addLayout(from_layout)
        # Ô 2 điền To.txt
        to_layout = QHBoxLayout()
        self.tab4_input_to = QLineEdit()
        self.tab4_input_to.setPlaceholderText("Nhập link To")
        self.browse_to_button = QPushButton("Browse")
        self.browse_to_button.clicked.connect(self.browse_to_directory)
        to_layout.addWidget(self.tab4_input_to)
        to_layout.addWidget(self.browse_to_button)
        tab4_layout.addLayout(to_layout)
        #hiển th?nội dung của form.txt và to.txt
        self.load_tab4_from()
        self.load_tab4_to()
        # Nút nhấn "Đồng B?ngay"
        self.sync_button = QPushButton("Đồng b?ngay")
        self.sync_button.clicked.connect(self.perform_sync) #kết nối với hàm x?lý
        tab4_layout.addWidget(self.sync_button)
        tab4_layout.setAlignment(Qt.AlignTop) # căn l?trên cho toàn b?layout tab4
        tab4.setLayout(tab4_layout) #thiết lập layout cho tab4
        self.tabs.addTab(tab4,"Tool Đồng b?hóa")

        # Tab 5: Project Tracking
        tab5 = QWidget()
        tab5_layout = QVBoxLayout()
        tab5_layout.setAlignment(Qt.AlignTop)

        # Thêm tiêu đ?
        title_label = QLabel("Theo Dõi D?Án / 项目跟踪")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        tab5_layout.addWidget(title_label)

        # Thêm mô t?
        desc_label = QLabel("Nhấn nút bên dưới đ?m?cửa s?theo dõi d?án\n点击下方按钮打开项目跟踪窗口")
        desc_label.setAlignment(Qt.AlignCenter)
        tab5_layout.addWidget(desc_label)

        # Thêm nút m?Project Tracking
        open_project_tracking_button = QPushButton("M?Theo Dõi D?Án / 打开项目跟踪")
        open_project_tracking_button.clicked.connect(self.open_project_tracking)
        open_project_tracking_button.setMinimumHeight(50)
        tab5_layout.addWidget(open_project_tracking_button)

        # Thêm spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab5_layout.addWidget(spacer)

        tab5.setLayout(tab5_layout)
        self.tabs.addTab(tab5, "Project Tracking")

        # Tab 6: Settings
        tab6 = SettingsTab()
        tab6.logout_requested.connect(self.on_logout)
        self.tabs.addTab(tab6, "Cài đặt")
        
        # Tab 7: About
        tab7 = AboutTab()
        self.tabs.addTab(tab7, "About")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(5000)
        # Kiểm tra kết nối sau 2000ms
        QTimer.singleShot(2000, self.check_connection)
        self.update_ui_texts()

    def request_code(self):
        if self.current_state != 'CONNECTED':
            self.result_label.setText(CLIENT_TEXT[self.current_language]['connection_error'])
            return
        server_ip = self.server_ip
        name = self.name_input.text().strip()
        category = self.category_combo.currentData()
        employee = self.employee_input.text().strip()
        if not server_ip or not name or not category or not employee:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['fill_info'])
            return
        if not (len(employee) == 3 and employee.isdigit() and employee != '000'):
            self.result_label.setText(CLIENT_TEXT[self.current_language]['invalid_employee'])
            return
        self.button.setEnabled(False)
        self.requester = CodeRequester(server_ip, name, category, employee)
        self.requester.code_received.connect(self.display_code, Qt.QueuedConnection)
        self.requester.finished.connect(self.requester.deleteLater)
        self.requester.start()

    def display_code(self, code):
        if code == "Lỗi kết nối":
            self.current_state = 'DISCONNECTED'
            self.update_connection_status('disconnected')
            self.result_label.setText(CLIENT_TEXT[self.current_language]['connection_error'])
        else:
            self.result_label.setText(code)
        self.button.setEnabled(True)
        if "Lỗi" not in code and code not in ["NO_MORE_CODES", "INVALID_REQUEST"]:
            self.save_last_name()
            self.save_last_employee()
            self.save_last_category()
            QTimer.singleShot(1000, self.request_history)  # Delay 1 giây trước khi refresh history

    def can_request_history(self):
        current_time = time.time()
        if current_time - self.last_refresh < 1.0:  # Debounce 1 giây
            return False
        self.last_refresh = current_time
        return True

    def request_history(self):
        print("Requested history (F5 or Refresh button)")
        # Reset search mode khi refresh data
        self.search_mode = False
        # Re-enable navigation buttons
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        if not self.can_request_history():
            print("Request blocked by debounce")
            return
        self.refresh_button.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.refresh_button.setEnabled(True))
        if self.current_state != 'CONNECTED':
            return
        server_ip = self.server_ip
        if server_ip:
            self.history_requester = HistoryRequester(server_ip, page=1)
            self.history_requester.history_received.connect(self.populate_history, Qt.QueuedConnection)
            self.history_requester.finished.connect(self.history_requester.deleteLater)
            self.history_requester.start()

    def populate_history(self, history):
        self.history_data = history  # Server đã sorted
        self.history_page = 0
        self.update_history_table()

    def update_history_table(self):
        # Hiển th?toàn b?self.history_data (100 bản ghi cho mỗi trang)
        page_data = self.history_data
        self.history_table.setRowCount(len(page_data))
        for row, item in enumerate(page_data):
            self.history_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
            self.history_table.setItem(row, 1, QTableWidgetItem(item.get('employee', '')))
            self.history_table.setItem(row, 2, QTableWidgetItem(item.get('category', '')))
            self.history_table.setItem(row, 3, QTableWidgetItem(item.get('code', '')))
            time_str = item.get('time', '')
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_time = time_str
            else:
                formatted_time = ''
            self.history_table.setItem(row, 4, QTableWidgetItem(formatted_time))
            for i in range(5):
                self.history_table.resizeColumnToContents(i)
            self.page_label.setText(CLIENT_TEXT[self.current_language]['page'].format(page=self.history_page + 1))

    def prev_page(self):
        print("Pressed Trước (Prev) button")
        self.prev_button.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.prev_button.setEnabled(True))
        if self.history_page > 0:
            self.history_page -= 1
            self.request_history_page(self.history_page)

    def next_page(self):
        print("Pressed Sau (Next) button")
        self.next_button.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.next_button.setEnabled(True))
        page_size = 100
        # Tăng history_page và yêu cầu d?liệu mới t?server
        self.history_page += 1
        self.request_history_page(self.history_page)
    
    def request_history_page(self, page):
        if not self.can_request_history():
            return
        if self.current_state != 'CONNECTED':
            return
        server_ip = self.server_ip
        if server_ip:
            self.history_requester = HistoryRequester(server_ip, page=page + 1)
            self.history_requester.history_received.connect(self.populate_history_page, Qt.QueuedConnection)
            self.history_requester.finished.connect(self.history_requester.deleteLater)
            self.history_requester.start()
    
    def populate_history_page(self, history):
        # Thay th?hoàn toàn history_data với d?liệu đã sorted t?server
        self.history_data = history
        self.update_history_table()

    def delete_history(self):
        selected = self.history_table.selectedItems()
        if not selected:
            print("No item selected for deletion")
            return
        row = selected[0].row()
        item = self.history_data[self.history_page * 100 + row]
        code = item.get('code')
        print(f"Attempting to delete code: {code}")
        pwd, ok = QInputDialog.getText(self, CLIENT_TEXT[self.current_language]['confirm_delete'], CLIENT_TEXT[self.current_language]['enter_password'], QLineEdit.Password)
        if ok and pwd == "kelly":
            print(f"Password confirmed, sending delete request for code: {code}")
            self.send_delete_request(code)
        else:
            print("Delete cancelled or incorrect password")

    def send_delete_request(self, code):
        server_ip = self.server_ip
        if server_ip:
            try:
                socket.getaddrinfo(server_ip, 8001)
            except socket.gaierror:
                print("Invalid server IP for delete")
                return
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((server_ip, 8001))
                request = {"request": "DELETE_HISTORY", "password": "kelly", "code": code}
                print(f"Sending delete request to server: {request}")
                client_socket.send(json.dumps(request).encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                client_socket.close()
                print(f"Server response: {response}")
                if response == "DELETED":
                    print("Delete successful, refreshing history")
                    self.request_history()
                else:
                    print("Delete failed")
            except Exception as e:
                print(f"Delete error: {e}")

    def export_xls(self):
        if self.current_state != 'CONNECTED':
            self.result_label.setText(CLIENT_TEXT[self.current_language]['connection_error'])
            return
        server_ip = self.server_ip
        if not server_ip:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['fill_info'])
            return
        file_path, _ = QFileDialog.getSaveFileName(self, CLIENT_TEXT[self.current_language]['export_xls'], "history.xlsx", "Excel Files (*.xlsx)")
        if not file_path:
            return
        self.export_button.setEnabled(False)
        self.export_requester = ExportHistoryRequester(server_ip)
        self.export_requester.history_received.connect(self.export_history_received, Qt.QueuedConnection)
        self.export_requester.finished.connect(self.export_requester.deleteLater)
        self.export_requester.start()
        self.export_file_path = file_path

    def export_history_received(self, history):
        if not history:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['no_data'])
            self.export_button.setEnabled(True)
            return
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.append([CLIENT_TEXT[self.current_language]['name'], CLIENT_TEXT[self.current_language]['employee'], CLIENT_TEXT[self.current_language]['category'], CLIENT_TEXT[self.current_language]['code'], CLIENT_TEXT[self.current_language]['time']])
            for item in history:
                time_str = item.get('time', '')
                if time_str:
                    try:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_time = time_str
                else:
                    formatted_time = ''
                ws.append([item.get('name', ''), item.get('employee', ''), item.get('category', ''), item.get('code', ''), formatted_time])
            wb.save(self.export_file_path)
            self.result_label.setText(CLIENT_TEXT[self.current_language]['exported'].format(file_path=self.export_file_path))
        except ImportError:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['need_openpyxl'])
        except Exception as e:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['export_error'].format(e=str(e)))
        finally:
            self.export_button.setEnabled(True)

    def load_last_name(self):
        try:
            with open('last_name.txt', 'r', encoding='utf-8') as f:
                name = f.read().strip()
                self.name_input.setText(name)
        except:
            pass

    def save_last_name(self):
        name = self.name_input.text().strip()
        try:
            with open('last_name.txt', 'w', encoding='utf-8') as f:
                f.write(name)
        except:
            pass

    def load_last_category(self):
        try:
            with open('last_category.txt', 'r', encoding='utf-8') as f:
                cat_code = f.read().strip()
                index = self.category_combo.findData(cat_code)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
        except:
            pass

    def save_last_category(self):
        cat_code = self.category_combo.currentData()
        try:
            with open('last_category.txt', 'w', encoding='utf-8-sig') as f:
                f.write(cat_code)
        except:
            pass
    
    def load_last_employee(self):
        try:
            with open('last_employee.txt', 'r', encoding='utf-8') as f:
                employee = f.read().strip()
                self.employee_input.setText(employee)
        except:
            pass
    
    def save_last_employee(self):
        employee = self.employee_input.text().strip()
        try:
            with open('last_employee.txt', 'w', encoding='utf-8') as f:
                f.write(employee)
        except:
            pass
    
    # hiển th?nội dung của From.txt và To.txt
    def load_tab4_from(self):
        try:
            with open('Toolsysnc/From.txt','r',encoding='utf-8') as f:
                content = f.read().strip()
                self.tab4_input_from.setText(content)
        except:
            pass

    def load_tab4_to(self):
        try:
            with open('Toolsysnc/To.txt','r',encoding='utf-8') as f:
                content = f.read().strip()
                self.tab4_input_to.setText(content)
        except:
            pass

    def on_tab_changed(self, index):
        if index == 1 and not self.history_data:  # Tab Lịch S?and no data loaded yet
            self.request_history()

    def check_connection(self):
        """Kiểm tra kết nối server với logging chi tiết"""
        if self.current_state == 'DISCONNECTED':
            server_ip = self.server_ip
            if not server_ip:
                print("[MainWindow] Không có server IP, không th?kết nối")
                self.connection_label.setText("Chưa cấu hình IP server")
                return
            
            print(f"[MainWindow] Đang kiểm tra kết nối đến {server_ip}...")
            self.connection_label.setText(CLIENT_TEXT[self.current_language]['checking'])
            self.connection_checker = ConnectionChecker(server_ip)
            self.connection_checker.connection_status.connect(self.update_connection_status, Qt.QueuedConnection)
            self.connection_checker.finished.connect(self.connection_checker.deleteLater)
            self.connection_checker.start()

    def update_connection_status(self, status_key):
        """Cập nhật trạng thái kết nối"""
        if status_key == 'connected':
            self.current_state = 'CONNECTED'
            self.timer.stop()
            print(f"[MainWindow] Kết nối thành công đến {self.server_ip}")
        else:
            self.current_state = 'DISCONNECTED'
            self.retry_interval = min(self.retry_interval * 2, self.max_retry_interval)
            self.timer.start(self.retry_interval * 1000)
            print(f"[MainWindow] Kết nối thất bại, th?lại sau {self.retry_interval} giây")
        
        # Cập nhật UI
        status_texts = {
            'connected': 'Đã kết nối',
            'disconnected': 'Mất kết nối - Đang th?lại...',
            'checking': 'Đang kiểm tra kết nối...'
        }
        self.connection_label.setText(status_texts.get(status_key, status_key))

    def load_language(self):
        self.current_language = load_language()
        self.language_combo.setCurrentIndex(0 if self.current_language == 'vi' else 1)

    def apply_language(self):
        self.current_language = self.language_combo.currentData()
        try:
            with open('language.txt', 'w', encoding='utf-8') as f:
                f.write(self.current_language)
        except:
            pass
        self.update_ui_texts()
        # Cập nhật nội dung README trong tab About
        self.tabs.widget(6).reload_readme()
        # Cập nhật ngôn ng?trong tab Settings
        self.tabs.widget(5).reload_language()

    def update_ui_texts(self):
        lang = self.current_language
        self.setWindowTitle(CLIENT_TEXT[lang]['window_title'])
        self.tabs.setTabText(0, CLIENT_TEXT[lang]['tab_draw'])
        self.tabs.setTabText(1, CLIENT_TEXT[lang]['tab_history'])
        self.tabs.setTabText(2, CLIENT_TEXT[lang]['tab_language'])
        self.tabs.setTabText(3, CLIENT_TEXT[lang]['tab_sync'])
        self.tabs.setTabText(4, CLIENT_TEXT[lang]['tab_project_tracking'])
        self.tabs.setTabText(5, CLIENT_TEXT[lang]['tab_settings'])
        self.tabs.setTabText(6, CLIENT_TEXT[lang]['tab_about'])
        self.name_label.setText(CLIENT_TEXT[lang]['name_label'])
        self.employee_label.setText(CLIENT_TEXT[lang]['employee_label'])
        self.category_label.setText(CLIENT_TEXT[lang]['category_label'])
        self.button.setText(CLIENT_TEXT[lang]['draw_button'])
        self.result_label.setText(CLIENT_TEXT[lang]['result_placeholder'])
        self.history_table.setHorizontalHeaderLabels([
            CLIENT_TEXT[lang]['name'],
            CLIENT_TEXT[lang]['employee'],
            CLIENT_TEXT[lang]['category'],
            CLIENT_TEXT[lang]['code'],
            CLIENT_TEXT[lang]['time']
        ])
        self.prev_button.setText(CLIENT_TEXT[lang]['prev'])
        self.next_button.setText(CLIENT_TEXT[lang]['next'])
        self.delete_button.setText(CLIENT_TEXT[lang]['delete_selected'])
        self.export_button.setText(CLIENT_TEXT[lang]['export_xls'])
        self.refresh_button.setText(CLIENT_TEXT[lang]['refresh'])
        self.page_label.setText(CLIENT_TEXT[lang]['page'].format(page=self.history_page + 1))
        self.language_label.setText(CLIENT_TEXT[lang]['select_language'])
        self.language_combo.setItemText(0, CLIENT_TEXT[lang]['vietnamese'])
        self.language_combo.setItemText(1, CLIENT_TEXT[lang]['chinese'])
        self.apply_button.setText(CLIENT_TEXT[lang]['apply'])
        self.language_combo.setCurrentIndex(0 if self.current_language == 'vi' else 1)
    
    #logic tool đồng b?hóa
    def perform_sync(self):
        from_text = self.tab4_input_from.text().strip()
        to_text = self.tab4_input_to.text().strip()
        if not from_text or not to_text:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_fill_info'])
            return
        try:
            with open('Toolsysnc/From.txt', 'w', encoding='utf-8') as f:
                f.write(from_text)
            with open('Toolsysnc/To.txt', 'w', encoding='utf-8') as f:
                f.write(to_text)
            self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_saved'])
            try:
                subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'Toolsysnc/T?Tool  đồng b?hóa.bat'], shell=True)
                self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_running'])
            except FileNotFoundError:
                self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_not_found'])
            except Exception as e:
                self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_unknown_error'] + str(e))
        except Exception as e:
            self.result_label.setText(CLIENT_TEXT[self.current_language]['sync_save_error'] + str(e))

    def browse_from_directory(self):
        directory = QFileDialog.getExistingDirectory(self, CLIENT_TEXT[self.current_language]['browse_from'])
        if directory:
            self.tab4_input_from.setText(directory.replace('/', '\\'))

    def browse_to_directory(self):
        directory = QFileDialog.getExistingDirectory(self, CLIENT_TEXT[self.current_language]['browse_to'])
        if directory:
            self.tab4_input_to.setText(directory.replace('/', '\\'))

    def open_project_tracking(self):
        """Mở cửa sổ Project Tracking - chạm một cửa sổ"""
        # Kiểm tra nếu cửa s?đã m?và đang hiển th?
        if self.project_tracking_window is not None and self.project_tracking_window.isVisible():
            # Focus vào cửa s?đã m?
            self.project_tracking_window.activateWindow()
            self.project_tracking_window.raise_()
            return
        # Tạo cửa s?mới
        self.project_tracking_window = ProjectTrackingMainWindow(server_ip=self.server_ip)
        self.project_tracking_window.show()

    def on_logout(self):
        """Xử lý đăng xuất - đóng cửa sổ hiện tại và hiện dialog đăng nhập lại"""
        logger.info("Người dùng yêu cầu đăng xuất")
        
        print("[MainWindow] Đang đăng xuất...")
        
        # QUAN TRỌNG: Ngắt kết nối signals và ch?threads kết thúc trước khi đóng window
        # đ?tránh thread c?gắng access window đã b?hủy gây crash
        try:
            if hasattr(self, 'connection_checker') and self.connection_checker.isRunning():
                self.connection_checker.blockSignals(True)
                self.connection_checker.wait(1000)
        except:
            pass
        try:
            if hasattr(self, 'history_requester') and self.history_requester.isRunning():
                self.history_requester.blockSignals(True)
                self.history_requester.wait(1000)
        except:
            pass
        try:
            if hasattr(self, 'requester') and self.requester.isRunning():
                self.requester.blockSignals(True)
                self.requester.wait(1000)
        except:
            pass
        try:
            if hasattr(self, 'export_requester') and self.export_requester.isRunning():
                self.export_requester.blockSignals(True)
                self.export_requester.wait(1000)
        except:
            pass
        
        # Hiển th?dialog đăng nhập lại
        print("[MainWindow] Hiển th?dialog đăng nhập")
        login_dialog = LoginDialog()
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.close()
            # S?dụng biến toàn cục đ?gi?tham chiếu đến MainWindow mới
            global _main_window_instance
            _main_window_instance = MainWindow()
            _main_window_instance.show()
        else:
            # Hủy đăng nhập, thoát app
            print("[MainWindow] Đã hủy đăng nhập, thoát app")
            self.close()
            import sys
            sys.exit(0)

    def open_search_dialog(self):
        """
        Mở dialog tìm kiếm lịch sử - Ctrl+F handler
        Sử dụng static method của SearchDialog để tập trung logic
        """
        SearchDialog.open_search_dialog(
            self, 
            self.server_ip, 
            self.history_data, 
            self.history_headers,
            search_type="HISTORY"
        )
    
    def keyPressEvent(self, event):
        if self.tabs.currentIndex() == 1:  # Tab Lịch S?
            if event.key() == Qt.Key_F5:
                print("Pressed F5 key")
                self.request_history()
            elif event.key() == Qt.Key_Delete:
                self.delete_history()
            elif event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
                print("Pressed Ctrl+F key")
                self.open_search_dialog()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Stop the timer to prevent new threads
        self.timer.stop()
        # Wait for any running threads before closing
        try:
            if hasattr(self, 'requester') and self.requester.isRunning():
                self.requester.wait(5000)  # Wait up to 5 seconds
        except RuntimeError:
            pass
        try:
            if hasattr(self, 'history_requester') and self.history_requester.isRunning():
                self.history_requester.wait(5000)
        except RuntimeError:
            pass
        try:
            if hasattr(self, 'connection_checker') and self.connection_checker.isRunning():
                self.connection_checker.wait(5000)
        except RuntimeError:
            pass
        try:
            if hasattr(self, 'export_requester') and self.export_requester.isRunning():
                self.export_requester.wait(5000)
        except RuntimeError:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Th?auto login với xác thực server
    auto_login_success = False
    auto_login_error = None
    
    # Bước 1: Kiểm tra session cục b?
    if session_manager.is_logged_in():
        print(f"[AutoLogin] Session cục b?tồn tại cho user: {session_manager.get_current_user()}")
        
        # Bước 2: Lấy server IP t?session hoặc file
        server_ip = session_manager.get_server_ip() or session_manager.load_server_ip_from_file()
        
        if server_ip:
            print(f"[AutoLogin] Đang xác thực với server {server_ip}...")
            
            # Bước 3: Th?xác thực với server bằng credentials đã lưu
            result = session_manager.validate_session_with_server(server_ip)
            
            if result['success']:
                print(f"[AutoLogin] Xác thực server thành công cho user: {result['user_info'].get('username', 'unknown')}")
                auto_login_success = True
            else:
                auto_login_error = result.get('error', 'Xác thực thất bại')
                print(f"[AutoLogin] Xác thực server thất bại: {auto_login_error}")
                print("[AutoLogin] S?hiển th?dialog đăng nhập...")
        else:
            print("[AutoLogin] Không tìm thấy server IP")
    else:
        print("[AutoLogin] Không có session cục bộ")
    
    # Nếu auto login thành công, hiển th?cửa s?Project Tracking trực tiếp
    if auto_login_success:
        server_ip = session_manager.get_server_ip() or ""
        pt_window = ProjectTrackingMainWindow(server_ip=server_ip)
        pt_window.show()
        sys.exit(app.exec())
    
    # Nếu auto login thất bại, hiện dialog đăng nhập
    if auto_login_error:
        print(f"[AutoLogin] Lỗi: {auto_login_error}")
    
    # Hiện dialog đăng nhập
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        # Đăng nhập thành công, m?cửa s?Project Tracking trực tiếp
        server_ip = session_manager.get_server_ip() or ""
        pt_window = ProjectTrackingMainWindow(server_ip=server_ip)
        pt_window.show()
        sys.exit(app.exec())
    else:
        # Hủy đăng nhập, thoát app
        print("Đã hủy đăng nhập")
        sys.exit(0)
