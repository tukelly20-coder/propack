"""
Login Dialog - Giao diện đăng nhập tiêu chuẩn
Module riêng biệt cho việc xác thực người dùng
"""

from typing import Optional
import socket
import json
import logging

# Cấu hình logging cho login
LOG_FILE = "login_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QCheckBox, QComboBox,
                               QMessageBox, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QTimer, QThread
from PySide6.QtGui import QFont, QAction, QCursor

from src.language_manager import load_language, CLIENT_TEXT
from src.session_manager import session_manager, get_session_manager


# Login Requester - xác thực với server
class LoginRequester(QThread):
    """Thread đ�?gửi login request lên server"""
    login_result = Signal(dict)  # {"success": bool, "user_info": dict, "error": str}
    
    def __init__(self, server_ip, username, password):
        super().__init__()
        self.server_ip = server_ip
        self.username = username
        self.password = password
    
    def run(self):
        """Gửi login request lên server với x�?lý lỗi chi tiết"""
        logger.info(f"Bắt đầu login request đến {self.server_ip}")
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # Tăng timeout lên 10 giây
            
            logger.debug(f"Đang kết nối đến {self.server_ip}:8001")
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "LOGIN",
                "username": self.username,
                "password": self.password
            }
            logger.debug(f"Gửi request: {request['request']} cho user {self.username}")
            
            client_socket.send(json.dumps(request).encode('utf-8'))
            
            # Đợi response với timeout
            client_socket.settimeout(10)
            data = client_socket.recv(4096).decode('utf-8')
            logger.debug(f"Nhận được response: {data[:200] if len(data) > 200 else data}")
            
            client_socket.close()
            
            result = json.loads(data)
            logger.info(f"Login result: success={result.get('success')}")
            self.login_result.emit(result)
            
        except socket.timeout:
            logger.error(f"Timeout khi kết nối đến {self.server_ip}")
            self.login_result.emit({
                "success": False, 
                "error": "Server không phản hồi sau 10 giây. Vui lòng kiểm tra server đang chạy."
            })
        except ConnectionRefusedError:
            logger.error(f"Server t�?chối kết nối t�?{self.server_ip}")
            self.login_result.emit({
                "success": False, 
                "error": "Server t�?chối kết nối. Vui lòng kiểm tra server đang chạy."
            })
        except ConnectionResetError:
            logger.error(f"Kết nối b�?reset bởi {self.server_ip}")
            self.login_result.emit({
                "success": False, 
                "error": "Kết nối b�?reset. Vui lòng th�?lại."
            })
        except json.JSONDecodeError as e:
            logger.error(f"Phản hồi t�?server không hợp l�? {e}")
            self.login_result.emit({
                "success": False, 
                "error": "Phản hồi t�?server không hợp l�? Vui lòng kiểm tra server."
            })
        except OSError as e:
            logger.error(f"Lỗi socket: {e}")
            self.login_result.emit({
                "success": False, 
                "error": f"Lỗi kết nối: {str(e)}"
            })
        except Exception as e:
            logger.error(f"Lỗi không xác định trong LoginRequester: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.login_result.emit({
                "success": False, 
                "error": f"Lỗi không xác định: {str(e)}"
            })


