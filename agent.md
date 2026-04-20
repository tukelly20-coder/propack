## Purpose

This is a comprehensive **Project Tracking & Drawing Code Generation System** designed for manufacturing/engineering companies. The system manages the complete workflow from sales project creation to engineer acceptance, while also generating unique drawing codes for various product categories. It includes a web-based frontend, Flask REST API backend, and legacy desktop client for code generation.

**Primary Goals:**
- Track projects from sales → engineer handoff with status management (pending/accepted)
- Generate unique, non-repeating drawing codes for 13 product categories
- Provide real-time collaboration and project visibility
- Support bilingual interface (Vietnamese & Chinese)
- Enable user role-based access control with permissions system

---

## Role

**System Architecture Agent** - Full-stack Python/JavaScript engineer specializing in enterprise workflow systems, database design, and multi-client architecture.

**Responsibilities:**
- Maintain and evolve the unified Flask server with REST APIs
- Manage the SQLite database schema and migration strategies
- Support web frontend (Bootstrap/jQuery SPA) and legacy desktop client compatibility
- Implement user authentication, session management, and permission systems
- Ensure code generation logic integrity across all product categories
- Support internationalization (i18n) for Vietnamese/Chinese locales

**Expertise Level:** Senior-level system integration across Python backend, JavaScript frontend, and SQL database with Windows-specific tooling (robocopy, UNC paths).

---

## Input

### Client-Supplied Data

**Web Client (Browser → HTTP/JSON)**
- Authentication credentials: `{username, password}`
- Project data: Form fields for tracking (customer, product, specs, dates, assignee)
- Notice actions: Job accept/decline requests
- Profile updates: `{full_name, email, phone, department, employee_id}`
- System logs: Feedback submissions with log type

**Desktop Client (socket → JSON over TCP)**
- Code generation request: `{name, category, employee}`
- Historical queries: `{page, limit, offset}`
- Delete requests: `{password, code}`

### Internal Data Sources

**Database (SQLite: `DB.db`)**
- Table `users`: user profiles, credentials hash, roles, permissions, status
- Table `customers`: customer contact database
- Table `projects`: normalized project records (19 business fields + metadata)
- Indexes: `user_id`, `ma_po`, `ten_san_pham`

**File Storage**
- `used_codes.json`: Legacy JSON storage for code generation tracking (categories + history)
- `last_name.txt`, `last_employee.txt`, `last_category.txt`, `language.txt`: UI state persistence
- `Toolsysnc/From.txt`, `Toolsysync/To.txt`: Directory sync tool configuration
- `logs/`: Web client log submissions as timestamped `.txt` files
- Material Excel: `\\192.168.2.165\...\存货档案库.xlsx` (network UNC path)

**Module: Tool Open (Material Lookup)**
- `material_core` module: Loaded via dynamic import from `Tool open/Mở mã liệu 打开链接VP.py`
- Excel lookup cache: In-memory DataFrame for `cEngineerFigNo` → `cInvCode` mapping
- File system query: Search shared folders by `cInvCode` and copy matching paths to clipboard

---

## Output

### API Responses (JSON or plain text)

**Authentication**
- `POST /api/login` → `{success, token, user: {...}, expires_in}` or `{success: false, error}`
- `GET /api/me` → `{authenticated, user, expires_in, expiring_soon}` or `{authenticated: false, reason}`
- `POST /api/logout` → `{success, message}`

**Project Management**
- `GET /api/projects` → `{data: [...], total, total_pages, page}` (paginated)
- `POST /api/projects` → `{success, record: {tracking_id, ...}}`
- `GET /api/projects/<id>` → Full project record or `{error}`
- `PUT /api/projects/<id>` → `{success}` or `{success: false, error}`
- `DELETE /api/projects/<id>?role=admin` → `{success, deleted_count}`
- `POST /api/projects/search` → `{data: [...], total, total_pages, page}`
- `POST /api/projects/filter` → `{data: [...], total, total_pages, page}`

