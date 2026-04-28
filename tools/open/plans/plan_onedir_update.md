# Kế hoạch tối ưu hóa Update cho OneDir

## Vấn đề hiện tại

Khi đóng gói thành onedir (như `Mo ma lieu UI.exe`):
- Thư mục onedir chỉ chứa file `.exe` và các resource, **không có file `.py` gốc**
- [`create_update.py`](create_update.py:19) hiện tại đóng gói các file `.py` → khi update chạy trong exe, không có file `.py` để ghi đè
- Cần thay đổi cơ chế update để phù hợp với onedir

## Giải pháp đề xuất

### Phương án: Update toàn bộ thư mục OneDir

Thay vì cập nhật từng file `.py`, sẽ cập nhật toàn bộ thư mục onedir:

```
Network Share/
└── updates/
    ├── update_info.json      # Thông tin version
    ├── onedir_v3.2.4.zip     # Toàn bộ thư mục onedir đóng gói
```

### Luồng hoạt động mới:

1. **Kiểm tra update**:
   - Đọc `update_info.json` để lấy version mới
   - So sánh với version hiện tại

2. **Tải và áp dụng update**:
   - Tải file `onedir_v{version}.zip` từ network
   - Giải nén vào thư mục tạm
   - Di chuyển thư mục hiện tại sang backup
   - Di chuyển thư mục mới vào vị trí
   - Khởi động app mới

3. **Xử lý backup**:
   - Giữ thư mục backup để rollback nếu lỗi

### Thay đổi cần thiết:

#### 1. [`create_update.py`](create_update.py:1)
- Thêm chức năng đóng gói toàn bộ thư mục onedir
- Tạo file `onedir_v{version}.zip` thay vì chỉ các file `.py`
- Cập nhật `update_info.json` với trường mới `onedir_filename`

#### 2. [`updater.py`](updater.py:1)
- Thêm hàm kiểm tra đang chạy ở chế độ onedir (`sys.frozen`)
- Thêm logic update onedir: tải và thay thế toàn bộ thư mục
- Xử lý việc restart app sau khi update

## Các bước thực hiện

1. **Bước 1**: Sửa `create_update.py` - Thêm chế độ đóng gói onedir
2. **Bước 2**: Sửa `updater.py` - Thêm logic xử lý update onedir
3. **Bước 3**: Test với network share
