"""
NoticeTab.py - Tab hiá» n thá»?thÃ´ng bÃ¡o/pending notices
Module nÃ y cung cáº¥p tab Ä á»?hiá» n thá»?danh sÃ¡ch yÃªu cáº§u chá»?xá»?lÃ½ vá» i cÃ¡c tÃ­nh nÄ ng:
- Hiá» n thá»?danh sÃ¡ch thÃ´ng bÃ¡o
- Filter theo tráº¡ng thÃ¡i (Táº¥t cáº? Chá»?nháº­n, Ä Ã£ nháº­n)
- Filter theo Ä á»?kháº©n (BÃ¬nh thÆ°á» ng, Kháº©n cáº¥p, Ráº¥t kháº©n)
- TÃ¬m kiáº¿m theo khÃ¡ch hÃ ng/sáº£n pháº©m
- Auto-refresh (cÃ³ thá»?báº­t/táº¯t)
- Badge sá»?lÆ°á»£ng thÃ´ng bÃ¡o chá»?
"""

import json
import socket
from datetime import datetime
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFrame, QGridLayout,
    QDateTimeEdit, QTextEdit, QGroupBox, QComboBox, QLineEdit, QCheckBox,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QColor

# Import language_manager
from src.language_manager import language_manager

# Import HorizontalScrollTableWidget for Shift+wheel horizontal scroll
from src.models import HorizontalScrollTableWidget


