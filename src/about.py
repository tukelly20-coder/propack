from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
import os
import sys

README_VI = """# Ứng dụng Tạo Mã Bản vẽ Tự động V7 散件图

Ứng dụng này bao gồm một server và một client để quản lý và phân phát mã duy nhất cho các hạng mục bản vẽ. Server chạy trên port 8001, quản lý mã theo từng hạng mục riêng biệt, lưu trữ dữ liệu trong file JSON local. Client là giao diện GUI với PySide6, hỗ trợ đa ngôn ngữ (Tiếng Việt và Tiếng Trung), và có thêm công cụ đồng bộ hóa thư mục.
được lên ý tưởng và xây dựng bởi Kelly.
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
- Lắng nghe trên port 8001.
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
3. Server sẽ lắng nghe trên port 8001 và hiển thị thông báo.

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
- Hỗ trợ đa ngôn ngữ: Tiếng Việt (vi) và Tiếng Trung (zh)."""

README_ZH = """# 自动生成图纸编码应用 V7 散件图

该应用程序包括一个服务器和一个客户端，用于管理和分发唯一的图纸编码。服务器在端口8001上运行，按每个类别单独管理编码，将数据存储在本地JSON文件中。客户端是使用PySide6的GUI界面，支持多语言（越南语和中文），并添加了目录同步工具。
开发者：Kelly.
## 主要功能

### 客户端（用户界面）
客户端应用程序有4个主要选项卡：

- **生成编码选项卡**：
  - 服务器IP输入框：默认192.168.2.188，可编辑并记住。
  - 申请人姓名输入框：最多100个字符，在`last_name.txt`中记住最后姓名。
  - 员工编号输入框：在`last_employee.txt`中记住员工编号（001-999）。
  - 类别下拉菜单：选择以下类别之一：
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
  - "生成编码"按钮：向服务器发送请求并显示返回的编码（可通过鼠标复制）。
  - 生成的编码格式：
    - 大多数类别：P[CODE][001-999]-0000-00-A0（例如：PWLJ001-0000-00-A0）。
    - SJT：PSJT[employee]-[0001-9999]-00-A0（例如：PSJT001-0001-00-A0）。

- **记录选项卡**：
  - 显示生成编码历史的表格：姓名、员工编号、类别、编码、时间（从最新到最旧排序）。
  - 分页：每页100行，前/后按钮。
  - "删除"按钮：选择行，输入密码"kelly"删除（编码可重新使用）。
  - "导出XLS"按钮：将整个历史导出到`history.xlsx`文件（需要openpyxl，已包含在可执行文件中）。
  - 复制：选择单元格并按Ctrl+C复制。
  - 快捷键：按F5刷新列表，按Delete删除选定项（需要输入密码"kelly"）。

- **语言选项卡**：
  - 选择语言下拉菜单：越南语或中文。
  - "应用"按钮应用语言更改（保存在`language.txt`中）。

- **同步工具选项卡**：
  - 来源路径输入框（From）：输入来源目录路径，保存在`Toolsysnc/From.txt`中。
  - 目标路径输入框（To）：输入目标目录路径，保存在`Toolsysnc/To.txt`中。
  - "Browse"按钮选择目录。
  - "立即同步"按钮：保存信息到文件并运行同步工具，使用`robocopy`进行镜像模式同步，从来源复制并同步到目标，删除目标中不存在的文件。

### 服务器（服务器）
- 在端口8001上监听。
- 按类别单独管理编码：
  - 大多数类别：001到999（例如：PWLJ001到PWLJ999）。
  - SJT：按员工编号，从每个员工的0001到9999（例如：PSJT001-0001到PSJT001-9999）。
- 将数据存储在本地JSON文件：`used_codes.json`。
- 支持请求：
  - REQUEST_CODE：生成并返回新编码。
  - GET_HISTORY：发送历史（支持分页）。
  - DELETE_HISTORY：删除编码（需要密码"kelly"）。
  - PING：检查连接。

## 系统要求

- Python 3.x
- PySide6（用于客户端GUI）
- openpyxl（用于XLS导出，可选 - 已包含在可执行文件中）
- Windows（用于同步工具中的robocopy）

## 安装

1. 确保Python 3.x、PySide6已安装：`pip install PySide6 openpyxl`
2. 将`server.py`、`client.py`和相关文件复制到项目目录中。

## 运行服务器

1. 打开终端，导航到项目目录。
2. 运行：`python server.py`
3. 服务器将在端口8001上监听并显示消息。

*注意*：如果端口被占用，请检查并停止其他进程。

## 运行客户端

1. 打开终端，导航到项目目录。
2. 运行：`python client.py`
3. 界面显示，输入信息并生成编码。

## 工作原理

- 客户端通过套接字向服务器发送JSON请求。
- 服务器为类别/员工生成唯一编码，存储在本地JSON中。
- 确保同一类别/员工中编码不重复。
- 如果编码用完，返回"NO_MORE_CODES"。
- 历史记录以ISO时间戳存储。

## 构建可执行文件

要从Python代码创建可执行文件：

1. 安装PyInstaller：`pip install pyinstaller`

2. 运行：`pyinstaller client.spec`构建客户端。

3. 运行：`pyinstaller server.spec`构建服务器。

可执行文件将在`build/client/`和`build/server/`目录中创建。

*注意*：客户端可执行文件已包含`openpyxl`和配置文件，以支持XLS导出和在目标机器上无需安装库的情况下记住设置。

## 文件结构

- `server.py`：服务器套接字逻辑，管理编码和历史。
- `client.py`：带有4个选项卡的GUI界面。
- `used_codes.json`：已用编码和历史数据（本地）。
- `last_name.txt`：记住最后用户姓名。
- `last_employee.txt`：记住最后员工编号。
- `last_ip.txt`：记住最后服务器IP。
- `last_category.txt`：记住最后类别。
- `language.txt`：记住当前语言（vi或zh）。
- `Toolsysnc/From.txt`、`Toolsysnc/To.txt`：保存同步工具的路径。
- `client.spec`、`server.spec`：PyInstaller配置文件。
- `build/`：构建后可执行文件目录。
- `src/`、`Test/`：补充目录（可能包含旧代码或测试）。

## 注意事项

- 服务器需要持续运行以使客户端工作。
- 删除历史密码："kelly"。
- 编码可从界面复制。
- 客户端每5秒自动检查连接。
- 同步工具使用robocopy的/MIR进行目录镜像。
- 支持多语言：越南语（vi）和中文（zh）。"""

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        self.load_readme()

    def get_base_path(self):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_readme(self):
        base_path = self.get_base_path()
        # Đọc ngôn ngữ từ language.txt, ưu tiên file trong thư mục hiện tại
        current_language = 'vi'  # Mặc định
        # Thử đọc từ thư mục hiện tại trước
        language_file = 'language.txt'
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                lang = f.read().strip()
                if lang in ['vi', 'zh']:
                    current_language = lang
        except:
            # Nếu không có, đọc từ base_path
            language_file = os.path.join(base_path, 'language.txt')
            try:
                with open(language_file, 'r', encoding='utf-8') as f:
                    lang = f.read().strip()
                    if lang in ['vi', 'zh']:
                        current_language = lang
            except:
                pass

        # Chọn nội dung README phù hợp
        if current_language == 'zh':
            content = README_ZH
        else:
            content = README_VI

        self.text_edit.setMarkdown(content)

    def reload_readme(self):
        self.load_readme()