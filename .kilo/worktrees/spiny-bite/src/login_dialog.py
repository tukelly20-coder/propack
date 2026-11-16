"""
Login Dialog - Giao diá» n Ä Ä ng nháº­p tiÃªu chuáº©n
Module riÃªng biá» t cho viá» c xÃ¡c thá»±c ngÆ°á» i dÃ¹ng
"""

from typing import Optional
import socket
import json
import logging

# Cáº¥u hÃ¬nh logging cho login
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

SOCKET_PORT_CANDIDATES = (12345, 8001)

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QCheckBox, QComboBox,
                               QMessageBox, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QTimer, QThread
from PySide6.QtGui import QFont, QAction, QCursor

from src.language_manager import load_language, CLIENT_TEXT
from src.session_manager import session_manager, get_session_manager


# Login Requester - xÃ¡c thá»±c vá» i server
class LoginRequester(QThread):
    """Thread Ä á»?gá»­i login request lÃªn server"""
    login_result = Signal(dict)  # {"success": bool, "user_info": dict, "error": str}
    
    def __init__(self, server_ip, username, password):
        super().__init__()
        self.server_ip = server_ip
        self.username = username
        self.password = password
    
    def run(self):
        """Send login request to server with detailed error handling."""
        logger.info(f"Starting login request to {self.server_ip}")
        last_error = None
        request = {
            "request": "LOGIN",
            "username": self.username,
            "password": self.password
        }

        for port in SOCKET_PORT_CANDIDATES:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(10)  # Increase timeout to 10 seconds

                logger.debug(f"Connecting to {self.server_ip}:{port}")
                client_socket.connect((self.server_ip, port))
                logger.debug(f"Sending request {request['request']} for user {self.username}")

                client_socket.send(json.dumps(request).encode('utf-8'))

                # Wait for response with timeout
                client_socket.settimeout(10)
                data = client_socket.recv(4096).decode('utf-8')
                logger.debug(f"Received response from {self.server_ip}:{port} -> {data[:200] if len(data) > 200 else data}")
                client_socket.close()

                result = json.loads(data)
                logger.info(f"Login result: success={result.get('success')} via port {port}")
                self.login_result.emit(result)
                return
            except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError, json.JSONDecodeError) as e:
                last_error = e
                logger.warning(f"Login attempt failed on {self.server_ip}:{port} - {e}")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in LoginRequester on port {port}: {e}")
                break

        logger.error(f"Could not login to {self.server_ip} on ports {SOCKET_PORT_CANDIDATES}. Last error: {last_error}")
        self.login_result.emit({
            "success": False,
            "error": "Cannot connect/login to server. Please verify server is running and TCP port 12345 is open."
        })


# Connection Checker - kiá» m tra káº¿t ná» i server
class ConnectionChecker(QThread):
    """Thread Ä á»?kiá» m tra káº¿t ná» i server"""
    connection_status = Signal(str)  # 'connected' hoáº·c 'disconnected'
    
    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip
    
    def run(self):
        """Check server connectivity with detailed error handling."""
        logger.info(f"Checking connection to {self.server_ip}")

        # DNS/IP check first
        try:
            socket.getaddrinfo(self.server_ip, SOCKET_PORT_CANDIDATES[0], socket.AF_INET, socket.SOCK_STREAM)
            logger.debug(f"DNS resolution successful for {self.server_ip}")
        except socket.gaierror as e:
            logger.error(f"DNS resolution error for {self.server_ip}: {e}")
            self.connection_status.emit('disconnected')
            return

        last_error = None
        for port in SOCKET_PORT_CANDIDATES:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5)  # 5 seconds timeout

                logger.debug(f"Connecting socket to {self.server_ip}:{port}")
                client_socket.connect((self.server_ip, port))

                # Send PING
                request = {"request": "PING"}
                client_socket.send(json.dumps(request).encode('utf-8'))
                logger.debug(f"PING request sent to {self.server_ip}:{port}")

                # Wait for PONG with timeout
                client_socket.settimeout(5)
                response = client_socket.recv(1024).decode('utf-8')
                logger.debug(f"Received response from {self.server_ip}:{port}: {response}")
                client_socket.close()

                if response == "PONG":
                    logger.info(f"Connection successful to {self.server_ip}:{port}")
                    self.connection_status.emit('connected')
                    return

                last_error = RuntimeError(f"Unexpected response: {response}")
                logger.warning(f"Unexpected response from {self.server_ip}:{port}: {response}")
            except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError) as e:
                last_error = e
                logger.warning(f"Connection check failed on {self.server_ip}:{port} - {e}")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in ConnectionChecker on port {port}: {e}")
                break

        logger.error(f"Connection check failed for {self.server_ip} on ports {SOCKET_PORT_CANDIDATES}. Last error: {last_error}")
        self.connection_status.emit('disconnected')


