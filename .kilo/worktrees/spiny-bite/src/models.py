"""
Models - TableModel and NumericSortProxyModel
Tách từ Project_Tracking.py
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QTableWidget
from PySide6.QtGui import QWheelEvent
from datetime import datetime

# Import language_manager for urgency level translation
try:
    from src.language_manager import language_manager
except ImportError:
    from language_manager import language_manager


def format_datetime_vietnam(value):
    """
    Format datetime thành định dạng "Năm Tháng Ngày Giờ Phút"
    Ví dụ: "2026-02-25 10:56"
    """
    if not value:
        return ""
    
    try:
        # Thử parse datetime từ nhiều format khác nhau
        if isinstance(value, datetime):
            dt = value
        else:
            # Thử ISO format trước
            try:
                dt = datetime.fromisoformat(str(value))
            except:
                try:
                    # Thử format khác: YYYY-MM-DD HH:MM:SS
                    dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        # Thử format: YYYY-MM-DD
                        dt = datetime.strptime(str(value), "%Y-%m-%d")
                    except:
                        # Nếu không parse được, trả về nguyên giá trị
                        return str(value)
        
        # Format: Năm-Tháng-Ngày Giờ:Phút
        return f"{dt.year}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"
    except:
        return str(value)


# Các cột thời gian cần format - bao gồm cả database keys và display headers
DATETIME_COLUMNS = [
    # Database keys (không dấu)
    "thoi_gian_mong_muon_ban_ve",
    "thoi_gian_hoan_thanh_ke_hoach",
    "accepted_at",
    # Display headers tiếng Việt (có dấu)
    "Thời gian mong muốn có bản vẽ",
    "Thời gian hoàn thành kế hoạch",
    "Thời gian nhận",
    # Display headers tiếng Trung
    "期望出图时间",
    "方案完成时间",
    "接收时间"
]


def safe_int(value):
    """
    Chuyển đổi giá trị thành int, trả về 0 nếu là None hoặc không thể chuyển đổi
    """
    try:
        return int(value) if value is not None else 0
    except (ValueError, TypeError):
        return 0


class TableModel(QAbstractTableModel):
    """Custom Table Model cho QTableView"""
    
    def __init__(self, data, headers, key_mapping=None, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self._key_mapping = key_mapping or {}
    
    @staticmethod
    def number_to_letters(n):
        """Chuyển đổi số thành chữ cái Excel (0=A, 1=B, 2=C, ..., 26=AA, etc.)"""
        result = ""
        num = n
        while num >= 0:
            result = chr(num % 26 + ord('A')) + result
            num = num // 26 - 1
        return result
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            # Lấy display header và chuyển đổi sang actual key
            if col < len(self._headers):
                display_header = self._headers[col]
                actual_key = self._key_mapping.get(display_header, display_header)
                # Truy cập dữ liệu bằng actual key từ DB.json
                value = self._data[row].get(actual_key, "")
                # Tracking ID giữ nguyên là số nguyên
                if actual_key == "Tracking ID":
                    return value if value is not None else 0
                # Kiểm tra nếu là cột thời gian thì format
                if actual_key in DATETIME_COLUMNS:
                    return format_datetime_vietnam(value)
                # Kiểm tra nếu là cột urgency_level thì dịch sang ngôn ngữ hiện tại
                if actual_key == "urgency_level":
                    return language_manager.get_urgency_level_display(value)
                return str(value) if value is not None else ""
            return ""
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            # Hiển thị tên cột gốc
            if section < len(self._headers):
                return self._headers[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            # Hiển thị số dòng bắt đầu từ 1 (giống Excel)
            return section + 1
        return None
    
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        # Lấy display header và chuyển đổi sang actual key
        if column < len(self._headers):
            display_header = self._headers[column]
            actual_key = self._key_mapping.get(display_header, display_header)
            
            # Sắp xếp số cho Tracking ID, chuỗi cho các cột khác
            if actual_key == "Tracking ID":
                self._data.sort(key=lambda x: safe_int(x.get(actual_key)), 
                               reverse=(order == Qt.DescendingOrder))
            else:
                self._data.sort(key=lambda x: str(x.get(actual_key, "")), 
                               reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()


class NumericSortProxyModel(QSortFilterProxyModel):
    """Custom Proxy Model với numeric sort cho cột Tracking ID"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key_mapping = {}

    def set_key_mapping(self, key_mapping):
        """Thiết lập key mapping để xác định cột Tracking ID"""
        self._key_mapping = key_mapping

    def lessThan(self, left_index, right_index):
        """So sánh với numeric sort cho cột Tracking ID"""
        # Lấy source model
        source_model = self.sourceModel()

        # Lấy column của left và right
        left_column = left_index.column()
        right_column = right_index.column()

        # Lấy display headers để xác định nếu là cột Tracking ID
        if hasattr(source_model, '_headers'):
            headers = source_model._headers
            if left_column < len(headers) and right_column < len(headers):
                left_header = headers[left_column]
                right_header = headers[right_column]

                # Kiểm tra nếu là cột Tracking ID
                key_mapping = getattr(source_model, '_key_mapping', {})
                left_key = key_mapping.get(left_header, left_header)
                right_key = key_mapping.get(right_header, right_header)

                if left_key == "Tracking ID" and right_key == "Tracking ID":
                    # Numeric sort cho Tracking ID
                    left_data = source_model.data(left_index, Qt.DisplayRole)
                    right_data = source_model.data(right_index, Qt.DisplayRole)

                    # Sử dụng safe_int để xử lý None value
                    left_val = safe_int(left_data)
                    right_val = safe_int(right_data)
                    return left_val < right_val

        # Default: string comparison cho các cột khác
        return super().lessThan(left_index, right_index)


