"""
New_Sales_Wizard.py - Multi-step Wizard cho phép Sales tạo dự án mới
Thiết kế theo UX best practices:
- Chia nhỏ 28 fields thành 4 bước để giảm cognitive load
- Real-time validation với error highlighting
- Progress indicator để user biết đang ở đâu
- Save draft để tránh mất dữ liệu
- Material Design 3 color scheme
"""

import json
import socket
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QDateTimeEdit, QFrame,
    QGridLayout, QWidget, QStackedWidget, QProgressBar, QCheckBox,
    QScrollArea
)
from PySide6.QtCore import Qt, QDateTime, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QIcon

from src.language_manager import language_manager


class ValidationHelper:
    """Helper class cho validation"""
    
    @staticmethod
    def validate_required(value: str, field_name: str) -> tuple:
        """Validate trường bắt buộc"""
        if not value or not value.strip():
            return False, f"{field_name} là trường bắt buộc"
        return True, ""
    
    @staticmethod
    def validate_email(value: str) -> tuple:
        """Validate email format"""
        if not value:
            return True, ""  # Optional field
        if "@" not in value or "." not in value.split("@")[-1]:
            return False, "Định dạng email không hợp lệ"
        return True, ""
    
    @staticmethod
    def validate_phone(value: str) -> tuple:
        """Validate phone number"""
        if not value:
            return True, ""  # Optional field
        digits = ''.join(c for c in value if c.isdigit())
        if len(digits) < 8 or len(digits) > 15:
            return False, "Số điện thoại phải có 8-15 chữ số"
        return True, ""
    
    @staticmethod
    def validate_number(value: str, field_name: str, min_val: int = None, max_val: int = None) -> tuple:
        """Validate số"""
        if not value:
            return True, ""  # Optional field
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False, f"{field_name} phải >= {min_val}"
            if max_val is not None and num > max_val:
                return False, f"{field_name} phải <= {max_val}"
            return True, ""
        except ValueError:
            return False, f"{field_name} phải là số nguyên"