class LoginDialog(QDialog):
    """
    Dialog Ä Ä ng nháº­p tiÃªu chuáº©n
    
    Signals:
        login_success: PhÃ¡t ra khi Ä Ä ng nháº­p thÃ nh cÃ´ng (username, user_info)
        login_failed: PhÃ¡t ra khi Ä Ä ng nháº­p tháº¥t báº¡i (error_message)
        login_cancelled: PhÃ¡t ra khi ngÆ°á» i dÃ¹ng há»§y Ä Ä ng nháº­p
    """
    
    login_success = Signal(str, dict)
    login_failed = Signal(str)
    login_cancelled = Signal()
    
    def __init__(self, parent=None, language: Optional[str] = None):
        """
        Khá» i táº¡o dialog Ä Ä ng nháº­p
        
        Args:
            parent: Widget cha
            language: NgÃ´n ngá»?('vi' hoáº·c 'zh'), náº¿u None sáº?tá»?Ä á» ng load
        """
        super().__init__(parent)
        
        # Load ngÃ´n ngá»?
        self.current_language = language or load_language()
        
        # Thiáº¿t láº­p dialog
        self.setWindowTitle(CLIENT_TEXT[self.current_language]['login_title'])
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(460, 720)
        self.setModal(True)
        
        # Thiáº¿t láº­p style
        self.setup_style()
        
        # Táº¡o giao diá» n
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        
        # Load credentials Ä Ã£ lÆ°u (náº¿u cÃ³)
        self.load_saved_credentials()
    
    def setup_style(self):
        """Thiáº¿t láº­p style cho dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #eef2ff,
                    stop: 0.5 #f8fafc,
                    stop: 1 #ecfeff
                );
            }
            QFrame#login_card {
                background: #ffffff;
                border: 1px solid #d9e2ff;
                border-radius: 18px;
            }
            QLabel {
                color: #0f172a;
                font-size: 14px;
            }
            QLabel#field_label {
                color: #334155;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#badge_label {
                color: #1d4ed8;
                font-size: 11px;
                font-weight: 700;
                background: #dbeafe;
                border-radius: 10px;
                padding: 4px 10px;
            }
            QLabel#title_label {
                color: #0f172a;
                font-size: 30px;
                font-weight: 700;
            }
            QLabel#subtitle_label {
                color: #475569;
                font-size: 14px;
            }
            QLineEdit {
                padding: 12px 14px;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                font-size: 14px;
                min-height: 22px;
                background-color: #ffffff;
                selection-background-color: #bfdbfe;
                color: #0f172a;
            }
            QLineEdit:hover {
                border-color: #94a3b8;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
            }
            QLineEdit[error="true"] {
                border: 2px solid #ef4444;
                background: #fef2f2;
            }
            QPushButton {
                padding: 11px 18px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#login_button {
                background-color: #2563eb;
                color: white;
            }
            QPushButton#login_button:hover {
                background-color: #1d4ed8;
            }
            QPushButton#login_button:pressed {
                background-color: #1e40af;
            }
            QPushButton#login_button:disabled {
                background-color: #93c5fd;
                color: #e0f2fe;
            }
            QPushButton#cancel_button {
                background-color: #e2e8f0;
                color: #334155;
            }
            QPushButton#cancel_button:hover {
                background-color: #cbd5e1;
            }
            QPushButton#cancel_button:pressed {
                background-color: #94a3b8;
            }
            QCheckBox {
                font-size: 13px;
                color: #334155;
            }
            QComboBox {
                padding: 7px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                font-size: 13px;
                background: #ffffff;
                min-width: 110px;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox:focus {
                border: 2px solid #2563eb;
            }
            QPushButton#toggle_password_button {
                background-color: #eff6ff;
                color: #1d4ed8;
                padding: 8px 12px;
                min-width: 58px;
                font-size: 12px;
                border: 1px solid #bfdbfe;
            }
            QPushButton#toggle_password_button:hover {
                background-color: #dbeafe;
            }
            QLabel#status_label {
                color: #dc2626;
                font-size: 12px;
                font-weight: 600;
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 8px 10px;
            }
            QLabel#forgot_label {
                color: #2563eb;
                font-size: 12px;
            }
        """)
    
    def create_widgets(self):
        """Táº¡o cÃ¡c widget"""
        # Language selector
        self.language_label = QLabel(CLIENT_TEXT[self.current_language]['select_language'])
        self.language_label.setObjectName("field_label")
        self.language_combo = QComboBox()
        self.language_combo.addItem(CLIENT_TEXT[self.current_language]['vietnamese'], 'vi')
        self.language_combo.addItem(CLIENT_TEXT[self.current_language]['chinese'], 'zh')
        self.language_combo.setCurrentIndex(0 if self.current_language == 'vi' else 1)
        
        self.badge_label = QLabel("SECURE ACCESS")
        self.badge_label.setObjectName("badge_label")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_label = QLabel("Project Tracking")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle_label = QLabel(CLIENT_TEXT[self.current_language]['login_title'])
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        
        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setStyleSheet("color: #e2e8f0;")
        
        # Username
        self.username_label = QLabel(CLIENT_TEXT[self.current_language]['login_username'])
        self.username_label.setObjectName("field_label")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_username_placeholder'])
        self.username_input.setClearButtonEnabled(True)
        
        # Password
        self.password_label = QLabel(CLIENT_TEXT[self.current_language]['login_password'])
        self.password_label.setObjectName("field_label")
        
        # Password input with toggle button
        self.password_layout = QHBoxLayout()
        self.password_layout.setSpacing(10)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_password_placeholder'])
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setClearButtonEnabled(True)
        
        # Toggle password visibility button
        self.toggle_password_button = QPushButton("Show")
        self.toggle_password_button.setObjectName("toggle_password_button")
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setChecked(False)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        
        self.password_layout.addWidget(self.password_input)
        self.password_layout.addWidget(self.toggle_password_button)
        
        # Server IP
        self.server_ip_label = QLabel(CLIENT_TEXT[self.current_language]['login_server_ip'])
        self.server_ip_label.setObjectName("field_label")
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText(CLIENT_TEXT[self.current_language]['login_server_ip_placeholder'])
        
        # Options
        self.remember_checkbox = QCheckBox(CLIENT_TEXT[self.current_language]['login_remember'])
        self.remember_checkbox.setChecked(True)
        
        # Forgot password link
        self.forgot_label = QLabel(f'<a href="#forgot" style="color: #2196F3; text-decoration: none;">{CLIENT_TEXT[self.current_language]["login_forgot"]}</a>')
        self.forgot_label.setObjectName("forgot_label")
        self.forgot_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.forgot_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Buttons
        self.login_button = QPushButton(CLIENT_TEXT[self.current_language]['login_button'])
        self.login_button.setObjectName("login_button")
      
        self.cancel_button = QPushButton(CLIENT_TEXT[self.current_language]['login_cancel'])
        self.cancel_button.setObjectName("cancel_button")
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        
    def setup_layout(self):
        """Thiáº¿t láº­p layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 20, 18, 20)

        self.login_card = QFrame()
        self.login_card.setObjectName("login_card")
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        card_layout.setSpacing(12)

        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        lang_layout.addWidget(self.language_label)
        lang_layout.addWidget(self.language_combo)
        card_layout.addLayout(lang_layout)

        # Title
        card_layout.addSpacing(4)
        card_layout.addWidget(self.badge_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.separator)
        
        # Username
        card_layout.addSpacing(2)
        card_layout.addWidget(self.username_label)
        card_layout.addWidget(self.username_input)
        
        # Password
        card_layout.addWidget(self.password_label)
        card_layout.addLayout(self.password_layout)
        
        # Server IP
        card_layout.addWidget(self.server_ip_label)
        card_layout.addWidget(self.server_ip_input)
        
        # Options
        card_layout.addSpacing(2)
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.forgot_label)
        card_layout.addLayout(options_layout)
        
        # Status
        card_layout.addSpacing(8)
        card_layout.addWidget(self.status_label)
        card_layout.addSpacing(8)
        
        # Buttons Ä Ä ng nháº­p vÃ  há»§y
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.cancel_button)
        card_layout.addLayout(buttons_layout)
        card_layout.addSpacing(6)

        layout.addStretch()
        layout.addWidget(self.login_card)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Káº¿t ná» i signals"""
        self.login_button.clicked.connect(self.attempt_login)
        self.cancel_button.clicked.connect(self.reject)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        self.forgot_label.linkActivated.connect(self.on_forgot_password)
    
    def toggle_password_visibility(self, checked=None):
        """Hiá» n/áº©n password"""
        if checked is None:
            # Toggle state when called from button without parameter
            checked = not self.toggle_password_button.isChecked()
            self.toggle_password_button.setChecked(checked)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle_password_button.setText("Hide" if checked else "Show")
    
    def change_language(self, index):
        """Change UI language."""
        self.current_language = self.language_combo.currentData()
        
        # Cáº­p nháº­t text
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
        
        # LÆ°u ngÃ´n ngá»?
        try:
            with open('language.txt', 'w', encoding='utf-8') as f:
                f.write(self.current_language)
        except:
            pass
    
    def load_saved_credentials(self):
        """Load saved credentials and server IP."""
        # Load credentials
        credentials = get_session_manager().load_credentials()
        if credentials:
            self.username_input.setText(credentials.get('username', ''))
            self.password_input.setText(credentials.get('password', ''))
            # Sá»?dá»¥ng remember flag Ä Ã£ lÆ°u, máº·c Ä á» nh False náº¿u khÃ´ng cÃ³
            remember_value = credentials.get('remember', False)
            # Ä áº£m báº£o giÃ¡ trá»?lÃ  boolean
            self.remember_checkbox.setChecked(bool(remember_value))
        else:
            # KhÃ´ng cÃ³ credentials, Ä á»?checkbox unchecked theo máº·c Ä á» nh
            self.remember_checkbox.setChecked(False)
        
        # Load saved IP - Æ¯U TIÃ N Tá»?FILE RIÃ NG, sau Ä Ã³ má» i tá»?session
        saved_ip = get_session_manager().load_server_ip_from_file()
        if saved_ip:
            self.server_ip_input.setText(saved_ip)
        else:
            # Fallback: thá»?tá»?session
            saved_ip = get_session_manager().get_server_ip()
            if saved_ip:
                self.server_ip_input.setText(saved_ip)
    
    def check_existing_session(self):
        """Kiá» m tra session Ä Ã£ tá» n táº¡i"""
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
        """Thá»±c hiá» n Ä Ä ng nháº­p - cÃ³ kiá» m tra káº¿t ná» i trÆ°á» c"""
        self.reset_input_style()

        # Validate
        is_valid, username, password, server_ip = self.validate_inputs()
        
        if not is_valid:
            # Kiá» m tra thiáº¿u gÃ¬ Ä á»?hiá» n thá»?lá» i chÃ­nh xÃ¡c
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
        
        # # áº¨n lá» i cÅ©
        # self.status_label.hide()
        
        # Disable controls during request
        self.set_form_enabled(False)
        self.login_button.setText(CLIENT_TEXT[self.current_language]['login_checking_connection'])
        
        # LÆ¯U THÃ NG TIN Ä á»?Sá»?Dá»¤NG SAU KHI CONNECTION CHECK XONG
        self._pending_login = {
            'username': username,
            'password': password,
            'server_ip': server_ip
        }
        
        # KIá» M TRA Káº¾T Ná» I TRÆ¯á» C
        self.connection_checker = ConnectionChecker(server_ip)
        self.connection_checker.connection_status.connect(self.on_connection_check_result)
        self.connection_checker.start()
    
    def on_connection_check_result(self, status: str):
        """Xá»?lÃ½ káº¿t quáº?kiá» m tra káº¿t ná» i"""
        if status == 'connected':
            # Káº¿t ná» i Ä Æ°á»£c, tiáº¿p tá»¥c Ä Ä ng nháº­p
            pending = self._pending_login
            self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])  # Reset text
            self.login_button.setText("Dang dang nhap...")
            
            self.login_requester = LoginRequester(
                pending['server_ip'], 
                pending['username'], 
                pending['password']
            )
            self.login_requester.login_result.connect(self.on_login_result)
            self.login_requester.start()
        else:
            # KhÃ´ng káº¿t ná» i Ä Æ°á»£c
            self.set_form_enabled(True)
            self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])
            self.show_error(CLIENT_TEXT[self.current_language]['login_connection_failed'])
    
    def on_login_result(self, result: dict):
        """Xá»?lÃ½ káº¿t quáº?Ä Ä ng nháº­p tá»?server"""
        # Re-enable button
        self.set_form_enabled(True)
        self.login_button.setText(CLIENT_TEXT[self.current_language]['login_button'])
        
        if result.get('success'):
            # Ä Ä ng nháº­p thÃ nh cÃ´ng tá»?server
            user_info = result.get('user_info', {})
            username = user_info.get('username', '')
            server_ip = self.server_ip_input.text().strip()
            remember = self.remember_checkbox.isChecked()
            password = self.password_input.text()
            
            logger.info(f"Login successful for user: {username}")
            
            # LÆ°u credentials
            session_manager.save_credentials(username, password, remember)
            
            # LÆ¯U IP VÃ O FILE RIÃ NG BIá» T (quan trá» ng!)
            session_manager.save_server_ip_to_file(server_ip)
            
            # Táº¡o session vá» i server_ip
            session_manager.create_session(username, user_info, server_ip=server_ip)
            
            # Emit success signal
            logger.info(f"Session created, IP: {server_ip}")
            self.login_success.emit(username, user_info)
            self.accept()
        else:
            # Ä Ä ng nháº­p tháº¥t báº¡i
            error_msg = result.get('error', CLIENT_TEXT[self.current_language]['login_failed_invalid'])
            logger.warning(f"Login failed: {error_msg}")
            self.show_error(error_msg)
            self.login_failed.emit(error_msg)
    
    def show_error(self, message: str):
        """Hiá» n thá»?lá» i"""
        self.status_label.setText(message)
        self.status_label.show()
        
        # Highlight invalid inputs
        self.username_input.setProperty("error", True)
        self.password_input.setProperty("error", True)
        self.server_ip_input.setProperty("error", True)
        self.refresh_input_styles()
        
        # Reset style sau 2 giÃ¢y
        QTimer.singleShot(2000, self.reset_input_style)
    
    def reset_input_style(self):
        """Reset style cá»§a input"""
        self.username_input.setProperty("error", False)
        self.password_input.setProperty("error", False)
        self.server_ip_input.setProperty("error", False)
        self.refresh_input_styles()
        self.status_label.hide()

    def refresh_input_styles(self):
        """Refresh dynamic style properties for line edits."""
        for widget in (self.username_input, self.password_input, self.server_ip_input):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def set_form_enabled(self, enabled: bool):
        """Enable/disable form controls while processing login."""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.server_ip_input.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        self.language_combo.setEnabled(enabled)
        self.toggle_password_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
    
    def on_forgot_password(self, link):
        """Xá»?lÃ½ khi click forgot password"""
        QMessageBox.information(
            self,
            CLIENT_TEXT[self.current_language]['login_title'],
            "Vui long lien he quan tri vien de lay lai mat khau."
        )
    
    def get_username(self) -> str:
        """Láº¥y username Ä Ã£ nháº­p"""
        return self.username_input.text().strip()
    
    def get_password(self) -> str:
        """Láº¥y password Ä Ã£ nháº­p"""
        return self.password_input.text()
    
    def get_server_ip(self) -> str:
        """Láº¥y server IP Ä Ã£ nháº­p"""
        return self.server_ip_input.text().strip()
    
    def is_remembered(self) -> bool:
        """Kiá» m tra cÃ³ ghi nhá»?Ä Ä ng nháº­p khÃ´ng"""
        return self.remember_checkbox.isChecked()
    
    def reject(self):
        """Há»§y Ä Ä ng nháº­p"""
        self.login_cancelled.emit()
        super().reject()


# =============================================================================
# HÃ m tiá» n Ã­ch (convenience functions)
# =============================================================================

def show_login_dialog(parent=None, language: Optional[str] = None) -> tuple:
    """
    Hiá» n dialog Ä Ä ng nháº­p vÃ  tráº?vá»?káº¿t quáº?
    
    Args:
        parent: Widget cha
        language: NgÃ´n ngá»?('vi' hoáº·c 'zh')
        
    Returns:
        (result, username, server_ip)
        - result: True náº¿u Ä Ä ng nháº­p thÃ nh cÃ´ng, False náº¿u há»§y
        - username: TÃªn Ä Ä ng nháº­p
        - server_ip: IP mÃ¡y chá»?
    """
    dialog = LoginDialog(parent, language)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return True, dialog.get_username(), dialog.get_server_ip()
    else:
        return False, "", ""
