"""
UserManagement.py - Module quản lý users cho Admin
Module này cung cấp giao diện đ�?admin quản lý tài khoản người dùng
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
    """Thread đ�?load users t�?server"""
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
    """Dialog thêm/sửa user"""
    
    user_saved = Signal(dict)
    
    def __init__(self, parent=None, server_ip: str = "localhost", edit_user: Optional[Dict] = None):
        super().__init__(parent)
        
        self.server_ip = server_ip
        self.edit_user = edit_user
        self.setWindowTitle("Sửa người dùng / 编辑用户" if edit_user else "Thêm người dùng / 添加用户")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QFormLayout()
        layout.setSpacing(10)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Mật khẩu / 密码:", self.password_input)
        
        # Full Name
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("H�?và tên")
        layout.addRow("H�?tên / 姓名:", self.fullname_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItem("Sales", "sales")
        self.role_combo.addItem("Engineer", "engineer")
        self.role_combo.addItem("Admin", "admin")
        self.role_combo.addItem("IT", "IT")
        self.role_combo.addItem("Pur", "Pur")
        layout.addRow("Vai trò / 角色:", self.role_combo)
        
        # Employee ID
        self.employee_id_input = QLineEdit()
        self.employee_id_input.setPlaceholderText("Mã nhân viên (cho Engineer)")
        layout.addRow("Mã NV / 工号:", self.employee_id_input)
        
        # Department
        self.department_combo = QComboBox()
        self.department_combo.addItem("Sales", "Sales")
        self.department_combo.addItem("Engineering", "Engineering")
        self.department_combo.addItem("IT", "IT")
        self.department_combo.addItem("Purchasing", "Purchasing")
        self.department_combo.addItem("Administration", "Administration")
        layout.addRow("Phòng ban / 部门:", self.department_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Hoạt động / 激�?, "active")
        self.status_combo.addItem("Khóa / 锁定", "locked")
        layout.addRow("Trạng thái / 状�?", self.status_combo)
        
        # Permissions Group
        permissions_group = QGroupBox("Quyền hạn / 权限")
        permissions_layout = QVBoxLayout()
        
        # Permission checkboxes
        self.permission_checkboxes = {}
        
        # create_code
        self.create_code_cb = QCheckBox("Tạo mã / 创建编码")
        self.create_code_cb.setToolTip("Quyền tạo mã code mới")
        self.permission_checkboxes['create_code'] = self.create_code_cb
        permissions_layout.addWidget(self.create_code_cb)
        
        # view_history
        self.view_history_cb = QCheckBox("Xem lịch s�?/ 查看历史")
        self.view_history_cb.setToolTip("Quyền xem lịch s�?tạo code")
        self.permission_checkboxes['view_history'] = self.view_history_cb
        permissions_layout.addWidget(self.view_history_cb)
        
        # delete_history
        self.delete_history_cb = QCheckBox("Xóa lịch s�?/ 删除历史")
        self.delete_history_cb.setToolTip("Quyền xóa lịch s�?tạo code")
        self.permission_checkboxes['delete_history'] = self.delete_history_cb
        permissions_layout.addWidget(self.delete_history_cb)
        
        # export
        self.export_cb = QCheckBox("Xuất d�?liệu / 导出数据")
        self.export_cb.setToolTip("Quyền xuất d�?liệu")
        self.permission_checkboxes['export'] = self.export_cb
        permissions_layout.addWidget(self.export_cb)
        
        # admin
        self.admin_cb = QCheckBox("Quản tr�?/ 管理�?)
        self.admin_cb.setToolTip("Quyền quản tr�?h�?thống")
        self.permission_checkboxes['admin'] = self.admin_cb
        permissions_layout.addWidget(self.admin_cb)
        
        # job_accept
        self.job_accept_cb = QCheckBox("Nhận Job / 接收工作")
        self.job_accept_cb.setToolTip("Quyền nhận job t�?danh sách ch�?)
        self.permission_checkboxes['job_accept'] = self.job_accept_cb
        permissions_layout.addWidget(self.job_accept_cb)
        
        permissions_group.setLayout(permissions_layout)
        layout.addRow("", permissions_group)
        
        # Connect role change to update default permissions
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_btn = QPushButton("💾 Lưu / 保存")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self.save)
        
        self.cancel_btn = QPushButton("�?Hủy / 取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addRow("", buttons_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Load d�?liệu user cần sửa"""
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
        """Cập nhật permissions khi role thay đổi (ch�?khi thêm mới)"""
        if self.edit_user is None:  # Only for new users
            role = self.role_combo.currentData()
            default_perms = self.get_default_permissions(role)
            self.set_permissions(default_perms)
    
    def get_default_permissions(self, role: str) -> List[str]:
        """Lấy permissions mặc định theo role"""
        defaults = {
            'sales': ['create_code', 'view_history', 'export'],
            'engineer': ['create_code', 'view_history'],
            'admin': ['create_code', 'view_history', 'delete_history', 'export', 'admin'],
            'IT': ['create_code', 'view_history', 'delete_history', 'export', 'admin'],
            'Pur': ['view_history', 'export']
        }
        return defaults.get(role, ['view_history'])
    
    def set_permissions(self, permissions: List[str]):
        """Set trạng thái các checkbox"""
        for perm, cb in self.permission_checkboxes.items():
            cb.setChecked(perm in permissions)
    
    def get_selected_permissions(self) -> List[str]:
        """Lấy danh sách permissions được chọn"""
        return [perm for perm, cb in self.permission_checkboxes.items() if cb.isChecked()]
    
    def validate(self) -> tuple:
        """Validate d�?liệu"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        fullname = self.fullname_input.text().strip()
        status = self.status_combo.currentData()
        
        if not username:
            return False, "Vui lòng nhập username"
        
        if not password:
            return False, "Vui lòng nhập mật khẩu"
        
        if not fullname:
            return False, "Vui lòng nhập h�?tên"
        
        # Kiểm tra nếu tạo mới user có status = 'locked'
        if self.edit_user is None and status == 'locked':
            return False, "Không th�?tạo user mới với trạng thái b�?khóa. Vui lòng chọn 'Hoạt động'."
        
        return True, ""
    
    def save(self):
        """Lưu user"""
        is_valid, error = self.validate()
        if not is_valid:
            QMessageBox.warning(self, "Lỗi", error)
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
    Widget quản lý users cho Admin
    """
    
    def __init__(self, parent=None, server_ip: str = "localhost"):
        super().__init__(parent)
        
        self.server_ip = server_ip
        self.users: List[Dict] = []
        
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("👥 QUẢN LÝ NGƯỜI DÙNG / 用户管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Info
        self.info_label = QLabel("Ch�?Admin và IT mới có quyền quản lý người dùng.")
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.info_label)
        
        # Table
        self.table = HorizontalScrollTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "Username",
            "H�?tên / 姓名",
            "Vai trò / 角色",
            "Mã NV / 工号",
            "Phòng ban / 部门",
            "Trạng thái / 状�?,
            "Đăng nhập cuối / 最后登�?,
            "Ngày tạo / 创建日期",
            "Tạo Code",
            "Xem History",
            "Xóa History",
            "Export",
            "Admin",
            "Nhận Job"
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
        self.table.setColumnWidth(13, 70)  # Nhận Job
        
        # Style
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                alternate-background-color: #f9f9f9;
                background-color: white;
            }
            QTableWidget::item:selected {
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
        
        layout.addWidget(self.table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Làm mới / 刷新")
        self.refresh_btn.clicked.connect(self.load_users)
        buttons_layout.addWidget(self.refresh_btn)
        
        self.add_btn = QPushButton("�?Thêm / 添加")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.add_btn.clicked.connect(self.add_user)
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Sửa / 编辑")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_user)
        buttons_layout.addWidget(self.edit_btn)
        
        self.lock_btn = QPushButton("🔒 Khóa/M�?/ 锁定/解锁")
        self.lock_btn.clicked.connect(self.toggle_lock)
        buttons_layout.addWidget(self.lock_btn)
        
        self.delete_btn = QPushButton("🗑�?Xóa / 删除")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_user)
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_users(self):
        """Load users t�?server"""
        self.users_loader = UsersLoader(self.server_ip)
        self.users_loader.users_loaded.connect(self.on_users_loaded)
        self.users_loader.error_occurred.connect(self.on_users_error)
        self.users_loader.start()
        
        self.info_label.setText("�?Đang tải... / 加载�?..")
    
    def on_users_loaded(self, users: List[Dict]):
        """X�?lý khi load users thành công"""
        self.users = users
        self.populate_table()
        self.info_label.setText(f"📊 Tổng s�?người dùng: {len(users)}")
    
    def on_users_error(self, error: str):
        """X�?lý khi load users lỗi"""
        QMessageBox.warning(self, "Lỗi", f"Không th�?tải danh sách users: {error}")
        self.info_label.setText("�?Lỗi khi tải d�?liệu")
    
    def populate_table(self):
        """Hiển th�?users lên table"""
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
            status_display = "🔴 Khóa" if status == 'locked' else "🟢 Hoạt động"
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
            item_code = QTableWidgetItem("�? if 'create_code' in permissions else "�?)
            item_code.setBackground(QColor(200, 255, 200) if 'create_code' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 8, item_code)
            
            # view_history
            item_history = QTableWidgetItem("�? if 'view_history' in permissions else "�?)
            item_history.setBackground(QColor(200, 255, 200) if 'view_history' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 9, item_history)
            
            # delete_history
            item_delete = QTableWidgetItem("�? if 'delete_history' in permissions else "�?)
            item_delete.setBackground(QColor(200, 255, 200) if 'delete_history' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 10, item_delete)
            
            # export
            item_export = QTableWidgetItem("�? if 'export' in permissions else "�?)
            item_export.setBackground(QColor(200, 255, 200) if 'export' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 11, item_export)
            
            # admin
            item_admin = QTableWidgetItem("�? if 'admin' in permissions else "�?)
            item_admin.setBackground(QColor(200, 255, 200) if 'admin' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 12, item_admin)
            
            # job_accept
            item_job_accept = QTableWidgetItem("�? if 'job_accept' in permissions else "�?)
            item_job_accept.setBackground(QColor(200, 255, 200) if 'job_accept' in permissions else QColor(255, 200, 200))
            self.table.setItem(row, 13, item_job_accept)
        
        self.table.resizeColumnsToContents()
    
    def add_user(self):
        """Thêm user mới"""
        dialog = AddUserDialog(self, self.server_ip)
        dialog.user_saved.connect(lambda data: self.on_user_saved(data, None))
        dialog.exec()
    
    def edit_user(self):
        """Sửa user được chọn"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một người dùng đ�?sửa.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        
        dialog = AddUserDialog(self, self.server_ip, edit_user=user)
        dialog.user_saved.connect(lambda data: self.on_user_saved(data, user))
        dialog.exec()
    
    def on_user_saved(self, user_data: Dict, edit_user: Optional[Dict] = None):
        """X�?lý khi user được lưu (thêm/sửa)"""
        # Gửi request lên server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            # Kiểm tra là add hay edit
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
                QMessageBox.information(self, "Thành công", "Đã lưu người dùng thành công!")
                self.load_users()
            else:
                error = response.get("error", "Unknown error")
                QMessageBox.critical(self, "Lỗi", f"Không th�?lưu: {error}")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi kết nối: {e}")
    
    def toggle_lock(self):
        """Khóa/M�?khóa user"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một người dùng.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        user_id = user.get('user_id')
        current_status = user.get('status', 'active')
        
        new_status = 'active' if current_status == 'locked' else 'locked'
        action_text = "m�?khóa" if new_status == 'active' else "khóa"
        
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có chắc muốn {action_text} user '{user.get('username')}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Gửi request
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
                QMessageBox.information(self, "Thành công", f"Đã {action_text} user!")
                self.load_users()
            else:
                QMessageBox.critical(self, "Lỗi", "Không th�?cập nhật trạng thái.")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi kết nối: {e}")
    
    def delete_user(self):
        """Xóa user"""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một người dùng đ�?xóa.")
            return
        
        row = selected[0].row()
        if row >= len(self.users):
            return
        
        user = self.users[row]
        user_id = user.get('user_id')
        username = user.get('username')
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa user '{username}' không?\n\nHành động này không th�?hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Gửi request
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
                QMessageBox.information(self, "Thành công", "Đã xóa user!")
                self.load_users()
            else:
                QMessageBox.critical(self, "Lỗi", "Không th�?xóa user.")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi kết nối: {e}")
    
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
