# Ứng dụng Tạo Mã Bản vẽ Tự động V8 大日程

Ứng dụng quản lý dự án cho Kinh Doanh và Công trình. Bao gồm server và web client để quản lý và phân phát mã duy nhất cho các hạng mục bản vẽ.

## Tính năng chính

- Quản lý mã bản vẽ tự động
- Giao diện web đa ngôn ngữ (Tiếng Việt, Tiếng Trung)
- API cho các tính năng AI
- Quản lý dự án và khách hàng
- Quản lý phiếu thu/chi

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy Server

```bash
python server.py
```

Server chạy trên port 12345.

## Cấu trúc

- `server.py` - Main server
- `src/` - Source code
- `web/` - Web client
- `routes/` - API routes
- `plans/` - Project plans
