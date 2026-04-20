# Development Guide - V8 Drawing Code Generator

## Coding Conventions

### Python
- **Naming**: snake_case cho file, function, variable; PascalCase cho class.
- **Type hints**: Khuyến khích sử dụng.
- **Formatting**: Black (line length 120).
- **Linting**: flake8, mypy.
- **Imports**: Standard lib -> third-party -> local.

### JavaScript
- **Naming**: camelCase cho variable/function; PascalCase cho class.
- **Indentation**: 2 spaces.
- **Modules**: ES6+ import/export.

### CSS
- Sử dụng BEM hoặc utility-first.
- Variables trong `_variables.css`.
- Partial files tên bắt đầu bằng `_`.

## Project Structure (Xem docs/PROJECT_STRUCTURE.md)

## Cleanup Policy
- **Không commit**:
  - Debug scripts (`debug_*.py`, `check_*.py`, `inspect_*.py`, ...)
  - Temporary files (`*.log`, `*.tmp`, `*.bak`)
  - Bytecode (`__pycache__/`, `*.pyc`)
  - Data files trong `data/` (đã ignore)
  - Logs trong `logs/`
  - Secrets (`credentials.json`, `.env`)
- **Chỉ commit** source code, config mẫu (`.env.example`), tài liệu.

## Adding New Features
1. Tạo branch theo feature: `feat/ten-tinh-nang`.
2. Viết code theo quy ước.
3. Test locally.
4. Commit với message rõ ràng.
5. Push và tạo PR.

## Testing
```bash
pytest
pytest --cov=src
```

## Type Checking
```bash
pyright
```

## Formatting
```bash
black src/ web/js/
```

## Environment Setup
Sao chép `.env.example` thành `.env` và điền:
```
FLASK_SECRET_KEY=your-secret-key
FLASK_ENV=development
```

## Database
- SQLite files nằm trong `data/` (ignored).
- Migration scripts nằm trong `src/db_helper.py`.

## Troubleshooting
- **Port đã dùng**: Kiểm tra process trên port 8001/12345.
- **Lỗi import**: Đảm bảo `PYTHONPATH` includes project root.
- **Lỗi encoding**: Sử dụng UTF-8 everywhere.