class NoticeLoader(QThread):
    """Thread Ä á»?load notices tá»?server"""
    notices_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, server_ip: str, user_id: Optional[int] = None):
        super().__init__()
        self.server_ip = server_ip
        self.user_id = user_id
    
    def run(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, 8001))
            
            request = {"request": "GET_PENDING_NOTICES"}
            if self.user_id:
                request["user_id"] = self.user_id
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            notices = json.loads(data.decode('utf-8'))
            self.notices_loaded.emit(notices)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class NoticeCountLoader(QThread):
    """Thread Ä á»?load sá»?lÆ°á»£ng notice tá»?server"""
    count_loaded = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, server_ip: str, user_id: Optional[int] = None):
        super().__init__()
        self.server_ip = server_ip
        self.user_id = user_id
    
    def run(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, 8001))
            
            request = {"request": "GET_PENDING_COUNT"}
            if self.user_id:
                request["user_id"] = self.user_id
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            count = response.get('count', 0) if isinstance(response, dict) else 0
            self.count_loaded.emit(count)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class EngineerNoticeLoader(QThread):
    """Thread Ä á»?load táº¥t cáº?notices cho Engineer (pending + accepted)"""
    notices_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, server_ip: str, engineer_name: str):
        super().__init__()
        self.server_ip = server_ip
        self.engineer_name = engineer_name
    
    def run(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "GET_ALL_NOTICES_FOR_ENGINEER",
                "engineer_name": self.engineer_name
            }
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            notices = json.loads(data.decode('utf-8'))
            self.notices_loaded.emit(notices)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class NoticeTab(QWidget):
    """
    Tab hiá» n thá»?notices vá» i cÃ¡c tÃ­nh nÄ ng:
    - Filter theo tráº¡ng thÃ¡i
    - Filter theo Ä á»?kháº©n
    - TÃ¬m kiáº¿m
    - Auto-refresh
    
    Signals:
        record_accepted: PhÃ¡t ra khi engineer nháº­n job thÃ nh cÃ´ng
        record_viewed: PhÃ¡t ra khi click vÃ o record Ä á»?xem
        data_updated: PhÃ¡t ra khi cÃ³ cáº­p nháº­t dá»?liá» u (reload)
    """
    
    record_accepted = Signal(dict)
    record_viewed = Signal(dict)
    data_updated = Signal()
    
    def __init__(self, parent=None, server_ip: str = "localhost"):
        super().__init__(parent)
        
        self.server_ip = server_ip
        self.notices: List[Dict] = []
        self.current_user_info = None
        self.current_status_filter = language_manager.get_notice_tab_text('filter_all')
        self.current_urgency_filter = language_manager.get_notice_tab_text('urgency_all')
        self.current_search_text = ""
        
        # Auto-refresh timer
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 30000  # 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_notices)
        self.refresh_timer.start(self.auto_refresh_interval)
        
        # Setup UI
        self.setup_ui()
        
        # Load notices
        self.load_notices()
    
    def setup_ui(self):
        """Thiáº¿t láº­p giao diá» n"""
        self.setStyleSheet("""
            QWidget {
                background: #F7FAFD;
                color: #1E293B;
            }
            QGroupBox {
                border: 1px solid #D8E0EA;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: #FFFFFF;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                border: 1px solid #C9D5E3;
                border-radius: 8px;
                background: #FFFFFF;
                padding: 6px 8px;
            }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
                border-color: #4C93D6;
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
            QPushButton#acceptButton {
                background: #1F7ACB;
                color: #FFFFFF;
                border-color: #1A6EB6;
            }
            QPushButton#acceptButton:hover {
                background: #1A6EB6;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_text = language_manager.get_notice_tab_text('tab_title')
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 12px;
                padding: 8px;
                background-color: #EEF4FB;
                border: 1px solid #D5E3F2;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.info_label)
        
        # Filter & Search layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # Status filter
        status_filter_label = language_manager.get_notice_tab_text('status_filter')
        filter_layout.addWidget(QLabel(status_filter_label))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            language_manager.get_notice_tab_text('filter_all'),
            language_manager.get_notice_tab_text('filter_pending'),
            language_manager.get_notice_tab_text('filter_accepted')
        ])
        self.status_filter_combo.setMinimumWidth(120)
        self.status_filter_combo.currentTextChanged.connect(self.on_status_filter_changed)
        filter_layout.addWidget(self.status_filter_combo)
        
        # Urgency filter
        urgency_filter_label = language_manager.get_notice_tab_text('urgency_filter')
        filter_layout.addWidget(QLabel(urgency_filter_label))
        self.urgency_filter_combo = QComboBox()
        self.urgency_filter_combo.addItems([
            language_manager.get_notice_tab_text('urgency_all'),
            language_manager.get_notice_tab_text('urgency_normal'),
            language_manager.get_notice_tab_text('urgency_urgent'),
            language_manager.get_notice_tab_text('urgency_very_urgent')
        ])
        self.urgency_filter_combo.setMinimumWidth(120)
        self.urgency_filter_combo.currentTextChanged.connect(self.on_urgency_filter_changed)
        filter_layout.addWidget(self.urgency_filter_combo)
        
        # Search
        search_label = language_manager.get_notice_tab_text('search_label')
        filter_layout.addWidget(QLabel(search_label))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(language_manager.get_notice_tab_text('search_placeholder'))
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Auto-refresh checkbox
        auto_refresh_layout = QHBoxLayout()
        auto_refresh_text = language_manager.get_notice_tab_text('auto_refresh')
        self.auto_refresh_cb = QCheckBox(auto_refresh_text)
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.toggled.connect(self.on_auto_refresh_toggled)
        auto_refresh_layout.addWidget(self.auto_refresh_cb)
        auto_refresh_layout.addStretch()
        layout.addLayout(auto_refresh_layout)
        
        # Table
        self.table = HorizontalScrollTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            language_manager.get_notice_tab_text('header_tracking_id'),
            language_manager.get_notice_tab_text('header_customer'),
            language_manager.get_notice_tab_text('header_product'),
            language_manager.get_notice_tab_text('header_date'),
            language_manager.get_notice_tab_text('header_urgency'),
            language_manager.get_notice_tab_text('header_status'),
            language_manager.get_notice_tab_text('header_accepted_by')
        ])
        
        # Setup table
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.on_double_click)
        
        # Column widths
        self.table.setColumnWidth(0, 80)   # Tracking ID
        self.table.setColumnWidth(1, 180)   # Customer
        self.table.setColumnWidth(2, 200)   # Product
        self.table.setColumnWidth(3, 130)   # Date
        self.table.setColumnWidth(4, 100)   # Urgency
        self.table.setColumnWidth(5, 100)   # Status
        
        # Style
        self.table.setStyleSheet("""
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
        """)
        
        layout.addWidget(self.table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        refresh_text = language_manager.get_notice_tab_text('btn_refresh')
        self.refresh_btn = QPushButton(refresh_text)
        self.refresh_btn.clicked.connect(self.load_notices)
        buttons_layout.addWidget(self.refresh_btn)
        
        self.refresh_btn.setMinimumWidth(120)
        
        view_text = language_manager.get_notice_tab_text('btn_view')
        self.view_btn = QPushButton(view_text)
        self.view_btn.clicked.connect(self.view_selected)
        buttons_layout.addWidget(self.view_btn)
        
        accept_text = language_manager.get_notice_tab_text('btn_accept')
        self.accept_btn = QPushButton(accept_text)
        self.accept_btn.setObjectName("acceptButton")
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F7ACB;
                color: #FFFFFF;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                border: 1px solid #1A6EB6;
            }
            QPushButton:hover {
                background-color: #1A6EB6;
            }
            QPushButton:disabled {
                background-color: #CBD5E1;
            }
        """)
        self.accept_btn.clicked.connect(self.accept_job)
        buttons_layout.addWidget(self.accept_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Details panel (expandable)
        details_title = language_manager.get_notice_tab_text('details_title')
        self.details_group = QGroupBox(details_title)
        self.details_group.setVisible(False)
        details_layout = QGridLayout()
        
        self.details_label = QLabel()
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #FFFFFF;
                border: 1px solid #D8E0EA;
                border-radius: 8px;
            }
        """)
        details_layout.addWidget(self.details_label, 0, 0, 1, 2)
        
        close_text = language_manager.get_notice_tab_text('btn_close')
        self.close_details_btn = QPushButton(close_text)
        self.close_details_btn.clicked.connect(self.hide_details)
        details_layout.addWidget(self.close_details_btn, 1, 1, Qt.AlignRight)
        
        self.details_group.setLayout(details_layout)
        layout.addWidget(self.details_group)
        
        self.setLayout(layout)
    
    def set_user_info(self, user_info: Dict[str, Any]):
        """Thiáº¿t láº­p thÃ´ng tin user hiá» n táº¡i"""
        self.current_user_info = user_info
        
        # Update info label
        role = user_info.get('role', '')
        role_map = {
            'sales': language_manager.get_notice_tab_text('role_sales'),
            'engineer': language_manager.get_notice_tab_text('role_engineer'),
            'admin': language_manager.get_notice_tab_text('role_admin'),
            'IT': language_manager.get_notice_tab_text('role_it'),
            'Pur': language_manager.get_notice_tab_text('role_pur')
        }
        role_display = role_map.get(role, role)
        
        full_name = user_info.get('full_name', '')
        user_info_text = language_manager.get_notice_tab_text('user_info').format(full_name, role_display)
        info_sales_text = language_manager.get_notice_tab_text('info_sales')
        self.info_label.setText(f"{user_info_text}\n{info_sales_text}")
        
        # Show/hide accept button based on permission
        from src.session_manager import session_manager
        if session_manager.can_accept_job_with_permission():
            self.accept_btn.setVisible(True)
            # Engineers can see "Cá»§a tÃ´i" filter
            self.status_filter_combo.addItem(language_manager.get_notice_tab_text('filter_mine'))
        else:
            self.accept_btn.setVisible(False)
        
        # Reload notices
        self.load_notices()
    
    def load_notices(self):
        """Load notices tá»?server"""
        from src.session_manager import session_manager
        
        # Show loading text
        loading_text = language_manager.get_notice_tab_text('loading')
        self.info_label.setText(loading_text)
        
        # Check user role
        if session_manager.is_engineer() or session_manager.is_admin():
            # Engineer/Admin: Load ALL notices (pending + accepted)
            engineer_name = session_manager.get_full_name() or session_manager.get_current_user()
            if engineer_name:
                self.notice_loader = EngineerNoticeLoader(self.server_ip, engineer_name)
                self.notice_loader.notices_loaded.connect(self.on_notices_loaded)
                self.notice_loader.error_occurred.connect(self.on_notices_error)
                self.notice_loader.start()
                return
        
        # Sales: Only load their own pending notices
        user_id = None
        if session_manager.is_sales():
            user_id = session_manager.get_user_id()
        
        self.notice_loader = NoticeLoader(self.server_ip, user_id)
        self.notice_loader.notices_loaded.connect(self.on_notices_loaded)
        self.notice_loader.error_occurred.connect(self.on_notices_error)
        self.notice_loader.start()
    
    def on_notices_loaded(self, notices: List[Dict]):
        """Xá»?lÃ½ khi load notices thÃ nh cÃ´ng"""
        self.notices = notices
        self.apply_filters()
        
        # Update info
        count = len(notices)
        if count == 0:
            no_requests_text = language_manager.get_notice_tab_text('no_requests')
            self.info_label.setText(no_requests_text)
        else:
            total_text = language_manager.get_notice_tab_text('total_requests').format(count)
            info_text = language_manager.get_notice_tab_text('info_double_click')
            self.info_label.setText(f"{total_text}\n{info_text}")
    
    def on_notices_error(self, error: str):
        """Xá»?lÃ½ khi load notices lá» i"""
        error_title = language_manager.get_notice_tab_text('error_title')
        load_error = language_manager.get_notice_tab_text('load_error').format(error)
        QMessageBox.warning(self, error_title, load_error)
        self.info_label.setText(language_manager.get_notice_tab_text('load_error').format(error))
    
    def on_status_filter_changed(self, text: str):
        """Xá»?lÃ½ khi thay Ä á» i filter tráº¡ng thÃ¡i"""
        self.current_status_filter = text
        self.apply_filters()
    
    def on_urgency_filter_changed(self, text: str):
        """Xá»?lÃ½ khi thay Ä á» i filter Ä á»?kháº©n"""
        self.current_urgency_filter = text
        self.apply_filters()
    
    def on_search_text_changed(self, text: str):
        """Xá»?lÃ½ khi thay Ä á» i text tÃ¬m kiáº¿m"""
        self.current_search_text = text.strip().lower()
        self.apply_filters()
    
    def on_auto_refresh_toggled(self, checked: bool):
        """Xá»?lÃ½ khi thay Ä á» i auto-refresh"""
        self.auto_refresh_enabled = checked
        if checked:
            self.refresh_timer.start(self.auto_refresh_interval)
        else:
            self.refresh_timer.stop()
    
    def apply_filters(self):
        """Apply all filters and refresh table."""
        filtered_notices = self.notices.copy()
        
        # Get filter values from language_manager
        filter_pending = language_manager.get_notice_tab_text('filter_pending')
        filter_accepted = language_manager.get_notice_tab_text('filter_accepted')
        filter_mine = language_manager.get_notice_tab_text('filter_mine')
        urgency_all = language_manager.get_notice_tab_text('urgency_all')
        urgency_normal = language_manager.get_notice_tab_text('urgency_normal')
        urgency_urgent = language_manager.get_notice_tab_text('urgency_urgent')
        urgency_very_urgent = language_manager.get_notice_tab_text('urgency_very_urgent')
        
        # Filter by status
        if self.current_status_filter == filter_pending:
            filtered_notices = [n for n in filtered_notices if n.get('is_pending') == 'yes']
        elif self.current_status_filter == filter_accepted:
            filtered_notices = [n for n in filtered_notices if n.get('is_pending') == 'no']
        elif self.current_status_filter == filter_mine:
            # For engineers: show jobs they accepted
            from src.session_manager import session_manager
            current_user = session_manager.get_full_name() or session_manager.get_current_user()
            filtered_notices = [n for n in filtered_notices 
                               if n.get('accepted_by') == current_user]
        
        # Filter by urgency
        if self.current_urgency_filter != urgency_all:
            urgency_map = {
                urgency_normal: "normal",
                urgency_urgent: "urgent",
                urgency_very_urgent: "very_urgent"
            }
            target_urgency = urgency_map.get(self.current_urgency_filter, "")
            if target_urgency:
                filtered_notices = [n for n in filtered_notices 
                                  if n.get('urgency_level') == target_urgency]
        
        # Filter by search text
        if self.current_search_text:
            search_text = self.current_search_text
            filtered_notices = [n for n in filtered_notices if self._matches_search(n, search_text)]
        
        self.populate_table(filtered_notices)
    
    def _matches_search(self, notice: Dict, search_text: str) -> bool:
        """Kiá» m tra notice cÃ³ khá» p vá» i text tÃ¬m kiáº¿m khÃ´ng"""
        # Láº¥y data - Æ°u tiÃªn tá»?root level, náº¿u khÃ´ng cÃ³ thÃ¬ parse tá»?'data' field
        if 'KhÃ¡ch hÃ ng' in notice:
            data = notice  # Dá»?liá» u á»?root level (schema má» i)
        else:
            # Parse data tá»?'data' field (schema cÅ©)
            data_str = notice.get('data', '{}')
            try:
                data = json.loads(data_str) if isinstance(data_str, str) else data_str
            except:
                data = {}
        
        # Check various fields
        customer = data.get('KhÃ¡ch hÃ ng', '').lower()
        product = data.get('TÃªn sáº£n pháº©m', '').lower()
        tracking_id = str(notice.get('Tracking ID', ''))
        sales_name = data.get('NhÃ¢n viÃªn kinh doanh', '').lower()
        
        return (search_text in customer or
                search_text in product or 
                search_text in tracking_id or
                search_text in sales_name)
    
    def populate_table(self, notices: List[Dict]):
        """Hiá» n thá»?notices lÃªn table"""
        self.table.setRowCount(0)
        
        for notice in notices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Láº¥y data - Æ°u tiÃªn tá»?root level, náº¿u khÃ´ng cÃ³ thÃ¬ parse tá»?'data' field
            if 'KhÃ¡ch hÃ ng' in notice:
                data = notice  # Dá»?liá» u á»?root level (schema má» i)
            else:
                # Parse data tá»?'data' field (schema cÅ©)
                data_str = notice.get('data', '{}')
                try:
                    data = json.loads(data_str) if isinstance(data_str, str) else data_str
                except:
                    data = {}
            
            # Format tracking ID with leading zeros
            tracking_id = notice.get('Tracking ID', 0)
            tracking_id_str = str(tracking_id)
            
            # Tracking ID
            item_id = QTableWidgetItem(tracking_id_str)
            item_id.setData(Qt.UserRole, notice)  # Store full notice data
            self.table.setItem(row, 0, item_id)
            
            # Customer
            customer = data.get('KhÃ¡ch hÃ ng', '-')
            self.table.setItem(row, 1, QTableWidgetItem(customer))
            
            # Product
            product = data.get('TÃªn sáº£n pháº©m', '-')
            self.table.setItem(row, 2, QTableWidgetItem(product))
            
            # Created Date - sá»?dá»¥ng Created_Date hoáº·c NgÃ y thay vÃ¬ created_at
            created = notice.get('Created_Date', notice.get('NgÃ y', '-'))
            if created and created != '-':
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            self.table.setItem(row, 3, QTableWidgetItem(created))
            
            # Urgency
            urgency = notice.get('urgency_level', 'normal')
            urgency_display_map = {
                'normal': language_manager.get_notice_tab_text('urgency_normal_display'),
                'urgent': language_manager.get_notice_tab_text('urgency_urgent_display'),
                'very_urgent': language_manager.get_notice_tab_text('urgency_very_urgent_display')
            }
            urgency_text = urgency_display_map.get(urgency, '-')
            
            item_urgency = QTableWidgetItem(urgency_text)
            
            # Color based on urgency
            if urgency == 'very_urgent':
                item_urgency.setBackground(QColor(255, 200, 200))  # Red
            elif urgency == 'urgent':
                item_urgency.setBackground(QColor(255, 255, 200))  # Yellow
            else:
                item_urgency.setBackground(QColor(200, 255, 200))  # Green
            
            self.table.setItem(row, 4, item_urgency)
            
            # Status
            is_pending = notice.get('is_pending', 'yes')
            if is_pending == 'yes':
                status_text = language_manager.get_notice_tab_text('status_pending')
                status_color = QColor(255, 255, 200)  # Yellow
            else:
                status_text = language_manager.get_notice_tab_text('status_accepted')
                status_color = QColor(200, 255, 200)  # Green
            
            item_status = QTableWidgetItem(status_text)
            item_status.setBackground(status_color)
            self.table.setItem(row, 5, item_status)
            
            # Accepted by
            accepted_by = notice.get('accepted_by', '-')
            self.table.setItem(row, 6, QTableWidgetItem(accepted_by))
        
        # Resize columns
        self.table.resizeColumnsToContents()
    
    def on_double_click(self, index):
        """Xá»?lÃ½ khi double-click vÃ o row"""
        row = index.row()
        self.view_details(row)
    
    def view_selected(self):
        """Xem chi tiáº¿t record Ä Æ°á»£c chá» n"""
        selected = self.table.selectedIndexes()
        if not selected:
            select_warning = language_manager.get_notice_tab_text('select_to_view')
            QMessageBox.warning(self, language_manager.get_notice_tab_text('notice_confirm_accept'), select_warning)
            return
        
        row = selected[0].row()
        self.view_details(row)
    
    def view_details(self, row: int):
        """Hiá» n thá»?chi tiáº¿t cá»§a row"""
        # Get the notice from the table item
        item = self.table.item(row, 0)
        if not item:
            return
        
        notice = item.data(Qt.UserRole)
        if not notice:
            return
        
        # Láº¥y data - Æ°u tiÃªn tá»?root level, náº¿u khÃ´ng cÃ³ thÃ¬ parse tá»?'data' field
        if 'KhÃ¡ch hÃ ng' in notice:
            data = notice  # Dá»?liá» u á»?root level (schema má» i)
        else:
            data_str = notice.get('data', '{}')
            try:
                data = json.loads(data_str) if isinstance(data_str, str) else data_str
            except:
                data = {}
        
        # Get texts from language_manager
        texts = language_manager.get_all_ui_texts()
        
        # Build details text using language_manager
        is_pending = notice.get('is_pending', 'yes')
        status_pending = texts.get('notice_status_pending', 'â ?Chá»?nháº­n')
        status_accepted = texts.get('notice_status_accepted', 'â ?Ä Ã£ nháº­n')
        status_text = status_pending if is_pending == 'yes' else status_accepted
        accepted_by = notice.get('accepted_by', '-')
        accepted_at = notice.get('accepted_at', '-')
        
        # Get desired time - check both new and old keys for compatibility
        desired_time = data.get('Desired Solution Time', '-')
        
        # Get urgency level and display in current language
        urgency_value = notice.get('urgency_level', data.get('urgency_level', 'normal'))
        urgency_display = language_manager.get_urgency_level_display(urgency_value)
        
        details = f"""
