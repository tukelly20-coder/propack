"""
New_Sales.py - Dialog tạo project mới cho Sales
Module này cung cấp giao diện để Sales tạo yêu cầu project mới
"""

import json
import socket
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QDateTimeEdit, QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QFont

from src.language_manager import language_manager


class NewSalesDialog(QDialog):
    """
    Dialog tạo project mới cho Sales
    
    Signals:
        record_created: Phát ra khi tạo thành công (record_data)
    """
    
    record_created = Signal(dict)
    
    # Urgency levels
    URGENCY_NORMAL = "normal"
    URGENCY_URGENT = "urgent"
    URGENCY_VERY_URGENT = "very_urgent"
    
    def __init__(self, parent=None, server_ip: str = None):
        super().__init__(parent)
        
        # Lấy IP từ session nếu không được truyền vào
        if server_ip is None:
            try:
                from src.session_manager import session_manager
                server_ip = session_manager.get_server_ip() or "localhost"
            except:
                server_ip = "localhost"
        
        self.server_ip = server_ip
        
        # Setup dialog
        self.setWindowTitle(language_manager.get_new_sales_text("title"))
        self.setMinimumWidth(1000)
        self.setModal(True)
        
        # Setup style
        self.setup_style()
        
        # Create widgets
        self.create_widgets()
        
        # Setup layout
        self.setup_layout()
        
        # Connect signals
        self.connect_signals()
    
    def setup_style(self):
        """Thiết lập style cho dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #F7FAFD;
            }
            QLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #C9D5E3;
                border-radius: 8px;
                font-size: 13px;
                min-height: 20px;
                background: #FFFFFF;
            }
            QLineEdit:focus {
                border-color: #4C93D6;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #C9D5E3;
                border-radius: 8px;
                font-size: 13px;
                min-height: 20px;
                background: #FFFFFF;
            }
            QComboBox:focus {
                border-color: #4C93D6;
            }
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #C8D3E0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#save_button {
                background-color: #1F7ACB;
                color: white;
                border-color: #1A6EB6;
            }
            QPushButton#save_button:hover {
                background-color: #1A6EB6;
            }
            QPushButton#cancel_button {
                background-color: #FFFFFF;
                color: #1E293B;
            }
            QPushButton#cancel_button:hover {
                background-color: #F3F7FC;
            }
            QLabel.section_title {
                font-size: 15px;
                font-weight: bold;
                color: #1F3B57;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            QLabel.required {
                color: #C2410C;
            }
        """)
    
    def create_widgets(self):
        """Tạo các widget""" 
        # Title
        self.title_label = QLabel(language_manager.get_new_sales_text("title_label"))
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        # Section: Basic Info 
        self.basic_section = QLabel(language_manager.get_new_sales_text("basic_section"))
        
        # Tracking ID (read-only, auto-generated)
        self.tracking_id_label = QLabel(language_manager.get_new_sales_text("tracking_id"))
        self.tracking_id_label.setProperty("class", "required")
        self.tracking_id_input = QLineEdit()
        self.tracking_id_input.setReadOnly(True)
        self.tracking_id_input.setPlaceholderText("...")
        self.tracking_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #F3F6FA;
                color: #64748B;
                font-weight: bold;
                border: 1px solid #C9D5E3;
            }
        """)
        
        # Created Date (read-only, auto-generated)
        self.created_date_label = QLabel(language_manager.get_new_sales_text("created_date"))
        self.created_date_input = QLineEdit()
        self.created_date_input.setReadOnly(True)
        self.created_date_input.setStyleSheet("""
            QLineEdit {
                background-color: #F3F6FA;
                color: #64748B;
                border: 1px solid #C9D5E3;
            }
        """)
        
        # Sales Name (read-only, auto-filled)
        self.sales_name_label = QLabel(language_manager.get_new_sales_text("sales_name"))
        self.sales_name_label.setProperty("class", "required")
        self.sales_name_input = QLineEdit()
        self.sales_name_input.setReadOnly(True)
        self.sales_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #F3F6FA;
                color: #64748B;
                border: 1px solid #C9D5E3;
            }
        """)
        
        # Auto-fill từ session
        self.user_id = None
        self.user_role = None
        self.user_permissions = []
        try:
            from src.session_manager import session_manager
            user_info = session_manager.get_user_info()
            if user_info:
                full_name = user_info.get('full_name', '')
                self.sales_name_input.setText(full_name)
                # Lấy user_id từ session
                self.user_id = user_info.get('user_id')
                # Lấy role và permissions
                self.user_role = user_info.get('role')
                self.user_permissions = user_info.get('permissions', [])
        except Exception as e:
            print(f"[NewSalesDialog] Error getting user info: {e}")
        
        # Section: Customer Info
        self.customer_section = QLabel(language_manager.get_new_sales_text("customer_section"))
        self.customer_section.setProperty("class", "section_title")
        
        # Customer Name (Simple LineEdit - nhập thủ công)
        self.customer_label = QLabel(language_manager.get_new_sales_text("customer"))
        self.customer_label.setProperty("class", "required")
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_customer"))
        
        # Section: Project Info
        self.project_section = QLabel(language_manager.get_new_sales_text("project_section"))
        self.project_section.setProperty("class", "section_title")
        
        # Product Name
        self.product_name_label = QLabel(language_manager.get_new_sales_text("product_name"))
        self.product_name_label.setProperty("class", "required")
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_product"))
        
        # Specifications
        self.specs_label = QLabel(language_manager.get_new_sales_text("specs"))
        self.specs_input = QLineEdit()
        self.specs_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_specs"))
        
        # Contact Person
        self.contact_label = QLabel(language_manager.get_new_sales_text("contact"))
        self.contact_label.setProperty("class", "required")
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_contact"))
        
        # Số lượng (so_luong)
        self.so_luong_label = QLabel(language_manager.get_new_sales_text("so_luong"))
        self.so_luong_input = QLineEdit()
        self.so_luong_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_so_luong"))
        
        # PO号 (Mã PO)
        self.mapo_label = QLabel(language_manager.get_new_sales_text("mapo"))
        self.mapo_input = QLineEdit()
        self.mapo_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_mapo"))
        
        # 图纸编码 (Mã bản vẽ - phương án trước khi đặt hàng)
        self.mabave_label = QLabel(language_manager.get_new_sales_text("mabave"))
        self.mabave_input = QLineEdit()
        self.mabave_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_mabave"))
        
        # 技术图纸编码 (Mã bản vẽ kỹ thuật - sau khi đặt hàng)
        self.mabavkythuat_label = QLabel(language_manager.get_new_sales_text("mabavkythuat"))
        self.mabavkythuat_input = QLineEdit()
        self.mabavkythuat_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_mabavkythuat"))
        
        # 母料号 (Mã mẹ)
        self.mame_label = QLabel(language_manager.get_new_sales_text("mame"))
        self.mame_input = QLineEdit()
        self.mame_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_mame"))
        
        # 产品类型 (Loại sản phẩm)
        self.loaisanpham_label = QLabel(language_manager.get_new_sales_text("loaisanpham"))
        self.loaisanpham_input = QLineEdit()
        self.loaisanpham_input.setPlaceholderText(language_manager.get_new_sales_text("placeholder_loaisanpham"))
        
        # Section: Urgency
        self.urgency_section = QLabel(language_manager.get_new_sales_text("urgency_section"))
        self.urgency_section.setProperty("class", "section_title")
        
        # Urgency Level
        self.urgency_label = QLabel(language_manager.get_new_sales_text("urgency"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItem(language_manager.get_new_sales_text("urgency_normal"), self.URGENCY_NORMAL)
        self.urgency_combo.addItem(language_manager.get_new_sales_text("urgency_urgent"), self.URGENCY_URGENT)
        self.urgency_combo.addItem(language_manager.get_new_sales_text("urgency_very_urgent"), self.URGENCY_VERY_URGENT)
        
        # Desired Solution Time
        self.desired_time_label = QLabel(language_manager.get_new_sales_text("desired_time"))
        self.desired_time_label.setProperty("class", "required")
        self.desired_time_input = QDateTimeEdit()
        self.desired_time_input.setCalendarPopup(True)
        self.desired_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()
        
        self.save_button = QPushButton(language_manager.get_new_sales_text("btn_save"))
        self.save_button.setObjectName("save_button")
        self.save_button.setMinimumWidth(120)
        
        self.cancel_button = QPushButton(language_manager.get_new_sales_text("btn_cancel"))
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setMinimumWidth(100)
        
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        
        # Initialize values
        self.init_values()
    
    def setup_layout(self):
        """Thiết lập layout"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        layout.addWidget(self.title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Basic Info section
        form_layout.addRow(self.tracking_id_label, self.tracking_id_input)
        form_layout.addRow(self.created_date_label, self.created_date_input)
        form_layout.addRow(self.sales_name_label, self.sales_name_input)
        
        # Customer Info section
        form_layout.addRow(self.customer_label, self.customer_input)
        
        # Project Info section
        form_layout.addRow(self.product_name_label, self.product_name_input)
        form_layout.addRow(self.specs_label, self.specs_input)
        form_layout.addRow(self.contact_label, self.contact_input)
        form_layout.addRow(self.so_luong_label, self.so_luong_input)
        form_layout.addRow(self.mapo_label, self.mapo_input)
        form_layout.addRow(self.mabave_label, self.mabave_input)
        form_layout.addRow(self.mabavkythuat_label, self.mabavkythuat_input)
        
        # Urgency section
        form_layout.addRow(self.urgency_label, self.urgency_combo)
        form_layout.addRow(self.desired_time_label, self.desired_time_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        layout.addLayout(self.buttons_layout)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Kết nối signals"""
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_record)
        self.urgency_combo.currentIndexChanged.connect(self.on_urgency_changed)
    
    def init_values(self):
        """Khởi tạo giá trị mặc định"""
        # Tracking ID format: 000001-999999
        # Tự động lấy số tiếp theo (hiển thị dạng string)
        self.tracking_id_input.setText("AUTO")
        
        # Created date: format "YYYY-MM-DD HH:MM"
        now = datetime.now()
        created_str = now.strftime("%Y-%m-%d %H:%M")
        self.created_date_input.setText(created_str)
        
        # Set default urgency
        self.urgency_combo.setCurrentIndex(0)  # Normal
        
        # Initialize user_id - KHÔNG reset nếu đã được set từ session
        if not hasattr(self, 'user_id') or self.user_id is None:
            self.user_id = None
        
        # Calculate desired time for normal urgency (now + 2 days)
        self.calculate_desired_time()
    
    def on_urgency_changed(self, index: str):
        """Xử lý khi thay đổi urgency level"""
        self.calculate_desired_time()
    
    def calculate_desired_time(self):
        """Tính toán thời gian mong muốn dựa trên urgency"""
        urgency = self.urgency_combo.currentData()
        
        now = datetime.now()
        
        if urgency == self.URGENCY_NORMAL:
            # Normal: now + 2 days
            desired = now + timedelta(days=2)
        elif urgency == self.URGENCY_URGENT:
            # Urgent: now + 24 hours
            desired = now + timedelta(hours=24)
        elif urgency == self.URGENCY_VERY_URGENT:
            # Very urgent: now + 12 hours
            desired = now + timedelta(hours=12)
        else:
            desired = now + timedelta(days=2)
        
        # Set to QDateTimeEdit
        qdatetime = QDateTime(desired.year, desired.month, desired.day, desired.hour, desired.minute, desired.second)
        self.desired_time_input.setDateTime(qdatetime)
    
    def validate(self) -> tuple:
        """
        Validate form data
        Returns: (is_valid, error_message)
        """
        # Check required fields
        customer = self.customer_input.text().strip()
        if not customer:
            return False, language_manager.get_new_sales_text("validate_customer")
        
        product_name = self.product_name_input.text().strip()
        if not product_name:
            return False, language_manager.get_new_sales_text("validate_product")
        
        contact = self.contact_input.text().strip()
        if not contact:
            return False, language_manager.get_new_sales_text("validate_contact")
        
        return True, ""
    
    def get_record_data(self) -> Dict[str, Any]:
        """
        Lấy dữ liệu từ form
        Returns: dict chứa tất cả thông tin project
        """
        # Get urgency display text
        urgency_index = self.urgency_combo.currentIndex()
        urgency_text = self.urgency_combo.itemText(urgency_index)
        urgency_level = self.urgency_combo.currentData()
        
        # Get desired time
        desired_qdatetime = self.desired_time_input.dateTime()
        desired_time = desired_qdatetime.toString("yyyy-MM-dd HH:mm")
        
        # Get current date for Created_Date
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Get customer name
        customer_name = self.customer_input.text().strip()
        
        # Build record data - dùng đúng key để khớp với bảng projects trong database
        # Lưu ý: sales_name được gán vào cột "Nhân viên kinh doanh" thay vì trường metadata riêng
        record = {
            # Tracking ID will be assigned by server
            "Tracking ID": "AUTO",
            
            # Basic Info - khớp với cột Created_Date
            "Ngày": created_date,
            "Nhân viên kinh doanh": self.sales_name_input.text().strip(),
            
            # Customer Info
            "Khách hàng": customer_name,
            
            # Project Info - đầy đủ các fields để khớp với database
            "Tên sản phẩm": self.product_name_input.text().strip(),
            "Quy cách": self.specs_input.text().strip(),
            "Người liên hệ\n(KH)": self.contact_input.text().strip(),
            "Số lượng": self.so_luong_input.text().strip(),
            "Mã PO": self.mapo_input.text().strip(),
            "Mã bản vẽ": self.mabave_input.text().strip(),
            "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": self.mabavkythuat_input.text().strip(),
            "Mã mẹ": "",
            "Loại sản phẩm": "",
            "Nhân viên thiết kế": "",
            "Tình trạng hoàn thành dự án": "",
            "Thời gian mong muốn có bản vẽ": desired_time,
            "Thời gian hoàn thành kế hoạch": "",
            
            # Urgency Info
            "urgency_level": urgency_level,
            
            # User ID - lấy từ session
            "user_id": self.user_id,
            
            # Status - is_pending='yes' = đang chờ nhận
            "is_pending": "yes"
        }
        
        return record
    
    def save_record(self):
        """Lưu record và gửi lên server"""
        # Validate
        is_valid, error_msg = self.validate()
        if not is_valid:
            QMessageBox.warning(self, language_manager.get_new_sales_text("warning"), error_msg)
            return
        
        # Get record data
        record = self.get_record_data()
        
        # Disable save button
        self.save_button.setEnabled(False)
        self.save_button.setText(language_manager.get_new_sales_text("btn_saving"))
        
        # Send to server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "ADD_SALES_RECORD",
                "record": record,
                "user_role": self.user_role,
                "user_permissions": self.user_permissions
            }
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            # Receive response
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            
            if response.get("success"):
                new_record = response.get("record", {})
                
                # Emit signal
                self.record_created.emit(new_record)
                
                QMessageBox.information(
                    self, 
                    language_manager.get_new_sales_text("success"),
                    language_manager.get_new_sales_text("save_success").format(new_record.get('Tracking ID', 'N/A'))
                )
                
                self.accept()
            else:
                error = response.get("error", "Unknown error")
                QMessageBox.critical(self, language_manager.get_new_sales_text("error"), language_manager.get_new_sales_text("save_failed").format(error))
                
        except Exception as e:
            QMessageBox.critical(self, language_manager.get_new_sales_text("error"), language_manager.get_new_sales_text("conn_error").format(e))
            print(f"[NewSalesDialog] Save error: {e}")
        finally:
            # Re-enable save button
            self.save_button.setEnabled(True)
            self.save_button.setText(language_manager.get_new_sales_text("btn_save"))
    
    def get_data(self) -> Dict[str, Any]:
        """
        Lấy dữ liệu từ form (cho tương thích với EditDialog)
        Returns: dict chứa tất cả thông tin project
        """
        return self.get_record_data()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = NewSalesDialog(server_ip="localhost")
    if dialog.exec() == QDialog.Accepted:
        print("Record created:", dialog.get_data())
