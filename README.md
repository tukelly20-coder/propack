# Propack VP - Quản Lý Dự Án Web

Ứng dụng web quản lý dự án và tạo mã bản vẽ tự động. Phiên bản web cho phép truy cập từ xa qua trình duyệt, hỗ trợ nhiều người dùng đồng thời.

## Tính năng chính

### Quản Lý Dự Án
- Bảng danh sách dự án với phân trang, sắp xếp, tìm kiếm và lọc
- Tạo, chỉnh sửa và xóa dự án (theo phân quyền)
- Xuất dữ liệu ra Excel
- Xem chi tiết dự án với các trường thông tin đầy đủ

### Hệ Thống Thông Báo
- Thông báo công việc từ Sales giao cho Kỹ thuật
- Chấp nhận hoặc từ chối công việc
- Theo dõi trạng thái dự án (đang chờ, đang thực hiện, hoàn thành)
- Thông báo số lượng công việc chờ xử lý

### Tạo Mã Bản Vẽ
- Tự động tạo mã bản vẽ duy nhất theo hạng mục
- Hỗ trợ nhiều hạng mục: SJT, WLJ, ZZC, GZT, WCP, LSX, ZWJ, GZL, BSX, WLL, GTX, ZHT, LHX
- Lịch sử tạo mã với phân trang
- Xóa và tái sử dụng mã (với mật khẩu)

### Quản Lý Người Dùng
- Đăng nhập với session (24 giờ)
- Quản lý hồ sơ cá nhân
- Đổi mật khẩu
- Phân quyền: Admin, IT, Sales, Kỹ thuật

### PropackAI
- Tích hợp AI hỗ trợ tra cứu và trả lời câu hỏi
- Tìm kiếm thông tin dự án và mã liệu

### Đa Ngôn Ngữ
- Giao diện hỗ trợ Tiếng Việt và Tiếng Trung
- Chuyển đổi ngôn ngữ dễ dàng

## Công Nghệ

- **Backend**: Python Flask + SQLite
- **Frontend**: HTML5, CSS3, JavaScript (jQuery, Bootstrap 5)
- **Database**: SQLite (cục bộ)

## Yêu Cầu

- Python 3.8+
- Kết nối mạng nội bộ hoặc Internet (khi triển khai WAN)

## Cài Đặt

```bash
pip install -r requirements.txt
```

## Chạy Ứng Dụng

```bash
python server.py
```

Mở trình duyệt: **http://localhost:8001**

## Triển Khai WAN

Ứng dụng hỗ trợ truy cập từ xa qua URL:
- `http://propackvp.duckdns.org:8001`
- `https://propackvp.duckdns.org:8001`

## Cấu Trúc File

```
propack/
├── server.py              # Flask server (port 8001)
├── client.py            # Desktop GUI (PySide6)
├── src/
│   ├── db_helper.py    # Database operations
│   └── ...
├── web/
│   ├── index.html    # Main web UI
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── modules/
├── Tool open/
│   ├── app.py        # Tool Open backend
│   └── Mở mã liệu...
└── ...
```

## API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/login` | POST | Đăng nhập |
| `/api/logout` | POST | Đăng xuất |
| `/api/me` | GET | Thông tin user hiện tại |
| `/api/projects` | GET/POST | Danh sách/Tạo dự án |
| `/api/projects/search` | POST | Tìm kiếm dự án |
| `/api/projects/filter` | POST | Lọc dự án |
| `/api/codes/create` | POST | Tạo mã bản vẽ |
| `/api/codes/history` | GET | Lịch sử tạo mã |
| `/api/notices` | GET | Danh sách thông báo |
| `/api/tool-search` | POST | Tìm kiếm mã liệu |

## Tích Hợp Tool Mở Mã Liệu

Ứng dụng tích hợp module **Tool Mở Mã Liệu** để tra cứu bản vẽ kỹ thuật:
- Tìm kiếm theo mã kỹ sư (cEngineerFigNo) hoặc mã hàng (cInvCode)
- Truy cập file Excel từ thư mục chia sẻ network
- Copy đường dẫn vào clipboard

## Lưu Ý

- Port mặc định: 8001
- Session timeout: 24 giờ
- Rate limit đăng nhập: 5 lần/5 phút
- Mật khẩu xóa mã: kelly

## Giấy Phép

© 2026