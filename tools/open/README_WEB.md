# Mở mã liệu Web App

Phiên bản web của ứng dụng Mở mã liệu với giao diện HTML/CSS/JS kết nối Python Backend.

## Yêu cầu

- Python 3.8+
- Các thư viện trong `requirements.txt`
- Kết nối mạng nội bộ để truy cập:
  - API: `192.168.2.164:8080`
  - File Excel: `\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx`

## Cài đặt

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
# Chạy Flask server
python app.py
```

Sau đó mở trình duyệt tại: **http://localhost:5000**

## Cấu trúc thư mục

```
Tool open/
├── app.py                    # Flask server (backend)
├── templates/
│   └── index.html           # Giao diện HTML
├── static/
│   ├── css/
│   │   └── styles.css      # Styles (Tokyo Night theme)
│   └── js/
│       └── app.js          # JavaScript xử lý frontend
├── requirements.txt         # Python dependencies
├── Mở mã liệu 打开链接VP.py  # Module core (đã có)
└── ...
```

## Tính năng

- ✅ Tìm kiếm mã liệu (cEngineerFigNo và cInvCode)
- ✅ Hiển thị nhiều kết quả khi có matches
- ✅ Lưu lịch sử tìm kiếm
- ✅ Copy đường dẫn vào clipboard
- ✅ Giao diện dark mode (Tokyo Night theme)
- ✅ Phím tắt (Enter tìm kiếm, Ctrl+H lịch sử)
- ✅ Menu Trợ giúp

## Lưu ý

⚠️ **Hạn chế của phiên bản web:**
- Do hạn chế bảo mật của trình duyệt, chức năng "mở Windows Explorer tự động" **không hoạt động**.
- **Giải pháp:** Khi tìm kiếm thành công, đường dẫn sẽ được **copy vào clipboard**. Bạn chỉ cần:
  1. Mở Windows Explorer (Win + E)
  2. Dán đường dẫn vào thanh địa chỉ (Ctrl + V)
  3. Enter để mở thư mục

## Khác biệt so với phiên bản Desktop

| Tính năng | Desktop (PySide6) | Web (Flask) |
|-----------|-------------------|-------------|
| Mở Explorer tự động | ✅ | ❌ (copy clipboard) |
| Chạy standalone | ✅ | ❌ (cần Python) |
| Giao diện native | ✅ | ❌ (web) |
| Triển khai từ xa | ❌ | ✅ |
| Nhiều người dùng | ❌ | ✅ |

## Keyboard Shortcuts

- **Enter** - Tìm kiếm
- **↑↓** - Chọn từ lịch sử
- **Ctrl+H** - Hiển/Ẩn lịch sử
- **Escape** - Đóng modal/dropdown

---

© 2026
