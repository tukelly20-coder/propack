import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QComboBox
)
from PySide6.QtCore import Qt
from Main import MainWindow
class login_dialog (QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập hệ thống Project Tracking")
        self.setFixedSize(420, 700)
        self.label_name = QLabel("Tên đăng nhập: ")
        self.input_name = QLineEdit()
        self.label_pass = QLabel("Nhập mật khẩu: ")
        self.input_pass = QLineEdit()
        self.btn_submit = QPushButton("Đăng nhập")
        self.btn_huy    = QPushButton("Hủy")
        self.label_KQ = QLabel("")
        self.label_KQ.setWordWrap(True)

        layout = QVBoxLayout() 
        layout.addWidget(self.label_name)
        layout.addWidget(self.input_name)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.input_pass)
        layout.addWidget(self.btn_submit)
        layout.addWidget(self.btn_huy)
        layout.addWidget(self.label_KQ)
        layout.addStretch()
        self.setLayout(layout)

        self.btn_submit.clicked.connect(self.submit_error)
        self.btn_submit.clicked.connect(self.open_main)
        self.btn_huy.clicked.connect(self.clear_label)

    def submit_error(self):
        self.label_KQ.setText(f"Sai thông tin đăng nhập, bạn nhập sai tài khoản hoặc mật khẩu!!!")
    def clear_label(self):
        self.label_KQ.setText(f"")
    def open_main(self):
        self.open_main = MainWindow()
        self.open_main.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = login_dialog()
    window.show()
    sys.exit(app.exec())

