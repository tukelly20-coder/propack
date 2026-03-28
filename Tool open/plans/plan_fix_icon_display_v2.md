# Kế hoạch sửa lỗi icon không hiển thị khi chạy exe từ thư mục khác (v2)

## Vấn đề hiện tại
- Icon chỉ hiển thị khi chạy exe từ thư mục gốc "Tool open"
- Khi copy exe sang "C:\Users\Kelly\Desktop\in use 打开料号\" icon mất

## Phân tích nguyên nhân
Có 2 loại icon cần xử lý:
1. **Window icon** - icon trên cửa sổ ứng dụng (dùng `setWindowIcon()`)
2. **Executable icon** - icon hiển thị trong Windows Explorer

Code hiện tại (dòng 284-293 và 928-936) đã xử lý `sys._MEIPASS` nhưng cần cải thiện.

## Giải pháp

### Bước 1: Cập nhật code xử lý icon trong MaterialQueryUI.__init__ (dòng ~283)
```python
# Set window icon (favicon)
import sys
if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
    # Chạy dưới dạng exe
    icon_path = os.path.join(sys._MEIPASS, "favicon.ico")
else:
    # Chạy dev mode hoặc fallback
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "favicon.ico")

if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
    print(f"[INFO] Window icon loaded from: {icon_path}")
else:
    print(f"[WARNING] Icon not found at: {icon_path}")
```

### Bước 2: Cập nhật code xử lý icon trong main (dòng ~928)
```python
# Xử lý icon cho app
if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(base_path, "favicon.ico")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))
    print(f"[INFO] App icon loaded from: {icon_path}")
```

### Bước 3: Rebuild ứng dụng
Sử dụng PyInstaller với spec file hiện tại.

### Bước 4: Test
- Chạy exe từ thư mục gốc
- Copy exe sang thư mục khác và chạy
- Kiểm tra icon trên cửa sổ và trong Explorer
