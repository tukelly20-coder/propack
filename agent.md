## Mục Đích

Đây là hệ thống **Quản Lý Dự Án & Tạo Mã Bản Vẽ** toàn diện được thiết kế cho các công ty sản xuất/kỹ thuật. Hệ thống quản lý toàn bộ quy trình từ tạo dự án kinh doanh đến kỹ thuật viên tiếp nhận, đồng thời tạo mã bản vẽ duy nhất cho nhiều hạng mục sản phẩm. Bao gồm giao diện web, REST API backend bằng Flask, và client desktop cũ để tạo mã.

**Mục Tiêu Chính:**
- Theo dõi dự án từ sales → kỹ thuật với quản lý trạng thái (chờ tiếp nhận/đã tiếp nhận)
- Tạo mã bản vẽ duy nhất, không trùng lặp cho 13 hạng mục sản phẩm
- Cung cấp cộng tác thời gian thực và hiển thị dự án
- Hỗ trợ giao diện song ngữ (Tiếng Việt & Tiếng Trung)
- Cho phép kiểm soát truy cập dựa trên vai trò với hệ thống phân quyền

---

## Vai Trò

**Agent Kiến Trúc Hệ Thống** - Kỹ sư Full-stack Python/JavaScript chuyên về hệ thống workflow doanh nghiệp, thiết kế database và kiến trúc multi-client.

**Trách Nhiệm:**
- Duy trì và phát triển Flask server thống nhất với REST API
- Quản lý schema SQLite và chiến lược migration
- Hỗ trợ web frontend (Bootstrap/jQuery SPA) và tương thích desktop client cũ
- Triển khai xác thực, quản lý session và hệ thống phân quyền
- Đảm bảo tính toàn vẹn logic tạo mã qua tất cả hạng mục sản phẩm
- Hỗ trợ quốc tế hóa (i18n) cho ngôn ngữ Tiếng Việt/Tiếng Trung

**Mức Độ Chuyên Môn:** Senior-level tích hợp hệ thống với Python backend, JavaScript frontend và SQL database với công cụ Windows-specific (robocopy, UNC paths).

---

## Đầu Vào

### Dữ Liệu Từ Client

**Web Client (Trình duyệt → HTTP/JSON)**
- Thông tin xác thực: `{username, password}`
- Dữ liệu dự án: Form fields để theo dõi (khách hàng, sản phẩm, thông số, ngày, người được giao)
- Hành động thông báo: Yêu cầu tiếp nhận/từ chối công việc
- Cập nhật profile: `{full_name, email, phone, department, employee_id}`
- System logs: Phản hồi với loại log

**Desktop Client (socket → JSON over TCP)**
- Yêu cầu tạo mã: `{name, category, employee}`
- Truy vấn lịch sử: `{page, limit, offset}`
- Yêu cầu xóa: `{password, code}`

### Nguồn Dữ Liệu Nội Bộ

**Database (SQLite: `DB.db`)**
- Table `users`: Hồ sơ user, mật khẩu hash, vai trò, quyền, trạng thái
- Table `customers`: Database liên hệ khách hàng
- Table `projects`: Bản ghi dự án chuẩn hóa (19 trường business + metadata)
- Indexes: `user_id`, `ma_po`, `ten_san_pham`

**File Storage**
- `used_codes.json`: Storage JSON cũ cho việc theo dõi tạo mã (categories + history)
- `last_name.txt`, `last_employee.txt`, `last_category.txt`, `language.txt`: Lưu trạng thái UI
- `tools/sync/From.txt`, `tools/sync/To.txt`: Cấu hình tool đồng bộ thư mục                       
- `logs/`: Log submissions từ web client dạng `.txt` có timestamp
- Material Excel: `\\192.168.2.165\...\存货档案库.xlsx` (network UNC path)

**Module: Tool Open (Tra cứu Vật liệu)**
- Module `material_core`: Load động từ `tools/open/Mở mã liệu 打开链接VP.py`                      
- Excel lookup cache: DataFrame in-memory cho mapping `cEngineerFigNo` → `cInvCode`
- Query file system: Tìm kiếm thư mục chia sẻ theo `cInvCode` và copy đường dẫn matching vào clipboard

