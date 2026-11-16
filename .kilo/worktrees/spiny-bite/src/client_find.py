"""
Module SearchDialog - Dialog tÃ¬m kiáº¿m trong lá» ch sá»?
Tham kháº£o tá»?FilterbyValue.py vÃ  Project_Tracking.py

Features:
- TÃ¬m kiáº¿m real-time khi gÃµ (local)
- TÃ¬m kiáº¿m vá» i server khi nháº¥n OK
- Checkbox Ä á»?chá» n cá» t tÃ¬m kiáº¿m
- Hiá» n thá»?sá»?káº¿t quáº?real-time
- Case-insensitive, substring match
- Sau khi server tráº?vá»?káº¿t quáº? clear danh sÃ¡ch lá» ch sá»?vÃ  hiá» n thá»?káº¿t quáº?

Logging:
- Sá»?dá»¥ng logging module Ä á»?theo dÃµi cÃ¡c hoáº¡t Ä á» ng
- Format: [TIMESTAMP] [LEVEL] [MODULE] Message
"""

import logging
from datetime import datetime
import socket
import json

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QFrame,
    QDialogButtonBox, QMessageBox, QTableWidgetItem,
    QDialogButtonBox, QComboBox, QWidget, QListWidget, QListWidgetItem
)
from PySide6.QtCore import (
    Qt
)
from PySide6.QtGui import QAction

# Setup logger
logger = logging.getLogger(__name__)

# Import language_manager
try:
    from src.language_manager import language_manager
except ImportError:
    from language_manager import language_manager


class DialogSearchRequester(QThread):
    """
    Thread Ä á»?tÃ¬m kiáº¿m lá» ch sá»?tá»?server - cho SearchDialog
    
    Args:
        server_ip: Ä á» a chá»?IP cá»§a server
        search_text: Tá»?khÃ³a tÃ¬m kiáº¿m
        columns: Danh sÃ¡ch cÃ¡c cá» t Ä á»?tÃ¬m kiáº¿m
        search_type: Loáº¡i tÃ¬m kiáº¿m - "DB_DATA" hoáº·c "HISTORY"
    
    Logging:
        - Thread initialization, connection, request sending, response handling
        - Errors: socket, JSON decode, timeout
    """
    search_completed = Signal(list)
    
    def __init__(self, server_ip, search_text, columns, search_type="DB_DATA"):
        """
        Initialize DialogSearchRequester thread
        
        Args:
            server_ip: Server IP address
            search_text: Search keyword
            columns: List of columns to search
            search_type: Search type - "DB_DATA" or "HISTORY"
        """
        super().__init__()
        self.server_ip = server_ip
        self.search_text = search_text
        self.columns = columns
        self.search_type = search_type
        
        logger.info(f"[DialogSearchRequester] Initialized - IP: {server_ip}, "
                   f"Search: '{search_text}', Columns: {columns}, SearchType: {search_type}")
    
    def run(self):
        """
        Thá»±c hiá» n tÃ¬m kiáº¿m trÃªn server
        
        Logging:
            - Connection attempt and success
            - Request sending
            - Response received (data length)
            - Search completion (result count)
            - Errors (socket, JSON, timeout)
        
        Returns:
            list: Danh sÃ¡ch cÃ¡c báº£n ghi phÃ¹ há»£p vá» i Ä iá» u kiá» n tÃ¬m kiáº¿m
        """
        logger.debug(f"[DialogSearchRequester] Starting search request to {self.server_ip}")
        
        # Validate server IP
        try:
            socket.getaddrinfo(self.server_ip, 8001)
            logger.debug(f"[DialogSearchRequester] Server IP {self.server_ip} is valid")
        except socket.gaierror as e:
            logger.error(f"[DialogSearchRequester] Invalid server IP: {self.server_ip}, Error: {e}")
            self.search_completed.emit([])
            return
        
        # Connect to server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            
            logger.debug(f"[DialogSearchRequester] Connecting to {self.server_ip}:8001")
            client_socket.connect((self.server_ip, 8001))
            logger.info(f"[DialogSearchRequester] Connected to server successfully")
            
            # Send search request
            request_type = "SEARCH_DB_DATA" if self.search_type == "DB_DATA" else "SEARCH_HISTORY"
            request = {
                "request": request_type,
                "search_text": self.search_text,
                "columns": self.columns
            }
            logger.debug(f"[DialogSearchRequester] Sending request: {json.dumps(request)}")
            client_socket.send(json.dumps(request).encode('utf-8'))
            
            # Receive response
            data = b''
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk
            
            data_length = len(data)
            logger.debug(f"[DialogSearchRequester] Received {data_length} bytes")
            
            if not data.strip():
                results = []
                logger.info(f"[DialogSearchRequester] Empty response from server")
            else:
                results = json.loads(data)
                logger.info(f"[DialogSearchRequester] Search completed - {len(results)} results found")
            
            client_socket.close()
            self.search_completed.emit(results)
            
        except json.JSONDecodeError as e:
            logger.error(f"[DialogSearchRequester] JSON decode error: {e}")
            self.search_completed.emit([])
        except socket.timeout:
            logger.warning(f"[DialogSearchRequester] Socket timeout connecting to {self.server_ip}")
            self.search_completed.emit([])
        except ConnectionRefusedError as e:
            logger.warning(f"[DialogSearchRequester] Connection refused by {self.server_ip}: {e}")
            self.search_completed.emit([])
        except Exception as e:
            logger.error(f"[DialogSearchRequester] Unexpected error: {e}")
            self.search_completed.emit([])
        
        logger.debug(f"[DialogSearchRequester] Thread finished")