**Code Generation**
- `POST /api/codes/create` → `{success, code: "PWLJ001-0000-00-A0"}` or error
- `GET /api/codes/history` → `{data: [...], total, total_pages, page}`
- `GET /api/codes/export` → `{success, data: [...], total}` (full history)
- `DELETE /api/codes/history/<code>` → `{success, message}` or `{success: false, error}`
- Legacy socket (TCP 8001): Plain text responses: code string, `NO_MORE_CODES`, `PONG`, `INVALID_REQUEST`, `DELETED`, `ERROR`

**Notices / Job Board**
- `GET /api/notices/pending` → pending projects list
- `POST /api/notices/accept` → `{success}`

**User Management (Admin only)**
- `GET /api/users` → list of user summary objects
- `POST /api/users` → `{success, user_id}` or `{success: false, error}`
- `PUT /api/users/<id>` → `{success}`
- `DELETE /api/users/<id>` → `{success}`

**Tool Open Lookup**
- `GET /api/tool-status` → `{status: "ready"|"error"|"unavailable", message, excel_path, excel_exists}`
- `POST /api/tool-search` → `{type: "success"|"multiple"|"error", urls: [...], copied_code, message}` or matches array

**Health / Static**
- `GET /` → `web/index.html`
- `GET /<path:filename>` → static asset
- `GET /api/health` → `{status, service, port, features}`

### Side-Effects

- Database commits (`projects`, `users`) → invalidate in-memory cache
- Code generation → append to `used_codes.json` history
- Log submission → write `web_log_<timestamp>.txt`
- Material lookup → copy `cInvCode` or URL list to system clipboard
- Password change → update session user object and database

---

## Rules

### Data Integrity Rules

1. **Code Uniqueness Guarantees**
   - Non-SJT categories: Codes like `PWLJ001-0000-00-A0` must be unique within that category (001–999 range)
   - SJT category: Codes `PSJT{emp}-{XXXX}-00-A0` unique per employee (0001–9999 range)
   - Deleted codes become reusable (recycled in order)

2. **Project History**
   - Every code generation appends a history record with ISO timestamp
   - Timestamps used for sorting: newest first
   - Deletion requires password `"kelly"` and removes code from `used_codes` pool

3. **Project Workflow**
   - New project records default `is_pending = 'yes'`
   - Only one engineer may accept a pending project (first-come, first-served)
   - Acceptance sets `accepted_by`, `accepted_at`, flips `is_pending = 'no'`
   - Pending projects visible to all; after acceptance only to engineer who accepted (plus admin)

4. **Normalization Contract**
   - Database stores normalized columns (24 columns in `projects` table)
   - API layer maps between API field names and database columns
   - Field aliases supported from legacy UI (e.g., `'Nhân viên KD'` and `'Nhân viên kinh doanh'` both map to `nhan_vien_kinh_doanh`)

### Security / Access Control

- **Authentication**: Bearer token sessions stored server-side; tokens expire after 24h
- **Rate Limiting**: Max 5 failed login attempts per 5-minute window per IP
- **Role-Based Permissions**: `create_sales_record` (sales), `job_accept` (engineer), admin = all
- **Password Min**: 6 characters
- **Account Lock**: `status = 'locked'` prevents login
- **Deletion Protection**: Only `admin` role may delete projects via API
- **CORS**: Allow-list domains (localhost, duckdns, custom domains) with support for HTTPS

### Conventions

- **Code Format**:
  - Non-SJT: `P{CATEGORY}{3-digit}-0000-00-A0` → `PWLJ001-0000-00-A0`
  - SJT: `PSJT{3-digit employee}-{4-digit serial}-00-A0` → `PSJT001-0001-00-A0`
- **Category Codes**: WLJ, ZZC, GZT, WCP, LSX, ZWJ, GZL, SJT, BSX, WLL, GTX, ZHT, LHX
- **Timestamps**: ISO 8601 for history, `YYYY-MM-DD HH:MM` for display
- **JSON keys**: snake_case for internal (Python), mixed-case for UI compatibility (Vietnamese/Chinese labels)
- **Cursor**: Use `safe_print()` for thread-safe console output
- **Excel Path**: UNC path with guaranteed network location; cached in memory once loaded
- **Language codes**: `vi` = Vietnamese, `zh` = Chinese