---

## Đầu Ra

### API Responses (JSON hoặc plain text)

**Xác Thực**
- `POST /api/login` → `{success, token, user: {...}, expires_in}` hoặc `{success: false, error}`
- `GET /api/me` → `{authenticated, user, expires_in, expiring_soon}` hoặc `{authenticated: false, reason}`
- `POST /api/logout` → `{success, message}`

**Quản Lý Dự Án**
- `GET /api/projects` → `{data: [...], total, total_pages, page}` (có phân trang)
- `POST /api/projects` → `{success, record: {tracking_id, ...}}`
- `GET /api/projects/<id>` → Full project record hoặc `{error}`
- `PUT /api/projects/<id>` → `{success}` hoặc `{success: false, error}`
- `DELETE /api/projects/<id>?role=admin` → `{success, deleted_count}`
- `POST /api/projects/search` → `{data: [...], total, total_pages, page}`
- `POST /api/projects/filter` → `{data: [...], total, total_pages, page}`

**Tạo Mã**
- `POST /api/codes/create` → `{success, code: "PWLJ001-0000-00-A0"}` hoặc error
- `GET /api/codes/history` → `{data: [...], total, total_pages, page}`
- `GET /api/codes/export` → `{success, data: [...], total}` (full history)
- `DELETE /api/codes/history/<code>` → `{success, message}` hoặc `{success: false, error}`
- Legacy socket (TCP 8001): Plain text responses: code string, `NO_MORE_CODES`, `PONG`, `INVALID_REQUEST`, `DELETED`, `ERROR`

**Thông Báo / Bảng Việc**
- `GET /api/notices/pending` → Danh sách dự án chờ
- `POST /api/notices/accept` → `{success}`

**Quản Lý User (Admin only)**
- `GET /api/users` → Danh sách user summary objects
- `POST /api/users` → `{success, user_id}` hoặc `{success: false, error}`
- `PUT /api/users/<id>` → `{success}`
- `DELETE /api/users/<id>` → `{success}`

**Tool Open Lookup**
- `GET /api/tool-status` → `{status: "ready"|"error"|"unavailable", message, excel_path, excel_exists}`
- `POST /api/tool-search` → `{type: "success"|"multiple"|"error", urls: [...], copied_code, message}` hoặc matches array

**Health / Static**
- `GET /` → `web/index.html`
- `GET /<path:filename>` → Static asset
- `GET /api/health` → `{status, service, port, features}`

### Side-Effects

- Database commits (`projects`, `users`) → vô hiệu hóa in-memory cache
- Tạo mã → append vào `used_codes.json` history
- Log submission → ghi `web_log_<timestamp>.txt`
- Material lookup → copy `cInvCode` hoặc URL list vào system clipboard
- Đổi mật khẩu → cập nhật session user object và database

---

## Quy Tắc

### Quy Tắc Toàn Vẹn Dữ Liệu

1. **Đảm Bảo Tính Duy Nhất Của Mã**
   - Hạng mục non-SJT: Mã như `PWLJ001-0000-00-A0` phải duy nhất trong hạng mục đó (phạm vi 001–999)
   - Hạng mục SJT: Mã `PSJT{emp}-{XXXX}-00-A0` duy nhất theo nhân viên (phạm vi 0001–9999)
   - Mã đã xóa có thể tái sử dụng (tái chế theo thứ tự)

2. **Lịch Sử Dự Án**
   - Mỗi lần tạo mã append bản ghi lịch sử với timestamp ISO
   - Timestamps dùng để sắp xếp: mới nhất trước
   - Xóa cần mật khẩu `"kelly"` và remove mã khỏi `used_codes` pool

3. **Workflow Dự Án**
   - Bản ghi dự án mới mặc định `is_pending = 'yes'`
   - Chỉ một kỹ thuật viên có thể tiếp nhận dự án chờ (first-come, first-served)
   - Tiếp nhận set `accepted_by`, `accepted_at`, flip `is_pending = 'no'`
   - Dự án chờ hiển thị với tất cả; sau khi tiếp nhận chỉ hiển thị với kỹ thuật viên đã tiếp nhận (và admin)

