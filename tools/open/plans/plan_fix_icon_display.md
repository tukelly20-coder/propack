# Kế hoạch sửa lỗi icon không hiển thị ổn định

## Vấn đề
Icon (`favicon.ico`) không hiển thị ổn định trên ứng dụng khi chạy dưới dạng file exe.

## Nguyên nhân gốc rễ
Trong `MaterialQueryUI.__init__` (dòng 284-286), đường dẫn icon được xác định bằng:
```python
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
```

Khi chạy dưới dạng file exe (PyInstaller), biến `__file__` không trỏ đến thư mục đúng chứa tài nguyên (`sys._MEIPASS`).

## Giải pháp

### Bước 1: Sửa đường dẫn icon trong MaterialQueryUI.__init__

Thay thế code hiện tại (dòng 283-286):
```python
# Set window icon (favicon)
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
```

Bằng code mới:
```python
# Set window icon (favicon)
import sys
if getattr(sys, 'frozen', False):
    # Chạy dưới dạng exe - lấy đường dẫn từ sys._MEIPASS
    icon_path = os.path.join(sys._MEIPASS, "favicon.ico")
else:
    # Chạy dev mode
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")

if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
else:
    print(f"Warning: Icon not found at {icon_path}")
```

### Bước 2: Build lại ứng dụng

Sử dụng PyInstaller để build lại file exe với icon mới.

### Bước 3: Test
- Chạy file exe và kiểm tra icon có hiển thị đúng trên cửa sổ và taskbar