class HorizontalScrollTableView(QTableView):
    """
    QTableView subclass với tính năng Shift + wheel để cuộn ngang
    
    Cách sử dụng:
        Thay thế QTableView bằng HorizontalScrollTableView
        Khi nhấn giữ Shift + cuộn chuột, bảng sẽ cuộn ngang thay vì dọc
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_speed = 1  # Hệ số tốc độ cuộn
    
    def wheelEvent(self, event):
        """
        Xử lý sự kiện wheel:
        - Nếu nhấn Shift: cuộn ngang
        - Nếu không nhấn Shift: cuộn dọc bình thường
        """
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Cuộn ngang khi nhấn Shift
            horizontal_scroll = self.horizontalScrollBar()
            delta = event.angleDelta().y()
            # Điều chỉnh giá trị cuộn
            new_value = horizontal_scroll.value() + (delta * self._scroll_speed)
            horizontal_scroll.setValue(new_value)
            event.accept()
        else:
            # Xử lý bình thường khi không nhấn Shift
            super().wheelEvent(event)


class HorizontalScrollTableWidget(QTableWidget):
    """
    QTableWidget subclass với tính năng Shift + wheel để cuộn ngang
    
    Cách sử dụng:
        Thay thế QTableWidget bằng HorizontalScrollTableWidget
        Khi nhấn giữ Shift + cuộn chuột, bảng sẽ cuộn ngang thay vì dọc
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_speed = 1  # Hệ số tốc độ cuộn
    
    def wheelEvent(self, event):
        """
        Xử lý sự kiện wheel:
        - Nếu nhấn Shift: cuộn ngang
        - Nếu không nhấn Shift: cuộn dọc bình thường
        """
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Cuộn ngang khi nhấn Shift
            horizontal_scroll = self.horizontalScrollBar()
            delta = event.angleDelta().y()
            # Điều chỉnh giá trị cuộn
            new_value = horizontal_scroll.value() + (delta * self._scroll_speed)
            horizontal_scroll.setValue(new_value)
            event.accept()
        else:
            # Xử lý bình thường khi không nhấn Shift
            super().wheelEvent(event)