4. **Contract Chuẩn Hóa**
   - Database lưu normalized columns (24 columns trong `projects` table)
   - API layer map giữa tên field API và database columns
   - Hỗ trợ field aliases từ legacy UI (ví dụ: `'Nhân viên KD'` và `'Nhân viên kinh doanh'` đều map đến `nhan_vien_kinh_doanh`)

### Bảo Mật / Kiểm Soát Truy Cập

- **Xác thực**: Bearer token sessions lưu server-side; tokens hết hạn sau 24h
- **Rate Limiting**: Tối đa 5 lần đăng nhập thất bại mỗi 5 phút mỗi IP
- **Quyền Dựa Trên Vai Trò**: `create_sales_record` (sales), `job_accept` (engineer), admin = tất cả
- **Mật khẩu Tối thiểu**: 6 ký tự
- **Khóa Tài khoản**: `status = 'locked'` ngăn đăng nhập
- **Bảo Vệ Xóa**: Chỉ role `admin` mới được xóa dự án qua API
- **CORS**: Allow-list domains (localhost, duckdns, custom domains) với hỗ trợ HTTPS

### Quy Ước

- **Format Mã**:
  - Non-SJT: `P{CATEGORY}{3-digit}-0000-00-A0` → `PWLJ001-0000-00-A0`
  - SJT: `PSJT{3-digit employee}-{4-digit serial}-00-A0` → `PSJT001-0001-00-A0`
- **Mã Hạng Mục**: WLJ, ZZC, GZT, WCP, LSX, ZWJ, GZL, SJT, BSX, WLL, GTX, ZHT, LHX
- **Timestamps**: ISO 8601 cho history, `YYYY-MM-DD HH:MM` cho hiển thị
- **JSON keys**: snake_case cho nội bộ (Python), mixed-case để tương thích UI (labels Tiếng Việt/Tiếng Trung)
- **Cursor**: Dùng `safe_print()` cho thread-safe console output
- **Excel Path**: UNC path với network location đảm bảo; cached in-memory sau khi load
- **Language codes**: `vi` = Tiếng Việt, `zh` = Tiếng Trung

---

## Quy Trình

### 1. Khởi Động Hệ Thống

```
server.py start → Flask app initialized
  ├─ CORS configured
  ├─ DB init: init_db() + migrate_to_v2() + ensure_default_users()
  ├─ Tool Open module loaded (optional)
  └─ Listen on port 8001 (HTTP)
```

### 2. Luồng Đăng Nhập User

```
Web client: POST /api/login {username, password}
  ├─ Rate limit check (max 5/5min per IP)
  ├─ Verify credentials via get_user_with_permissions()
  ├─ If admin lock: reject
  ├─ If success:
  │   ├─ Generate random token (secrets.token_hex(32))
  │   ├─ Store in sessions dict: {token, user_info, created_at, ip}
  │   ├─ Return token + user info (password stripped)
  │   └─ Client stores token in localStorage, attaches as Bearer in headers
  └─ If fail: record attempt, return 401
```

### 3. Tạo Dự Án (Sales Workflow)

```
Client: POST /api/projects with form data
  ├─ API auto-sets is_pending = 'yes'
  ├─ add_record() maps form fields → normalized columns
  ├─ INSERT into SQLite (tracking_id auto-increments)
  ├─ Cache invalidated
  └─ Returns {success, record} with tracking_id
```

### 4. Tiếp Nhận Công Việc (Engineer Workflow)

```
Engineer clicks 'Nhận Job' (Notices tab)
  ├─ Frontend: POST /api/notices/accept {tracking_id, engineer_name}
  ├─ Backend: accept_job(tracking_id, engineer_name)
  │   ├─ UPDATE projects SET is_pending='no', accepted_by=?, accepted_at=now()
  │   └─ WHERE tracking_id=? AND is_pending='yes'
  ├─ Notices list refreshes (pending job disappears)
  └─ Job appears in engineer's accepted projects list
```

### 5. Tạo Mã Bản Vẽ (Legacy Desktop Client HOẶC Web Tool)

