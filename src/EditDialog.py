from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                               QSpinBox, QLineEdit, QDialogButtonBox, 
                               QComboBox, QDateTimeEdit, QCompleter)
from PySide6.QtCore import Qt, QDateTime, QDate
from PySide6.QtGui import QIntValidator

# Import language_manager - hỗ trợ cả chạy từ thư mục gốc và thư mục src/
try:
    from src.language_manager import language_manager
except ImportError:
    from language_manager import language_manager

import json
import os


class EditDialog(QDialog):
    """Dialog chỉnh sửa/thêm bản ghi - Phiên bản nâng cấp với nhiều widget types"""
    
    def __init__(self, parent=None, record=None, is_new=False):
        super().__init__(parent)
        
        # Get UI texts
        texts = language_manager.get_all_ui_texts()
        self.setWindowTitle(texts["dialog_add_title"] if is_new else texts["dialog_edit_title"])
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        self.parent_window = parent
        self.is_new = is_new
        self.result_data = None
        
        # Layout chính
        layout = QVBoxLayout(self)
        
        # Form layout cho các trường
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Khởi tạo các widget
        self.widgets = {}
        self.comboboxes = {}  # Lưu reference đến các combobox để cập nhật completer
        
        # Định nghĩa các trường từ language manager
        self.field_defs = language_manager.get_dialog_fields()
        
        # Load dữ liệu dropdown từ DB.json
        self.dropdown_data = self.load_dropdown_data()
        
        # Tạo các widget dựa trên field_type
        for display_name, field_key, field_type in self.field_defs:
            widget = self.create_widget(field_key, field_type)
            self.widgets[field_key] = widget
            form_layout.addRow(display_name, widget)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Nếu là chỉnh sửa, điền dữ liệu
        if record and not is_new:
            self.populate_data(record)
            # Tracking ID luôn readonly khi chỉnh sửa
            if "Tracking ID" in self.widgets:
                self.widgets["Tracking ID"].setReadOnly(True)
        elif is_new:
            # Điền Tracking ID tự động tăng (readonly)
            max_tracking_id = 0
            if parent and parent.data:
                for item in parent.data:
                    tracking_id = item.get("Tracking ID", 0)
                    if isinstance(tracking_id, int) and tracking_id > max_tracking_id:
                        max_tracking_id = tracking_id
            if "Tracking ID" in self.widgets:
                self.widgets["Tracking ID"].setValue(max_tracking_id + 1)
                self.widgets["Tracking ID"].setReadOnly(True)
            
            # Điền Ngày = today() với thời gian hiện tại
            if "Ngày" in self.widgets:
                now = QDateTime.currentDateTime()
                self.widgets["Ngày"].setDateTime(now)
    
    def create_widget(self, field_key, field_type):
        """Tạo widget dựa trên field_type"""
        widget = None
        
        if field_type == "spinbox_readonly":
            # SpinBox chỉ đọc cho Tracking ID
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(999999)  # 6 chữ số: 000001-999999
            # KHÔNG setReadOnly ở đây - sẽ set sau khi setValue() trong phần xử lý is_new
            widget.setButtonSymbols(QSpinBox.NoButtons)
            
        elif field_type == "datetime":
            # DateTimeEdit với format ngày + giờ phút (24h)
            widget = QDateTimeEdit()
            widget.setDateTime(QDateTime.currentDateTime())
            widget.setDisplayFormat("yyyy-MM-dd HH:mm")
            widget.setCalendarPopup(True)  # Hiện lịch khi click
            # QDateTime yêu cầu đủ 6 tham số: year, month, day, hour, minute, second
            widget.setDateRange(QDate(1900, 1, 1), QDate(2100, 12, 31))
            
        elif field_type == "combobox_editable":
            # ComboBox có thể chọn và đánh tay
            widget = QComboBox()
            widget.setEditable(True)
            widget.setInsertPolicy(QComboBox.NoInsert)
            widget.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            
            # Thêm completer để hỗ trợ autocomplete
            completer = QCompleter()
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            widget.setCompleter(completer)
            
            # Lưu reference để cập nhật completer sau
            self.comboboxes[field_key] = widget
            
            # Điền dữ liệu từ DB.json nếu có
            self.populate_combobox_from_db(widget, field_key)
            
        elif field_type == "number":
            # SpinBox cho số lượng
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(999999)
            widget.setValue(1)
            
        elif field_type == "combobox":
            # ComboBox không edit được (dropdown thuần)
            widget = QComboBox()
            widget.setEditable(False)
            
            # Lấy danh sách mức độ khẩn cấp từ language manager
            urgency_levels = language_manager.get_urgency_levels()
            for display_value, key_value in urgency_levels:
                widget.addItem(display_value, key_value)
            
        elif field_type == "date":
            # DateEdit đơn giản (cho các trường ngày khác)
            widget = QDateTimeEdit()
            widget.setDateTime(QDateTime.currentDateTime())
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setCalendarPopup(True)
            
        else:
            # Mặc định là LineEdit
            widget = QLineEdit()
        
        return widget
    
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
        
        # Chuyển set thành list và sort (chuyển sang string để tránh lỗi so sánh int vs str)
        for key in data:
            # Chuyển tất cả giá trị thành string trước khi sort
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
    
    def populate_data(self, record):
        """Điền dữ liệu vào form"""
        for field_key, widget in self.widgets.items():
            value = record.get(field_key, "")
            if value is None:
                value = ""
            
            if isinstance(widget, QSpinBox) and not widget.isReadOnly():
                try:
                    widget.setValue(int(value) if value else 0)
                except (ValueError, TypeError):
                    widget.setValue(0)
            
            elif isinstance(widget, QDateTimeEdit):
                # Parse ngày giờ từ chuỗi
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
            
            elif isinstance(widget, QComboBox):
                # Tìm item phù hợp trong combobox
                found = False
                for i in range(widget.count()):
                    item_text = widget.itemText(i)
                    # So sánh với cả display value và data value
                    if item_text == str(value) or widget.itemData(i) == value:
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
                    # Lấy data value (key)
                    data[field_key] = widget.currentData()
                    if data[field_key] is None:
                        data[field_key] = widget.currentText()
            
            else:
                # QLineEdit
                if isinstance(widget, QLineEdit):
                    data[field_key] = widget.text()
                else:
                    data[field_key] = ""
        
        return data
