# Cấu trúc Dự án V8 - Tạo Mã Bản vẽ Tự động

## Tổng quan
Ứng dụng Flask quản lý mã bản vẽ, hỗ trợ đa ngôn ngữ (Tiếng Việt/Tiếng Trung), tích hợp AI, chạy trên hai ports:
- **Port 8001**: HTTP Server (Web UI, REST API)
- **Port 12345**: TCP Socket Server (compatibility với client V7 cũ)

## Cấu trúc Thư mục

```
/ (root)
├── server.py                  # Main Flask server
├── client.py                  # Client module
├── server_gui.py              # GUI server (desktop)
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── pyrightconfig.json         # Type checking config
├── MIGRATION_GUIDE.md         # Migration guide
├── README.md                  # README Tiếng Việt
├── README_zh.md               # README Tiếng Trung
│
├── src/                       # Source code Python chính
│   ├── __init__.py
│   ├── db_helper.py           # Database helper (SQLite)
│   ├── code_generator.py      # Logic tạo mã bản vẽ
│   ├── session_manager.py     # Session management
│   ├── config.py              # Configuration
│   ├── logging_config.py      # Logging setup
│   ├── security.py            # Security utils
│   ├── models.py              # Data models
│   ├── excel_helper.py        # Excel integration
│   ├── language_manager.py    # i18n
│   ├── tcp_server.py          # Legacy TCP server (V7)
│   ├── socket_api.py          # Socket API over HTTP
│   ├── chat_db.py             # Chat database
│   ├── chat_routes.py         # Chat API routes
│   ├── chat_service.py        # Chat service logic
│   ├── ai_memory.py           # AI long-term memory
│   ├── intent_detector.py     # Intent detection
│   ├── mcp_tools.py           # MCP tools
│   ├── system_prompt.py       # System prompts
│   │
│   ├── ai/                    # AI integration modules
│   │   ├── gemini_routes.py
│   │   ├── ollama_routes.py
│   │   ├── openrouter_routes.py
│   │   └── agent_routes.py
│   │
│   ├── utils/                 # Utilities
│   │   └── file_handler.py
│   │
│   └── (các module khác: about.py, notice_tab.py, user_management.py, ...)
│
├── web/                       # Web client (static files)
│   ├── index.html
│   ├── css/
│   │   ├── _base.css
│   │   ├── _layout.css
│   │   ├── _components.css
│   │   ├── _variables.css
│   │   └── style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       ├── i18n.js
│       ├── components.js
│       ├── status.js
│       ├── notices.js
│       ├── profile.js
│       └── modules/
│           ├── ai.js
│           ├── projects.js
│           ├── notices.js
│           ├── profile.js
│           └── taomabanve.js
│
├── routes/                    # Flask blueprints
│   ├── auth_routes.py
│   ├── project_routes.py
│   ├── code_routes.py
│   ├── notice_routes.py
│   ├── customer_routes.py
│   └── log_routes.py
│
├── Tool open/                 # Legacy tool integration (V7)
│   └── Mở mã liệu 打开链接VP.py
│
├── docs/                      # Documentation
│   ├── PROJECT_STRUCTURE.md   # (file này)
│   ├── DEVELOPMENT.md         # Development guide
│   └── plans/                 # Project planning docs
│       ├── plan_fix_ui_project_modal.md
│       ├── ui-review-report.md
│       └── upload-attachments-plan.md
│
├── data/                      # Runtime data (IGNORED by git)
│   ├── used_codes.json        # Generated drawing codes history
│   ├── column_settings.json   # Column configuration
│   ├── session.json           # Session data
│   ├── sessions.json          # Multi-session data
│   ├── key_management.xlsx    # Key management spreadsheet
│   ├── DB.db                  # Main database
│   ├── chat_sessions.db       # Chat sessions database
│   └── ai_memory.db           # AI memory database
│
├── logs/                      # Application logs (IGNORED)
│   └── (generated at runtime)
│
└── tests/                     # Test files (if any)
```

## Mô tả Chi tiết

### Source Code (`src/`)
Chứa toàn bộ logic nghiệp vụ, models, AI integration.
- **ai/**: AI agents và routes cho Gemini/Ollama/OpenRouter.
- **utils/**: Tiện ích chung (file_handler.py).

### Web Client (`web/`)
- Giao diện người dùng, CSS/JS tách riêng.
- CSS dùng partials: base, layout, components, variables.
- JS modular với thư mục `modules/`.

### Routes (`routes/`)
- Flask blueprints cho các nhóm endpoint: auth, projects, codes, notices, customers, logs.

### Tool Open (`Tool open/`)
- Module legacy để tích hợp tool V7 (mở link vật liệu).

### Data (`data/`)
- **KHÔNG ĐƯỢC COMMIT** (đã ignore). Chứa dữ liệu runtime, databases, cấu hình người dùng.

### Logs (`logs/`)
- Log files, ignore.

## Khởi chạy

```bash
pip install -r requirements.txt
python server.py
```

Truy cập: http://localhost:8001

## Ghi chú
- Server chạy trên port 8001 (HTTP) và 12345 (TCP socket cho client V7 cũ).
- File `credentials.json` chứa secret keys, không commit, phải được tạo thủ công từ `.env.example`.
- Thư mục `data/` và `logs/` được ignore, nội dung được tạo khi chạy.
