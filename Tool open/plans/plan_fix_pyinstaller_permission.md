# Kế hoạch sửa lỗi PyInstaller - PermissionError

## Vấn đề
PyInstaller báo lỗi `PermissionError: [WinError 5] Access denied` khi cố gắng xóa thư mục `dist\Mo ma lieu UI` cũ để tạo bản build mới.

**Nguyên nhân có thể:**
1. File `.exe` trong thư mục `dist` đang chạy hoặc bị khóa bởi tiến trình khác
2. Windows Antivirus đang quét các file .pyd
3. Windows indexing service đang truy cập các file

## Giải pháp

### Bước 1: Kiểm tra và đóng tiến trình
- Đóng bất kỳ ứng dụng nào đang chạy từ thư mục `dist\Mo ma lieu UI`
- Kiểm tra Task Manager và đóng tiến trình `Mo ma lieu UI.exe` nếu đang chạy

### Bước 2: Cập nhật file .bat để tự động xử lý
Cập nhật `One click Package.bat` để:
1. Thêm `--noconfirm` để bỏ qua prompt xác nhận xóa
2. Thêm logic xóa thư mục dist trước khi build (nếu cần)
3. Thêm xử lý lỗi permission

### Bước 3: Sửa đổi spec file (tùy chọn)
Thêm tùy chọn để xử lý tốt hơn trên Windows:
- Sử dụng `upx_exclude` để loại trừ các file gây vấn đề
- Thêm các binary dependencies cần thiết

## File cần sửa
- `One click Package.bat` - Thêm xử lý lỗi và xóa thư mục trước khi build

## Lệnh build thay thế
```batch
@echo off
rem Xóa thư mục dist nếu tồn tại (bỏ qua lỗi nếu có)
if exist "dist\Mo ma lieu UI" rmdir /s /q "dist\Mo ma lieu UI" 2>nul
rem Build với noconfirm
python -m PyInstaller "Mo ma lieu UI.spec" --noconfirm
pause
```
