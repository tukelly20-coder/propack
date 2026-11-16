"""
Module quản lý cài đặt hiển thị cột (Column Settings)
Tách riêng từ Project_Tracking.py để dễ bảo trì
Bao gồm tính năng sắp xếp cột bằng kéo thả
"""

import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QDialogButtonBox, QListWidget, QListWidgetItem,
    QLabel, QMessageBox, QWidget, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

# Import language_manager - hỗ trợ cả chạy từ thư mục gốc và thư mục src/
try:
    from src.language_manager import language_manager, CLIENT_TEXT
except ImportError:
    from language_manager import language_manager, CLIENT_TEXT

# Import session_manager
try:
    from src.session_manager import session_manager
except ImportError:
    from session_manager import session_manager

# Default port for server connection
DEFAULT_SERVER_PORT = 8001


class ColumnSettingsDialog(QDialog):
    """Dialog cài đặt hiển thị cột với khả năng kéo thả sắp xếp"""
    
    def __init__(self, parent=None, visible_columns=None, column_order=None):
        super().__init__(parent)
        
        texts = language_manager.get_all_ui_texts()
        self.setWindowTitle(texts["dialog_column_settings"])
        self.setMinimumWidth(450)
        self.setMinimumHeight(500)
        
        self.parent_window = parent
        self.visible_columns = visible_columns or {}
        self.column_order = column_order  # Thứ tự cột từ settings
        
        # Layout chính
        layout = QVBoxLayout(self)
        
        # Hướng dẫn
        hint_label = QLabel("Kéo thả để sắp xếp lại thứ tự cột")
        hint_label.setStyleSheet("font-style: italic; color: gray;")
        layout.addWidget(hint_label)
        
        # List widget với drag & drop
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setSortingEnabled(False)
        layout.addWidget(self.list_widget)
        
        # Buttons chọn tất cả / bỏ chọn tất cả
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton(texts["select_all"])
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton(texts["deselect_all"])
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(button_layout)
        
        # Buttons OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Điền danh sách cột
        self.populate_items()
    
    def populate_items(self):
        """Điền danh sách cột vào list widget - BAO GỒM METADATA"""
        headers = language_manager.get_all_headers()  # Lấy tất cả headers bao gồm metadata
        current_lang = language_manager.get_language()
        
        # Sắp xếp headers theo column_order nếu có
        if self.column_order:
            # Kiểm tra xem column_order có hợp lệ với ngôn ngữ hiện tại không
            matching_headers = [h for h in self.column_order if h in headers]
            if len(matching_headers) > len(self.column_order) * 0.5:
                # Sử dụng thứ tự đã lưu
                order_dict = {h: i for i, h in enumerate(self.column_order)}
                sorted_headers = sorted(headers, key=lambda h: order_dict.get(h, len(order_dict)))
            else:
                print(f"[WARNING] Column order doesn't match current language '{current_lang}'. Using default order.")
                sorted_headers = headers
        else:
            sorted_headers = headers
        
        for header in sorted_headers:
            item = QListWidgetItem(header)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
            
            # Mặc định visible nếu không có cấu hình
            is_visible = self.visible_columns.get(header, True)
            item.setCheckState(Qt.Checked if is_visible else Qt.Unchecked)
            
            self.list_widget.addItem(item)
    
    def select_all(self):
        """Chọn tất cả cột"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """Bỏ chọn tất cả cột"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def get_column_settings(self):
        """Lấy cấu hình cột (visible + order)
        
        Returns:
            tuple: (visible_columns dict, column_order list)
        """
        visible_columns = {}
        column_order = []
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            header = item.text()
            is_visible = item.checkState() == Qt.Checked
            visible_columns[header] = is_visible
            column_order.append(header)
        
        return visible_columns, column_order


