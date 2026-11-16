# Kế hoạch sửa lỗi UI "Chọn các mã liên quan" không khởi tạo đúng khi mới khởi động

## Tổng quan vấn đề

**Triệu chứng:** UI "Chọn các mã liên quan (Ctrl+Click)" hiển thị sẵn 25 kết quả ngay khi ứng dụng khởi động, thay vì phải tìm kiếm mới hiện ra.

**Hiển thị hiện tại:**
- "Tổng: 25 kết quả"
- "Mã duy nhất: 25"
- "Open Selected"
- "Open All Files"

---

## Phân tích nguyên nhân

### 1. Kiểm tra code hiện tại

| Vị trí | Code | Trạng thái |
|--------|------|------------|
| Line 367 | `self.lbl_list.setVisible(False)` | ✅ Đã ẩn |
| Line 372 | `self.list_matches.setVisible(False)` | ✅ Đã ẩn |
| Line 381 | `self.lbl_results_info.setVisible(False)` | ✅ Đã ẩn |
| Line 386 | `self.btn_open_selected.setVisible(False)` | ✅ Đã ẩn |
| Line 392 | `self.btn_open_all.setVisible(False)` | ✅ Đã ẩn |
| Line 437 | `self.cached_matches = []` | ✅ List rỗng |

### 2. Nguyên nhân có thể

1. **Thiếu gọi `hide_multiple_selection()` trong `on_init_finished()`** - Sau khi khởi tạo xong, UI cần được ẩn rõ ràng
2. **PySide6 bug** - Widget không bị ẩn đúng cách khi dùng `setVisible(False)` trong `__init__`
3. **Dữ liệu cũ** - Cached data từ lần chạy trước được lưu lại

---

## Giải pháp đề xuất

### ✅ Sửa lỗi: Thêm `hide_multiple_selection()` trong `on_init_finished()`

**Vị trí:** [`Mở mã liệu UI.py:694-700`](Mở mã liệu UI.py:694)

**Code hiện tại:**
```python
def on_init_finished(self):
    self.set_gui_enabled(True)
    self.txt_code.clear()
    self.txt_code.setFocus()
    self.progress_bar.setVisible(False)
    self.status_label.setText("Sẵn sàng")
    self.append_log("[SYSTEM] Hệ thống sẵn sàng.")
```

**Code sửa:**
```python
def on_init_finished(self):
    self.set_gui_enabled(True)
    self.txt_code.clear()
    self.txt_code.setFocus()
    self.progress_bar.setVisible(False)
    self.status_label.setText("Sẵn sàng")
    self.append_log("[SYSTEM] Hệ thống sẵn sàng.")
    
    # Đảm bảo UI chọn mã liên quan bị ẩn khi khởi động
    self.hide_multiple_selection()
    self.cached_matches = []  # Reset cached data
```

---

## Các bước thực hiện (Code mode)

### Bước 1: Sửa hàm `on_init_finished()`
- Thêm `self.hide_multiple_selection()` 
- Thêm `self.cached_matches = []` để reset dữ liệu

### Bước 2: Kiểm tra `user_settings.json`
- Xóa file `user_settings.json` để reset dữ liệu cũ (nếu có lưu cached matches)

### Bước 3: Test
- Chạy ứng dụng
- Kiểm tra xem UI "Chọn các mã liên quan" có bị ẩn khi khởi động không
- Tìm kiếm một mã để xác nhận UI hoạt động đúng

---

## Kiểm tra sau khi sửa

- [ ] Khi khởi động, UI "Chọn các mã liên quan" bị ẩn hoàn toàn
- [ ] Các nút "Open Selected" và "Open All Files" không hiển thị
- [ ] Kết quả tìm kiếm hiển thị đúng khi có nhiều kết quả
- [ ] Xóa dữ liệu cũ trong user_settings.json không ảnh hưởng

---

## Files cần sửa

| File | Hàm cần sửa |
|------|-------------|
| `Mở mã liệu UI.py` | `on_init_finished()` |
