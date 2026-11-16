from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction, QKeySequence

# Import Session Manager - lấy thông tin user và role
try:
    from src.session_manager import session_manager
except ImportError:
    from session_manager import session_manager


class Toolbar:
    """Class quản lý context menu - tách từ Project_Tracking.py"""
    
    def __init__(self, parent_window, texts):
        """
        Khởi tạo context menu
        
        Args:
            parent_window: Reference to MainWindow (để kết nối signals)
            texts: Dictionary chứa các text theo ngôn ngữ
        """
        self.parent = parent_window
        self.texts = texts
        self.menu = None
        self._last_context_pos = None
        self.table_view = None
    
    def create_context_menu(self, parent_widget):
        """Tạo và cấu hình context menu cho widget cha"""
        self.menu = QMenu(parent_widget)
        
        # Nút Thêm mới
        add_action = QAction(self.texts["toolbar_add"], parent_widget)
        add_action.triggered.connect(self.parent.add_record)
        self.menu.addAction(add_action)
        
        # Nút Chỉnh sửa
        edit_action = QAction(self.texts["toolbar_edit"], parent_widget)
        edit_action.triggered.connect(self.parent.edit_record)
        self.menu.addAction(edit_action)
        
        # Nút Xóa - Chỉ hiển thị cho Admin
        if session_manager.can_delete_project():
            delete_action = QAction(self.texts["toolbar_delete"], parent_widget)
            delete_action.triggered.connect(self.parent.delete_records)
            self.menu.addAction(delete_action)
            self.menu.addSeparator()
        
        # Nút Tìm kiếm
        search_action = QAction(self.texts["toolbar_search"], parent_widget)
        search_action.triggered.connect(self.parent.search_data)
        self.menu.addAction(search_action)
        
        # Nút Làm mới (F5)
        refresh_action = QAction(self.texts["toolbar_refresh"], parent_widget)
        refresh_action.triggered.connect(self.parent.refresh_data)
        self.menu.addAction(refresh_action)
        
        self.menu.addSeparator()
        
        # Nút Xuất Excel
        export_excel_action = QAction(self.texts["toolbar_export_excel"], parent_widget)
        export_excel_action.triggered.connect(self.parent.export_excel)
        self.menu.addAction(export_excel_action)
        
        # Nút Xuất CSV
        export_csv_action = QAction(self.texts["toolbar_export_csv"], parent_widget)
        export_csv_action.triggered.connect(self.parent.export_csv)
        self.menu.addAction(export_csv_action)
        
        self.menu.addSeparator()
        
        # Nút Hướng dẫn Filter
        filter_action = QAction(self.texts.get("menu_filter", "📋 Lọc dữ liệu"), parent_widget)
        filter_action.triggered.connect(self.parent.show_filter_dialog)
        self.menu.addAction(filter_action)
        
        # Nút Xóa Filter
        clear_filter_action = QAction(self.texts.get("action_clear_filter", "Xóa lọc"), parent_widget)
        clear_filter_action.triggered.connect(self.parent.clear_all_filters)
        self.menu.addAction(clear_filter_action)
        
        self.menu.addSeparator()
        
        # Nút Lọc giá trị này (Filter This Item Only)
        filter_this_action = QAction(self.texts.get("action_filter_this", "Lọc giá trị này"), parent_widget)
        filter_this_action.triggered.connect(self.filter_this_item)
        self.menu.addAction(filter_this_action)
        
        return self.menu
    
    def show_context_menu(self, pos):
        """Hiển thị context menu tại vị trí chuột"""
        self._last_context_pos = pos
        if hasattr(self, 'menu') and self.menu:
            self.menu.exec_(self.table_view.viewport().mapToGlobal(pos))
    
    def filter_this_item(self):
        """Lọc dữ liệu theo giá trị của cell được chọn"""
        if hasattr(self, '_last_context_pos') and self._last_context_pos:
            column_key, value = self.parent.get_cell_value_from_position(self._last_context_pos)
            if column_key and value:
                self.parent.filter_by_cell_value(column_key, value)
