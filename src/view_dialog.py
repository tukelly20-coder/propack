"""
ViewDialog - Dialog xem chi tiết bản ghi (hỗ trợ chỉnh sửa trực tiếp)
Phiên bản hoàn thiện - Hiển thị tất cả thông tin bao gồm metadata
Tách từ Project_Tracking.py
Hỗ trợ đa ngôn ngữ (Tiếng Việt / Tiếng Trung)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QHBoxLayout, QPushButton, QDialogButtonBox,
    QLineEdit, QSpinBox, QMessageBox,
    QWidget, QTabWidget, QCheckBox, QDateTimeEdit,
    QComboBox, QCompleter
)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QIntValidator

try:
    from src.language_manager import language_manager
except ImportError:
    from language_manager import language_manager

import json
import os


class ViewDialog(QDialog):
    """Dialog xem chi tiết bản ghi (hỗ trợ chỉnh sửa trực tiếp) - Phiên bản hỗ trợ đa ngôn ngữ"""
    
    def __init__(self, parent=None, record=None):
        super().__init__(parent)
        
        # Lấy texts từ language_manager
        texts = language_manager.get_all_ui_texts()
        self.setWindowTitle(texts["dialog_view_title"])
        self.setMinimumWidth(800)
        self.setMinimumHeight(650)
        
        self.parent_window = parent
        self.record = record
        self.texts = texts
        
        # Trạng thái chế độ chỉnh sửa
        self.is_edit_mode = False
        
        # Lưu dữ liệu gốc để hủy khi cần
        self.original_record = dict(record) if record else {}
        
        # Khởi tạo widgets dictionary
        self.widgets = {}
        
        # Lưu reference đến các combobox để cập nhật completer
        self.comboboxes = {}
        
        # Load dữ liệu dropdown từ DB.json
        self.dropdown_data = self.load_dropdown_data()
        
        # Mapping từ widget key sang view_label key trong language_manager
        self.label_key_map = {
            "Tracking ID": "view_label_tracking_id",
            "Ngày": "view_label_date",
            "Khách hàng": "view_label_customer",
            "Nhân viên kinh doanh": "view_label_sales",
            "Người liên hệ\n(KH)": "view_label_contact",
            "Mã PO": "view_label_po",
            "Tên sản phẩm": "view_label_product_name",
            "Quy cách": "view_label_specs",
            "Số lượng": "view_label_quantity",
            "Loại sản phẩm": "view_label_product_type",
            "Mã bản vẽ": "view_label_drawing_code",
            "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": "view_label_drawing_code_tech",
            "Mã mẹ": "view_label_mother_code",
            "Nhân viên thiết kế": "view_label_designer",
            "Thời gian mong muốn có bản vẽ": "view_label_desired_time",
            "Thời gian hoàn thành kế hoạch": "view_label_complete_time",
            "Tình trạng hoàn thành dự án": "view_label_completion_status",
            "user_id": "view_label_user_id",
            "is_pending": "view_label_pending_status",
            "accepted_by": "view_label_accepted_by",
            "accepted_at": "view_label_accepted_at",
            "urgency_level": "view_label_urgency_level",
            # Key mapping cho Project Tracking headers
            "Mã bản vẽ phương án (mã trước khi đặt hàng)": "view_label_drawing_code",
            "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": "view_label_drawing_code_tech",
            "Mã thành phẩm (Mã mẹ)": "view_label_mother_code",
            "Kỹ sư thiết kế": "view_label_designer",
            "Hạng mục": "view_label_product_type",
        }
        
        # Layout chính
        main_layout = QVBoxLayout(self)
        
        # Tạo tab widget
        self.tab_widget = QTabWidget()
        
        # Tạo các tab
        self.create_basic_info_tab()
        self.create_product_info_tab()
        self.create_drawing_info_tab()
        self.create_progress_info_tab()
        self.create_metadata_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Buttons - Tạo button layout
        self.button_layout = QHBoxLayout()
        
        # Nút Chỉnh sửa (ban đầu)
        self.edit_btn = QPushButton(self.texts["action_edit"])
        self.edit_btn.clicked.connect(self.enable_edit_mode)
        self.button_layout.addWidget(self.edit_btn)
        
        self.button_layout.addStretch()
        
        # Nút Lưu (ban đầu ẩn)
        self.save_btn = QPushButton(self.texts.get("action_save", "Lưu"))
        self.save_btn.clicked.connect(self.save_record)
        self.save_btn.setVisible(False)
        self.button_layout.addWidget(self.save_btn)
        
        # Nút Hủy (ban đầu ẩn)
        self.cancel_btn = QPushButton(self.texts.get("action_cancel", "Hủy"))
        self.cancel_btn.clicked.connect(self.cancel_edit)
        self.cancel_btn.setVisible(False)
        self.button_layout.addWidget(self.cancel_btn)
        
        # Button box OK (ban đầu hiện)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_layout.addWidget(self.button_box)
        
        main_layout.addLayout(self.button_layout)
        
        # Điền dữ liệu
        if record:
            self.populate_data(record)
    
    def load_dropdown_data(self):
        """Load dữ liệu dropdown từ DB.json"""
        data = {
            "Khách hàng": set(),
            "Nhân viên kinh doanh": set(),
            "Tên sản phẩm": set(),
            "Quy cách": set(),
            "Loại sản phẩm": set(),
            "Nhân viên thiết kế": set(),
            "Tình trạng hoàn thành dự án": set(),
        }
        
        # Tìm file DB.json
        db_paths = ["DB.json", "src/DB.json", "../DB.json"]
        db_path = None
        
        for path in db_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if db_path is None:
            return data
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
                
                for record in records:
                    # Mapping cột DB.json sang tên trường
                    if "Khách hàng" in record and record["Khách hàng"]:
                        data["Khách hàng"].add(record["Khách hàng"])
                    if "Nhân viên kinh doanh" in record and record["Nhân viên kinh doanh"]:
                        data["Nhân viên kinh doanh"].add(record["Nhân viên kinh doanh"])
                    if "Tên sản phẩm" in record and record["Tên sản phẩm"]:
                        data["Tên sản phẩm"].add(record["Tên sản phẩm"])
                    if "Quy cách" in record and record["Quy cách"]:
                        data["Quy cách"].add(record["Quy cách"])
                    if "Loại sản phẩm" in record and record["Loại sản phẩm"]:
                        data["Loại sản phẩm"].add(record["Loại sản phẩm"])
                    if "Nhân viên thiết kế" in record and record["Nhân viên thiết kế"]:
                        data["Nhân viên thiết kế"].add(record["Nhân viên thiết kế"])
                    if "Tình trạng hoàn thành dự án" in record and record["Tình trạng hoàn thành dự án"]:
                        data["Tình trạng hoàn thành dự án"].add(record["Tình trạng hoàn thành dự án"])
                
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"Lỗi khi đọc DB.json: {e}")
        
        # Chuyển set thành list và sort
        for key in data:
            str_list = [str(item) for item in data[key]]
            data[key] = sorted(str_list)
        
        return data
    
    def populate_combobox_from_db(self, combobox, field_key):
        """Điền dữ liệu vào combobox từ DB.json"""
        if field_key in self.dropdown_data:
            items = self.dropdown_data[field_key]
            if items:
                for item in items:
                    combobox.addItem(item)
    
    def _get_label(self, widget_key):
        """Lấy label từ language_manager dựa trên widget key"""
        label_key = self.label_key_map.get(widget_key, "")
        if label_key and label_key in self.texts:
            return self.texts[label_key]
        # Fallback: sử dụng widget key làm label
        return widget_key.replace("\n", " ") + ":"
    
    def create_basic_info_tab(self):
        """Tạo tab thông tin cơ bản"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Tracking ID - luôn readonly
        tracking_id = QSpinBox()
        tracking_id.setEnabled(False)
        tracking_id.setMaximum(999999)
        self.widgets["Tracking ID"] = tracking_id
        layout.addRow(self._get_label("Tracking ID"), tracking_id)
        
        # Ngày khởi tạo - editable datetime
        self.widgets["Ngày"] = self._create_editable_datetime("Ngày", layout)
        
        # Khách hàng - editable combobox
        self.widgets["Khách hàng"] = self._create_editable_combobox("Khách hàng", layout)
        
        # Nhân viên kinh doanh - editable combobox
        self.widgets["Nhân viên kinh doanh"] = self._create_editable_combobox("Nhân viên kinh doanh", layout)
        
        # Người liên hệ (KH) - editable
        self.widgets["Người liên hệ\n(KH)"] = self._create_editable_lineedit("Người liên hệ\n(KH)", layout)
        
        # Mã PO - editable
        self.widgets["Mã PO"] = self._create_editable_lineedit("Mã PO", layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, self.texts.get("view_tab_basic", "📋 Cơ bản"))
    
    def create_product_info_tab(self):
        """Tạo tab thông tin sản phẩm"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Tên sản phẩm - editable combobox
        self.widgets["Tên sản phẩm"] = self._create_editable_combobox("Tên sản phẩm", layout)
        
        # Quy cách - editable combobox
        self.widgets["Quy cách"] = self._create_editable_combobox("Quy cách", layout)
        
        # Số lượng - editable spinbox
        quantity = QSpinBox()
        quantity.setMaximum(999999)
        self.widgets["Số lượng"] = quantity
        layout.addRow(self._get_label("Số lượng"), quantity)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, self.texts.get("view_tab_product", "📦 Sản phẩm"))
    
    def create_drawing_info_tab(self):
        """Tạo tab thông tin bản vẽ"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Mã bản vẽ (phương án) - editable
        self.widgets["Mã bản vẽ"] = self._create_editable_lineedit("Mã bản vẽ", layout)
        
        # Mã bản vẽ kỹ thuật - editable
        self.widgets["Mã bản vẽ kỹ thuật (sau khi đặt hàng)"] = self._create_editable_lineedit("Mã bản vẽ kỹ thuật (sau khi đặt hàng)", layout)
        
        # Mã mẹ - editable
        self.widgets["Mã mẹ"] = self._create_editable_lineedit("Mã mẹ", layout)
        
        # Loại sản phẩm / Hạng mục - editable combobox (đặt giữa Mã mẹ và Nhân viên thiết kế)
        self.widgets["Loại sản phẩm"] = self._create_editable_combobox("Loại sản phẩm", layout)
        
        # Nhân viên thiết kế - editable combobox
        self.widgets["Nhân viên thiết kế"] = self._create_editable_combobox("Nhân viên thiết kế", layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, self.texts.get("view_tab_drawing", "📐 Bản vẽ"))
    
    def create_progress_info_tab(self):
        """Tạo tab thông tin tiến độ"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Thời gian mong muốn có bản vẽ - editable datetime
        self.widgets["Thời gian mong muốn có bản vẽ"] = self._create_editable_datetime("Thời gian mong muốn có bản vẽ", layout)
        
        # Thời gian hoàn thành kế hoạch - editable datetime
        self.widgets["Thời gian hoàn thành kế hoạch"] = self._create_editable_datetime("Thời gian hoàn thành kế hoạch", layout)
        
        # Tình trạng hoàn thành dự án - editable combobox
        self.widgets["Tình trạng hoàn thành dự án"] = self._create_editable_combobox("Tình trạng hoàn thành dự án", layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, self.texts.get("view_tab_progress", "⏱️ Tiến độ"))
    
    def create_metadata_tab(self):
        """Tạo tab thông tin metadata"""
        tab = QWidget()
        layout = QFormLayout()
        
        # User ID - editable
        self.widgets["user_id"] = self._create_editable_lineedit("user_id", layout)
        
        # Trạng thái chờ - editable checkbox
        self.widgets["is_pending"] = self._create_editable_checkbox("is_pending", layout)
        
        # Người nhận - editable
        self.widgets["accepted_by"] = self._create_editable_lineedit("accepted_by", layout)
        
        # Thời gian nhận - editable datetime
        self.widgets["accepted_at"] = self._create_editable_datetime("accepted_at", layout)
        
        # Mức độ khẩn cấp - editable combobox
        self.widgets["urgency_level"] = self._create_urgency_combobox("urgency_level", layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, self.texts.get("view_tab_metadata", "🔧 Metadata"))
    
    def _create_editable_lineedit(self, label_key, layout):
        """Tạo widget QLineEdit - mặc định disabled (read-only)"""
        widget = QLineEdit()
        widget.setEnabled(False)  # Ban đầu ở chế độ read-only
        label = self._get_label(label_key)
        layout.addRow(label, widget)
        return widget
    
    def _create_editable_datetime(self, label_key, layout):
        """Tạo widget QDateTimeEdit - mặc định disabled (read-only)"""
        widget = QDateTimeEdit()
        widget.setEnabled(False)  # Ban đầu ở chế độ read-only
        widget.setDisplayFormat("yyyy-MM-dd HH:mm")
        widget.setCalendarPopup(True)
        label = self._get_label(label_key)
        layout.addRow(label, widget)
        return widget
    
    def _create_editable_checkbox(self, label_key, layout):
        """Tạo widget QCheckBox - mặc định disabled (read-only)"""
        widget = QCheckBox()
        widget.setEnabled(False)  # Ban đầu ở chế độ read-only
        label = self._get_label(label_key)
        layout.addRow(label, widget)
        return widget
    
    def _create_urgency_combobox(self, label_key, layout):
        """Tạo widget QComboBox cho urgency_level - mặc định disabled (read-only)"""
        widget = QComboBox()
        widget.setEditable(False)
        widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        widget.setEnabled(False)  # Ban đầu ở chế độ read-only
        
        # Thêm các mức độ khẩn cấp từ language_manager
        urgency_levels = language_manager.get_urgency_levels()
        for key_value, display_value in urgency_levels:
            widget.addItem(display_value, key_value)
        
        label = self._get_label(label_key)
        layout.addRow(label, widget)
        return widget
    
    def _create_editable_combobox(self, label_key, layout):
        """Tạo widget QComboBox editable - mặc định disabled (read-only)"""
        widget = QComboBox()
        widget.setEditable(True)
        widget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        widget.setEnabled(False)  # Ban đầu ở chế độ read-only
        
        # Thêm completer để hỗ trợ autocomplete
        completer = QCompleter()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        widget.setCompleter(completer)
        
        # Lưu reference để cập nhật completer
        self.comboboxes[label_key] = widget
        
        # Điền dữ liệu từ DB.json nếu có
        self.populate_combobox_from_db(widget, label_key)
        
        label = self._get_label(label_key)
        layout.addRow(label, widget)
        return widget
    
    def enable_edit_mode(self):
        """Bật chế độ chỉnh sửa - chuyển tất cả widgets sang editable"""
        self.is_edit_mode = True
        
        # Bật chế độ editable cho tất cả widgets
        for field_key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                widget.setEnabled(True)
            elif isinstance(widget, QDateTimeEdit):
                widget.setEnabled(True)
            elif isinstance(widget, QCheckBox):
                widget.setEnabled(True)
            elif isinstance(widget, QComboBox):
                widget.setEnabled(True)
            elif isinstance(widget, QSpinBox):
                # Tracking ID và Số lượng đặc biệt
                if field_key == "Tracking ID":
                    # Tracking ID luôn disabled
                    widget.setEnabled(False)
                else:
                    # Số lượng có thể edit
                    widget.setEnabled(True)
        
        # Ẩn nút Chỉnh sửa, hiện nút Lưu và Hủy
        self.edit_btn.setVisible(False)
        self.save_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        
        # Ẩn button box OK
        self.button_box.setVisible(False)
        
        # Cập nhật tiêu đề dialog
        self.setWindowTitle(self.texts.get("dialog_edit_title", "Chỉnh sửa"))
    
    def disable_edit_mode(self):
        """Tắt chế độ chỉnh sửa - chuyển tất cả widgets sang read-only"""
        self.is_edit_mode = False
        
        # Tắt chế độ editable cho tất cả widgets (trừ những cái đặc biệt)
        for field_key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                widget.setEnabled(False)
            elif isinstance(widget, QDateTimeEdit):
                widget.setEnabled(False)
            elif isinstance(widget, QCheckBox):
                widget.setEnabled(False)
            elif isinstance(widget, QComboBox):
                widget.setEnabled(False)
            elif isinstance(widget, QSpinBox):
                widget.setEnabled(False)
        
        # Hiện nút Chỉnh sửa, ẩn nút Lưu và Hủy
        self.edit_btn.setVisible(True)
        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        
        # Hiện button box OK
        self.button_box.setVisible(True)
        
        # Cập nhật tiêu đề dialog
        self.setWindowTitle(self.texts["dialog_view_title"])
    
    def get_data(self):
        """Lấy dữ liệu từ form"""
        data = {}
        for field_key, widget in self.widgets.items():
            if isinstance(widget, QSpinBox):
                data[field_key] = widget.value()
            
            elif isinstance(widget, QDateTimeEdit):
                # Format: yyyy-MM-dd HH:mm
                data[field_key] = widget.dateTime().toString("yyyy-MM-dd HH:mm")
            
            elif isinstance(widget, QComboBox):
                if widget.isEditable():
                    # Lấy text từ lineedit
                    data[field_key] = widget.currentText()
                else:
                    # Cho urgency_level combobox: lưu giá trị key (English) thay vì display text
                    if field_key == "urgency_level":
                        data[field_key] = widget.currentData()  # Lưu key như "normal", "urgent", etc.
                    else:
                        data[field_key] = widget.currentText()
            
            elif isinstance(widget, QCheckBox):
                data[field_key] = widget.isChecked()
            
            else:
                # QLineEdit
                if isinstance(widget, QLineEdit):
                    data[field_key] = widget.text()
                else:
                    data[field_key] = ""
        
        return data
    
    def save_record(self):
        """Lưu dữ liệu sau khi chỉnh sửa"""
        # Lấy dữ liệu từ form
        new_data = self.get_data()
        
        # Debug: In ra dữ liệu trước khi lưu
        print(f"[ViewDialog] Saving record with Tracking ID: {self.record.get('Tracking ID')}")
        print(f"[ViewDialog] New data: {new_data}")
        
        # Cập nhật dữ liệu trong parent window (sẽ gửi lên server)
        if self.parent_window:
            # Kiểm tra xem parent có phương thức update_record không
            if hasattr(self.parent_window, 'update_record'):
                # Gọi phương thức update_record của parent để lưu vào DB qua server
                self.parent_window.update_record(self.record, new_data)
                
                # Cập nhật record hiện tại
                self.record = new_data
                
                # Refresh dialog data
                self.populate_data(new_data)
                
                # Chuyển về chế độ xem
                self.disable_edit_mode()
                
                # Hiển thị thông báo thành công
                texts = language_manager.get_all_ui_texts()
                QMessageBox.information(self, texts.get("new_sales_success", "Thành công"), texts.get("msg_edit_success", "Đã cập nhật bản ghi"))
            else:
                QMessageBox.critical(self, "Lỗi", "Parent window không hỗ trợ cập nhật dữ liệu")
        else:
            # Nếu không có parent, thông báo lỗi
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy cửa sổ cha để cập nhật dữ liệu")
    
    def cancel_edit(self):
        """Hủy chỉnh sửa và khôi phục dữ liệu gốc"""
        # Khôi phục dữ liệu gốc
        self.record = dict(self.original_record)
        self.populate_data(self.original_record)
        
        # Chuyển về chế độ xem
        self.disable_edit_mode()
    
    def populate_data(self, record):
        """Điền dữ liệu vào form"""
        for field_key, widget in self.widgets.items():
            # Lấy giá trị từ record (hỗ trợ cả tên tiếng Việt và key tiếng Anh)
            value = record.get(field_key, "")
            
            # Nếu không tìm thấy, thử các tên field khác
            if value == "":
                # Mapping các tên field tiếng Việt
                field_mapping = {
                    "Người liên hệ (KH)": "Người liên hệ\n(KH)",
                    "Mã bản vẽ": "Mã bản vẽ",
                    "Mã bản vẽ kỹ thuật": "Mã bản vẽ kỹ thuật (sau khi đặt hàng)",
                    "Mã mẹ": "Mã mẹ",  # Database (đã sửa lỗi dấu cách)
                    "Mã mẹ ": "Mã mẹ",  # Database cũ (có dấu cách)
                    "Mã thành phẩm (Mã mẹ)": "Mã mẹ",
                    "Kỹ sư thiết kế": "Nhân viên thiết kế",
                    "Hạng mục": "Loại sản phẩm",
                    "Mã bản vẽ phương án (mã trước khi đặt hàng)": "Mã bản vẽ",
                    "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": "Mã bản vẽ kỹ thuật (sau khi đặt hàng)",
                }
                alt_key = field_mapping.get(field_key, field_key)
                value = record.get(alt_key, "")
                
                # Thử tìm với dấu cách nếu không tìm thấy
                if value == "" and field_key == "Mã mẹ":
                    value = record.get("Mã mẹ ", "")
            
            if value is None:
                value = ""
            
            if isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(value) if value else 0)
                except (ValueError, TypeError):
                    widget.setValue(0)
            elif isinstance(widget, QDateTimeEdit):
                if value:
                    try:
                        # Thử format với thời gian
                        dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm")
                        if not dt.isValid():
                            # Thử format chỉ ngày
                            dt = QDateTime.fromString(value, "yyyy-MM-dd")
                        widget.setDateTime(dt)
                    except Exception:
                        widget.setDateTime(QDateTime.currentDateTime())
                else:
                    widget.setDateTime(QDateTime.currentDateTime())
            elif isinstance(widget, QCheckBox):
                # Chuyển đổi giá trị thành boolean
                if isinstance(value, bool):
                    widget.setChecked(value)
                elif str(value).lower() in ('true', '1', 'yes', 'có'):
                    widget.setChecked(True)
                else:
                    widget.setChecked(False)
            elif isinstance(widget, QComboBox):
                # Tìm item phù hợp trong combobox
                # Đặc biệt xử lý urgency_level: dịch từ English sang ngôn ngữ hiện tại
                found = False
                if field_key == "urgency_level":
                    # Tìm theo key (English value)
                    for i in range(widget.count()):
                        key_value = widget.itemData(i)
                        if key_value == value:
                            widget.setCurrentIndex(i)
                            found = True
                            break
                    if not found:
                        # Thử tìm theo display text
                        for i in range(widget.count()):
                            item_text = widget.itemText(i)
                            if item_text == str(value):
                                widget.setCurrentIndex(i)
                                found = True
                                break
                else:
                    # Các combobox khác
                    for i in range(widget.count()):
                        item_text = widget.itemText(i)
                        if item_text == str(value):
                            widget.setCurrentIndex(i)
                            found = True
                            break
                if not found and widget.isEditable():
                    # Nếu là combobox editable, điền giá trị vào lineedit
                    widget.setCurrentText(str(value))
            else:
                # QLineEdit
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
    
    # Giữ phương thức edit_record để tương thích ngược (có thể được gọi từ đâu đó)
    def edit_record(self):
        """Bật chế độ chỉnh sửa (giữ để tương thích ngược)"""
        self.enable_edit_mode()
