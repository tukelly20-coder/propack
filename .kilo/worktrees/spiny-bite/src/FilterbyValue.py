"""
Module Filter by Value - Lọc dữ liệu theo từng cột giống Excel
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QScrollArea,
    QListWidget, QListWidgetItem, QDialogButtonBox,
    QFrame, QWidget, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QPoint

# Import language_manager
try:
    from src.language_manager import language_manager
except ImportError:
    from language_manager import language_manager


class FilterByValueDialog(QDialog):
    """
    Dialog filter theo giá trị cột - giống Excel Filter
    
    Features:
    - Hiển thị danh sách các giá trị unique của cột
    - Checkbox để chọn/bỏ chọn từng giá trị
    - Search box để tìm kiếm trong list values
    - Nút Select All / Clear All
    """
    
    def __init__(self, parent=None, column_name="", column_key="", values=None, checked_values=None):
        """
        Args:
            parent: Parent widget
            column_name: Tên hiển thị của cột
            column_key: Key trong dữ liệu
            values: Danh sách tất cả giá trị unique
            checked_values: Dict {value: is_checked}
        """
        super().__init__(parent)
        
        self.column_name = column_name
        self.column_key = column_key
        self.all_values = list(values) if values else []
        self.checked_values = checked_values or {}
        self.sort_order = "asc"  # Default: ascending
        
        # Sắp xếp values theo mặc định
        
        # Lấy texts
        self.texts = language_manager.get_all_ui_texts()
        
        self.setup_ui()
        self.populate_values()
    
    def setup_ui(self):
        """Thiết lập giao diện dialog"""
        # Sử dụng texts từ language_manager, fallback về tiếng Việt mặc định
        window_title = self.texts.get("filter_dialog_title", "Lọc dữ liệu").replace("Hướng dẫn lọc dữ liệu", "Lọc")
        self.setWindowTitle(f"{window_title} - {self.column_name}")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label_text = self.texts.get("search_label", "Tìm kiếm:").replace("Tìm kiếm:", "Tìm:")
        search_label = QLabel(search_label_text)
        search_label.setFixedWidth(50)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.texts.get("search_placeholder", "Nhập để tìm kiếm..."))
        self.search_input.textChanged.connect(self.filter_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Sort controls (Ascending / Descending)
        sort_layout = QHBoxLayout()
        sort_label = QLabel(self.texts.get("sort_label", "Sắp xếp:"))
        sort_label.setFixedWidth(60)
        sort_layout.addWidget(sort_label)
        
        self.sort_button_group = QButtonGroup()
        
        self.asc_radio = QRadioButton(self.texts.get("sort_asc", "↑ Tăng dần"))
        self.asc_radio.setChecked(True)
        self.asc_radio.toggled.connect(self.on_sort_changed)
        self.sort_button_group.addButton(self.asc_radio)
        sort_layout.addWidget(self.asc_radio)
        
        self.desc_radio = QRadioButton(self.texts.get("sort_desc", "↓ Giảm dần"))
        self.desc_radio.toggled.connect(self.on_sort_changed)
        self.sort_button_group.addButton(self.desc_radio)
        sort_layout.addWidget(self.desc_radio)
        
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
        
        # Select All / Clear All / Filter This Item Only buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton(self.texts.get("select_all", "Chọn tất cả"))
        self.select_all_btn.setFixedWidth(100)
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.clear_all_btn = QPushButton(self.texts.get("deselect_all", "Bỏ chọn tất cả"))
        self.clear_all_btn.setFixedWidth(110)
        self.clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_btn)
        
        self.filter_this_btn = QPushButton(self.texts.get("filter_this_item", "Chỉ chọn mục này"))
        self.filter_this_btn.setFixedWidth(120)
        self.filter_this_btn.clicked.connect(self.filter_this_item_only)
        button_layout.addWidget(self.filter_this_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Thông tin về tổng số giá trị
        total_text = self.texts.get("filter_total", "Tổng số giá trị: {}").format(len(self.all_values))
        self.info_label = QLabel(total_text)
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # Line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # List các giá trị với checkbox
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setSpacing(2)
        layout.addWidget(self.list_widget)
        
        # Số lượng đã chọn
        self.count_label = QLabel()
        self.count_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addWidget(self.count_label)
        
        # Line separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Buttons OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Kết nối click vào item và double-click
        self.list_widget.itemClicked.connect(self.update_count)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def populate_values(self, filter_text=""):
        """Điền danh sách giá trị vào list widget"""
        self.list_widget.clear()
        
        # Sắp xếp values theo sort_order (nếu là STT thì sort theo số)
        def sort_key(val):
            if self.column_key == "STT":
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            return str(val)
        
        sorted_values = sorted(self.all_values, key=sort_key, reverse=(self.sort_order == "desc"))
        
        for value in sorted_values:
            if filter_text and filter_text.lower() not in str(value).lower():
                continue
            
            item = QListWidgetItem(str(value))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Check nếu giá trị được chọn
            is_checked = self.checked_values.get(str(value), True)
            item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
            
            self.list_widget.addItem(item)
        
        self.update_count()
    
    def filter_list(self):
        """Lọc danh sách theo text search"""
        filter_text = self.search_input.text()
        self.populate_values(filter_text)
    
    def on_sort_changed(self, checked):
        """Xử lý khi user thay đổi sort order"""
        if checked:
            self.sort_order = "asc" if self.asc_radio.isChecked() else "desc"
            self.populate_values(self.search_input.text())
    
    def select_all(self):
        """Chọn tất cả"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)
        self.update_count()
    
    def clear_all(self):
        """Bỏ chọn tất cả"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)
        self.update_count()
    
    def update_count(self, item=None):
        """Cập nhật số lượng đã chọn"""
        checked_count = 0
        visible_count = self.list_widget.count()
        
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item.checkState() == Qt.Checked:
                checked_count += 1
        
        count_text = self.texts.get("filter_count", "Đã chọn: {} / {}").format(checked_count, visible_count)
        self.count_label.setText(count_text)
    
    def get_selected_values(self):
        """Lấy danh sách giá trị được chọn"""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected
    
    def get_all_checked_values(self):
        """
        Lấy tất cả các giá trị đã check (bao gồm cả những giá trị không hiển thị do search)
        Returns dict {value: is_checked}
        """
        # Bắt đầu với checked_values ban đầu
        result = dict(self.checked_values)
        
        # Cập nhật với trạng thái hiện tại của list widget
        filter_text = self.search_input.text()
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            value = item.text()
            result[value] = (item.checkState() == Qt.Checked)
        
        return result
    
    def accept(self):
        """Override accept để validate"""
        # Luôn cho phép OK, ngay cả khi không chọn gì
        # Người dùng có thể muốn xóa filter
        super().accept()
    
    def filter_this_item_only(self):
        """Chỉ chọn item đang được highlight và đóng dialog"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            # Bỏ chọn tất cả
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item.setCheckState(Qt.Unchecked)
            # Chọn item hiện tại
            item = self.list_widget.item(current_row)
            item.setCheckState(Qt.Checked)
            self.update_count()
            # Đóng dialog với Accept
            self.accept()
    
    def on_item_double_clicked(self, item):
        """Xử lý khi user double-click vào một item"""
        # Bỏ chọn tất cả
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item != item:
                list_item.setCheckState(Qt.Unchecked)
        # Chọn item được double-click
        item.setCheckState(Qt.Checked)
        self.update_count()
        # Đóng dialog
        self.accept()