```
Client → POST /api/codes/create {name, category, employee}
  ├─ Server: validate name/category/employee present
  ├─ Call generate_code(used_codes, category, employee)
  │   ├─ If SJT: key="SJT_{employee}", reuse deleted codes first (sorted), then 0001–9999
  │   ├─ Else: category range 001–999, skip deleted
  │   └─ If none available → return None
  ├─ On success: append to history list with timestamp + parent_code=''
  ├─ Save used_codes + history → used_codes.json
  ├─ Return code string
  └─ On fail: return 'NO_MORE_CODES' or 'INVALID_REQUEST'
```

### 6. Luồng Tra Cứu Vật Liệu (Tool Open)

```
Client: POST /api/tool-search {code}
  ├─ Server loads Excel (cached) once via get_excel_data()
  ├─ material_core.is_engineer_fig_no(code)?
  │   ├─ Yes → batch find_cinvcode_from_excel(code) (partial match supported)
  │   ├─ Single match → copy cInvCode to clipboard, query folder paths by cInvCode
  │   └─ Multiple matches → return match list for user selection
  ├─ If not engineer fig no → query material directly by code
  ├─ Copy URLs to clipboard, return {type, urls, folder_count}
  └─ On error → {type: 'error', message}
```

### 7. Tìm Kiếm & Lọc

```
Search:
  POST /api/projects/search {search, page, limit, sort_by, sort_order}
    → search_data_sql(search_text, ...) → JSON results with pagination

Filter:
  POST /api/projects/filter {filters: {field: value}, page, limit, sort_by, sort_order}
    → filter_data_sql(filter_dict, ...) → JSON results with pagination
```

---

## Kiến Thức

### Kiến Thức Nghiệp Vụ (Sản Xuất Kỹ Thuật)

- **Bản vẽ (Drawings)**:
  - Bản vẽ chính (`Mã bản vẽ`): Số bản vẽ chính
  - Bản vẽ kỹ thuật (`Mã bản vẽ kỹ thuật`): Biến thể bản vẽ sau PO
  - Mã mẹ (`Mã mẹ`): Bill of Materials root identifier
- **Hạng Mục Sản Phẩm**:
  - SJT = 散件 (bản vẽ tách chi tiết), duy nhất theo nhân viên
  - Các hạng mục chung: WLJ=物料架 (giá đỡ vật liệu), ZZC=周转车 (xe trung chuyển), GZT=工作台 (bàn thao tác), WCP=无尘棚 (phòng sạch), v.v.
- **Vòng Đời Dự Án**: Sales tạo → Kỹ thuật tiếp nhận → Mã bản vẽ được gán khi lập kế hoạch sản xuất

### Công Nghệ & Tiêu Chuẩn

- **Backend**: Python 3.x, Flask 2.x, SQLite3
- **Frontend**: HTML5, Bootstrap 5, jQuery 3.7, DataTables, i18n JavaScript
- **Desktop Client**: PySide6 (Qt6), legacy socket-based communication trên port 8001
- **Serialization**: JSON over HTTP và legacy TCP
- **File Formats**: `.xlsx` (Excel via openpyxl/pandas), `.json` (state files), `.txt` (logs/configs)
- **Concurrency**: Threading cho socket server (legacy), Flask handles requests linearly (nhưng session locking qua `sessions_lock`)
- **Internationalization**: Dynamic client-side language switching với `language.txt` persisted, i18n.js với dictionaries Tiếng Việt/Tiếng Trung

### Tham Chiếu Dữ Liệu

- **Dữ Liệu Nhạy Cảm**: `credentials.json` tồn tại nhưng không nên được log/commit
- **Network Paths**: UNC path đến shared inventory Excel trên `192.168.2.165`
- **Config Files**: `column_settings.json` kiểm soát visibility của UI columns, `used_codes.json` theo dõi state
- **Tools**: `robocopy` cho Windows directory mirroring, `PyInstaller` specs cho packaging

---

## Xử Lý Lỗi

### Thiếu / Đầu Vào Không Hợp Lệ