<b>{texts.get('notice_details_title', 'ð    Chi tiáº¿t')}</b>

<b>{texts.get('notice_details_tracking_id', 'Tracking ID:')}</b> {notice.get('Tracking ID', 0)}
<b>{texts.get('notice_details_created_date', 'NgÃ y táº¡o:')}</b> {notice.get('Created_Date', notice.get('NgÃ y', '-'))}

<b>{texts.get('notice_details_customer_info', 'ð  ¤ THÃ NG TIN KHÃ CH HÃ NG')}</b>
<b>{texts.get('notice_details_customer_name', 'TÃªn khÃ¡ch hÃ ng:')}</b> {data.get('KhÃ¡ch hÃ ng', '-')}
<b>{texts.get('notice_details_contact', 'NgÆ°á» i liÃªn há»?')}</b> {data.get('NgÆ°á» i liÃªn há» \n(KH)', '-')}

<b>{texts.get('notice_details_product_info', 'ð  ¦ THÃ NG TIN Sáº¢N PHáº¨M')}</b>
<b>{texts.get('notice_details_product_name', 'TÃªn sáº£n pháº©m:')}</b> {data.get('TÃªn sáº£n pháº©m', '-')}
<b>{texts.get('notice_details_specs', 'Quy cÃ¡ch:')}</b> {data.get('Quy cÃ¡ch', '-')}

