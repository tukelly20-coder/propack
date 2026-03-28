# Ứng dụng Tạo Mã Bản vẽ Tự động V7 散件图

Ứng dụng này bao gồm một server và một client để quản lý và phân phát mã duy nhất cho các hạng mục bản vẽ. Server chạy trên port 12345, quản lý mã theo từng hạng mục riêng biệt, lưu trữ dữ liệu trong file JSON local. Client là giao diện GUI với PySide6, hỗ trợ đa ngôn ngữ (Tiếng Việt và Tiếng Trung), và có thêm công cụ đồng bộ hóa thư mục.

## Tính năng chính

### Client (Giao diện người dùng)
Ứng dụng client có 4 tab chính:

- **Tab Tạo Mã**:
  - Ô IP server: Mặc định 192.168.2.188, có thể chỉnh sửa và ghi nhớ.
  - Ô tên người xin mã: Tối đa 100 ký tự, ghi nhớ tên cuối cùng trong file `last_name.txt`.
  - Ô mã nhân viên: Nhập mã nhân viên (001-999), ghi nhớ trong `last_employee.txt`.
  - Dropdown hạng mục: Chọn một trong các hạng mục sau:
    - SJT散件图 - Bản vẽ tách chi tiết
    - WLJ物料架 - Giá đựng vật liệu
    - ZZC周转车 - Xe trung chuyển
    - GZT工作台 - Bàn thao tác
    - WCP无尘棚 - Phòng sạch
    - LSX流水线 - Băng tải
    - ZWJ转弯机 - Băng tải chuyển hướng 90,180
    - GZL改造类 - Cải tạo
    - BSX倍速线 - Băng chuyền xích
    - WLL围栏类 - Hàng rào
    - GTX滚筒线 - Băng chuyền con lăn
    - ZHT展会图 - Bản vẽ mặt bằng
    - LHX老化线 - Băng chuyền lão hóa
  - Nút "Tạo Mã": Gửi yêu cầu đến server và hiển thị mã trả về (có thể sao chép bằng chuột).
  - Mã được tạo theo định dạng:
    - Cho hầu hết hạng mục: P[CODE][001-999]-0000-00-A0 (ví dụ: PWLJ001-0000-00-A0).
    - Cho SJT: PSJT[employee]-[0001-9999]-00-A0 (ví dụ: PSJT001-0001-00-A0).

- **Tab Lịch Sử**:
  - Bảng hiển thị lịch sử tạo mã: Tên, Mã nhân viên, Hạng mục, Mã, Thời gian (sắp xếp từ mới nhất đến cũ nhất).
  - Phân trang: 100 dòng/trang, nút Trước/Sau.
  - Nút "Xóa": Chọn dòng, nhập mật khẩu "kelly" để xóa (mã sẽ có thể tái sử dụng).
  - Nút "Xuất XLS": Xuất toàn bộ lịch sử ra file `history.xlsx` (cần openpyxl, đã include trong executable).
  - Sao chép: Chọn ô và nhấn Ctrl+C để sao chép.
  - Phím tắt: Nhấn F5 để làm mới danh sách lịch sử, nhấn Delete để xóa mục đã chọn (cần nhập mật khẩu "kelly").

- **Tab Ngôn ngữ**:
  - Dropdown chọn ngôn ngữ: Tiếng Việt hoặc Tiếng Trung.
  - Nút "Áp dụng" để thay đổi ngôn ngữ giao diện (lưu trong `language.txt`).

- **Tab Tool Đồng bộ hóa**:
  - Ô nhập đường dẫn nguồn (From): Nhập đường dẫn thư mục nguồn, lưu vào file `Toolsysnc/From.txt`.
  - Ô nhập đường dẫn đích (To): Nhập đường dẫn thư mục đích, lưu vào file `Toolsysnc/To.txt`.
  - Nút "Browse" để chọn thư mục.
  - Nút "Đồng Bộ ngay": Lưu thông tin vào file và chạy tool đồng bộ hóa sử dụng `robocopy` với chế độ mirror để sao chép và đồng bộ hóa thư mục từ nguồn sang đích, xóa các file không tồn tại ở đích.

