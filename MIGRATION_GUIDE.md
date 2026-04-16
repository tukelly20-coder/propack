# MIGRATION_GUIDE.md
## Hướng dẫn di chuyển cấu trúc project V8

### Tổng quan thay đổi

Project đã được tái cấu trúc với các mục tiêu:
1. **Modularization** - Tách server.py thành các modules nhỏ hơn
2. **Security** - Cải thiện CORS và credentials management
3. **Type Safety** - Thêm Type Hints và cấu hình Pyright
4. **Logging** - Thay thế print() bằng structured logging
5. **Testing** - Infrastructure cho unit tests
6. **API Versioning** - Hỗ trợ /api/v1/ endpoints

### Cấu trúc mới

```
project/
├── src/                    # Core packages
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── logging_config.py   # Logging utilities
│   ├── security.py         # Security utilities
│   └── [existing modules]  # db_helper, chat_service, etc.
│
├── routes/                 # Flask blueprints
│   ├── __init__.py         # Blueprint registration + versioning
│   ├── auth_routes.py      # Authentication routes
│   ├── api_routes.py       # Projects/Codes/Notices APIs
│   ├── ai_routes.py        # AI integration routes
│   ├── socket_routes.py    # HTTP Socket API
│   └── tool_routes.py      # Tool Open integration
│
├── tests/                  # Test infrastructure
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_config.py      # Config module tests
│   ├── test_security.py    # Security module tests
│   ├── test_logging.py     # Logging module tests
│   └── test_routes.py      # Route tests
│
├── server.py               # Main entry point (updated)
├── requirements.txt        # Python dependencies
├── pyrightconfig.json      # Type checking configuration
├── .env.example           # Environment variables template
└── credentials.json       # (existing) API keys & secrets
```

### Các module mới

#### 1. src/config.py
- Quản lý cấu hình từ environment variables và credentials.json
- Singleton pattern cho global config access
- Type-safe configuration classes (ServerConfig, SecurityConfig, AIConfig, etc.)

**Sử dụng:**
```python
from src.config import get_config

config = get_config()
print(config.server.port)
print(config.ai.gemini.model)
```

#### 2. src/logging_config.py
- Centralized logging với rotation
- Thread-safe logging
- Structured logging utilities

**Sử dụng:**
```python
from src.logging_config import get_logger, setup_logging

# Setup logging
setup_logging(log_to_file=True, log_to_console=True)

# Get logger
logger = get_logger('my_module')
logger.info("Info message", operation="test")
```

#### 3. src/security.py
- CORS configuration
- Rate limiting helpers
- Input sanitization
- Password hashing utilities

**Sử dụng:**
```python
from src.security import RateLimiter, sanitize_input

# Rate limiting
limiter = RateLimiter(max_attempts=5, window_seconds=300)
allowed, remaining = limiter.check_rate_limit("192.168.1.1")

# Input sanitization
clean_input = sanitize_input(user_input, max_length=1000)
```

### API Versioning

#### Legacy endpoints (backward compatible)
- `/api/login`, `/api/logout`, `/api/me`
- `/api/projects`, `/api/codes/create`, `/api/notices/*`
- `/api/ai/*`

#### V1 endpoints (new)
- `/api/v1/*` - Tất cả endpoints dưới prefix /api/v1/
- Ví dụ: `/api/v1/projects`, `/api/v1/auth/login`

### Environment Variables

Các biến mới trong `.env`:
```bash
# Server
FLASK_HOST=0.0.0.0
FLASK_PORT=8001
FLASK_DEBUG=false
FLASK_SECRET_KEY=your-secret-key-here

# AI
OLLAMA_HOST=localhost:11434
GEMINI_API_KEY=your-key
OPENROUTER_API_KEY=your-key

# Database
DB_PATH=DB.db
```

### Cập nhật server.py (backward compatibility)

server.py hiện tại vẫn hoạt động. Để tích hợp modules mới:

```python
# Import new modules
from src.config import get_config
from src.logging_config import setup_logging, get_logger
from src.security import configure_cors, add_security_headers_to_app

# Initialize
setup_logging()
config = get_config()

# Configure CORS
configure_cors(app, config.security)

# Add security headers
add_security_headers_to_app(app)

# Use logging instead of print
logger = get_logger('server')
logger.info("Server started", port=config.server.port)
```

### Chạy tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Pyright type checking

```bash
# Check types
pyright src/ routes/ tests/

# Or use the configured pyrightconfig.json
pyright
```

### Troubleshooting

#### Import errors
Đảm bảo Python path bao gồm project root:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

#### Type checking warnings
Các warnings về Optional types là bình thường trong code cũ.
Có thể ignore các cảnh báo không quan trọng trong pyrightconfig.json.

#### Test import errors
Nếu pytest không tìm thấy modules:
```bash
cd /path/to/project
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

### Backward Compatibility

Tất cả các endpoints hiện tại vẫn hoạt động:
- `/api/*` - Tất cả endpoints cũ
- `/api/socket` - Socket API vẫn hoạt động
- Database schema không thay đổi
- Session management vẫn tương thích

### Liên hệ hỗ trợ

Nếu có vấn đề với migration, kiểm tra:
1. Python version (>= 3.11)
2. Đã cài đặt tất cả dependencies
3. Đang chạy từ project root directory