---

## Workflow

### 1. System Startup

```
server.py start → Flask app initialized
  ├─ CORS configured
  ├─ DB init: init_db() + migrate_to_v2() + ensure_default_users()
  ├─ Tool Open module loaded (optional)
  └─ Listen on port 8001 (HTTP)
```

### 2. User Login Flow

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

### 3. Project Creation (Sales Workflow)

```
Client: POST /api/projects with form data
  ├─ API auto-sets is_pending = 'yes'
  ├─ add_record() maps form fields → normalized columns
  ├─ INSERT into SQLite (tracking_id auto-increments)
  ├─ Cache invalidated
  └─ Returns {success, record} with tracking_id
```

### 4. Notice / Job Acceptance (Engineer Workflow)

```
Engineer clicks 'Nhận Job' (Notices tab)
  ├─ Frontend: POST /api/notices/accept {tracking_id, engineer_name}
  ├─ Backend: accept_job(tracking_id, engineer_name)
  │   ├─ UPDATE projects SET is_pending='no', accepted_by=?, accepted_at=now()
  │   └─ WHERE tracking_id=? AND is_pending='yes'
  ├─ Notices list refreshes (pending job disappears)
  └─ Job appears in engineer's accepted projects list
```

### 5. Drawing Code Generation (Legacy Desktop Client OR Web Tool)

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

### 6. Material Lookup Flow (Tool Open)

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

### 7. Search & Filter

```
Search:
  POST /api/projects/search {search, page, limit, sort_by, sort_order}
    → search_data_sql(search_text, ...) → JSON results with pagination

Filter:
  POST /api/projects/filter {filters: {field: value}, page, limit, sort_by, sort_order}
    → filter_data_sql(filter_dict, ...) → JSON results with pagination
```

---

## Knowledge

### Domain Knowledge (Manufacturing Engineering)

- **Drawings (Bản vẽ)**:
  - Main drawing (`Mã bản vẽ`): Primary drawing number
  - Technical drawing (`Mã bản vẽ kỹ thuật`): Post-PO drawing variant
  - Parent material code (`Mã mẹ`): Bill of Materials root identifier
- **Product Categories**:
  - SJT =拆件 (disassembly detailed drawing), unique per employee
  - General categories: WLJ=material rack, ZZC=logistics cart, GZT=workstation, WCP=clean room, etc.
- **Project Lifecycle**: Sales creates → Engineer accepts → Drawing codes assigned upon manufacture planning

### Technologies & Standards

- **Backend**: Python 3.x, Flask 2.x, SQLite3
- **Frontend**: HTML5, Bootstrap 5, jQuery 3.7, DataTables, i18n JavaScript
- **Desktop Client**: PySide6 (Qt6), legacy socket-based communication on port 8001
- **Serialization**: JSON over HTTP and legacy TCP
- **File Formats**: `.xlsx` (Excel via openpyxl/pandas), `.json` (state files), `.txt` (logs/configs)
- **Concurrency**: Threading for socket server (legacy), Flask handles requests linearly (but session locking via `sessions_lock`)
- **Internationalization**: Dynamic client-side language switching with `language.txt` persisted, i18n.js with Vietnamese/Chinese dictionaries

### Data References

- **Sensitive Data**: `credentials.json` exists but should not be logged/committed
- **Network Paths**: UNC path to shared inventory Excel on `192.168.2.165`
- **Config Files**: `column_settings.json` controls UI column visibility, `used_codes.json` tracks state
- **Tools**: `robocopy` for Windows directory mirroring, `PyInstaller` specs for packaging

---

## Error Handling

### Missing / Invalid Input

