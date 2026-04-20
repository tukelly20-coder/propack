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
import socket
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
# Session Manager Class - High-level user session and role management
# =============================================================================

class SessionManager:
    """Quản lý session và authentication cho user"""
    
    def __init__(self):
        self._current_user = None
        self._user_info = None
        self._server_ip = None
        self._current_session = None  # Dict chứa session token và thông tin phiên
        self._credentials_file = 'credentials.json'
    
    def is_logged_in(self) -> bool:
        """Kiểm tra user đã login chưa"""
        return self._current_user is not None
    
    def get_current_user(self) -> Optional[str]:
        """Lấy username hiện tại"""
        return self._current_user
    
    def get_user_info(self) -> Optional[dict]:
        """Lấy thông tin user hiện tại"""
        return self._user_info
    
    def get_user_role(self) -> Optional[str]:
        """Lấy role của user hiện tại"""
        if self._user_info:
            return self._user_info.get('role')
        return None
    
    def get_server_ip(self) -> Optional[str]:
        """Lấy server IP đã lưu"""
        if self._server_ip:
            return self._server_ip
        # Fallback: load từ file
        return self.load_server_ip_from_file()
    
    def is_sales(self) -> bool:
        """Kiểm tra user có role Sales không"""
        return self.get_user_role() == 'sales'
    
    def is_engineer(self) -> bool:
        """Kiểm tra user có role Engineer không"""
        return self.get_user_role() == 'engineer'
    
    def is_admin(self) -> bool:
        """Kiểm tra user có role Admin không"""
        return self.get_user_role() == 'admin'
    
    def is_it(self) -> bool:
        """Kiểm tra user có role IT không"""
        return self.get_user_role() == 'IT'
    
    def is_pur(self) -> bool:
        """Kiểm tra user có role PUR không"""
        return self.get_user_role() == 'PUR'
    
    def get_user_id(self) -> Optional[str]:
        """Lấy user_id từ user_info"""
        if self._user_info:
            return self._user_info.get('user_id') or self._user_info.get('id')
        return None
    
    def get_full_name(self) -> Optional[str]:
        """Lấy full name từ user_info"""
        if self._user_info:
            return self._user_info.get('full_name') or self._user_info.get('name')
        return None
    
    def can_delete_project(self) -> bool:
        """Kiểm tra user có quyền xóa project không (chỉ Admin)"""
        return self.is_admin()
    
    def can_accept_job_with_permission(self) -> bool:
        """Kiểm tra user có quyền accept job không (Admin, Engineer, Sales)"""
        return self.is_admin() or self.is_engineer() or self.is_sales()
    
    def save_credentials(self, username: str, password: str, remember: bool = False) -> None:
        """Lưu credentials vào file JSON"""
        if not remember:
            return
        try:
            with open(self._credentials_file, 'w', encoding='utf-8') as f:
                json.dump({'username': username, 'password': password}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _print_safe(f"[SessionManager] Error saving credentials: {e}")
    
    def load_credentials(self) -> Optional[dict]:
        """Load credentials từ file JSON"""
        try:
            if os.path.exists(self._credentials_file):
                with open(self._credentials_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            _print_safe(f"[SessionManager] Error loading credentials: {e}")
        return None
    
    def save_server_ip_to_file(self, server_ip: str) -> None:
        """Lưu server IP vào file riêng"""
        try:
            with open('server_ip.txt', 'w', encoding='utf-8') as f:
                f.write(server_ip)
            self._server_ip = server_ip
        except Exception as e:
            _print_safe(f"[SessionManager] Error saving server IP: {e}")
    
    def load_server_ip_from_file(self) -> Optional[str]:
        """Load server IP từ file riêng"""
        try:
            if os.path.exists('server_ip.txt'):
                with open('server_ip.txt', 'r', encoding='utf-8') as f:
                    ip = f.read().strip()
                    if ip:
                        self._server_ip = ip
                        return ip
        except Exception as e:
            _print_safe(f"[SessionManager] Error loading server IP: {e}")
        return None
    
    def create_session(self, username: str, user_info: dict, server_ip: str = None) -> None:
        """Tạo session cho user đã login"""
        self._current_user = username
        self._user_info = user_info
        if server_ip:
            self._server_ip = server_ip
        
        # Tạo session token và lưu vào global sessions
        token = generate_token()
        session_data = {
            'username': username,
            'user_info': user_info,
            'created_at': time.time(),
            'login_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with sessions_lock:
            sessions[token] = session_data
        
        # Lưu session hiện tại
        self._current_session = {
            'token': token,
            'login_time': session_data['login_time'],
            'username': username
        }
        
        # Debounce save sessions to file
        schedule_save_sessions()
    
    def clear_session(self) -> None:
        """Xóa session cục bộ (không logout khỏi server)"""
        self._current_user = None
        self._user_info = None
        self._current_session = None
        # Không xóa _server_ip để giữ lại cấu hình
    
    def end_session(self) -> None:
        """Kết thúc session hiện tại (logout)"""
        # Xóa session token khỏi global sessions nếu có
        if self._current_session and 'token' in self._current_session:
            token = self._current_session['token']
            with sessions_lock:
                if token in sessions:
                    del sessions[token]
            schedule_save_sessions()
        
        self.clear_session()
    
    def validate_session_with_server(self, server_ip: str) -> dict:
        """Xác thực session với server"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)
            client_socket.connect((server_ip, 8001))
            
            request = {"request": "VALIDATE_SESSION", "username": self._current_user}
            client_socket.send(json.dumps(request).encode('utf-8'))
            
            response_data = client_socket.recv(4096).decode('utf-8')
            client_socket.close()
            
            result = json.loads(response_data)
            if result.get('valid'):
                # Cập nhật user info từ server
                self._user_info = result.get('user_info', self._user_info)
                # Update current session info
                self._current_session = {
                    'token': self._current_session.get('token') if self._current_session else generate_token(),
                    'login_time': self._current_session.get('login_time', time.strftime('%Y-%m-%d %H:%M:%S')),
                    'username': self._current_user
                }
                return {'success': True, 'user_info': self._user_info}
            else:
                self.clear_session()
                return {'success': False, 'error': result.get('error', 'Session expired')}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# =============================================================================
# Singleton Instance
# =============================================================================

session_manager = SessionManager()


# =============================================================================
# Convenience Functions
# =============================================================================

def get_session_manager() -> SessionManager:
    """Lấy singleton instance của SessionManager"""
    return session_manager


# =============================================================================
# Module Info (update __all__)
# =============================================================================

__all__ = [
    # Global state
    'sessions',
    'sessions_lock',
    'SESSION_TIMEOUT',
    'SESSION_FILE',
    'session_manager',
    'get_session_manager',
    
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