- **Thiếu fields** (tạo mã): return `"INVALID_REQUEST"` string
- **Chưa xác thực**: 401 với `{success: false, error: "Chưa đăng nhập"}`
- **Thông tin không hợp lệ**: 401 với `{success: false, error: "Tên đăng nhập hoặc mật khẩu không đúng"}`
- **Mã nhân viên không hợp lệ** (không phải 3 chữ số hoặc 000): 400 với `{error: "Mã nhân viên phải là 3 chữ số..."}`
- **Không còn mã**: 400 với `{success: false, error: "Không còn mã available cho hạng mục này"}`
- **JSON malformed**: 400 `Dữ liệu không hợp lệ`

### Rate Limiting

- Đăng nhập thất bại tracked per IP → sau 5 attempts trong 5 phút, 429 Too Many Requests với `code: "RATE_LIMITED"`
- Auto-reset sau `LOGIN_RATE_WINDOW` (300 giây)

### Tài Nguyên Cạn Kiệt

- **Code pool exhausted**: `generate_code()` returns `None` → `NO_MORE_CODES` response
- **Excel load failure**: Tool Open hiển thị `"Không thể kết nối Excel"`; tool-status endpoint returns `"error"`
- **File I/O errors**: `used_codes.json` corrupted → fallback to empty state `{}, []`
- **Unicode decode failures**: Thử nhiều encodings (`utf-8`, `utf-8-sig`, `gbk`, `gb2312`, `latin-1`)

### Database Errors

- Connection failures → caught; return 500 với `str(e)`
- Migration failures → logged nhưng allow fallback operation
- Constraint violations (ví dụ: duplicate tracking_id) → gracefully handled via `MAX(tracking_id)+1`

### Unknown Request Types

- Unknown socket request → return `{"success": false, "error": "Unknown request type: ..."}`

### Generic Catch-All

Tất cả endpoints có top-level `try/except Exception as e` which returns 500 và `traceback.print_exc()` for debugging.

---

## Phong Cách

### Phong Cách Đầu Ra

- **Mặc định**: Compact JSON responses với field names matching database column naming (snake_case nội bộ, user-friendly display bên ngoài)
- **Error messages**: Tiếng Việt chính (`"Vui lòng nhập đầy đủ thông tin"`), với một số chuỗi Tiếng Trung thay thế khi áp dụng
- **Boolean values**: Lowercase `true`/`false` trong JSON
- **Pagination**: Tất cả lists bao gồm `page`, `total_pages`, `total`, và `data` array fields

### Agent Response Patterns

Từ server.py log style:
- Prefix log lines với `[MODULE]` tags để dễ lọc: `[Unified]`, `[SocketAPI]`, `[Excel]`, `[DB]`
- Thread-safe logging qua `safe_print()` với try/except around print
- Minimal user-facing messages; prefer structured data

### Phong Cách Code (Python)

- **Encoding**: `# -*- coding: utf-8 -*-` header trên tất cả modules
- **Imports**: Standard lib → third-party → local
- **Type hints**: Optional nhưng present trong `db_helper.py`
- **Docstrings**: Tiếng Việt/Tiếng Anh mix, descriptive nhưng không exhaustive
- **Naming**: snake_case cho functions/variables; UPPER_CASE cho constants
- **Constants defined at top of file** (CATEGORY_PREFIXES, SESSION_TIMEOUT, LOGIN_RATE_LIMIT)

### Phong Cách Frontend (JavaScript/CSS)

- **CSS**: `.main-tabs` navigation với custom active states; utility classes `.module-loading` cho async content
- **JS modules**: Mỗi feature cô lập (projects.js, notices.js, profile.js, ai.js, api.js)
- **i18n**: `data-i18n` attributes; dynamic translation qua `t()` function
- **DOM events**: Delegated where possible (`$(document).on(...)`), namespaced custom events (`languageChanged`)
- **State**: Single global `AppState` object tracks current tab + auth + module loaded flags
- **API client**: Wrapper around `fetch` với error/response normalization trong `api.js`

### Quy Ước UI/UX

- **Colors** (CSS vars): primary blue, info, success green, warning, danger red
- **Loading UX**: Spinner + message per tab; non-blocking toast cho operations
- **Responsive**: Mobile-first với media queries (`max-width: 768px`) ẩn text labels
- **Form validation**: Client-side checks trước API call + server-side revalidation
- **Confirmation**: Delete operations require password (not just confirm dialog)
