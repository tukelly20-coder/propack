import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thu thập dữ liệu người dùng")
        self.resize(400, 300)
        self.move(400, 400)

        self.label = QLabel("Họ tên: ")
        self.input_name = QLineEdit("Hoàng Đình Kelly")
        self.label_age = QLabel("Tuổi: ")
        self.input_age = QLineEdit("18")
        self.label_cao = QLabel("Chiều cao: ")
        self.input_cao = QLineEdit("180")
        self.btn_submit = QPushButton("Điền")
        self.Kq_label = QLabel("")
        self.Kq_label.setWordWrap(True)
        self.Kq_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout = QVBoxLayout() 

        layout.addWidget(self.label)
        layout.addWidget(self.input_name) 
        layout.addWidget(self.label_age)
        layout.addWidget(self.input_age)
        layout.addWidget(self.label_cao)
        layout.addWidget(self.input_cao)
        layout.addWidget(self.btn_submit)
        layout.addWidget(self.Kq_label)
        layout.addStretch()
        self.setLayout(layout)
        
        self.btn_submit.clicked.connect(self.tong_hop) #Ket noi den tong_hop

    def tong_hop(self):
        name = self.input_name.text() #lấy văn bản từ QLineEdit và lưu vào biến name
        age = self.input_age.text()
        cao = self.input_cao.text()
        self.Kq_label.setText(f"Xin chào bạn {name}! mình đã ghi thông tin của bạn, năm nay bạn {age} tuổi, và cao {cao} cm Cảm ơn bạn đã tham gia trương trình!!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