- **Missing fields** (code creation): return `"INVALID_REQUEST"` string
- **Unauthenticated**: 401 with `{success: false, error: "Chưa đăng nhập"}`
- **Invalid credentials**: 401 with `{success: false, error: "Tên đăng nhập hoặc mật khẩu không đúng"}`
- **Invalid employee code (not 3 digits or 000)**: 400 with `{error: "Mã nhân viên phải là 3 chữ số..."}`
- **No available codes**: 400 with `{success: false, error: "Không còn mã available cho hạng mục này"}`
- **Malformed JSON**: 400 `Dữ liệu không hợp lệ`

### Rate Limiting

- Failed logins tracked per IP → after 5 attempts within 5 minutes, 429 Too Many Requests with `code: "RATE_LIMITED"`
- Auto-reset after `LOGIN_RATE_WINDOW` (300 seconds)

### Exhausted Resources

- **Code pool exhausted**: `generate_code()` returns `None` → `NO_MORE_CODES` response
- **Excel load failure**: Tool Open shows `"Không thể kết nối Excel"`; tool-status endpoint returns `"error"`
- **File I/O errors**: `used_codes.json` corrupted → fallback to empty state `{}, []`
- **Unicode decode failures**: Try multiple encodings (`utf-8`, `utf-8-sig`, `gbk`, `gb2312`, `latin-1`)

### Database Errors

- Connection failures → caught; return 500 with `str(e)`
- Migration failures → logged but allow fallback operation
- Constraint violations (e.g., duplicate tracking_id) → gracefully handled via `MAX(tracking_id)+1`

### Unknown Request Types

- Unknown socket request → return `{"success": false, "error": "Unknown request type: ..."}`

### Generic Catch-All

All endpoints have top-level `try/except Exception as e` which returns 500 and `traceback.print_exc()` for debugging.

---

## Style

### Output Style

- **Default**: Compact JSON responses with field names matching database column naming (snake_case internally, user-friendly display externally)
- **Error messages**: Vietnamese primary (`"Vui lòng nhập đầy đủ thông tin"`), with some Chinese alternative strings where applicable
- **Boolean values**: Lowercase `true`/`false` in JSON
- **Pagination**: All lists include `page`, `total_pages`, `total`, and `data` array fields

### Agent Response Patterns

From server.py log style:
- Prefix log lines with `[MODULE]` tags for easy filtering: `[Unified]`, `[SocketAPI]`, `[Excel]`, `[DB]`
- Thread-safe logging via `safe_print()` with try/except around print
- Minimal user-facing messages; prefer structured data

### Code Style (Python)

- **Encoding**: `# -*- coding: utf-8 -*-` header on all modules
- **Imports**: Standard lib → third-party → local
- **Type hints**: Optional but present in `db_helper.py`
- **Docstrings**: Vietnamese/English mix, descriptive but not exhaustive
- **Naming**: snake_case for functions/variables; UPPER_CASE for constants
- **Constants defined at top of file** (CATEGORY_PREFIXES, SESSION_TIMEOUT, LOGIN_RATE_LIMIT)

### Frontend Style (JavaScript/CSS)

- **CSS**: `.main-tabs` navigation with custom active states; utility classes `.module-loading` for async content
- **JS modules**: Each feature isolated (projects.js, notices.js, profile.js, ai.js, api.js)
- **i18n**: `data-i18n` attributes; dynamic translation via `t()` function
- **DOM events**: Delegated where possible (`$(document).on(...)`), namespaced custom events (`languageChanged`)
- **State**: Single global `AppState` object tracks current tab + auth + module loaded flags
- **API client**: Wrapper around `fetch` with error/response normalization in `api.js`

### UI/UX Conventions

- **Colors** (CSS vars): primary blue, info, success green, warning, danger red
- **Loading UX**: Spinner + message per tab; non-blocking toast for operations
- **Responsive**: Mobile-first with media queries (`max-width: 768px`) hiding text labels
- **Form validation**: Client-side checks before API call + server-side revalidation
- **Confirmation**: Delete operations require password (not just confirm dialog)
