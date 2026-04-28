# Kế hoạch sửa lỗi Updater - Không có gì xảy ra khi bấm Yes để cập nhật

## Tổng quan vấn đề

**Triệu chứng:** Khi người dùng bấm "Yes" để xác nhận cập nhật, ứng dụng không có dấu hiệu thay đổi gì cả.

**Luồng hoạt động hiện tại:**
```
User clicks Yes → UI.perform_update() 
  → updater.perform_update() 
    → apply_onedir_update() [tạo batch script, set BAT_PAYLOAD_PATH]
      → nếu thành công → UI gọi restart_application() 
        → chạy batch script để swap folder
```

---

## Các vấn đề đã xác định

### 🔴 Vấn đề 1: Đường dẫn `final_extracted_folder` không được escape trong batch script

**Vị trí:** [`updater.py:391`](updater.py:391)

**Mã hiện tại:**
```python
move /y "{final_extracted_folder}" "{onedir_path}" > NUL
```

**Vấn đề:** Biến `final_extracted_folder` chứa đường dẫn với dấu backslash `\` chưa được escape. Khi đường dẫn chứa khoảng trắng hoặc ký tự đặc biệt, batch script sẽ chạy lỗi.

**So sánh với biến khác đã được escape:**
- Line 375: `backup_path_escaped = backup_path.replace('\\', '\\\\')` ✅
- Line 400: `"{backup_path_escaped}"` ✅  
- Line 391: `"{final_extracted_folder}"` ❌ CHƯA ESCAPE!

---

### 🔴 Vấn đề 2: Tên thư mục chứa ký tự Tiếng Việt

**Vị trí:** [`updater.py:311-317`](updater.py:311)

```python
app_name = os.path.basename(onedir_path)  # "Mở mã liệu UI"
temp_folder = os.path.join(tempfile.gettempdir(), f"{app_name}_update_temp")
# Kết quả: C:\Users\Kelly\AppData\Local\Temp\Mở mã liệu UI_update_temp
```

**Vấn đề:** 
1. Tên thư mục chứa ký tự Tiếng Việt có dấu (Ử, ự, ệ)
2. Khi tạo batch script với encoding UTF-8, cmd.exe có thể không xử lý đúng
3. Batch script chứa đường dẫn với Unicode có thể bị lỗi

---

### 🔴 Vấn đề 3: Thiếu logging/logic debug

**Vị trí:** [`updater.py:424-445`](updater.py:424)

Khi `perform_update()` trả về `False`, không có thông báo lỗi rõ ràng để người dùng biết vấn đề ở đâu.

---

## Giải pháp đề xuất

### ✅ Sửa vấn đề 1: Escape đường dẫn `final_extracted_folder`

**Thêm dòng sau line 375:**
```python
final_extracted_folder_escaped = final_extracted_folder.replace('\\', '\\\\')
```

**Sửa dòng 391:**
```python
# Trước:
move /y "{final_extracted_folder}" "{onedir_path}" > NUL

# Sau:
move /y "{final_extracted_folder_escaped}" "{onedir_path}" > NUL
```

---

### ✅ Sửa vấn đề 2: Sử dụng tên thư mục an toàn

**Thay thế cách tạo temp_folder:**
```python
# Thay vì:
temp_folder = os.path.join(tempfile.gettempdir(), f"{app_name}_update_temp")

# Sử dụng tên không dấu:
safe_app_name = "app_update"  # hoặc tạo từ hash
temp_folder = os.path.join(tempfile.gettempdir(), f"{safe_app_name}_{timestamp}")
```

**Hoặc thêm xử lý Unicode an toàn hơn trong batch script:**
- Đảm bảo batch script sử dụng đường dẫn ngắn 8.3 (nếu có thể)
- Hoặc wrap đường dẫn trong dấu ngoặc kép đúng cách

---

### ✅ Sửa vấn đề 3: Thêm logging rõ ràng hơn

**Trong hàm `perform_update()`:**
- Thêm log chi tiết từng bước
- Trả về thông báo lỗi cụ thể hơn

---

## Các bước thực hiện (Code mode)

### Bước 1: Sửa escape đường dẫn trong batch script
- Thêm `final_extracted_folder_escaped`
- Sử dụng biến escaped trong batch script

### Bước 2: Cải thiện tên thư mục tạm
- Sử dụng tên thư mục không dấu hoặc timestamp

### Bước 3: Thêm logging chi tiết
- Log từng bước trong quá trình update
- Hiển thị đường dẫn batch script để debug

### Bước 4: Test
- Chạy ứng dụng và bấm Kiểm tra cập nhật
- Bấm Yes để xác nhận update
- Kiểm tra xem batch script có được tạo và chạy không

---

## Kiểm tra sau khi sửa

- [ ] Khi bấm Yes, log hiển thị các bước tải → giải nén → chuẩn bị update
- [ ] Batch script được tạo trong thư mục temp
- [ ] Batch script chạy thành công và swap folder
- [ ] Ứng dụng khởi động lại với phiên bản mới

---

## Backup/Recovery

Nếu quá trình update thất bại:
- Thư mục backup được tạo: `{app_name}_backup_{timestamp}`
- Batch script sẽ tự động restore nếu lỗi xảy ra
- Kiểm tra `update_state.json` để xem trạng thái
