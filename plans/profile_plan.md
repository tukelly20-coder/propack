# Kế hoạch tạo trang Profile User

## Mục tiêu
Tạo trang HTML mới `profile.html` để quản lý profile cho user, cho phép user xem và cập nhật thông tin cá nhân.

## Các trường thông tin user cần quản lý

Dựa trên cấu trúc database, các trường thông tin bao gồm:
1. **username** - Tên đăng nhập (chỉ đọc)
2. **full_name** - Họ tên đầy đủ
3. **employee_id** - Mã nhân viên
4. **department** - Phòng ban
5. **role** - Vai trò (chỉ đọc)
6. **email** - Email (có thể thêm)
7. **phone** - Số điện thoại (có thể thêm)
8. **status** - Trạng thái (chỉ đọc)
9. **last_login** - Đăng nhập lần cuối (chỉ đọc)

## Cấu trúc trang profile.html

### 1. Header & Navigation
- Giống index.html: navbar với brand "Quản Lý Dự Án"
- Menu điều hướng: Dự Án | Thông báo | Profile
- Phần user info: hiển thị username + nút đăng xuất

### 2. Nội dung chính - Form Profile
- Card thông tin user với các trường:
  - Avatar/icon người dùng
  - Thông tin cơ bản (username, role, status)
  - Thông tin cá nhân (full_name, employee_id, department)
  - Thông tin liên lạc (email, phone)
  - Lịch sử đăng nhập (last_login)

### 3. Chức năng
- **Xem thông tin**: Hiển thị tất cả thông tin user (một số trường chỉ đọc)
- **Chỉnh sửa thông tin**: Cho phép cập nhật các trường có thể thay đổi
- **Đổi mật khẩu**: Chức năng đổi mật khẩu (modal)

### 4. UI/UX
- Sử dụng Bootstrap 5 như index.html
- Icons Bootstrap Icons
- Responsive design
- Toast notifications cho thông báo

## Các bước thực hiện

1. **Tạo file profile.html** trong thư mục web/
   - Copy cấu trúc từ index.html
   - Thêm form hiển thị/chỉnh sửa thông tin user

2. **Tạo file JS riêng** hoặc thêm vào app.js
   - API gọi lấy thông tin user
   - API cập nhật thông tin user
   - Xử lý form chỉnh sửa
   - Xử lý đổi mật khẩu

3. **Kiểm tra**
   - Hiển thị đúng thông tin user đang đăng nhập
   - Cho phép cập nhật các trường hợp lệ
   - Toast notification khi lưu thành công/thất bại