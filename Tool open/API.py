import sys
import json
import requests
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QTabWidget,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QClipboard


class TraCuuTuhaoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tra cứu Mã Bản Vẽ")
        self.resize(1050, 780)
        self.setMinimumSize(900, 650)

        # Widget chính
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(16)

        # ==================== HEADER ====================
        title = QLabel("🔍 Tra cứu Thông tin Bản Vẽ")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Nhập mã bản vẽ để tra cứu thông tin vật liệu và số hiệu")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555;")
        main_layout.addWidget(subtitle)

        # ==================== INPUT ====================
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        input_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 12px;")
        input_layout = QHBoxLayout(input_frame)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Nhập mã bản vẽ tại đây... (ví dụ: PLSX104-0000-00-A0)")
        self.entry.setFont(QFont("Arial", 12))
        self.entry.setMinimumHeight(48)
        self.entry.returnPressed.connect(self.tra_cuu)

        self.btn_search = QPushButton("🚀 Tra cứu")
        self.btn_search.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_search.setMinimumHeight(48)
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        self.btn_search.clicked.connect(self.tra_cuu)

        input_layout.addWidget(QLabel("Mã bản vẽ:"), 0)
        input_layout.addWidget(self.entry, 1)
        input_layout.addWidget(self.btn_search)
        main_layout.addWidget(input_frame)

        # ==================== TABS ====================
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.tabs, 1)

        # Tab Kết quả
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont("Consolas", 10.5))
        self.result_text.setReadOnly(True)
        self.tabs.addTab(self.result_text, "📋 Kết quả")

        # Tab Log
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9.5))
        self.log_text.setReadOnly(True)
        self.tabs.addTab(self.log_text, "📜 Log hệ thống")

        # ==================== BUTTON BAR ====================
        btn_layout = QHBoxLayout()

        self.btn_copy_full = QPushButton("📋 Copy Toàn Bộ Kết Quả")
        self.btn_copy_full.clicked.connect(self.copy_full_result)

        self.btn_copy_summary = QPushButton("📋 Copy Tóm Tắt")
        self.btn_copy_summary.clicked.connect(self.copy_summary)

        self.btn_clear = QPushButton("🗑️ Xóa Kết Quả")
        self.btn_clear.clicked.connect(self.clear_all)

        for btn in (self.btn_copy_full, self.btn_copy_summary, self.btn_clear):
            btn.setMinimumHeight(42)
            btn.setFont(QFont("Arial", 10))

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_copy_full)
        btn_layout.addWidget(self.btn_copy_summary)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        self.log("✅ Chương trình đã sẵn sàng. Mời bạn nhập mã bản vẽ.")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def tra_cuu(self):
        code = self.entry.text().strip()
        if not code:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhập mã bản vẽ!")
            return

        self.result_text.clear()
        self.log(f"🔍 Bắt đầu tra cứu mã: {code}")

        URL = "http://192.168.2.164:8080/tuhaozhaoliaohao"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "text/plain"
        }

        try:
            response = requests.post(URL, data=code, headers=headers, timeout=30)
            self.log(f"Nhận phản hồi - Status: {response.status_code}")

            self.result_text.append(f"Status Code: {response.status_code}\n")
            self.result_text.append("=" * 85 + "\n\n")

            try:
                data = response.json()
                self.result_text.append(json.dumps(data, indent=2, ensure_ascii=False))

                # Tóm tắt
                self.result_text.append("\n" + "=" * 85 + "\n")
                self.result_text.append("                  【 TÓM TẮT KẾT QUẢ 】\n\n")

                if isinstance(data, list) and len(data) > 0:
                    for i, item in enumerate(data, 1):
                        self.result_text.append(f"Kết quả {i}:")
                        self.result_text.append(f"   • Mã vật liệu       : {item.get('cInvCode', 'N/A')}")
                        self.result_text.append(f"   • Số bản vẽ         : {item.get('cEngineerFigNo', 'N/A')}")
                        self.result_text.append(f"   • Tên vật liệu      : {item.get('cInvName', 'N/A')}")
                        self.result_text.append("-" * 70 + "\n")
                    self.log(f"✅ Tra cứu thành công - Trả về {len(data)} kết quả")

                elif isinstance(data, dict):
                    self.result_text.append(f"• Mã vật liệu       : {data.get('cInvCode', 'N/A')}")
                    self.result_text.append(f"• Số bản vẽ         : {data.get('cEngineerFigNo', 'N/A')}")
                    self.result_text.append(f"• Tên vật liệu      : {data.get('cInvName', 'N/A')}")
                    self.log("✅ Tra cứu thành công")

            except:
                self.result_text.append(response.text)
                self.log("⚠️ Phản hồi không phải JSON")

        except Exception as e:
            self.log(f"❌ Lỗi: {e}")
            self.result_text.append(f"Lỗi kết nối API:\n{str(e)}")

    def copy_full_result(self):
        text = self.result_text.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copy thành công", "Đã copy toàn bộ kết quả vào clipboard!")
        else:
            QMessageBox.warning(self, "Thông báo", "Chưa có kết quả để copy!")

    def copy_summary(self):
        # Copy chỉ phần tóm tắt (tìm từ 【 TÓM TẮT 】 trở xuống)
        full_text = self.result_text.toPlainText()
        if "【 TÓM TẮT KẾT QUẢ 】" in full_text:
            summary = full_text.split("【 TÓM TẮT KẾT QUẢ 】")[-1].strip()
            QApplication.clipboard().setText("【 TÓM TẮT KẾT QUẢ 】\n\n" + summary)
            QMessageBox.information(self, "Copy thành công", "Đã copy phần tóm tắt!")
        else:
            QMessageBox.warning(self, "Thông báo", "Chưa có phần tóm tắt để copy!")

    def clear_all(self):
        self.result_text.clear()
        self.log("🧹 Đã xóa toàn bộ kết quả hiển thị")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TraCuuTuhaoWindow()
    window.show()
    window.entry.setFocus()        # Tự động focus vào ô nhập
    sys.exit(app.exec())