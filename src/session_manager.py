# -*- coding: utf-8 -*-
"""
Session Manager Module - Quản lý Session và Authentication

Module riêng biệt xử lý:
- Lưu trữ và quản lý user sessions (persistent across server restarts)
- Rate limiting cho đăng nhập
- Token generation cho authentication
- Session persistence vào file JSON

Các thành phần chính:
- sessions: Dict lưu trữ session data
- sessions_lock: Thread lock cho thread-safety
- SESSION_TIMEOUT: Thời gian session hết hạn (30 phút mặc định)
- SESSION_FILE: File lưu session (sessions.json)

Export:
- sessions, sessions_lock, SESSION_TIMEOUT, SESSION_FILE
- load_sessions_from_file, save_sessions_to_file, schedule_save_sessions, cleanup_sessions
- generate_token, check_rate_limit, record_login_attempt
- register_routes
"""

import json
import os
import threading
import time
import secrets
import atexit
from typing import Optional, Dict, Any, Tuple

# =============================================================================
# Global State
# =============================================================================

# Sessions dictionary - lưu trữ token -> user info mapping
sessions: Dict[str, Dict[str, Any]] = {}

# Thread lock cho thread-safety operations
sessions_lock = threading.Lock()

# Session timeout: 30 phút (như yêu cầu)
SESSION_TIMEOUT = 30 * 60  # 30 phút tính bằng giây

# Session persistence file
SESSION_FILE = 'sessions.json'

# Rate limiting configuration
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300  # 5 phút

# Login attempts tracking
login_attempts: Dict[str, list] = {}
login_attempts_lock = threading.Lock()

# Debounce timer cho việc lưu sessions
_session_save_timer = None
_session_save_lock = threading.Lock()

# Session save debounce delay (giảm số lần ghi file)
SESSION_SAVE_DEBOUNCE_SECONDS = 2.0

# =============================================================================
# Session Persistence Functions
# =============================================================================

def load_sessions_from_file() -> None:
    """Load sessions từ JSON file on startup"""
    global sessions
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                if not raw_content.strip():
                    _print_safe("[Sessions] Empty session file, starting fresh")
                    sessions = {}
                    return
                loaded = json.loads(raw_content)
                if not isinstance(loaded, dict):
                    _print_safe("[Sessions] Invalid session file format (not a dict), starting fresh")
                    sessions = {}
                    return
                
                # Filter out expired sessions
                current_time = time.time()
                valid_sessions = {}
                for token, data in loaded.items():
                    if not isinstance(data, dict):
                        continue
                    created_at = data.get('created_at', 0)
                    if not isinstance(created_at, (int, float)):
                        continue
                    elapsed = current_time - created_at
                    if elapsed < SESSION_TIMEOUT:
                        valid_sessions[token] = data
                
                sessions = valid_sessions
                _print_safe(f"[Sessions] Loaded {len(sessions)} valid sessions from file")
        except json.JSONDecodeError as e:
            _print_safe(f"[Sessions] Invalid JSON in session file: {e}")
            sessions = {}
        except Exception as e:
            _print_safe(f"[Sessions] Error loading sessions: {e}")
            sessions = {}

def save_sessions_to_file() -> None:
    """Save sessions vào JSON file (called on login/logout)"""
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(dict(sessions), f, ensure_ascii=False, indent=2)
    except Exception as e:
        _print_safe(f"[Sessions] Error saving sessions: {e}")

def schedule_save_sessions() -> None:
    """Schedule a debounced save (prevents excessive file writes)"""
    global _session_save_timer
    with _session_save_lock:
        # Cancel existing timer if any
        if _session_save_timer:
            _session_save_timer.cancel()
        # Schedule new save with debounce delay
        _session_save_timer = threading.Timer(SESSION_SAVE_DEBOUNCE_SECONDS, save_sessions_to_file)
        _session_save_timer.daemon = True
        _session_save_timer.start()

def cleanup_sessions() -> None:
    """Save sessions on server shutdown (called by atexit)"""
    global _session_save_timer
    # Cancel pending timer
    with _session_save_lock:
        if _session_save_timer:
            _session_save_timer.cancel()
            _session_save_timer = None
    # Force save all sessions
    save_sessions_to_file()
    _print_safe("[Sessions] Sessions saved on shutdown")

# Register cleanup for server shutdown
atexit.register(cleanup_sessions)

# =============================================================================
# Token Generation
# =============================================================================

def generate_token() -> str:
    """Tạo token ngẫu nhiên 64 ký tự hex"""
    return secrets.token_hex(32)

# =============================================================================
# Rate Limiting Functions
# =============================================================================

def check_rate_limit(ip: str) -> Tuple[bool, int]:
    """Kiểm tra rate limit cho IP đăng nhập
    
    Args:
        ip: Địa chỉ IP của client
        
    Returns:
        Tuple[bool, int]: (allowed, remaining_attempts)
    """
    current_time = time.time()
    with login_attempts_lock:
        if ip in login_attempts:
            # Filter out old attempts outside the window
            login_attempts[ip] = [
                (t, s) for t, s in login_attempts[ip]
                if current_time - t < LOGIN_RATE_WINDOW
            ]
            if len(login_attempts[ip]) >= LOGIN_RATE_LIMIT:
                return False, 0
            return True, LOGIN_RATE_LIMIT - len(login_attempts[ip])
        return True, LOGIN_RATE_LIMIT

def record_login_attempt(ip: str, success: bool) -> None:
    """Ghi nhận attempt đăng nhập
    
    Args:
        ip: Địa chỉ IP của client
        success: True nếu đăng nhập thành công
    """
    with login_attempts_lock:
        if ip not in login_attempts:
            login_attempts[ip] = []
        login_attempts[ip].append((time.time(), success))

# =============================================================================
# Helper Functions
# =============================================================================

def _print_safe(*args, **kwargs) -> None:
    """Thread-safe print cho module này"""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# =============================================================================
# Flask Routes Registration
# =============================================================================

def register_routes(app):
    """Đăng ký các session-related routes vào Flask app (nếu cần)
    
    Hiện tại api_me endpoint được giữ trong server.py.
    Function này có thể được sử dụng để đăng ký thêm routes nếu cần.
    
    Args:
        app: Flask application instance
    """
    _print_safe("[SessionManager] Module loaded successfully")

# =============================================================================
# Initialization
# =============================================================================

# Load sessions on module import
load_sessions_from_file()

# =============================================================================
# Module Info
# =============================================================================

__all__ = [
    # Global state
    'sessions',
    'sessions_lock',
    'SESSION_TIMEOUT',
    'SESSION_FILE',
    
    # Functions
    'load_sessions_from_file',
    'save_sessions_to_file',
    'schedule_save_sessions',
    'cleanup_sessions',
    'generate_token',
    'check_rate_limit',
    'record_login_attempt',
    'register_routes',
]