class SearchDialog(QDialog):
    """
    Dialog tÃ¬m kiáº¿m trong lá» ch sá»?- tham kháº£o FilterByValueDialog
    
    Features:
    - TÃ¬m kiáº¿m real-time khi gÃµ (local)
    - TÃ¬m kiáº¿m vá» i server khi nháº¥n OK
    - Checkbox Ä á»?chá» n cá» t tÃ¬m kiáº¿m
    - Hiá» n thá»?sá»?káº¿t quáº?real-time
    - Case-insensitive, substring match
    - Sau khi server tráº?vá»?káº¿t quáº? clear danh sÃ¡ch lá» ch sá»?vÃ  hiá» n thá»?káº¿t quáº?
    
    Logging:
        - Dialog initialization, search operations, result handling
        - User interactions (accept, reject, cancel)
    """
    
    def __init__(self, parent=None, server_ip=None, history_data=None, headers=None, search_type="DB_DATA"):
        """
        Initialize SearchDialog
        
        Args:
            parent: Parent widget (MainWindow)
            server_ip: Ä á» a chá»?IP cá»§a server
            history_data: Danh sÃ¡ch dá»?liá» u lá» ch sá»?Ä á»?tÃ¬m kiáº¿m (local)
            headers: Dictionary mapping display headers to data keys
                    Format: {"TÃªn": "name", "MÃ£ NV": "employee", ...}
            search_type: Loáº¡i tÃ¬m kiáº¿m - "DB_DATA" hoáº·c "HISTORY"
        
        Logging:
            - Dialog initialization with data count and headers
        """
        super().__init__(parent)
        
        self.parent_window = parent
        self.server_ip = server_ip
        self.all_history_data = history_data or []
        self.filtered_data = list(self.all_history_data)
        self.headers = headers or {}
        self.search_requester = None
        self.search_type = search_type
        
        logger.info(f"[SearchDialog] Initialized - Records: {len(self.all_history_data)}, "
                   f"Headers: {list(self.headers.keys())}, Server IP: {server_ip}, SearchType: {search_type}")
        
        # Láº¥y texts tá»?language_manager
        self.texts = language_manager.get_all_ui_texts()
        
        self.setup_ui()
        self.update_result_count()
        
        logger.debug(f"[SearchDialog] UI setup completed")
    
    def setup_ui(self):
        """Thiáº¿t láº­p giao diá» n dialog - tham kháº£o FilterbyValue.py"""
        # Window title
        window_title = self.texts.get("search_dialog_title", "TÃ¬m kiáº¿m")
        self.setWindowTitle(window_title)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Search input section - tham kháº£o FilterbyValue.py
        search_layout = QHBoxLayout()
        search_label_text = self.texts.get("search_label", "TÃ¬m:")
        search_label = QLabel(search_label_text)
        search_label.setFixedWidth(50)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.texts.get("search_placeholder", "Nháº­p tá»?khÃ³a tÃ¬m kiáº¿m..."))
        self.search_input.textChanged.connect(self.filter_list)
        # Focus vÃ o search input khi má»?dialog
        self.search_input.setFocus()
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Separator line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)
        
        # Column selection label
        columns_label_text = self.texts.get("search_columns_label", "TÃ¬m trong cÃ¡c cá» t:")
        columns_label = QLabel(columns_label_text)
        columns_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(columns_label)
        
        # Column selection using QListWidget with checkboxes - UX improved
        column_select_layout = QHBoxLayout()
        
        # Create list widget for column selection
        self.column_list = QListWidget()
        self.column_list.setMaximumHeight(80)  # Compact height
        self.column_list.setSpacing(2)
        
        # Add columns as checkable items
        for data_key, display_header in self.headers.items():
            item = QListWidgetItem(display_header)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, data_key)  # Store data key
            self.column_list.addItem(item)
        
        # Connect selection changed to filter
        self.column_list.itemChanged.connect(self.on_column_changed)
        
        column_select_layout.addWidget(self.column_list)
        
        # Add All/None quick buttons in vertical layout
        button_layout = QVBoxLayout()
        button_layout.setSpacing(2)
        
        select_all_btn = QPushButton(self.texts.get("select_all", "All"))
        select_all_btn.setFixedWidth(40)
        select_all_btn.setToolTip(self.texts.get("select_all_tooltip", "Chá» n táº¥t cáº?cá» t"))
        select_all_btn.clicked.connect(self.select_all_columns)
        button_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton(self.texts.get("clear_all", "None"))
        clear_all_btn.setFixedWidth(40)
        clear_all_btn.setToolTip(self.texts.get("clear_all_tooltip", "Bo chon tat ca"))
        clear_all_btn.clicked.connect(self.clear_all_columns)
        button_layout.addWidget(clear_all_btn)
        
        column_select_layout.addLayout(button_layout)
        layout.addLayout(column_select_layout)
        
        # Separator line
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Result count label - tham kháº£o FilterbyValue.py
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold; color: blue; font-size: 12px;")
        layout.addWidget(self.result_label)
        
        # Buttons - OK / Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def filter_list(self):
        """
        Thá»±c hiá» n tÃ¬m kiáº¿m local - tham kháº£o Project_Tracking.search_data() (lines 624-643)
        
        Logic:
        - Case-insensitive: sá»?dá»¥ng .lower()
        - Substring match: sá»?dá»¥ng 'in' operator
        - Real-time: Ä Æ°á»£c gá» i khi text thay Ä á» i
        
        Logging:
            - Search text, selected columns, result count
        """
        search_text = self.search_input.text().lower().strip()
        selected_columns = self.get_selected_columns()
        
        logger.debug(f"[SearchDialog] Filtering - Text: '{search_text}', "
                    f"Columns: {selected_columns}, Results: {len(self.filtered_data)}")
        
        if not search_text:
            # KhÃ´ng cÃ³ text tÃ¬m kiáº¿m, hiá» n thá»?táº¥t cáº?dá»?liá» u
            self.filtered_data = list(self.all_history_data)
            logger.debug(f"[SearchDialog] No search text, showing all {len(self.filtered_data)} records")
        else:
            self.filtered_data = []
            for item in self.all_history_data:
                # TÃ¬m kiáº¿m trong cÃ¡c cá» t Ä Ã£ chá» n - tham kháº£o Project_Tracking.search_data
                found = False
                for col in selected_columns:
                    value = item.get(col, "")
                    if value and search_text in str(value).lower():
                        found = True
                        break
                
                if found:
                    self.filtered_data.append(item)
            
            logger.debug(f"[SearchDialog] Filtered {len(self.filtered_data)} records from {len(self.all_history_data)}")
        
        self.update_result_count()
    
    def get_selected_columns(self):
        """
        Tráº?vá»?danh sÃ¡ch cÃ¡c cá» t Ä Æ°á»£c chá» n Ä á»?search
        
        Returns:
            list: Danh sÃ¡ch data keys cá»§a cÃ¡c cá» t Ä Æ°á»£c checked
        
        Logging:
            - Selected columns list
        """
        selected = []
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if item.checkState() == Qt.Checked:
                data_key = item.data(Qt.UserRole)
                selected.append(data_key)
        logger.debug(f"[SearchDialog] Selected columns: {selected}")
        return selected
    
    def on_column_changed(self, item):
        """
        Xá»?lÃ½ khi checkbox cá»§a má» t cá» t thay Ä á» i
        
        Args:
            item: QListWidgetItem Ä Ã£ thay Ä á» i
        """
        self.filter_list()
    
    def select_all_columns(self):
        """
        Chá» n táº¥t cáº?cÃ¡c cá» t
        """
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.Checked)
        logger.debug(f"[SearchDialog] Selected all columns")
        self.filter_list()
    
    def clear_all_columns(self):
        """
        Bá»?chá» n táº¥t cáº?cÃ¡c cá» t
        """
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.Unchecked)
        logger.debug(f"[SearchDialog] Cleared all columns")
        self.filter_list()
    
    def update_result_count(self):
        """Cáº­p nháº­t sá»?káº¿t quáº?tÃ¬m kiáº¿m - tham kháº£o FilterbyValue.py
        
        Logging:
            - Total records and filtered count
        """
        total = len(self.all_history_data)
        filtered = len(self.filtered_data)
        
        if self.search_input.text().strip():
            # Ä ang cÃ³ tÃ¬m kiáº¿m local
            search_results_text = self.texts.get("search_results_count", "TÃ¬m tháº¥y: {} / {}")
            self.result_label.setText(search_results_text.format(filtered, total))
            logger.debug(f"[SearchDialog] Result count update - Filtered: {filtered}, Total: {total}")
        else:
            # KhÃ´ng cÃ³ tÃ¬m kiáº¿m
            total_records_text = self.texts.get("total_records", "Tá» ng sá»? {}")
            self.result_label.setText(total_records_text.format(total))
            logger.debug(f"[SearchDialog] Total records: {total}")
    
    def get_search_results(self):
        """
        Tráº?vá»?danh sÃ¡ch káº¿t quáº?tÃ¬m kiáº¿m (local)
        
        Returns:
            list: Danh sÃ¡ch cÃ¡c báº£n ghi phÃ¹ há»£p vá» i Ä iá» u kiá» n tÃ¬m kiáº¿m
        """
        return self.filtered_data
    
    def get_search_text(self):
        """
        Tráº?vá»?text tÃ¬m kiáº¿m hiá» n táº¡i
        
        Returns:
            str: Tá»?khÃ³a tÃ¬m kiáº¿m
        """
        return self.search_input.text().strip()
    
    def accept(self):
        """
        Override accept - gá»­i request tÃ¬m kiáº¿m lÃªn server, sau Ä Ã³ clear history vÃ  hiá» n thá»?káº¿t quáº?
        
        Logging:
            - Accept called, search parameters
            - Server search start or local search fallback
        """
        search_text = self.search_input.text().strip()
        selected_columns = self.get_selected_columns()
        
        logger.info(f"[SearchDialog] Accept called - Search: '{search_text}', Columns: {selected_columns}, SearchType: {self.search_type}")
        
        if search_text and self.server_ip:
            # Gá»­i request tÃ¬m kiáº¿m lÃªn server
            logger.info(f"[SearchDialog] Starting server search to {self.server_ip}, type: {self.search_type}")
            self.search_requester = DialogSearchRequester(
                self.server_ip, search_text, selected_columns, self.search_type
            )
            self.search_requester.search_completed.connect(
                self.on_search_completed, Qt.QueuedConnection
            )
            self.search_requester.finished.connect(
                self.search_requester.deleteLater
            )
            self.search_requester.start()
        else:
            # KhÃ´ng cÃ³ server_ip hoáº·c search_text, Ä Ã³ng dialog bÃ¬nh thÆ°á» ng
            # Náº¿u cÃ³ search_text nhÆ°ng khÃ´ng cÃ³ server_ip, thá»±c hiá» n tÃ¬m kiáº¿m local
            if search_text and not self.server_ip:
                logger.warning(f"[SearchDialog] No server IP, falling back to local search")
                self.on_search_completed(self.filtered_data)
            else:
                logger.debug(f"[SearchDialog] No search text, closing dialog")
                super().accept()
    
    def on_search_completed(self, results):
        """
        Xá»?lÃ½ káº¿t quáº?tÃ¬m kiáº¿m tá»?server
        
        Args:
            results: Danh sÃ¡ch káº¿t quáº?tÃ¬m kiáº¿m tá»?server
        
        Logging:
            - Search completion (result count)
            - History cleared and results displayed
            - No results warning
        """
        logger.info(f"[SearchDialog] Search completed - {len(results)} results received")
        
        if results:
            # CÃ³ káº¿t quáº?tá»?server
            # Clear danh sÃ¡ch lá» ch sá»?
            self.clear_history_list()
            
            # Hiá» n thá»?káº¿t quáº?
            self.display_search_results(results)
            
            logger.info(f"[SearchDialog] Cleared history and displaying {len(results)} results")
        else:
            # KhÃ´ng cÃ³ káº¿t quáº? hiá» n thá»?thÃ´ngbÃ¡o
            no_results_text = self.texts.get("search_no_results", "KhÃ´ng cÃ³ káº¿t quáº?nÃ o phÃ¹ há»£p")
            logger.warning(f"[SearchDialog] No results found for search")
            QMessageBox.information(self, "TÃ¬m kiáº¿m", no_results_text)
            # Quay láº¡i view ban Ä áº§u
            self.cancel_search()
        
        # Ä Ã³ng dialog
        super().accept()
    
    @staticmethod
    def open_search_dialog(parent, server_ip, history_data, history_headers, search_type="DB_DATA"):
        """
        Má»?dialog tÃ¬m kiáº¿m - static method Ä á»?dá»?gá» i tá»?Ctrl+F handler
        
        Args:
            parent: Parent widget (MainWindow)
            server_ip: Ä á» a chá»?IP cá»§a server
            history_data: Danh sÃ¡ch dá»?liá» u lá» ch sá»?
            history_headers: Dictionary mapping display headers to data keys
            search_type: Loáº¡i tÃ¬m kiáº¿m - "DB_DATA" hoáº·c "HISTORY"
        
        Returns:
            int: QDialog.Accepted hoáº·c QDialog.Rejected
        
        Logging:
            - Method called with parameters
            - Tab check result
            - Connection check result
            - Dialog opened or rejected
        """
        logger.info(f"[SearchDialog] open_search_dialog called - "
                   f"Server: {server_ip}, Records: {len(history_data)}, Headers: {list(history_headers.keys())}, SearchType: {search_type}")
        
        # Check náº¿u Ä ang á»?Tab Lá» ch sá»?
        if hasattr(parent, 'tabs') and parent.tabs.currentIndex() != 1:
            logger.warning(f"[SearchDialog] Not on History tab (current: {parent.tabs.currentIndex()}), ignoring request")
            return QDialog.Rejected
        
        logger.debug(f"[SearchDialog] User is on History tab")
        
        # Kiá» m tra káº¿t ná» i server
        if hasattr(parent, 'current_state') and parent.current_state != 'CONNECTED':
            logger.warning(f"[SearchDialog] Not connected to server (state: {parent.current_state}), cannot search")
            QMessageBox.warning(parent, "Lá» i káº¿t ná» i", 
                "Vui lÃ²ng káº¿t ná» i server trÆ°á» c khi tÃ¬m kiáº¿m.")
            return QDialog.Rejected
        
        logger.debug(f"[SearchDialog] Connected to server, opening search dialog")
        
        # Má»?dialog
        dialog = SearchDialog(parent, server_ip, history_data, history_headers, search_type)
        return dialog.exec()
    
    def display_search_results(self, search_results):
        """
        Hiá» n thá»?káº¿t quáº?tÃ¬m kiáº¿m trong parent window
        
        Args:
            search_results: Danh sÃ¡ch káº¿t quáº?tÃ¬m kiáº¿m tá»?server
        
        Logging:
            - Results displayed count
            - Parent window checks
        """
        parent = self.parent_window
        if not parent:
            logger.warning(f"[SearchDialog] No parent window, cannot display results")
            return
        
        logger.info(f"[SearchDialog] Displaying {len(search_results)} search results")
        
        # Disable pagination
        if hasattr(parent, 'prev_button'):
            parent.prev_button.setEnabled(False)
        if hasattr(parent, 'next_button'):
            parent.next_button.setEnabled(False)
        
        # Clear table first
        if hasattr(parent, 'history_table'):
            parent.history_table.setRowCount(0)
        
        # Hiá» n thá»?káº¿t quáº?
        if hasattr(parent, 'history_table'):
            parent.history_table.setRowCount(len(search_results))
            
            for row, item in enumerate(search_results):
                parent.history_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
                parent.history_table.setItem(row, 1, QTableWidgetItem(item.get('employee', '')))
                parent.history_table.setItem(row, 2, QTableWidgetItem(item.get('category', '')))
                parent.history_table.setItem(row, 3, QTableWidgetItem(item.get('code', '')))
                
                time_str = item.get('time', '')
                if time_str:
                    try:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_time = time_str
                else:
                    formatted_time = ''
                parent.history_table.setItem(row, 4, QTableWidgetItem(formatted_time))
            
            for i in range(5):
                parent.history_table.resizeColumnToContents(i)
        
        # Cáº­p nháº­t page label
        total_results = len(search_results)
        if hasattr(parent, 'page_label'):
            parent.page_label.setText(f"Tim thay: {total_results} ket qua")
        
        # Set search mode
        if hasattr(parent, 'search_mode'):
            parent.search_mode = True
        
        logger.debug(f"[SearchDialog] Results displayed successfully")
    
    def clear_history_list(self):
        """
        Clear danh sÃ¡ch lá» ch sá»?trong parent window
        
        Logging:
            - History cleared
        """
        parent = self.parent_window
        if not parent:
            logger.warning(f"[SearchDialog] No parent window, cannot clear history")
            return
        
        if hasattr(parent, 'history_data'):
            old_count = len(parent.history_data)
            parent.history_data = []
            logger.info(f"[SearchDialog] Cleared {old_count} records from history_data")
        
        if hasattr(parent, 'history_table'):
            parent.history_table.setRowCount(0)
    
    def cancel_search(self):
        """
        Há»§y bá»?cháº?Ä á»?tÃ¬m kiáº¿m vÃ  quay láº¡i view ban Ä áº§u
        
        Logging:
            - Search cancelled
        """
        parent = self.parent_window
        if not parent:
            return
        
        logger.info(f"[SearchDialog] Search cancelled, restoring view")
        
        # Reset search mode
        if hasattr(parent, 'search_mode'):
            parent.search_mode = False
        
        # Báº­t láº¡i pagination
        if hasattr(parent, 'prev_button'):
            parent.prev_button.setEnabled(True)
        if hasattr(parent, 'next_button'):
            parent.next_button.setEnabled(True)
        
        # Quay láº¡i trang hiá» n táº¡i
        if hasattr(parent, 'request_history'):
            parent.request_history()
        
        logger.debug(f"[SearchDialog] View restored")
    
    def reject(self):
        """Override reject - há»§y bá»?tÃ¬m kiáº¿m
        
        Logging:
            - Dialog rejected
            - Search thread terminated
        """
        logger.debug(f"[SearchDialog] Dialog rejected by user")
        
        # Há»§y bá»?search request náº¿u Ä ang cháº¡y
        if self.search_requester and self.search_requester.isRunning():
            self.search_requester.terminate()
            self.search_requester.wait(1000)
            logger.warning(f"[SearchDialog] Search thread terminated by user")
        
        super().reject()