# Connection Checker - kiểm tra kết nối server
class ConnectionChecker(QThread):
    """Thread đ�?kiểm tra kết nối server"""
    connection_status = Signal(str)  # 'connected' hoặc 'disconnected'
    
    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip
    
    def run(self):
        """Kiểm tra kết nối server với x�?lý lỗi chi tiết"""
        logger.info(f"Kiểm tra kết nối đến {self.server_ip}")
        
        # Kiểm tra DNS/IP trước
        try:
            socket.getaddrinfo(self.server_ip, 8001, socket.AF_INET, socket.SOCK_STREAM)
            logger.debug(f"DNS resolution thành công cho {self.server_ip}")
        except socket.gaierror as e:
            logger.error(f"Lỗi DNS resolution cho {self.server_ip}: {e}")
            self.connection_status.emit('disconnected')
            return
        
        # Th�?kết nối socket
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # Timeout 5 giây
            
            logger.debug(f"Đang kết nối socket đến {self.server_ip}:8001")
            client_socket.connect((self.server_ip, 8001))
            
            # Gửi PING
            request = {"request": "PING"}
            client_socket.send(json.dumps(request).encode('utf-8'))
            logger.debug("Đã gửi PING request")
            
            # Đợi PONG với timeout
            client_socket.settimeout(5)
            response = client_socket.recv(1024).decode('utf-8')
            logger.debug(f"Nhận được response: {response}")
            
            client_socket.close()
            
            if response == "PONG":
                logger.info(f"Kết nối thành công đến {self.server_ip}")
                self.connection_status.emit('connected')
            else:
                logger.warning(f"Phản hồi không mong đợi t�?{self.server_ip}: {response}")
                self.connection_status.emit('disconnected')
                
        except socket.timeout:
            logger.error(f"Timeout khi kiểm tra kết nối đến {self.server_ip}")
            self.connection_status.emit('disconnected')
            
        except ConnectionRefusedError:
            logger.error(f"Server t�?chối kết nối t�?{self.server_ip}")
            self.connection_status.emit('disconnected')
            
        except ConnectionResetError:
            logger.error(f"Kết nối b�?reset bởi {self.server_ip}")
            self.connection_status.emit('disconnected')
            
        except OSError as e:
            logger.error(f"Lỗi socket khi kết nối đến {self.server_ip}: {e}")
            self.connection_status.emit('disconnected')
            
        except Exception as e:
            logger.error(f"Lỗi không xác định trong ConnectionChecker: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.connection_status.emit('disconnected')


class LoginDialog(QDialog):
    """
    Dialog đăng nhập tiêu chuẩn
    
    Signals:
        login_success: Phát ra khi đăng nhập thành công (username, user_info)
        login_failed: Phát ra khi đăng nhập thất bại (error_message)
        login_cancelled: Phát ra khi người dùng hủy đăng nhập
    """
    
    login_success = Signal(str, dict)
    login_failed = Signal(str)
    login_cancelled = Signal()
    
    def __init__(self, parent=None, language: Optional[str] = None):
        """
        Khởi tạo dialog đăng nhập
        
        Args:
            parent: Widget cha
            language: Ngôn ng�?('vi' hoặc 'zh'), nếu None s�?t�?động load
        """
        super().__init__(parent)
        
        # Load ngôn ng�?
        self.current_language = language or load_language()
        
        # Thiết lập dialog
        self.setWindowTitle(CLIENT_TEXT[self.current_language]['login_title'])
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(420, 700)
        self.setModal(True)
        
        # Thiết lập style
        self.setup_style()
        
        # Tạo giao diện
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        
        # Load credentials đã lưu (nếu có)
        self.load_saved_credentials()
    
    def setup_style(self):
        """Thiết lập style cho dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                min-height: 20px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#login_button {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#login_button:hover {
                background-color: #45a049;
            }
            QPushButton#login_button:pressed {
                background-color: #3d8b40;
            }
            QPushButton#cancel_button {
                background-color: #f44336;
                color: white;
            }
            QPushButton#cancel_button:hover {
                background-color: #da190b;
            }
            QPushButton#cancel_button:pressed {
                background-color: #b71c1c;
            }
            QCheckBox {
                font-size: 13px;
                color: #555;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton#toggle_password_button {
                background-color: #e0e0e0;
                color: #333;
                padding: 8px 12px;
                min-width: 40px;
            }
            QPushButton#toggle_password_button:hover {
                background-color: #d0d0d0;
            }
        """)
    
    def create_widgets(self):
        """Tạo các widget"""
        # Language selector
        self.language_label = QLabel(CLIENT_TEXT[self.current_language]['select_language'])
        self.language_combo = QComboBox()
        self.language_combo.addItem(CLIENT_TEXT[self.current_language]['vietnamese'], 'vi')
        self.language_combo.addItem(CLIENT_TEXT[self.current_language]['chinese'], 'zh')
        self.language_combo.setCurrentIndex(0 if self.current_language == 'vi' else 1)
        
        # Title
        self.title_label = QLabel("Project Tracking")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #4CAF50;")
        
        self.subtitle_label = QLabel(CLIENT_TEXT[self.current_language]['login_title'])
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: #666;")
        
        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setStyleSheet("color: #ddd;")
        
        # Username
        self.username_label = QLabel(CLIENT_TEXT[self.current_language]['login_username'])
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_username_placeholder'])
        self.username_input.setClearButtonEnabled(True)
        
        # Password
        self.password_label = QLabel(CLIENT_TEXT[self.current_language]['login_password'])
        
        # Password input with toggle button
        self.password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_password_placeholder'])
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setClearButtonEnabled(True)
        
        # Toggle password visibility button
        self.toggle_password_button = QPushButton("👁")
        self.toggle_password_button.setObjectName("toggle_password_button")
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setChecked(False)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        
        self.password_layout.addWidget(self.password_input)
        self.password_layout.addWidget(self.toggle_password_button)
        
        # Server IP
        self.server_ip_label = QLabel(CLIENT_TEXT[self.current_language]['login_server_ip'])
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_server_ip_placeholder'])
        
        # Options
        self.remember_checkbox = QCheckBox(CLIENT_TEXT[self.current_language]['login_remember'])
        self.remember_checkbox.setChecked(True)
        
        # Forgot password link
        self.forgot_label = QLabel(f'<a href="#forgot" style="color: #2196F3; text-decoration: none;">{CLIENT_TEXT[self.current_language]["login_forgot"]}</a>')
        self.forgot_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.forgot_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Buttons
        self.login_button = QPushButton(CLIENT_TEXT[self.current_language]['login_button'])
        self.login_button.setObjectName("login_button")
      
        self.cancel_button = QPushButton(CLIENT_TEXT[self.current_language]['login_cancel'])
        self.cancel_button.setObjectName("cancel_button")
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #f44336; font-size: 13px;")
        self.status_label.hide()
        
    def setup_layout(self):
        """Thiết lập layout"""
        layout = QVBoxLayout()       
        
        # Title
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.separator)
        
        # Username
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(self.password_label)
        layout.addLayout(self.password_layout, 1)
        
        # Server IP
        layout.addWidget(self.server_ip_label)
        layout.addWidget(self.server_ip_input)
        
        # Options 
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.forgot_label)
        layout.addLayout(options_layout)
        
        # Status
        layout.addSpacing(30)  # Thêm khoảng cách 10px
        layout.addWidget(self.status_label)
        layout.addSpacing(30)
        
        # Buttons đăng nhập và hủy
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        # Thay đổi ngôn ng�?
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.language_label)
        lang_layout.addWidget(self.language_combo)
        layout.addLayout(lang_layout)

        # # Thêm spacer �?dưới
        layout.addStretch()
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Kết nối signals"""
        self.login_button.clicked.connect(self.attempt_login)
        self.cancel_button.clicked.connect(self.reject)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        self.forgot_label.linkActivated.connect(self.on_forgot_password)
    
    def toggle_password_visibility(self, checked=None):
        """Hiện/ẩn password"""
        if checked is None:
            # Toggle state when called from button without parameter
            checked = not self.toggle_password_button.isChecked()
            self.toggle_password_button.setChecked(checked)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle_password_button.setText("🙈" if checked else "👁")
    
    def change_language(self, index):
        """Thay đổi ngôn ng�?""
        self.current_language = self.language_combo.currentData()
        
        # Cập nhật text
        self.setWindowTitle(CLIENT_TEXT[self.current_language]['login_title'])
        self.subtitle_label.setText(CLIENT_TEXT[self.current_language]['login_title'])
        self.username_label.setText(CLIENT_TEXT[self.current_language]['login_username'])
        self.username_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_username_placeholder'])
        self.password_label.setText(CLIENT_TEXT[self.current_language]['login_password'])
        self.password_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_password_placeholder'])
        self.server_ip_label.setText(CLIENT_TEXT[self.current_language]['login_server_ip'])
        self.server_ip_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_server_ip_placeholder'])
        self.remember_checkbox.setText(CLIENT_TEXT[self.current_language]['login_remember'])
        self.forgot_label.setText(f'<a href="#forgot" style="color: #2196F3; text-decoration: none;">{CLIENT_TEXT[self.current_language]["login_forgot"]}</a>')
        self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])
        self.cancel_button.setText(CLIENT_TEXT[self.current_language]['login_cancel'])
        
        # Lưu ngôn ng�?
        try:
            with open('language.txt', 'w', encoding='utf-8') as f:
                f.write(self.current_language)
        except:
            pass
    
    def load_saved_credentials(self):
        """Load credentials và IP đã lưu"""
        # Load credentials
        credentials = get_session_manager().load_credentials()
        if credentials:
            self.username_input.setText(credentials.get('username', ''))
            self.password_input.setText(credentials.get('password', ''))
            # S�?dụng remember flag đã lưu, mặc định False nếu không có
            remember_value = credentials.get('remember', False)
            # Đảm bảo giá tr�?là boolean
            self.remember_checkbox.setChecked(bool(remember_value))
        else:
            # Không có credentials, đ�?checkbox unchecked theo mặc định
            self.remember_checkbox.setChecked(False)
        
        # Load saved IP - ƯU TIÊN T�?FILE RIÊNG, sau đó mới t�?session
        saved_ip = get_session_manager().load_server_ip_from_file()
        if saved_ip:
            self.server_ip_input.setText(saved_ip)
        else:
            # Fallback: th�?t�?session
            saved_ip = get_session_manager().get_server_ip()
            if saved_ip:
                self.server_ip_input.setText(saved_ip)
    
    def check_existing_session(self):
        """Kiểm tra session đã tồn tại"""
        if get_session_manager().is_logged_in():
            username = get_session_manager().get_current_user()
            welcome_text = CLIENT_TEXT[self.current_language]['login_welcome'].format(username)
            self.current_user_label.setText(welcome_text)
            self.current_user_label.show()
        else:
            self.current_user_label.hide()
    
    def validate_inputs(self) -> tuple:
        """
        Validate input
        
        Returns:
            (is_valid, username, password, server_ip)
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        server_ip = self.server_ip_input.text().strip()
        
        if not username:
            return False, "", "", ""
        
        if not password:
            return False, "", "", ""
        
        if not server_ip:
            return False, "", "", ""
        
        return True, username, password, server_ip
    
    def attempt_login(self):
        """Thực hiện đăng nhập - có kiểm tra kết nối trước"""
        # Validate
        is_valid, username, password, server_ip = self.validate_inputs()
        
        if not is_valid:
            # Kiểm tra thiếu gì đ�?hiển th�?lỗi chính xác
            username_val = self.username_input.text().strip()
            password_val = self.password_input.text()
            server_ip_val = self.server_ip_input.text().strip()
            
            if not username_val:
                self.show_error(CLIENT_TEXT[self.current_language]['login_failed_empty'])
            elif not password_val:
                self.show_error(CLIENT_TEXT[self.current_language]['login_failed_empty'])
            elif not server_ip_val:
                self.show_error(CLIENT_TEXT[self.current_language]['login_failed_empty_ip'])
            return
        
        # # Ẩn lỗi cũ
        # self.status_label.hide()
        
        # Disable login button during request
        self.login_button.setEnabled(False)
        self.login_button.setText(CLIENT_TEXT[self.current_language]['login_checking_connection'])
        
        # LƯU THÔNG TIN Đ�?S�?DỤNG SAU KHI CONNECTION CHECK XONG
        self._pending_login = {
            'username': username,
            'password': password,
            'server_ip': server_ip
        }
        
        # KIỂM TRA KẾT NỐI TRƯỚC
        self.connection_checker = ConnectionChecker(server_ip)
        self.connection_checker.connection_status.connect(self.on_connection_check_result)
        self.connection_checker.start()
    
    def on_connection_check_result(self, status: str):
        """X�?lý kết qu�?kiểm tra kết nối"""
        if status == 'connected':
            # Kết nối được, tiếp tục đăng nhập
            pending = self._pending_login
            self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])  # Reset text
            self.login_button.setText("Đang đăng nhập...")
            
            self.login_requester = LoginRequester(
                pending['server_ip'], 
                pending['username'], 
                pending['password']
            )
            self.login_requester.login_result.connect(self.on_login_result)
            self.login_requester.start()
        else:
            # Không kết nối được
            self.login_button.setEnabled(True)
            self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])
            self.show_error(CLIENT_TEXT[self.current_language]['login_connection_failed'])
    
    def on_login_result(self, result: dict):
        """X�?lý kết qu�?đăng nhập t�?server"""
        # Re-enable button
        self.login_button.setEnabled(True)
        self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])
        
        if result.get('success'):
            # Đăng nhập thành công t�?server
            user_info = result.get('user_info', {})
            username = user_info.get('username', '')
            server_ip = self.server_ip_input.text().strip()
            remember = self.remember_checkbox.isChecked()
            password = self.password_input.text()
            
            logger.info(f"Đăng nhập thành công cho user: {username}")
            
            # Lưu credentials
            session_manager.save_credentials(username, password, remember)
            
            # LƯU IP VÀO FILE RIÊNG BIỆT (quan trọng!)
            session_manager.save_server_ip_to_file(server_ip)
            
            # Tạo session với server_ip
            session_manager.create_session(username, user_info, server_ip=server_ip)
            
            # Emit success signal
            logger.info(f"Session được tạo, IP: {server_ip}")
            self.login_success.emit(username, user_info)
            self.accept()
        else:
            # Đăng nhập thất bại
            error_msg = result.get('error', CLIENT_TEXT[self.current_language]['login_failed_invalid'])
            logger.warning(f"Đăng nhập thất bại: {error_msg}")
            self.show_error(error_msg)
            self.login_failed.emit(error_msg)
    
    def show_error(self, message: str):
        """Hiển th�?lỗi"""
        self.status_label.setText(message)
        self.status_label.show()
        
        # Animation effect - highlight input
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #f44336;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ffebee;
            }
        """)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #f44336;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ffebee;
            }
        """)
        
        # Reset style sau 2 giây
        QTimer.singleShot(2000, self.reset_input_style)
    
    def reset_input_style(self):
        """Reset style của input"""
        self.username_input.setStyleSheet("")
        self.password_input.setStyleSheet("")
        self.status_label.hide()
    
    def on_forgot_password(self, link):
        """X�?lý khi click forgot password"""
        QMessageBox.information(
            self,
            CLIENT_TEXT[self.current_language]['login_title'],
            "Vui lòng liên h�?quản tr�?viên đ�?lấy lại mật khẩu.\n请联系管理员重置密码�?
        )
    
    def get_username(self) -> str:
        """Lấy username đã nhập"""
        return self.username_input.text().strip()
    
    def get_password(self) -> str:
        """Lấy password đã nhập"""
        return self.password_input.text()
    
    def get_server_ip(self) -> str:
        """Lấy server IP đã nhập"""
        return self.server_ip_input.text().strip()
    
    def is_remembered(self) -> bool:
        """Kiểm tra có ghi nh�?đăng nhập không"""
        return self.remember_checkbox.isChecked()
    
    def reject(self):
        """Hủy đăng nhập"""
        self.login_cancelled.emit()
        super().reject()


# =============================================================================
# Hàm tiện ích (convenience functions)
# =============================================================================

def show_login_dialog(parent=None, language: Optional[str] = None) -> tuple:
    """
    Hiện dialog đăng nhập và tr�?v�?kết qu�?
    
    Args:
        parent: Widget cha
        language: Ngôn ng�?('vi' hoặc 'zh')
        
    Returns:
        (result, username, server_ip)
        - result: True nếu đăng nhập thành công, False nếu hủy
        - username: Tên đăng nhập
        - server_ip: IP máy ch�?
    """
    dialog = LoginDialog(parent, language)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return True, dialog.get_username(), dialog.get_server_ip()
    else:
        return False, "", ""
