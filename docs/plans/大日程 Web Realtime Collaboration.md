# 大日程 Web Realtime Collaboration - Kế Hoạch Thiết Kế Hệ Thống

## 1. Mục Tiêu Dự Án

Xây dựng hệ thống 大日程 dạng Web cho phép nhiều người dùng truy cập đồng thời, cập nhật kế hoạch sản xuất theo thời gian thực và tránh xảy ra xung đột dữ liệu khi nhiều người cùng chỉnh sửa.

Mục tiêu cuối cùng là mang lại trải nghiệm tương tự Google Sheet nhưng được tối ưu cho môi trường sản xuất và quản lý tiến độ nội bộ doanh nghiệp.

---

# 2. Yêu Cầu Nghiệp Vụ

## 2.1 Chức năng cơ bản

- Hiển thị dữ liệu 大日程 dưới dạng bảng.

- Thêm, sửa, xóa dữ liệu.

- Tìm kiếm và lọc dữ liệu.

- Sắp xếp dữ liệu.

- Xuất Excel.

- Nhập dữ liệu từ Excel.

- Quản lý tài khoản người dùng.

- Phân quyền truy cập.

## 2.2 Chức năng Realtime

- Hiển thị người dùng đang online.

- Hiển thị người dùng đang chỉnh sửa dữ liệu.

- Đồng bộ thay đổi giữa các người dùng theo thời gian thực.

- Tự động cập nhật khi dữ liệu thay đổi.

- Tránh ghi đè dữ liệu khi nhiều người cùng sửa.

## 2.3 Chức năng quản lý tài liệu

Từ mã liệu trên 大日程:

- Mở tài liệu PDF.

- Xem bản vẽ.

- Xem BOM.

- Mở thư mục vật liệu.

- Xem thông tin ERP.

Hệ thống không truy cập trực tiếp từ trình duyệt đến ổ mạng.

Luồng xử lý:

```text
User
 ↓
Web
 ↓
API Server
 ↓
Tra mã liệu
 ↓
File Server / Shared Folder
 ↓
Trả dữ liệu về Browser
```

---

# 3. Kiến Trúc Hệ Thống

## 3.1 Tổng thể

```text
Browser
    │
    ├── HTTP API
    │
    └── WebSocket
            │
            ▼
    Backend Server
            │
            ├── Business Logic
            ├── Realtime Engine
            ├── Permission
            └── File Service
                    │
                    ├── PostgreSQL
                    └── Shared Folder
```

---

# 4. Công Nghệ Đề Xuất

## Frontend

- React

- TypeScript

- AG Grid hoặc Handsontable

- Socket.IO Client

## Backend

- Node.js

- Express

- Socket.IO

Hoặc:

- Python

- FastAPI

- WebSocket

## Database

- PostgreSQL

## Storage

- Shared Folder

- NAS

- File Server

---

# 5. Thiết Kế Realtime

## 5.1 Trạng thái Online

Server duy trì danh sách:

```json
{
  "userId": "kelly",
  "status": "online"
}
```

Hiển thị:

```text
● Kelly
● User A
● User B
```

---

## 5.2 Theo Dõi Ô Đang Chọn

Khi người dùng click vào ô:

```text
Dòng 15
Cột: Trạng thái
```

Server broadcast:

```json
{
  "user": "kelly",
  "row": 15,
  "column": "status"
}
```

Những người khác sẽ thấy:

```text
Kelly đang chỉnh sửa
```

---

# 6. Cơ Chế Chống Xung Đột

## 6.1 Khóa Ô (Cell Lock)

Khi người dùng bắt đầu sửa:

```text
User A
↓
Lock Cell
↓
Server xác nhận
↓
Ô được đánh dấu đang chỉnh sửa
```

Người dùng khác:

```text
Chỉ xem
Không được sửa
```

---

## 6.2 Timeout Tự Động

Nếu:

- Mất mạng

- Tắt trình duyệt

- Máy treo

Server sẽ tự mở khóa:

```text
30 giây không hoạt động
↓
Unlock
```

---

## 6.3 Version Check

Mỗi dòng dữ liệu có:

```text
version = 1
```

Khi lưu:

```text
User gửi version hiện tại
↓
Server kiểm tra
```

Nếu:

```text
Version khớp
```

→ Cho phép lưu.

Nếu:

```text
Version không khớp
```

→ Báo xung đột dữ liệu.

---

# 7. Cấu Trúc Database

## Bảng schedules

```sql
id
project_no
item_code
item_name
process
plan_date
status
owner
version
updated_by
updated_at
```

---

## Bảng cell_locks

```sql
id
schedule_id
field_name
locked_by
locked_at
expires_at
```

---

## Bảng change_logs

```sql
id
schedule_id
field_name
old_value
new_value
changed_by
changed_at
```

---

# 8. Nhật Ký Thay Đổi

Hệ thống lưu:

```text
Ai sửa
Sửa lúc nào
Từ giá trị nào
Sang giá trị nào
```

Ví dụ:

```text
2026-06-15 10:25

Kelly

Trạng thái:
"Chưa sản xuất"
→
"Đang sản xuất"
```

---

# 9. Quản Lý Tài Liệu

## Tra cứu theo mã liệu

Ví dụ:

```text
100701000009
```

Server thực hiện:

```text
Tra Database
↓
Lấy đường dẫn tài liệu
↓
Đọc file từ ổ chung
↓
Trả về Browser
```

Người dùng không cần truy cập trực tiếp vào ổ mạng.

---

# 10. Phân Quyền

## Admin

- Toàn quyền.

## Planner

- Chỉnh sửa kế hoạch.

- Xem tài liệu.

## Production

- Chỉ cập nhật trạng thái sản xuất.

## Viewer

- Chỉ xem.

---

# 11. Roadmap Triển Khai

## Phase 1

- Đăng nhập.

- CRUD dữ liệu.

- PostgreSQL.

- Xuất/Nhập Excel.

## Phase 2

- WebSocket.

- Online User.

- Đồng bộ dữ liệu realtime.

## Phase 3

- Cell Lock.

- Version Check.

- Change Log.

## Phase 4

- Xem tài liệu trực tiếp.

- Tích hợp ERP.

- Thông báo tự động.

## Phase 5

- Realtime Collaboration nâng cao.

- Cursor người dùng.

- Undo / Redo.

- Bình luận.

- Audit nâng cao.

---

# 12. Mục Tiêu Cuối Cùng

Xây dựng một hệ thống 大日程 hoạt động tương tự Google Sheet nhưng được tối ưu cho môi trường sản xuất:

- Nhiều người sử dụng đồng thời.

- Không mất dữ liệu.

- Không ghi đè dữ liệu.

- Theo dõi lịch sử chỉnh sửa.

- Liên kết trực tiếp với tài liệu kỹ thuật và ERP.

- Hỗ trợ mở rộng cho MES, BOM và quản lý tiến độ sản xuất trong tương lai.
