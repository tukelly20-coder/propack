"""
UserManagement.py - Module quáº£n lÃ½ users cho Admin
Module nÃ y cung cáº¥p giao diá» n Ä á»?admin quáº£n lÃ½ tÃ i khoáº£n ngÆ°á» i dÃ¹ng
"""

import json
import socket
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QComboBox, QDateTimeEdit, QGroupBox, QInputDialog, QLineEdit,
    QCheckBox, QScrollArea, QVBoxLayout
)
from PySide6.QtCore import Qt, QDateTime, Signal, QThread
from PySide6.QtGui import QFont, QColor

# Import HorizontalScrollTableWidget for Shift+wheel horizontal scroll
try:
    from src.models import HorizontalScrollTableWidget
except ImportError:
    from models import HorizontalScrollTableWidget


class UsersLoader(QThread):
    """Thread Ä á»?load users tá»?server"""
    users_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, server_ip: str):
        super().__init__()
        self.server_ip = server_ip
    
    def run(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, 8001))
            
            request = {"request": "GET_USERS"}
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            users = json.loads(data.decode('utf-8'))
            self.users_loaded.emit(users)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class AddUserDialog(QDialog):
    """Dialog thÃªm/sá»­a user"""
    
    user_saved = Signal(dict)
    
    def __init__(self, parent=None, server_ip: str = "localhost", edit_user: Optional[Dict] = None):
        super().__init__(parent)
        
        self.server_ip = server_ip
        self.edit_user = edit_user
        self.setWindowTitle("Sá»­a ngÆ°á» i dÃ¹ng / ç¼ è¾ ç ¨æ ·" if edit_user else "ThÃªm ngÆ°á» i dÃ¹ng / æ·»å  ç ¨æ ·")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Thiáº¿t láº­p giao diá» n"""
        self.setStyleSheet("""
            QDialog {
                background: #F7FAFD;
            }
            QGroupBox {
                border: 1px solid #D8E0EA;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: #FFFFFF;
                font-weight: 600;
                color: #334155;
            }
            QLabel {
                color: #334155;
                font-weight: 600;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                border: 1px solid #C9D5E3;
                border-radius: 8px;
                background: #FFFFFF;
                padding: 6px 8px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
                border-color: #4C93D6;
            }
            QCheckBox {
                color: #1F2937;
                spacing: 6px;
            }
            QPushButton {
                background: #FFFFFF;
                color: #1E293B;
                border: 1px solid #C8D3E0;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F3F7FC;
                border-color: #99B9DA;
            }
            QPushButton#saveButton {
                background: #1F7ACB;
                color: #FFFFFF;
                border-color: #1A6EB6;
            }
            QPushButton#saveButton:hover {
                background: #1A6EB6;
            }
        """)

        layout = QFormLayout()
        layout.setSpacing(10)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("TÃªn Ä Ä ng nháº­p")
        layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Máº­t kháº©u")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Máº­t kháº©u / å¯ ç  :", self.password_input)
        
        # Full Name
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Há»?vÃ  tÃªn")
        layout.addRow("Há»?tÃªn / å§ å  :", self.fullname_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItem("Sales", "sales")
        self.role_combo.addItem("Engineer", "engineer")
        self.role_combo.addItem("Admin", "admin")
        self.role_combo.addItem("IT", "IT")
        self.role_combo.addItem("Pur", "Pur")
        layout.addRow("Vai trÃ² / è§ è ²:", self.role_combo)
        
        # Employee ID
        self.employee_id_input = QLineEdit()
        self.employee_id_input.setPlaceholderText("MÃ£ nhÃ¢n viÃªn (cho Engineer)")
        layout.addRow("MÃ£ NV / å·¥å ·:", self.employee_id_input)
        
        # Department
        self.department_combo = QComboBox()
        self.department_combo.addItem("Sales", "Sales")
        self.department_combo.addItem("Engineering", "Engineering")
        self.department_combo.addItem("IT", "IT")
        self.department_combo.addItem("Purchasing", "Purchasing")
        self.department_combo.addItem("Administration", "Administration")
        layout.addRow("PhÃ²ng ban / é ¨é ¨:", self.department_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Active", "active")
        self.status_combo.addItem("KhÃ³a / é  å® ", "locked")
        layout.addRow("Tráº¡ng thÃ¡i / ç ¶æ ?", self.status_combo)
        
        # Permissions Group
        permissions_group = QGroupBox("Quyá» n háº¡n / æ  é  ")
        permissions_layout = QVBoxLayout()
        
        # Permission checkboxes
        self.permission_checkboxes = {}
        
        # create_code
        self.create_code_cb = QCheckBox("Táº¡o mÃ£ / å  å»ºç¼ ç  ")
        self.create_code_cb.setToolTip("Quyá» n táº¡o mÃ£ code má» i")
        self.permission_checkboxes['create_code'] = self.create_code_cb
        permissions_layout.addWidget(self.create_code_cb)
        
        # view_history
        self.view_history_cb = QCheckBox("Xem lá» ch sá»?/ æ ¥ç  å  å ²")
        self.view_history_cb.setToolTip("Quyá» n xem lá» ch sá»?táº¡o code")
        self.permission_checkboxes['view_history'] = self.view_history_cb
        permissions_layout.addWidget(self.view_history_cb)
        
        # delete_history
        self.delete_history_cb = QCheckBox("XÃ³a lá» ch sá»?/ å  é ¤å  å ²")
        self.delete_history_cb.setToolTip("Quyá» n xÃ³a lá» ch sá»?táº¡o code")
        self.permission_checkboxes['delete_history'] = self.delete_history_cb
        permissions_layout.addWidget(self.delete_history_cb)
        
        # export
        self.export_cb = QCheckBox("Xuáº¥t dá»?liá» u / å¯¼å ºæ °æ ®")
        self.export_cb.setToolTip("Quyá» n xuáº¥t dá»?liá» u")
        self.permission_checkboxes['export'] = self.export_cb
        permissions_layout.addWidget(self.export_cb)
        
        # admin
        self.admin_cb = QCheckBox("Admin")
        self.admin_cb.setToolTip("Quyá» n quáº£n trá»?há»?thá» ng")
        self.permission_checkboxes['admin'] = self.admin_cb
        permissions_layout.addWidget(self.admin_cb)
        
        # job_accept
        self.job_accept_cb = QCheckBox("Nháº­n Job / æ ¥æ ¶å·¥ä½ ")
        self.job_accept_cb.setToolTip("Quyen nhan job tu danh sach cho")
        self.permission_checkboxes['job_accept'] = self.job_accept_cb
        permissions_layout.addWidget(self.job_accept_cb)
        
        permissions_group.setLayout(permissions_layout)
        layout.addRow("", permissions_group)
        
        # Connect role change to update default permissions
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_btn = QPushButton("ð  ¾ LÆ°u / ä¿ å­ ")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.save)
        
        self.cancel_btn = QPushButton("â ?Há»§y / å  æ¶ ")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addRow("", buttons_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Load dá»?liá» u user cáº§n sá»­a"""
        if self.edit_user:
            self.username_input.setText(self.edit_user.get('username', ''))
            self.username_input.setEnabled(False)  # Can't change username
            self.password_input.setText(self.edit_user.get('passwords', ''))
            self.fullname_input.setText(self.edit_user.get('full_name', ''))
            
            # Set role
            role = self.edit_user.get('role', 'sales')
            index = self.role_combo.findData(role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
            
            self.employee_id_input.setText(self.edit_user.get('employee_id', '') or '')
            
            # Set department
            dept = self.edit_user.get('department', 'Sales')
            index = self.department_combo.findText(dept)
            if index >= 0:
                self.department_combo.setCurrentIndex(index)
            
            # Set status
            status = self.edit_user.get('status', 'active')
            index = self.status_combo.findData(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            # Load permissions
            permissions = self.edit_user.get('permissions', [])
            self.set_permissions(permissions)
    
    def on_role_changed(self):
        """Cáº­p nháº­t permissions khi role thay Ä á» i (chá»?khi thÃªm má» i)"""
        if self.edit_user is None:  # Only for new users
            role = self.role_combo.currentData()
            default_perms = self.get_default_permissions(role)
            self.set_permissions(default_perms)
    
    def get_default_permissions(self, role: str) -> List[str]:
        """Láº¥y permissions máº·c Ä á» nh theo role"""
        defaults = {
            'sales': ['create_code', 'view_history', 'export'],
            'engineer': ['create_code', 'view_history'],
            'admin': ['create_code', 'view_history', 'delete_history', 'export', 'admin'],
            'IT': ['create_code', 'view_history', 'delete_history', 'export', 'admin'],
            'Pur': ['view_history', 'export']
        }
        return defaults.get(role, ['view_history'])
    
    def set_permissions(self, permissions: List[str]):
        """Set tráº¡ng thÃ¡i cÃ¡c checkbox"""
        for perm, cb in self.permission_checkboxes.items():
            cb.setChecked(perm in permissions)
    
    def get_selected_permissions(self) -> List[str]:
        """Láº¥y danh sÃ¡ch permissions Ä Æ°á»£c chá» n"""
        return [perm for perm, cb in self.permission_checkboxes.items() if cb.isChecked()]
    
    def validate(self) -> tuple:
        """Validate dá»?liá» u"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        fullname = self.fullname_input.text().strip()
        status = self.status_combo.currentData()
        
        if not username:
            return False, "Vui lÃ²ng nháº­p username"
        
        if not password:
            return False, "Vui lÃ²ng nháº­p máº­t kháº©u"
        
        if not fullname:
            return False, "Vui lÃ²ng nháº­p há»?tÃªn"
        
        # Kiá» m tra náº¿u táº¡o má» i user cÃ³ status = 'locked'
        if self.edit_user is None and status == 'locked':
            return False, "KhÃ´ng thá»?táº¡o user má» i vá» i tráº¡ng thÃ¡i bá»?khÃ³a. Vui lÃ²ng chá» n 'Hoáº¡t Ä á» ng'."
        
        return True, ""
    
    def save(self):
        """LÆ°u user"""
        is_valid, error = self.validate()
        if not is_valid:
            QMessageBox.warning(self, "Lá» i", error)
            return
        
        user_data = {
            'username': self.username_input.text().strip(),
            'passwords': self.password_input.text().strip(),
            'full_name': self.fullname_input.text().strip(),
            'role': self.role_combo.currentData(),
            'employee_id': self.employee_id_input.text().strip() or None,
            'department': self.department_combo.currentText(),
            'status': self.status_combo.currentData(),
            'permissions': self.get_selected_permissions()
        }
        
        # Emit signal
        self.user_saved.emit(user_data)
        self.accept()


class UserManagement(QWidget):
    """
    Widget quáº£n lÃ½ users cho Admin
    """
    
    def __init__(self, parent=None, server_ip: str = "localhost"):
        super().__init__(parent)
        
        self.server_ip = server_ip
        self.users: List[Dict] = []
        
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        """Thiáº¿t láº­p giao diá» n"""
        self.setStyleSheet("""
            QWidget {
                background: #F7FAFD;
                color: #1E293B;
            }
            QLabel {
                color: #334155;
            }
            QTableWidget {
                gridline-color: transparent;
                alternate-background-color: #F8FAFC;
                background-color: #FFFFFF;
                border: 1px solid #D8E0EA;
                border-radius: 8px;
            }
            QTableWidget::item:selected {
                background-color: #D9ECFF;
                color: #0F172A;
            }
            QHeaderView::section {
                background-color: #EEF3F7;
                color: #22313F;
                padding: 7px;
                border: 1px solid #D4DEE8;
                font-weight: bold;
            }
            QPushButton {
                background: #FFFFFF;
                color: #1E293B;
                border: 1px solid #C8D3E0;
                border-radius: 8px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F3F7FC;
                border-color: #99B9DA;
            }
            QPushButton#primaryButton {
                background: #1F7ACB;
                color: #FFFFFF;
                border-color: #1A6EB6;
            }
            QPushButton#primaryButton:hover {
                background: #1A6EB6;
            }
            QPushButton#dangerButton {
                background: #B42318;
                color: #FFFFFF;
                border-color: #991B1B;
            }
            QPushButton#dangerButton:hover {
                background: #991B1B;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("ð  ¥ QUáº¢N LÃ  NGÆ¯á» I DÃ NG / ç ¨æ ·ç®¡ç  ")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Info
        self.info_label = QLabel("Chá»?Admin vÃ  IT má» i cÃ³ quyá» n quáº£n lÃ½ ngÆ°á» i dÃ¹ng.")
        self.info_label.setStyleSheet("color: #475569; font-size: 12px; background: #EEF4FB; border: 1px solid #D5E3F2; border-radius: 8px; padding: 8px;")
        layout.addWidget(self.info_label)
        
        # Table
        self.table = HorizontalScrollTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "Username",
            "Full Name",
            "Role",
            "Employee ID",
            "Department",
            "Trang thai",
            "Last Login",
            "Created At",
            "Táº¡o Code",
            "Xem History",
            "XÃ³a History",
            "Export",
            "Admin",
            "Nháº­n Job"
        ])
        
        # Setup table
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Column widths
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 110)
        # Permission columns are smaller
        self.table.setColumnWidth(8, 60)
        self.table.setColumnWidth(9, 70)
        self.table.setColumnWidth(10, 70)
        self.table.setColumnWidth(11, 55)
        self.table.setColumnWidth(12, 55)
        self.table.setColumnWidth(13, 70)  # Nháº­n Job
        
        layout.addWidget(self.table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("ð    LÃ m má» i / å ·æ °")
        self.refresh_btn.clicked.connect(self.load_users)
        buttons_layout.addWidget(self.refresh_btn)
        
        self.add_btn = QPushButton("â ?ThÃªm / æ·»å  ")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self.add_user)
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("â  ï¸  Sá»­a / ç¼ è¾ ")
        self.edit_btn.clicked.connect(self.edit_user)
        buttons_layout.addWidget(self.edit_btn)
        
        self.lock_btn = QPushButton("ð    KhÃ³a/Má»?/ é  å® /è§£é  ")
        self.lock_btn.clicked.connect(self.toggle_lock)
        buttons_layout.addWidget(self.lock_btn)
        
        self.delete_btn = QPushButton("ð   ï¸?XÃ³a / å  é ¤")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self.delete_user)
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_users(self):
        """Load users tá»?server"""
        self.users_loader = UsersLoader(self.server_ip)
        self.users_loader.users_loaded.connect(self.on_users_loaded)
        self.users_loader.error_occurred.connect(self.on_users_error)
        self.users_loader.start()
        
        self.info_label.setText("â ?Ä ang táº£i... / å  è½½ä¸?..")
    
    def on_users_loaded(self, users: List[Dict]):
        """Xá»?lÃ½ khi load users thÃ nh cÃ´ng"""
        self.users = users
        self.populate_table()
        self.info_label.setText(f"ð    Tá» ng sá»?ngÆ°á» i dÃ¹ng: {len(users)}")
    
    def on_users_error(self, error: str):
        """Xá»?lÃ½ khi load users lá» i"""
        QMessageBox.warning(self, "Lá» i", f"KhÃ´ng thá»?táº£i danh sÃ¡ch users: {error}")
        self.info_label.setText("â ?Lá» i khi táº£i dá»?liá» u")
    
    def populate_table(self):
        """Hiá» n thá»?users lÃªn table"""
        self.table.setRowCount(0)
        
        for user in self.users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Username
            self.table.setItem(row, 0, QTableWidgetItem(user.get('username', '-')))
            
            # Full name
            self.table.setItem(row, 1, QTableWidgetItem(user.get('full_name', '-')))
            
            # Role
            role = user.get('role', 'sales')
            role_display = {
                'sales': 'Sales',
                'engineer': 'Engineer',
                'admin': 'Admin',
                'IT': 'IT',
                'Pur': 'Pur'
            }.get(role, role)
            self.table.setItem(row, 2, QTableWidgetItem(str(role_display)))
            
            # Employee ID
            emp_id = user.get('employee_id', '-')
            self.table.setItem(row, 3, QTableWidgetItem(emp_id if emp_id else '-'))
            
            # Department
            self.table.setItem(row, 4, QTableWidgetItem(user.get('department', '-')))
            
            # Status
            status = user.get('status', 'active')
            status_display = "ð  ´ KhÃ³a" if status == 'locked' else "ð  ¢ Hoáº¡t Ä á» ng"
            item_status = QTableWidgetItem(status_display)
            if status == 'locked':
                item_status.setBackground(QColor(255, 200, 200))
            else:
                item_status.setBackground(QColor(200, 255, 200))
            self.table.setItem(row, 5, item_status)
            
            # Last login
            last_login = user.get('last_login', '-')
            if last_login and last_login != '-':
                try:
                    dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    last_login = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            self.table.setItem(row, 6, QTableWidgetItem(last_login))
            
            # User created at
            user_created = user.get('user_created_at', '-')
            if user_created and user_created != '-':
                try:
                    dt = datetime.fromisoformat(user_created.replace('Z', '+00:00'))
                    user_created = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            self.table.setItem(row, 7, QTableWidgetItem(user_created))
            
            # Permissions
            permissions = user.get('permissions', [])
            
            # create_code
            item_code = QTableWidgetItem("Yes" if 'create_code' in permissions else "No")
            item_code.setBackground(QColor(200, 255, 200) if 'create_code' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 8, item_code)
            
            # view_history
            item_history = QTableWidgetItem("Yes" if 'view_history' in permissions else "No")
            item_history.setBackground(QColor(200, 255, 200) if 'view_history' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 9, item_history)
            
            # delete_history
            item_delete = QTableWidgetItem("Yes" if 'delete_history' in permissions else "No")
            item_delete.setBackground(QColor(200, 255, 200) if 'delete_history' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 10, item_delete)
            
            # export
            item_export = QTableWidgetItem("Yes" if 'export' in permissions else "No")
            item_export.setBackground(QColor(200, 255, 200) if 'export' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 11, item_export)
            
            # admin
            item_admin = QTableWidgetItem("Yes" if 'admin' in permissions else "No")
            item_admin.setBackground(QColor(200, 255, 200) if 'admin' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 12, item_admin)
            
            # job_accept
            item_job_accept = QTableWidgetItem("Yes" if 'job_accept' in permissions else "No")
            item_job_accept.setBackground(QColor(200, 255, 200) if 'job_accept' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 13, item_job_accept)
        
        self.table.resizeColumnsToContents()
    
    def add_user(self):
        """ThÃªm user má» i"""
        dialog = AddUserDialog(self, self.server_ip)
        dialog.user_saved.connect(lambda data: self.on_user_saved(data, None))
        dialog.exec()
    
    def edit_user(self):
        """Sá»­a user Ä Æ°á»£c chá» n"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cáº£nh bÃ¡o", "Vui lÃ²ng chá» n má» t ngÆ°á» i dÃ¹ng Ä á»?sá»­a.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        
        dialog = AddUserDialog(self, self.server_ip, edit_user=user)
        dialog.user_saved.connect(lambda data: self.on_user_saved(data, user))
        dialog.exec()
    
    def on_user_saved(self, user_data: Dict, edit_user: Optional[Dict] = None):
        """Xá»?lÃ½ khi user Ä Æ°á»£c lÆ°u (thÃªm/sá»­a)"""
        # Gá»­i request lÃªn server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            # Kiá» m tra lÃ  add hay edit
            is_edit = edit_user is not None
            
            if is_edit:
                request = {
                    "request": "UPDATE_USER",
                    "user_id": edit_user.get('user_id'),
                    "user_data": user_data
                }
            else:
                request = {
                    "request": "ADD_USER",
                    "user_data": user_data
                }
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            
            if response.get("success"):
                QMessageBox.information(self, "ThÃ nh cÃ´ng", "Ä Ã£ lÆ°u ngÆ°á» i dÃ¹ng thÃ nh cÃ´ng!")
                self.load_users()
            else:
                error = response.get("error", "Unknown error")
                QMessageBox.critical(self, "Lá» i", f"KhÃ´ng thá»?lÆ°u: {error}")
                
        except Exception as e:
            QMessageBox.critical(self, "Lá» i", f"Lá» i káº¿t ná» i: {e}")
    
    def toggle_lock(self):
        """KhÃ³a/Má»?khÃ³a user"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cáº£nh bÃ¡o", "Vui lÃ²ng chá» n má» t ngÆ°á» i dÃ¹ng.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        user_id = user.get('user_id')
        current_status = user.get('status', 'active')
        
        new_status = 'active' if current_status == 'locked' else 'locked'
        action_text = "má»?khÃ³a" if new_status == 'active' else "khÃ³a"
        
        reply = QMessageBox.question(
            self, "XÃ¡c nháº­n",
            f"Báº¡n cÃ³ cháº¯c muá» n {action_text} user '{user.get('username')}' khÃ´ng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Gá»­i request
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "UPDATE_USER",
                "user_id": user_id,
                "user_data": {"status": new_status}
            }
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            
            if response.get("success"):
                QMessageBox.information(self, "ThÃ nh cÃ´ng", f"Ä Ã£ {action_text} user!")
                self.load_users()
            else:
                QMessageBox.critical(self, "Lá» i", "KhÃ´ng thá»?cáº­p nháº­t tráº¡ng thÃ¡i.")
                
        except Exception as e:
            QMessageBox.critical(self, "Lá» i", f"Lá» i káº¿t ná» i: {e}")
    
    def delete_user(self):
        """XÃ³a user"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cáº£nh bÃ¡o", "Vui lÃ²ng chá» n má» t ngÆ°á» i dÃ¹ng Ä á»?xÃ³a.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        user_id = user.get('user_id')
        username = user.get('username')
        
        reply = QMessageBox.question(
            self, "XÃ¡c nháº­n xÃ³a",
            f"Báº¡n cÃ³ cháº¯c muá» n xÃ³a user '{username}' khÃ´ng?\n\nHÃ nh Ä á» ng nÃ y khÃ´ng thá»?hoÃ n tÃ¡c!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Gá»­i request
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "DELETE_USER",
                "user_id": user_id
            }
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            
            if response.get("success"):
                QMessageBox.information(self, "ThÃ nh cÃ´ng", "Ä Ã£ xÃ³a user!")
                self.load_users()
            else:
                QMessageBox.critical(self, "Lá» i", "KhÃ´ng thá»?xÃ³a user.")
                
        except Exception as e:
            QMessageBox.critical(self, "Lá» i", f"Lá» i káº¿t ná» i: {e}")
    
    def refresh(self):
        """Refresh users"""
        self.load_users()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = UserManagement(server_ip="localhost")
    widget.show()
    
    sys.exit(app.exec())