<b>{texts.get('notice_details_time_info', 'â ?THá» I GIAN')}</b>
<b>{texts.get('notice_details_urgency', 'Ä á»?kháº©n:')}</b> {urgency_display}
<b>{texts.get('notice_details_desired_time', 'Thá» i gian mong muá» n:')}</b> {desired_time}

<b>{texts.get('notice_details_sales_info', 'ð  ¨â  ð  ?NHÃ N VIÃ N Táº O')}</b>
<b>{texts.get('notice_details_sales_name', 'TÃªn:')}</b> {data.get('NhÃ¢n viÃªn kinh doanh', '-')}

<b>{texts.get('notice_details_status_info', 'ð    TRáº NG THÃ I')}</b>
<b>{texts.get('notice_details_status', 'Tráº¡ng thÃ¡i:')}</b> {status_text}
<b>{texts.get('notice_details_accepted_by', 'NgÆ°á» i nháº­n:')}</b> {accepted_by}
<b>{texts.get('notice_details_accepted_at', 'Thá» i gian nháº­n:')}</b> {accepted_at}
        """
        
        self.details_label.setText(details)
        self.details_group.setVisible(True)
        
        # Emit signal
        self.record_viewed.emit(notice)
    
    def hide_details(self):
        """áº¨n panel chi tiáº¿t"""
        self.details_group.setVisible(False)
    
    def accept_job(self):
        """Engineer nháº­n job"""
        # Kiá» m tra permission trÆ°á» c
        from src.session_manager import session_manager
        if not session_manager.can_accept_job_with_permission():
            QMessageBox.warning(
                self, 
                language_manager.get_notice_tab_text('error_title'), 
                "Báº¡n khÃ´ng cÃ³ quyá» n nháº­n job.\nVui lÃ²ng liÃªn há»?Admin Ä á»?Ä Æ°á»£c cáº¥p quyá» n."
            )
            return
        
        selected = self.table.selectedIndexes()
        if not selected:
            select_warning = language_manager.get_notice_tab_text('select_to_accept')
            QMessageBox.warning(self, language_manager.get_notice_tab_text('notice_confirm_accept'), select_warning)
            return
        
        row = selected[0].row()
        
        # Get the notice from the table item
        item = self.table.item(row, 0)
        if not item:
            return
        
        notice = item.data(Qt.UserRole)
        if not notice:
            return
        
        # Check if already accepted
        if notice.get('is_pending') == 'no':
            already_accepted = language_manager.get_notice_tab_text('already_accepted')
            QMessageBox.warning(self, language_manager.get_notice_tab_text('notice_confirm_accept'), already_accepted)
            return
        
        # Láº¥y data - Æ°u tiÃªn tá»?root level, náº¿u khÃ´ng cÃ³ thÃ¬ parse tá»?'data' field
        if 'KhÃ¡ch hÃ ng' in notice:
            data = notice  # Dá»?liá» u á»?root level (schema má» i)
        else:
            data_str = notice.get('data', '{}')
            try:
                data = json.loads(data_str) if isinstance(data_str, str) else data_str
            except:
                data = {}
        
        confirm_title = language_manager.get_notice_tab_text('confirm_accept')
        confirm_msg = language_manager.get_notice_tab_text('confirm_accept_msg').format(
            notice.get('Tracking ID', 0),
            data.get('KhÃ¡ch hÃ ng', '-')
        )
        reply = QMessageBox.question(
            self,
            confirm_title,
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Get engineer name
        from src.session_manager import session_manager
        engineer_name = session_manager.get_full_name() or session_manager.get_current_user()
        
        if not engineer_name:
            cannot_identify = language_manager.get_notice_tab_text('cannot_identify_engineer')
            QMessageBox.warning(self, language_manager.get_notice_tab_text('error_title'), cannot_identify)
            return
        
        # Send accept request to server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((self.server_ip, 8001))
            
            request = {
                "request": "ACCEPT_JOB",
                "tracking_id": int(notice.get('Tracking ID', 0)),
                "engineer_name": engineer_name
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
                success_msg = language_manager.get_notice_tab_text('accept_success').format(
                    notice.get('Tracking ID', 0),
                    engineer_name
                )
                QMessageBox.information(
                    self,
                    language_manager.get_notice_tab_text('new_sales_success'),
                    success_msg
                )
                
                # Emit signals
                self.record_accepted.emit(notice)
                self.data_updated.emit()
                
                # Refresh list
                self.load_notices()
                self.hide_details()
            else:
                error = response.get("error", "Unknown error")
                accept_error = language_manager.get_notice_tab_text('accept_error').format(error)
                QMessageBox.critical(self, language_manager.get_notice_tab_text('error_title'), accept_error)
                
        except Exception as e:
            conn_error = language_manager.get_notice_tab_text('connection_error').format(str(e))
            QMessageBox.critical(self, language_manager.get_notice_tab_text('error_title'), conn_error)
            print(f"[NoticeTab] Accept job error: {e}")
    
    def refresh(self):
        """Refresh notices"""
        self.load_notices()
    
    def get_pending_count(self) -> int:
        """Láº¥y sá»?lÆ°á»£ng pending notices"""
        user_id = None
        from src.session_manager import session_manager
        if session_manager.is_sales():
            user_id = session_manager.get_user_id()
        
        self.count_loader = NoticeCountLoader(self.server_ip, user_id)
        self.count_loader.count_loaded.connect(self._on_count_loaded)
        self.count_loader.error_occurred.connect(lambda e: print(f"Error loading count: {e}"))
        self.count_loader.start()
        
        return 0  # Will be updated via signal
    
    def _on_count_loaded(self, count: int):
        """Xá»?lÃ½ khi load count thÃ nh cÃ´ng"""
        # Emit signal to parent for tab badge update
        self.data_updated.emit()
    
    def get_pending_count_sync(self) -> int:
        """Láº¥y sá»?lÆ°á»£ng pending notices (synchronous, for badge)"""
        user_id = None
        from src.session_manager import session_manager
        if session_manager.is_sales():
            user_id = session_manager.get_user_id()
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(3)
            client_socket.connect((self.server_ip, 8001))
            
            request = {"request": "GET_PENDING_COUNT"}
            if user_id:
                request["user_id"] = user_id
            
            client_socket.send(json.dumps(request, ensure_ascii=False).encode('utf-8'))
            
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            client_socket.close()
            
            response = json.loads(data.decode('utf-8'))
            return response.get('count', 0) if isinstance(response, dict) else 0
            
        except Exception as e:
            print(f"[NoticeTab] Error getting count: {e}")
            return 0


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    tab = NoticeTab(server_ip="localhost")
    tab.show()
    
    sys.exit(app.exec())