### Server (Máy chủ)
- Lắng nghe trên port 12345.
- Quản lý mã theo hạng mục riêng biệt:
  - Hầu hết hạng mục: 001 đến 999 (ví dụ: PWLJ001 đến PWLJ999).
  - SJT: Theo mã nhân viên, từ 0001 đến 9999 cho mỗi nhân viên (ví dụ: PSJT001-0001 đến PSJT001-9999).
- Lưu trữ dữ liệu trong file JSON local: `used_codes.json`.
- Hỗ trợ các yêu cầu:
  - REQUEST_CODE: Tạo và trả về mã mới.
  - GET_HISTORY: Gửi lịch sử (hỗ trợ phân trang).
  - DELETE_HISTORY: Xóa mã (cần mật khẩu "kelly").
  - PING: Kiểm tra kết nối.

## Yêu cầu hệ thống

- Python 3.x
- PySide6 (cho client GUI)
- openpyxl (cho xuất XLS, tùy chọn - đã include trong executable)
- Windows (cho robocopy trong tool đồng bộ hóa)

## Cài đặt

1. Đảm bảo Python 3.x, PySide6 đã cài đặt: `pip install PySide6 openpyxl`
2. Sao chép các file `server.py`, `client.py` và các file liên quan vào thư mục dự án.

## Chạy Server

1. Mở terminal, điều hướng đến thư mục dự án.
2. Chạy: `python server.py`
3. Server sẽ lắng nghe trên port 12345 và hiển thị thông báo.

*Lưu ý*: Nếu port bị chiếm, kiểm tra và dừng tiến trình khác.

## Chạy Client

1. Mở terminal, điều hướng đến thư mục dự án.
2. Chạy: `python client.py`
3. Giao diện hiển thị, nhập thông tin và tạo mã.

## Cách hoạt động

- Client gửi JSON request đến server qua socket.
- Server tạo mã duy nhất cho hạng mục/nhân viên, lưu vào JSON local.
- Đảm bảo không trùng mã trong cùng hạng mục/nhân viên.
- Nếu hết mã, trả về "NO_MORE_CODES".
- Lịch sử được lưu với timestamp ISO.

## Build Executable

Để tạo file executable từ code Python:

1. Cài đặt PyInstaller: `pip install pyinstaller`

2. Chạy: `pyinstaller client.spec` để build client.

3. Chạy: `pyinstaller server.spec` để build server.

File executable sẽ được tạo trong thư mục `build/client/` và `build/server/`.

*Lưu ý*: Client executable đã include `openpyxl` và các file cấu hình để hỗ trợ xuất XLS và ghi nhớ cài đặt mà không cần cài đặt thư viện trên máy đích.

## Cấu trúc file

- `server.py`: Logic server socket, quản lý mã và lịch sử.
- `client.py`: Giao diện GUI với 4 tabs.
- `used_codes.json`: Dữ liệu mã đã dùng và lịch sử (local).
- `last_name.txt`: Lưu tên người dùng cuối cùng.
- `last_employee.txt`: Lưu mã nhân viên cuối cùng.
- `last_ip.txt`: Lưu IP server cuối cùng.
- `last_category.txt`: Lưu hạng mục cuối cùng.
- `language.txt`: Lưu ngôn ngữ hiện tại (vi hoặc zh).
- `Toolsysnc/From.txt`, `Toolsysnc/To.txt`: Lưu đường dẫn cho tool đồng bộ hóa.
- `client.spec`, `server.spec`: File cấu hình PyInstaller.
- `build/`: Thư mục chứa file executable sau khi build.
- `src/`, `Test/`: Thư mục bổ sung (có thể chứa code cũ hoặc test).

## Lưu ý

- Server cần chạy liên tục để client hoạt động.
- Mật khẩu xóa lịch sử: "kelly".
- Mã có thể sao chép từ giao diện.
- Client kiểm tra kết nối tự động mỗi 5 giây.
- Tool đồng bộ hóa sử dụng robocopy với /MIR để mirror thư mục.
- Hỗ trợ đa ngôn ngữ: Tiếng Việt (vi) và Tiếng Trung (zh).