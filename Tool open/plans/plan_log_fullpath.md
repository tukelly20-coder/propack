# Kế hoạch: Hiển thị Log với đường dẫn đầy đủ

## Vấn đề hiện tại
1. Đường dẫn bị cắt ngắn bởi hàm `shorten_path_display` trong module core (max_len=50 ký tự)
2. QTextEdit (log panel) có thể đang wrap text khiến đường dẫn bị chia cắt

## Giải pháp

### Bước 1: Cấu hình QTextEdit cho log hiển thị đường dẫn đầy đủ
- Thiết lập `setLineWrapMode(QTextEdit.NoWrap)` để tắt wrap
- Thêm horizontal scrollbar: `setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)`
- Thiết lập font monospace để đường dẫn dễ đọc

### Bước 2: Loại bỏ việc rút gọn đường dẫn trong log
- Tại dòng 112 trong `Mở mã liệu UI.py`: thay đổi từ `core.shorten_path_display(fallback_path)` thành `fallback_path`
- Đường dẫn đầy đủ sẽ được hiển thị trong log

## Các file cần sửa đổi
1. `Mở mã liệu UI.py` - Cập nhật cấu hình QTextEdit và loại bỏ shorten_path_display

## Thay đổi cụ thể

### Thay đổi 1: Cấu hình QTextEdit (dòng ~393-395)
```python
self.txt_log = QTextEdit()
self.txt_log.setReadOnly(True)
self.txt_log.setLineWrapMode(QTextEdit.NoWrap)  # Thêm dòng này
self.txt_log.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Thêm scrollbar ngang
```

### Thay đổi 2: Loại bỏ shorten_path_display (dòng 112)
```python
# Trước:
core.safe_print(f"[INFO] Dùng đường dẫn dự phòng: {core.shorten_path_display(fallback_path)}")

# Sau:
core.safe_print(f"[INFO] Dùng đường dẫn dự phòng: {fallback_path}")
```

## Lưu ý
- Module core `Mở mã liệu 打开链接VP.py` vẫn còn nhiều lời gọi `shorten_path_display` khác
- Tuy nhiên, trong UI hiện tại, log được gửi qua signal `emitter.log_emit` 
- Các lời gọi trong core module sẽ vẫn hiển thị đường dẫn rút gọn trong log UI
- Nếu muốn hiển thị đầy đủ mọi nơi, cần sửa trực tiếp trong module core