class NewSalesWizard(QDialog):
    """
    Multi-step Wizard cho Sales tạo project mới
    
    Steps:
    1. Thông tin cơ bản (5 fields)
    2. Chi tiết kỹ thuật (8 fields)
    3. Thời gian & Độ khẩn (3 fields)
    4. Xác nhận & Gửi (review)
    
    Signals:
        record_created: Phát ra khi tạo thành công (record_data)
    """
    
    record_created = Signal(dict)
    
    URGENCY_NORMAL = "normal"
    URGENCY_URGENT = "urgent"
    URGENCY_VERY_URGENT = "very_urgent"
    
    # Design tokens - tông cơ bản trung tính
    COLORS = {
        "primary": "#1F7ACB",
        "primary_dark": "#1A6EB6",
        "primary_light": "#EAF3FC",
        "secondary": "#335E7E",
        "error": "#B42318",
        "error_light": "#FEE4E2",
        "success": "#157347",
        "success_light": "#E8F5EE",
        "warning": "#B54708",
        "warning_light": "#FFF4E5",
        "surface": "#F7FAFD",
        "surface_variant": "#E8EFF7",
        "on_surface": "#0F172A",
        "outline": "#9BAEC3",
        "outline_variant": "#D8E2EC",
    }
    
    def __init__(self, parent=None, server_ip: str = None):
        super().__init__(parent)
        
        # Get server IP from session if not provided
        if server_ip is None:
            try:
                from src.session_manager import session_manager
                server_ip = session_manager.get_server_ip() or "localhost"
            except:
                server_ip = "localhost"
        
        self.server_ip = server_ip
        
        # State
        self.current_step = 0
        self.total_steps = 4
        self.form_data = {}
        self.validation_errors = {}
        self.draft_file = "sales_draft.json"
        
        # User info
        self.user_id = None
        self.user_role = None
        self.user_permissions = []
        self._load_user_info()
        
        # Setup dialog
        self.setWindowTitle(language_manager.get_new_sales_text("title"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setModal(True)
        
        # Setup style - Material Design 3
        self.setup_style()
        
        # Create UI
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        
        # Load draft if exists
        self._load_draft()
    
    def _load_user_info(self):
        """Load user info from session"""
        try:
            from src.session_manager import session_manager
            user_info = session_manager.get_user_info()
            if user_info:
                self.user_id = user_info.get('user_id')
                self.user_role = user_info.get('role')
                self.user_permissions = user_info.get('permissions', [])
        except Exception as e:
            print(f"[NewSalesWizard] Error getting user info: {e}")
    
    def setup_style(self):
        """Thiết lập style theo Material Design 3"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.COLORS['surface']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
            
            /* Step Indicator */
            QLabel.step-title {{
                font-size: 20px;
                font-weight: 600;
                color: {self.COLORS['on_surface']};
            }}
            
            QLabel.step-subtitle {{
                font-size: 14px;
                color: #64748B;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {self.COLORS['surface_variant']};
                height: 8px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.COLORS['primary']};
                border-radius: 4px;
            }}
            
            /* Step Buttons ( circles ) */
            QLabel.step-indicator {{
                font-size: 14px;
                font-weight: 600;
                qproperty-alignment: AlignCenter;
            }}
            
            /* Form Labels */
            QLabel.form-label {{
                font-size: 14px;
                font-weight: 500;
                color: {self.COLORS['on_surface']};
                padding-bottom: 4px;
            }}
            
            QLabel.required-mark {{
                color: {self.COLORS['error']};
                font-size: 16px;
            }}
            
            QLabel.field-hint {{
                font-size: 12px;
                color: #888;
                font-style: italic;
            }}
            
            QLabel.error-text {{
                font-size: 12px;
                color: {self.COLORS['error']};
            }}
            
            /* Input Fields */
            QLineEdit, QComboBox, QDateTimeEdit {{
                padding: 12px;
                border: 1px solid {self.COLORS['outline']};
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border: 2px solid {self.COLORS['primary']};
            }}
            
            /* Valid/Invalid states */
            QLineEdit.field-valid {{
                border: 2px solid {self.COLORS['success']};
                background-color: {self.COLORS['success_light']};
            }}
            
            QLineEdit.field-invalid {{
                border: 2px solid {self.COLORS['error']};
                background-color: {self.COLORS['error_light']};
            }}
            
            /* Buttons */
            QPushButton {{
                padding: 12px 24px;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }}
            
            QPushButton#primary_button {{
                background-color: {self.COLORS['primary']};
                color: white;
            }}
            
            QPushButton#primary_button:hover {{
                background-color: {self.COLORS['primary_dark']};
            }}
            
            QPushButton#primary_button:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
            
            QPushButton#secondary_button {{
                background-color: transparent;
                color: {self.COLORS['primary']};
                border: 1px solid {self.COLORS['primary']};
            }}
            
            QPushButton#secondary_button:hover {{
                background-color: {self.COLORS['primary_light']}20;
            }}
            
            QPushButton#back_button {{
                background-color: {self.COLORS['surface_variant']};
                color: {self.COLORS['on_surface']};
            }}
            
            /* Section Headers */
            QLabel.section-header {{
                font-size: 16px;
                font-weight: 600;
                color: {self.COLORS['primary']};
                padding: 16px 0 8px 0;
            }}
            
            /* Urgency ComboBox custom */
            QComboBox#urgency_combo {{
                font-weight: 500;
            }}
        """)
    
    def create_widgets(self):
        """Tạo các widget cho wizard"""
        
        # ==================== HEADER ====================
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(25)
        
        # Step title
        self.step_title = QLabel()
        self.step_title.setProperty("class", "step-title")
        
        self.step_subtitle = QLabel()
        self.step_subtitle.setProperty("class", "step-subtitle")
        
        # Step indicators
        self.step_indicators = []
        for i in range(self.total_steps):
            indicator = QLabel(str(i + 1))
            indicator.setObjectName("step_indicator")
            indicator.setFixedSize(32, 32)
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.step_indicators.append(indicator)
        self._update_step_indicators()
        
        # ==================== STACKED WIDGET ====================
        self.stack = QStackedWidget()
        
        # Step 1: Basic Info
        step1_widget = self._create_step1_basic_info()
        self.stack.addWidget(step1_widget)
        
        # Step 2: Technical Details
        step2_widget = self._create_step2_technical()
        self.stack.addWidget(step2_widget)
        
        # Step 3: Time & Urgency
        step3_widget = self._create_step3_time_urgency()
        self.stack.addWidget(step3_widget)
        
        # Step 4: Confirmation
        step4_widget = self._create_step4_confirmation()
        self.stack.addWidget(step4_widget)
        
        # ==================== FOOTER BUTTONS ====================
        self.back_button = QPushButton("← Quay lại")
        self.back_button.setObjectName("back_button")
        self.back_button.clicked.connect(self._on_back)
        
        self.next_button = QPushButton("Tiếp tục →")
        self.next_button.setObjectName("primary_button")
        self.next_button.clicked.connect(self._on_next)
        
        self.save_draft_button = QPushButton("💾 Lưu nháp")
        self.save_draft_button.setObjectName("secondary_button")
        self.save_draft_button.clicked.connect(self._save_draft)
        
        self.cancel_button = QPushButton("Hủy")
        self.cancel_button.setObjectName("secondary_button")
        self.cancel_button.clicked.connect(self.reject)
        
        # Initialize buttons state
        self.back_button.setEnabled(False)
    
    def _update_step_indicators(self):
        """Cập nhật visual state của step indicators"""
        step_labels = [
            "1. Cơ bản",
            "2. Kỹ thuật",
            "3. Thời gian",
            "4. Xác nhận"
        ]
        
        for i, indicator in enumerate(self.step_indicators):
            if i < self.current_step:
                # Completed step - green
                indicator.setStyleSheet(f"""
                    background-color: {self.COLORS['success']};
                    color: white;
                    border-radius: 16px;
                    font-weight: 600;
                """)
                indicator.setText("✓")
            elif i == self.current_step:
                # Current step - primary
                indicator.setStyleSheet(f"""
                    background-color: {self.COLORS['primary']};
                    color: white;
                    border-radius: 16px;
                    font-weight: 600;
                """)
            else:
                # Future step - gray
                indicator.setStyleSheet(f"""
                    background-color: {self.COLORS['surface_variant']};
                    color: {self.COLORS['outline']};
                    border-radius: 16px;
                """)
        
        # Update step title
        self.step_title.setText(step_labels[self.current_step])
        
        subtitles = [
            "Nhập thông tin khách hàng và dự án",
            "Nhập chi tiết kỹ thuật và sản phẩm",
            "Chọn mức độ khẩn cấp và thời hạn",
            "Xem lại và xác nhận thông tin"
        ]
        self.step_subtitle.setText(subtitles[self.current_step])
    
    def _create_step1_basic_info(self) -> QWidget:
        """Step 1: Thông tin cơ bản"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("📋 Thông tin cơ bản")
        header.setObjectName("section-header")
        layout.addWidget(header)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Tracking ID (auto)
        self.step1_tracking_id_label = QLabel("Mã dự án")
        self.step1_tracking_id_input = QLineEdit()
        self.step1_tracking_id_input.setText("AUTO")
        self.step1_tracking_id_input.setReadOnly(True)
        self.step1_tracking_id_input.setStyleSheet("background-color: #F3F6FA; color: #64748B; border: 1px solid #C9D5E3;")
        form.addRow(self.step1_tracking_id_label, self.step1_tracking_id_input)
        
        # Ngày tạo (auto)
        self.step1_created_date_label = QLabel("Ngày tạo")
        self.step1_created_date_input = QLineEdit()
        self.step1_created_date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.step1_created_date_input.setReadOnly(True)
        self.step1_created_date_input.setStyleSheet("background-color: #F3F6FA; color: #64748B; border: 1px solid #C9D5E3;")
        form.addRow(self.step1_created_date_label, self.step1_created_date_input)
        
        # Nhân viên KD (auto từ session)
        self.step1_sales_name_label = QLabel("Nhân viên KD")
        self.step1_sales_name_input = QLineEdit()
        self.step1_sales_name_input.setReadOnly(True)
        
        # Auto-fill từ session
        try:
            from src.session_manager import session_manager
            user_info = session_manager.get_user_info()
            if user_info:
                self.step1_sales_name_input.setText(user_info.get('full_name', ''))
        except:
            pass
        
        self.step1_sales_name_input.setStyleSheet("background-color: #F3F6FA; color: #64748B; border: 1px solid #C9D5E3;")
        form.addRow(self.step1_sales_name_label, self.step1_sales_name_input)
        
        # Khách hàng (REQUIRED)
        self.step1_customer_label = QLabel("Khách hàng")
        self.step1_customer_input = QLineEdit()
        self.step1_customer_input.setPlaceholderText("Nhập tên khách hàng")
        self.step1_customer_input.textChanged.connect(lambda: self._validate_field_realtime('customer'))
        self.step1_customer_error = QLabel()
        self.step1_customer_error.setObjectName("error-text")
        self.step1_customer_error.setVisible(False)
        
        customer_layout = QVBoxLayout()
        customer_layout.addWidget(self.step1_customer_input)
        customer_layout.addWidget(self.step1_customer_error)
        form.addRow(self.step1_customer_label, customer_layout)
        
        # Tên sản phẩm (REQUIRED)
        self.step1_product_label = QLabel("Tên sản phẩm")
        self.step1_product_input = QLineEdit()
        self.step1_product_input.setPlaceholderText("Nhập tên sản phẩm")
        self.step1_product_input.textChanged.connect(lambda: self._validate_field_realtime('product_name'))
        self.step1_product_error = QLabel()
        self.step1_product_error.setObjectName("error-text")
        self.step1_product_error.setVisible(False)
        
        product_layout = QVBoxLayout()
        product_layout.addWidget(self.step1_product_input)
        product_layout.addWidget(self.step1_product_error)
        form.addRow(self.step1_product_label, product_layout)
        
        # Người liên hệ (REQUIRED)
        self.step1_contact_label = QLabel("Người liên hệ")
        self.step1_contact_input = QLineEdit()
        self.step1_contact_input.setPlaceholderText("Tên người liên hệ")
        self.step1_contact_input.textChanged.connect(lambda: self._validate_field_realtime('contact'))
        self.step1_contact_error = QLabel()
        self.step1_contact_error.setObjectName("error-text")
        self.step1_contact_error.setVisible(False)
        
        contact_layout = QVBoxLayout()
        contact_layout.addWidget(self.step1_contact_input)
        contact_layout.addWidget(self.step1_contact_error)
        form.addRow(self.step1_contact_label, contact_layout)
        
        layout.addLayout(form)
        
        # Info hint
        hint = QLabel("💡 Các trường có dấu * là bắt buộc")
        hint.setObjectName("field-hint")
        layout.addWidget(hint)
        
        layout.addStretch()
        return widget
    
    def _create_step2_technical(self) -> QWidget:
        """Step 2: Chi tiết kỹ thuật"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("🔧 Chi tiết kỹ thuật")
        header.setObjectName("section-header")
        layout.addWidget(header)
        
        # Form - 2 columns
        form = QFormLayout()
        form.setSpacing(12)
        
        # Quy cách
        self.step2_specs_label = QLabel("Quy cách")
        self.step2_specs_input = QLineEdit()
        self.step2_specs_input.setPlaceholderText("Kích thước, vật liệu, màu sắc...")
        form.addRow(self.step2_specs_label, self.step2_specs_input)
        
        # Số lượng
        self.step2_quantity_label = QLabel("Số lượng")
        self.step2_quantity_input = QLineEdit()
        self.step2_quantity_input.setPlaceholderText("Số lượng (chỉ nhập số)")
        self.step2_quantity_input.textChanged.connect(lambda: self._validate_field_realtime('quantity'))
        self.step2_quantity_error = QLabel()
        self.step2_quantity_error.setObjectName("error-text")
        self.step2_quantity_error.setVisible(False)
        
        qty_layout = QVBoxLayout()
        qty_layout.addWidget(self.step2_quantity_input)
        qty_layout.addWidget(self.step2_quantity_error)
        form.addRow(self.step2_quantity_label, qty_layout)
        
        # Mã PO
        self.step2_po_label = QLabel("Mã PO")
        self.step2_po_input = QLineEdit()
        self.step2_po_input.setPlaceholderText("Mã Purchase Order (nếu có)")
        form.addRow(self.step2_po_label, self.step2_po_input)
        
        # Mã bản vẽ (phương án)
        self.step2_drawing_label = QLabel("Mã bản vẽ phương án")
        self.step2_drawing_input = QLineEdit()
        self.step2_drawing_input.setPlaceholderText("Mã bản vẽ trước khi đặt hàng")
        form.addRow(self.step2_drawing_label, self.step2_drawing_input)
        
        # Mã bản vẽ kỹ thuật
        self.step2_tech_drawing_label = QLabel("Mã bản vẽ kỹ thuật")
        self.step2_tech_drawing_input = QLineEdit()
        self.step2_tech_drawing_input.setPlaceholderText("Mã bản vẽ sau khi đặt hàng")
        form.addRow(self.step2_tech_drawing_label, self.step2_tech_drawing_input)
        
        # Mã mẹ
        self.step2_parent_label = QLabel("Mã mẹ")
        self.step2_parent_input = QLineEdit()
        self.step2_parent_input.setPlaceholderText("Mã thành phẩm cha (nếu có)")
        form.addRow(self.step2_parent_label, self.step2_parent_input)
        
        # Loại sản phẩm
        self.step2_product_type_label = QLabel("Loại sản phẩm")
        self.step2_product_type_combo = QComboBox()
        self.step2_product_type_combo.addItem("-- Chọn loại sản phẩm --", "")
        self.step2_product_type_combo.addItem("SJT - Bản vẽ tách chi tiết", "SJT散件图")
        self.step2_product_type_combo.addItem("WLJ - Giá đựng vật liệu", "WLJ物料架")
        self.step2_product_type_combo.addItem("ZZC - Xe trung chuyển", "ZZC周转车")
        self.step2_product_type_combo.addItem("GZT - Bàn thao tác", "GZT工作台")
        self.step2_product_type_combo.addItem("WCP - Phòng sạch", "WCP无尘棚")
        self.step2_product_type_combo.addItem("LSX - Băng tải", "LSX流水线")
        self.step2_product_type_combo.addItem("ZWJ - Băng tải chuyển hướng", "ZWJ转弯机")
        self.step2_product_type_combo.addItem("GZL - Cải tạo", "GZL改造类")
        self.step2_product_type_combo.addItem("BSX - Băng chuyền xích", "BSX倍速线")
        self.step2_product_type_combo.addItem("WLL - Hàng rào", "WLL围栏类")
        self.step2_product_type_combo.addItem("GTX - Băng chuyền con lăn", "GTX滚筒线")
        self.step2_product_type_combo.addItem("ZHT - Bản vẽ mặt bằng", "ZHT展会图")
        self.step2_product_type_combo.addItem("LHX - Băng chuyền lão hóa", "LHX老化线")
        form.addRow(self.step2_product_type_label, self.step2_product_type_combo)
        
        layout.addLayout(form)
        
        layout.addStretch()
        return widget
    
    def _create_step3_time_urgency(self) -> QWidget:
        """Step 3: Thời gian & Độ khẩn"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("⏰ Thời gian & Độ khẩn")
        header.setObjectName("section-header")
        layout.addWidget(header)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Độ khẩn
        self.step3_urgency_label = QLabel("Mức độ khẩn cấp")
        self.step3_urgency_combo = QComboBox()
        self.step3_urgency_combo.setObjectName("urgency_combo")
        self.step3_urgency_combo.addItem("📘 Bình thường - 2 ngày", self.URGENCY_NORMAL)
        self.step3_urgency_combo.addItem("⚠️ Khẩn - 24 giờ", self.URGENCY_URGENT)
        self.step3_urgency_combo.addItem("🔴 Rất khẩn - 12 giờ", self.URGENCY_VERY_URGENT)
        self.step3_urgency_combo.currentIndexChanged.connect(self._on_urgency_changed)
        form.addRow(self.step3_urgency_label, self.step3_urgency_combo)
        
        # Thời gian mong muốn
        self.step3_desired_time_label = QLabel("Thời gian mong muốn")
        self.step3_desired_time_input = QDateTimeEdit()
        self.step3_desired_time_input.setCalendarPopup(True)
        self.step3_desired_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        # Set default based on urgency
        self._calculate_desired_time()
        
        form.addRow(self.step3_desired_time_label, self.step3_desired_time_input)
        
        # Auto-calculation hint
        hint = QLabel()
        hint.setObjectName("field-hint")
        hint.setText("⏱️ Hệ thống sẽ tự động tính thời gian dựa trên mức độ khẩn cấp đã chọn")
        form.addRow("", hint)
        
        layout.addLayout(form)
        
        # Urgency explanation
        urgency_frame = QFrame()
        urgency_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['surface_variant']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        urgency_layout = QVBoxLayout(urgency_frame)
        
        urgency_title = QLabel("📋 Hướng dẫn chọn mức độ khẩn cấp:")
        urgency_title.setStyleSheet("font-weight: 600;")
        urgency_layout.addWidget(urgency_title)
        
        urgency_layout.addWidget(QLabel("🟢 <b>Bình thường:</b> Dự án thông thường, deadline 2 ngày"))
        urgency_layout.addWidget(QLabel("🟡 <b>Khẩn:</b> Cần ưu tiên xử lý, deadline 24 giờ"))
        urgency_layout.addWidget(QLabel("🔴 <b>Rất khẩn:</b> Khẩn cấp cao, deadline 12 giờ"))
        
        layout.addWidget(urgency_frame)
        
        layout.addStretch()
        return widget
    
    def _create_step4_confirmation(self) -> QWidget:
        """Step 4: Xác nhận"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("✅ Xác nhận thông tin")
        header.setObjectName("section-header")
        layout.addWidget(header)
        
        # Review form
        self.review_label = QLabel("Vui lòng xem lại thông tin trước khi gửi:")
        layout.addWidget(self.review_label)
        
        # Scroll area for review
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        self.review_content = QWidget()
        self.review_layout = QVBoxLayout(self.review_content)
        
        scroll.setWidget(self.review_content)
        layout.addWidget(scroll)
        
        # Confirmation checkbox
        self.confirm_checkbox = QCheckBox("Tôi xác nhận thông tin dự án là chính xác")
        self.confirm_checkbox.stateChanged.connect(self._on_confirm_changed)
        layout.addWidget(self.confirm_checkbox)
        
        layout.addStretch()
        return widget
    
    def setup_layout(self):
        """Thiết lập layout chính"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Progress section
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        
        for indicator in self.step_indicators:
            progress_layout.addWidget(indicator)
        
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)
        
        # Title section
        title_layout = QVBoxLayout()
        title_layout.addWidget(self.step_title)
        title_layout.addWidget(self.step_subtitle)
        title_layout.setSpacing(4)
        main_layout.addLayout(title_layout)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {self.COLORS['outline_variant']};")
        main_layout.addWidget(sep)
        
        # Step content
        main_layout.addWidget(self.stack, 1)
        
        # Footer buttons
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.cancel_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_draft_button)
        footer_layout.addWidget(self.back_button)
        footer_layout.addWidget(self.next_button)
        
        main_layout.addLayout(footer_layout)
    
    def connect_signals(self):
        """Kết nối signals"""
        pass
    
    def _validate_field_realtime(self, field_name: str):
        """Real-time validation cho field"""
        is_valid = False
        error_msg = ""
        
        if field_name == 'customer':
            value = self.step1_customer_input.text()
            is_valid, error_msg = ValidationHelper.validate_required(value, "Khách hàng")
            if is_valid:
                self.step1_customer_input.setProperty("class", "field-valid")
                self.step1_customer_error.setVisible(False)
            else:
                self.step1_customer_input.setProperty("class", "field-invalid")
                self.step1_customer_error.setText(error_msg)
                self.step1_customer_error.setVisible(True)
        
        elif field_name == 'product_name':
            value = self.step1_product_input.text()
            is_valid, error_msg = ValidationHelper.validate_required(value, "Tên sản phẩm")
            if is_valid:
                self.step1_product_input.setProperty("class", "field-valid")
                self.step1_product_error.setVisible(False)
            else:
                self.step1_product_input.setProperty("class", "field-invalid")
                self.step1_product_error.setText(error_msg)
                self.step1_product_error.setVisible(True)
        
        elif field_name == 'contact':
            value = self.step1_contact_input.text()
            is_valid, error_msg = ValidationHelper.validate_required(value, "Người liên hệ")
            if is_valid:
                self.step1_contact_input.setProperty("class", "field-valid")
                self.step1_contact_error.setVisible(False)
            else:
                self.step1_contact_input.setProperty("class", "field-invalid")
                self.step1_contact_error.setText(error_msg)
                self.step1_contact_error.setVisible(True)
        
        elif field_name == 'quantity':
            value = self.step2_quantity_input.text()
            is_valid, error_msg = ValidationHelper.validate_number(value, "Số lượng", 1)
            if is_valid:
                self.step2_quantity_input.setProperty("class", "field-valid")
                self.step2_quantity_error.setVisible(False)
            else:
                self.step2_quantity_input.setProperty("class", "field-invalid")
                self.step2_quantity_error.setText(error_msg)
                self.step2_quantity_error.setVisible(True)
        
        # Force style update
        self.step1_customer_input.style().unpolish(self.step1_customer_input)
        self.step1_customer_input.style().polish(self.step1_customer_input)
        
        self.step1_product_input.style().unpolish(self.step1_product_input)
        self.step1_product_input.style().polish(self.step1_product_input)
        
        self.step1_contact_input.style().unpolish(self.step1_contact_input)
        self.step1_contact_input.style().polish(self.step1_contact_input)
        
        if self.step2_quantity_input.text():
            self.step2_quantity_input.style().unpolish(self.step2_quantity_input)
            self.step2_quantity_input.style().polish(self.step2_quantity_input)
    
    def _validate_current_step(self) -> bool:
        """Validate tất cả fields trong step hiện tại"""
        self.validation_errors = {}
        
        if self.current_step == 0:
            # Step 1: Basic Info
            customer = self.step1_customer_input.text().strip()
            if not customer:
                self.validation_errors['customer'] = "Khách hàng là trường bắt buộc"
                self.step1_customer_input.setProperty("class", "field-invalid")
                self.step1_customer_error.setText("Khách hàng là trường bắt buộc")
                self.step1_customer_error.setVisible(True)
            
            product = self.step1_product_input.text().strip()
            if not product:
                self.validation_errors['product_name'] = "Tên sản phẩm là trường bắt buộc"
                self.step1_product_input.setProperty("class", "field-invalid")
                self.step1_product_error.setText("Tên sản phẩm là trường bắt buộc")
                self.step1_product_error.setVisible(True)
            
            contact = self.step1_contact_input.text().strip()
            if not contact:
                self.validation_errors['contact'] = "Người liên hệ là trường bắt buộc"
                self.step1_contact_input.setProperty("class", "field-invalid")
                self.step1_contact_error.setText("Người liên hệ là trường bắt buộc")
                self.step1_contact_error.setVisible(True)
            
            return len(self.validation_errors) == 0
        
        elif self.current_step == 3:
            # Step 4: Confirmation
            if not self.confirm_checkbox.isChecked():
                self.validation_errors['confirm'] = "Bạn phải xác nhận thông tin trước khi gửi"
                QMessageBox.warning(
                    self, 
                    "⚠️ Xác nhận", 
                    "Vui lòng xác nhận thông tin dự án là chính xác bằng cách tích vào ô bên dưới."
                )
                return False
        
        return True
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Thu thập tất cả dữ liệu từ form"""
        # Get urgency display text
        urgency_index = self.step3_urgency_combo.currentIndex()
        urgency_text = self.step3_urgency_combo.itemText(urgency_index)
        urgency_level = self.step3_urgency_combo.currentData()
        
        # Get desired time
        desired_qdatetime = self.step3_desired_time_input.dateTime()
        desired_time = desired_qdatetime.toString("yyyy-MM-dd HH:mm")
        
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return {
            # Basic Info (Step 1)
            "Tracking ID": "AUTO",
            "Ngày": created_date,
            "Nhân viên kinh doanh": self.step1_sales_name_input.text().strip(),
            "Khách hàng": self.step1_customer_input.text().strip(),
            "Tên sản phẩm": self.step1_product_input.text().strip(),
            "Người liên hệ\n(KH)": self.step1_contact_input.text().strip(),
            
            # Technical (Step 2)
            "Quy cách": self.step2_specs_input.text().strip(),
            "Số lượng": self.step2_quantity_input.text().strip(),
            "Mã PO": self.step2_po_input.text().strip(),
            "Mã bản vẽ": self.step2_drawing_input.text().strip(),
            "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": self.step2_tech_drawing_input.text().strip(),
            "Mã mẹ": self.step2_parent_input.text().strip(),
            "Loại sản phẩm": self.step2_product_type_combo.currentData(),
            
            # Time & Urgency (Step 3)
            "urgency_level": urgency_level,
            "Thời gian mong muốn có bản vẽ": desired_time,
            
            # Metadata
            "user_id": self.user_id,
            "is_pending": "yes"
        }
    
    def _update_review(self):
        """Cập nhật nội dung review ở step 4"""
        # Clear existing
        while self.review_layout.count():
            item = self.review_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        data = self._collect_form_data()
        
        # Group fields by section
        sections = [
            ("📋 Thông tin cơ bản", [
                ("Mã dự án", data.get("Tracking ID", "-")),
                ("Ngày tạo", data.get("Ngày", "-")),
                ("Nhân viên KD", data.get("Nhân viên kinh doanh", "-")),
                ("Khách hàng", data.get("Khách hàng", "-")),
                ("Tên sản phẩm", data.get("Tên sản phẩm", "-")),
                ("Người liên hệ", data.get("Người liên hệ\n(KH)", "-")),
            ]),
            ("🔧 Chi tiết kỹ thuật", [
                ("Quy cách", data.get("Quy cách", "-")),
                ("Số lượng", data.get("Số lượng", "-")),
                ("Mã PO", data.get("Mã PO", "-")),
                ("Mã bản vẽ", data.get("Mã bản vẽ", "-")),
                ("Mã bản vẽ KT", data.get("Mã bản vẽ kỹ thuật (sau khi đặt hàng)", "-")),
                ("Mã mẹ", data.get("Mã mẹ", "-")),
                ("Loại sản phẩm", data.get("Loại sản phẩm", "-")),
            ]),
            ("⏰ Thời gian & Độ khẩn", [
                ("Mức độ khẩn cấp", self.step3_urgency_combo.currentText()),
                ("Thời gian mong muốn", data.get("Thời gian mong muốn có bản vẽ", "-")),
            ]),
        ]
        
        for section_title, fields in sections:
            section_label = QLabel(section_title)
            section_label.setStyleSheet(f"""
                font-size: 16px;
                font-weight: 600;
                color: {self.COLORS['primary']};
                padding: 8px 0;
            """)
            self.review_layout.addWidget(section_label)
            
            for label, value in fields:
                row = QHBoxLayout()
                row.setSpacing(8)
                
                field_label = QLabel(f"  {label}:")
                field_label.setStyleSheet("color: #64748B; min-width: 150px;")
                field_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                field_value = QLabel(value if value else "-")
                field_value.setStyleSheet("font-weight: 500; color: #1E293B;")
                
                row.addWidget(field_label)
                row.addWidget(field_value, 1)
                
                self.review_layout.addLayout(row)
            
            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"background-color: {self.COLORS['outline_variant']}; margin: 8px 0;")
            self.review_layout.addWidget(sep)
    
    def _on_urgency_changed(self, index: int):
        """Xử lý khi thay đổi urgency"""
        self._calculate_desired_time()
    
    def _calculate_desired_time(self):
        """Tính toán thời gian mong muốn dựa trên urgency"""
        urgency = self.step3_urgency_combo.currentData()
        
        now = datetime.now()
        
        if urgency == self.URGENCY_NORMAL:
            desired = now + timedelta(days=2)
        elif urgency == self.URGENCY_URGENT:
            desired = now + timedelta(hours=24)
        elif urgency == self.URGENCY_VERY_URGENT:
            desired = now + timedelta(hours=12)
        else:
            desired = now + timedelta(days=2)
        
        qdatetime = QDateTime(desired.year, desired.month, desired.day, desired.hour, desired.minute)
        self.step3_desired_time_input.setDateTime(qdatetime)
    
    def _on_confirm_changed(self, state: int):
        """Xử lý khi checkbox xác nhận thay đổi"""
        self.next_button.setEnabled(state == Qt.CheckState.Checked)
        
        if state == Qt.CheckState.Checked:
            self.next_button.setText("✓ Gửi dự án")
        else:
            self.next_button.setText("Tiếp tục →")
    
    def _on_back(self):
        """Xử lý nút Quay lại"""
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_indicators()
            self._update_buttons()
            
            # Update review if going to step 4
            if self.current_step == 3:
                self._update_review()
    
    def _on_next(self):
        """Xử lý nút Tiếp tục"""
        # Validate current step
        if not self._validate_current_step():
            return
        
        # If on last step, save
        if self.current_step == self.total_steps - 1:
            self._save_record()
            return
        
        # Move to next step
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_indicators()
            self._update_buttons()
            
            # Update review if going to step 4
            if self.current_step == 3:
                self._update_review()
    
    def _update_buttons(self):
        """Cập nhật trạng thái buttons"""
        # Back button
        self.back_button.setEnabled(self.current_step > 0)
        
        # Next button
        if self.current_step == self.total_steps - 1:
            self.next_button.setText("✓ Gửi dự án")
            self.next_button.setEnabled(self.confirm_checkbox.isChecked())
        else:
            self.next_button.setText("Tiếp tục →")
            self.next_button.setEnabled(True)
        
        # Progress bar
        progress = int((self.current_step + 1) / self.total_steps * 100)
        self.progress_bar.setValue(progress)
    
    def _save_draft(self):
        """Lưu draft vào file"""
        try:
            data = self._collect_form_data()
            data['saved_at'] = datetime.now().isoformat()
            
            with open(self.draft_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self,
                "💾 Lưu nháp thành công",
                "Dự án đã được lưu nháp.\nBạn có thể tiếp tục sau."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "❌ Lỗi lưu nháp",
                f"Không thể lưu nháp: {str(e)}"
            )
    
    def _load_draft(self):
        """Load draft đã lưu"""
        if not os.path.exists(self.draft_file):
            return
        
        try:
            with open(self.draft_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            reply = QMessageBox.question(
                self,
                "📂 Tìm thấy bản nháp",
                f"Tìm thấy bản nháp được lưu ngày: {data.get('saved_at', 'N/A')}\n\nBạn có muốn tiếp tục không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._populate_from_draft(data)
            else:
                # Delete draft
                os.remove(self.draft_file)
        except Exception as e:
            print(f"[NewSalesWizard] Error loading draft: {e}")
    
    def _populate_from_draft(self, data: Dict):
        """Điền dữ liệu từ draft"""
        # Step 1
        self.step1_customer_input.setText(data.get("Khách hàng", ""))
        self.step1_product_input.setText(data.get("Tên sản phẩm", ""))
        self.step1_contact_input.setText(data.get("Người liên hệ\n(KH)", ""))
        
        # Step 2
        self.step2_specs_input.setText(data.get("Quy cách", ""))
        self.step2_quantity_input.setText(data.get("Số lượng", ""))
        self.step2_po_input.setText(data.get("Mã PO", ""))
        self.step2_drawing_input.setText(data.get("Mã bản vẽ", ""))
        self.step2_tech_drawing_input.setText(data.get("Mã bản vẽ kỹ thuật (sau khi đặt hàng)", ""))
        self.step2_parent_input.setText(data.get("Mã mẹ", ""))
        
        product_type = data.get("Loại sản phẩm", "")
        index = self.step2_product_type_combo.findData(product_type)
        if index >= 0:
            self.step2_product_type_combo.setCurrentIndex(index)
        
        # Step 3
        urgency = data.get("urgency_level", self.URGENCY_NORMAL)
        index = self.step3_urgency_combo.findData(urgency)
        if index >= 0:
            self.step3_urgency_combo.setCurrentIndex(index)
    
    def _save_record(self):
        """Lưu record và gửi lên server"""
        # Get record data
        record = self._collect_form_data()
        
        # Disable save button
        self.next_button.setEnabled(False)
        self.next_button.setText("Đang gửi...")
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)
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
                
                # Delete draft if exists
                if os.path.exists(self.draft_file):
                    try:
                        os.remove(self.draft_file)
                    except:
                        pass
                
                # Emit signal
                self.record_created.emit(new_record)
                
                tracking_id = new_record.get('Tracking ID', 'N/A')
                QMessageBox.information(
                    self, 
                    "✅ Thành công",
                    f"Đã tạo dự án mới thành công!\n\nMã dự án: {tracking_id}"
                )
                
                self.accept()
            else:
                error = response.get("error", "Unknown error")
                QMessageBox.critical(
                    self, 
                    "❌ Lỗi",
                    f"Không thể lưu dự án:\n\n{error}"
                )
                self.next_button.setEnabled(True)
                self.next_button.setText("✓ Gửi dự án")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "❌ Lỗi kết nối",
                f"Không thể kết nối server:\n\n{str(e)}"
            )
            self.next_button.setEnabled(True)
            self.next_button.setText("✓ Gửi dự án")
    
    def get_data(self) -> Dict[str, Any]:
        """Lấy dữ liệu từ form (cho tương thích với EditDialog)"""
        return self._collect_form_data()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = NewSalesWizard(server_ip="localhost")
    if dialog.exec() == QDialog.Accepted:
        print("Record created:", dialog.get_data())