class ColumnSettingsManager:
    """Manager xử lý logic lưu/trữ cấu hình cột"""
    
    def __init__(self, settings_file='column_settings.json'):
        self.settings_file = settings_file
    
    def load_column_settings(self):
        """Đọc cấu hình cột từ file"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def load_column_order(self):
        """Đọc thứ tự cột từ file cấu hình"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('column_order', None)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def save_column_settings(self, visible_columns, items_per_page=None, column_order=None):
        """Lưu cấu hình cột vào file
        
        Args:
            visible_columns: dict chứa trạng thái visible của mỗi cột
            items_per_page: số dòng mỗi trang (tùy chọn)
            column_order: list thứ tự cột (tùy chọn)
        """
        try:
            # Đọc settings hiện tại để giữ lại các giá trị khác
            settings = {}
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Giữ lại page_size nếu được cung cấp
            if items_per_page:
                settings['page_size'] = items_per_page
            elif 'page_size' not in settings:
                settings['page_size'] = 50
            
            # Cập nhật visible_columns
            settings.update(visible_columns)
            
            # Lưu column_order nếu có
            if column_order:
                settings['column_order'] = column_order
            
            # Lưu lại
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu cấu hình cột: {e}")
    
    def load_column_widths(self):
        """Đọc chiều rộng cột từ file cấu hình
        
        Returns:
            dict: { "column_name": width } - theo tên cột thay vì index
        """
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                widths = settings.get('column_widths', {})
                
                # Kiểm tra nếu là format cũ (theo index) thì trả về rỗng
                # để trigger migration
                if widths and all(k.isdigit() for k in widths.keys()):
                    print("Phát hiện column_widths format cũ (theo index), sẽ reset")
                    return {}
                
                return widths
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_column_widths(self, column_widths):
        """Lưu chiều rộng cột vào file cấu hình
        
        Args:
            column_widths: dict { "column_name": width } - theo tên cột
        """
        try:
            # Đọc settings hiện tại
            settings = {}
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Cập nhật column_widths (theo tên cột)
            settings['column_widths'] = column_widths
            
            # Lưu lại
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu chiều rộng cột: {e}")
    
    def load_page_size(self):
        """Đọc page_size từ file cấu hình"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('page_size', 50)
        except (FileNotFoundError, json.JSONDecodeError):
            return 50
    
    def save_page_size(self, page_size):
        """Lưu page_size vào file cấu hình"""
        try:
            # Đọc settings hiện tại
            settings = {}
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Cập nhật page_size
            settings['page_size'] = page_size
            
            # Lưu lại
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu page_size: {e}")
    
    def load_window_state(self):
        """Đọc trạng thái cửa sổ từ file cấu hình
        
        Returns:
            dict: { 'x': int, 'y': int, 'width': int, 'height': int, 'is_maximized': bool }
                  hoặc {} nếu chưa có cấu hình
        """
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                window_state = settings.get('window_state', {})
                return window_state
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_window_state(self, window_state):
        """Lưu trạng thái cửa sổ vào file cấu hình
        
        Args:
            window_state: dict { 'x': int, 'y': int, 'width': int, 'height': int, 'is_maximized': bool }
        """
        try:
            # Đọc settings hiện tại
            settings = {}
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Cập nhật window_state
            settings['window_state'] = window_state
            
            # Lưu lại
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu window state: {e}")


class SettingsTab(QWidget):
    """Tab Cài đặt - Hiển thị thông tin người dùng và chức năng đăng xuất"""
    
    logout_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_language = language_manager.get_language()
        self.setup_ui()
        self.update_user_info()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        texts = CLIENT_TEXT[self.current_language]
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        
        # Tiêu đề
        title_label = QLabel(texts['settings_title'])
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Frame thông tin người dùng
        user_frame = QWidget()
        user_frame.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        user_layout = QVBoxLayout()
        user_layout.setSpacing(10)
        
        # Tiêu đề phần user
        user_title = QLabel(texts['settings_user_info'])
        user_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        user_layout.addWidget(user_title)
        
        # Thông tin người dùng
        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 16px; color: #4CAF50;")
        user_layout.addWidget(self.user_label)
        
        # Thời gian đăng nhập
        self.login_time_label = QLabel()
        self.login_time_label.setStyleSheet("font-size: 14px; color: #666;")
        user_layout.addWidget(self.login_time_label)
        
        user_frame.setLayout(user_layout)
        layout.addWidget(user_frame)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)
        
        # Nút đăng xuất
        self.logout_button = QPushButton(texts['settings_logout'])
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.logout_button.clicked.connect(self.on_logout)
        layout.addWidget(self.logout_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
    
    def update_user_info(self):
        """Cập nhật thông tin người dùng"""
        texts = CLIENT_TEXT[self.current_language]
        
        # Lấy thông tin từ session
        if session_manager.is_logged_in():
            username = session_manager.get_current_user() or "Demo User"
            user_info = session_manager.get_user_info() or {}
            login_time = session_manager._current_session.get("login_time", "") if session_manager._current_session else ""
            
            self.user_label.setText(f"{texts['settings_current_user']} {username}")
            
            if login_time:
                # Format thời gian đăng nhập
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(login_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    self.login_time_label.setText(f"{texts['settings_login_time']} {formatted_time}")
                except:
                    self.login_time_label.setText(f"{texts['settings_login_time']} {login_time}")
            else:
                self.login_time_label.setText(f"{texts['settings_login_time']} -")
        else:
            self.user_label.setText(f"{texts['settings_current_user']} -")
            self.login_time_label.setText(f"{texts['settings_login_time']} -")
    
    def on_logout(self):
        """Xử lý khi nhấn nút đăng xuất"""
        texts = CLIENT_TEXT[self.current_language]
        
        # Hiển thị dialog xác nhận
        reply = QMessageBox.question(
            self,
            texts['settings_logout'],
            texts['settings_logout_confirm'],
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Kết thúc session
            session_manager.end_session()
            # Phát signal để MainWindow xử lý
            self.logout_requested.emit()
    
    def reload_language(self):
        """Cập nhật ngôn ngữ khi thay đổi"""
        self.current_language = language_manager.get_language()
        texts = CLIENT_TEXT[self.current_language]
        
        # Cập nhật lại UI
        self.setup_ui()
        self.update_user_info()
