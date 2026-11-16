"""
Session Manager - Quáº£n lÃ½ Session vÃ  Credentials
Module riÃªng biá» t cho viá» c lÆ°u trá»?vÃ  quáº£n lÃ½ thÃ´ng tin Ä Ä ng nháº­p
"""

import json
import os
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


# File lÆ°u credentials
CREDENTIALS_FILE = "credentials.json"
SESSION_FILE = "session.json"
LAST_IP_FILE = "last_ip.txt"
SOCKET_PORT_CANDIDATES = (12345, 8001)

# Thá» i gian session háº¿t háº¡n máº·c Ä á» nh (24 giá»?
DEFAULT_SESSION_TIMEOUT = 24 * 60 * 60  # seconds


class SessionManager:
    """
    Quáº£n lÃ½ session vÃ  credentials cho á»©ng dá»¥ng SOFFT
    
    Features:
    - LÆ°u/Ä á» c credentials (Ä Ã£ mÃ£ hÃ³a base64)
    - Táº¡o/xÃ³a session
    - Kiá» m tra session cÃ²n hiá» u lá»±c
    - Há»?trá»?ghi nhá»?Ä Ä ng nháº­p
    """
    
    def __init__(self):
        self._current_session: Optional[Dict[str, Any]] = None
        self._is_logged_in = False
    
    def _generate_key(self, data: str) -> str:
        """
        Táº¡o khÃ³a Ä Æ¡n giáº£n tá»?data (sá»?dá»¥ng MD5 hash)
        Ä á»?mÃ£ hÃ³a/giáº£i mÃ£ credentials
        """
        return hashlib.md5(data.encode()).hexdigest()
    
    def _encode(self, text: str) -> str:
        """MÃ£ hÃ³a text thÃ nh base64"""
        return base64.b64encode(text.encode()).decode()
    
    def _decode(self, encoded: str) -> str:
        """Giáº£i mÃ£ base64 thÃ nh text"""
        return base64.b64decode(encoded.encode()).decode()
    
    def save_credentials(self, username: str, password: str, remember: bool = True) -> bool:
        """
        LÆ°u credentials vÃ o file
        
        Args:
            username: TÃªn Ä Ä ng nháº­p
            password: Máº­t kháº©u (sáº?Ä Æ°á»£c mÃ£ hÃ³a)
            remember: True = lÆ°u credentials, False = xÃ³a credentials cÅ©
            
        Returns:
            True náº¿u lÆ°u thÃ nh cÃ´ng, False náº¿u cÃ³ lá» i
        """
        try:
            if not remember:
                # XÃ³a credentials náº¿u khÃ´ng muá» n ghi nhá»?
                if os.path.exists(CREDENTIALS_FILE):
                    os.remove(CREDENTIALS_FILE)
                return True
            
            # Táº¡o dá»?liá» u credentials (username + password Ä Ã£ mÃ£ hÃ³a)
            credentials_data = {
                "username": self._encode(username),
                "password": self._encode(password),
                "remember": remember,
                "saved_at": datetime.now().isoformat()
            }
            
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(credentials_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to save credentials: {e}")
            return False
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Ä á» c credentials tá»?file
        
        Returns:
            Dict chá»©a 'username' vÃ  'password' náº¿u cÃ³ lÆ°u, None náº¿u chÆ°a lÆ°u
        """
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                credentials_data = json.load(f)
            
            # Giáº£i mÃ£
            username = self._decode(credentials_data.get("username", ""))
            password = self._decode(credentials_data.get("password", ""))
            remember = credentials_data.get("remember", False)
            
            return {"username": username, "password": password, "remember": remember}
        except Exception as e:
            print(f"[SessionManager] Failed to load credentials: {e}")
            return None
    
    def clear_credentials(self) -> bool:
        """
        XÃ³a credentials Ä Ã£ lÆ°u
        
        Returns:
            True náº¿u xÃ³a thÃ nh cÃ´ng
        """
        try:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to clear credentials: {e}")
            return False
    
    def create_session(self, username: str, user_info: Optional[Dict[str, Any]] = None, 
                       timeout: int = DEFAULT_SESSION_TIMEOUT,
                       server_ip: Optional[str] = None) -> bool:
        """
        Táº¡o session má» i sau khi Ä Ä ng nháº­p thÃ nh cÃ´ng
        
        Args:
            username: TÃªn Ä Ä ng nháº­p
            user_info: ThÃ´ng tin bá»?sung vá»?user
            timeout: Thá» i gian session háº¿t háº¡n (giÃ¢y)
            server_ip: Ä á» a chá»?IP mÃ¡y chá»?(optional)
            
        Returns:
            True náº¿u táº¡o thÃ nh cÃ´ng
        """
        try:
            session_data = {
                "username": username,
                "user_info": user_info or {},
                "login_time": datetime.now().isoformat(),
                "expire_time": (datetime.now() + timedelta(seconds=timeout)).isoformat(),
                "is_valid": True
            }
            
            # ThÃªm server_ip náº¿u cÃ³
            if server_ip:
                session_data["server_ip"] = server_ip
            
            with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self._current_session = session_data
            self._is_logged_in = True
            # XÃ³a cache role cÅ© Ä á»?force Ä á» c role má» i
            if hasattr(self, '_cached_role'):
                delattr(self, '_cached_role')
            
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to create session: {e}")
            return False
    
    def validate_session(self) -> bool:
        """
        Kiá» m tra session cÃ²n hiá» u lá»±c khÃ´ng
        
        Returns:
            True náº¿u session há»£p lá»?vÃ  chÆ°a háº¿t háº¡n
        """
        try:
            if not os.path.exists(SESSION_FILE):
                self._is_logged_in = False
                return False
            
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Kiá» m tra session cÃ²n hiá» u lá»±c
            if not session_data.get("is_valid", False):
                self._is_logged_in = False
                return False
            
            # Kiá» m tra thá» i gian háº¿t háº¡n
            expire_time = datetime.fromisoformat(session_data.get("expire_time", ""))
            if datetime.now() > expire_time:
                self.end_session()
                return False
            
            # Cáº­p nháº­t session hiá» n táº¡i
            self._current_session = session_data
            self._is_logged_in = True
            return True
            
        except Exception as e:
            print(f"[SessionManager] Failed to validate local session: {e}")
            self._is_logged_in = False
            return False
    
    def validate_session_with_server(self, server_ip: str) -> Dict[str, Any]:
        """
        XÃ¡c thá»±c session vá» i server báº±ng credentials Ä Ã£ lÆ°u
        
        Args:
            server_ip: Ä á» a chá»?IP mÃ¡y chá»?
            
        Returns:
            Dict chá»©a 'success', 'user_info', 'error'
        """
        import socket
        import json
        
        # Láº¥y credentials Ä Ã£ lÆ°u
        credentials = self.load_credentials()
        if not credentials:
            return {"success": False, "user_info": None, "error": "No credentials saved"}
        
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        
        if not username or not password:
            return {"success": False, "user_info": None, "error": "Invalid credentials"}
        
        request = {
            "request": "LOGIN",
            "username": username,
            "password": password
        }
        last_error = None

        for port in SOCKET_PORT_CANDIDATES:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5)
                client_socket.connect((server_ip, port))
                client_socket.send(json.dumps(request).encode('utf-8'))
                data = client_socket.recv(4096).decode('utf-8')
                client_socket.close()

                result = json.loads(data)
                if result.get("success"):
                    user_info = result.get("user_info", {})
                    self.create_session(username, user_info, server_ip=server_ip)
                    return {"success": True, "user_info": user_info, "error": None}

                error_msg = result.get("error", "Authentication failed")
                print(f"[SessionManager] Server rejected login on port {port}: {error_msg}")
                return {"success": False, "user_info": None, "error": error_msg}
            except (socket.timeout, ConnectionRefusedError, OSError, json.JSONDecodeError) as e:
                last_error = e
                print(f"[SessionManager] Login validation failed on {server_ip}:{port} - {e}")
                continue
            except Exception as e:
                print(f"[SessionManager] Unexpected error while validating with server: {e}")
                return {"success": False, "user_info": None, "error": str(e)}

        if isinstance(last_error, socket.timeout):
            return {"success": False, "user_info": None, "error": "Server timeout"}
        if isinstance(last_error, ConnectionRefusedError):
            return {"success": False, "user_info": None, "error": "Server refused connection"}
        if isinstance(last_error, json.JSONDecodeError):
            return {"success": False, "user_info": None, "error": "Invalid server response"}
        return {"success": False, "user_info": None, "error": str(last_error) if last_error else "Connection error"}
    
    def end_session(self) -> bool:
        """
        Káº¿t thÃºc session (Ä Ä ng xuáº¥t)
        
        Returns:
            True náº¿u káº¿t thÃºc thÃ nh cÃ´ng
        """
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            
            self._current_session = None
            self._is_logged_in = False
            # XÃ³a cache role
            if hasattr(self, '_cached_role'):
                delattr(self, '_cached_role')
            
            # KhÃ´ng xÃ³a credentials khi Ä Ä ng xuáº¥t
            # (user cÃ³ thá»?Ä Ä ng nháº­p láº¡i nhanh chÃ³ng)
            
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to end session: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """
        Kiá» m tra user Ä ang Ä Ä ng nháº­p
        
        Returns:
            True náº¿u cÃ³ session há»£p lá»?
        """
        return self._is_logged_in or self.validate_session()
    
    def get_current_user(self) -> Optional[str]:
        """
        Láº¥y username cá»§a user hiá» n Ä ang Ä Ä ng nháº­p
        
        Returns:
            Username hoáº·c None
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("username")
        return None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Láº¥y thÃ´ng tin user
        
        Returns:
            Dict chá»©a thÃ´ng tin user hoáº·c None
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("user_info")
        return None
    
    def login_user(self, username: str, password: str, remember: bool = True,
                    server_ip: Optional[str] = None) -> bool:
        """
        Ä Ä ng nháº­p user (wrapper cho save_credentials vÃ  create_session)
        
        Args:
            username: TÃªn Ä Ä ng nháº­p
            password: Máº­t kháº©u
            remember: True = lÆ°u credentials
            server_ip: Ä á» a chá»?IP mÃ¡y chá»?(optional)
            
        Returns:
            True náº¿u Ä Ä ng nháº­p thÃ nh cÃ´ng
        """
        # LÆ°u credentials náº¿u cáº§n
        self.save_credentials(username, password, remember)
        # Táº¡o session vá» i server_ip
        return self.create_session(username, server_ip=server_ip)
    
    def refresh_session(self) -> bool:
        """
        LÃ m má» i thá» i gian háº¿t háº¡n cá»§a session
        
        Returns:
            True náº¿u lÃ m má» i thÃ nh cÃ´ng
        """
        if self.validate_session() and self._current_session:
            username = self._current_session.get("username")
            user_info = self._current_session.get("user_info")
            if username:
                return self.create_session(username, user_info)
        return False
    
    def extend_session(self, additional_seconds: int = DEFAULT_SESSION_TIMEOUT) -> bool:
        """
        Gia háº¡n thÃªm thá» i gian cho session
        
        Args:
            additional_seconds: Sá»?giÃ¢y cáº§n gia thÃªm
            
        Returns:
            True náº¿u gia háº¡n thÃ nh cÃ´ng
        """
        if self.validate_session() and self._current_session:
            session_data = self._current_session.copy()
            session_data["expire_time"] = (datetime.now() + timedelta(seconds=additional_seconds)).isoformat()
            
            try:
                with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
                self._current_session = session_data
                return True
            except Exception as e:
                print(f"[SessionManager] Failed to extend session: {e}")
                return False
        return False
    
    def save_server_ip(self, ip: str) -> bool:
        """
        LÆ°u server IP vÃ o session data
        
        Args:
            ip: Ä á» a chá»?IP mÃ¡y chá»?
            
        Returns:
            True náº¿u lÆ°u thÃ nh cÃ´ng
        """
        try:
            # Cáº­p nháº­t session data vá» i IP
            if self.validate_session() and self._current_session:
                self._current_session["server_ip"] = ip
                with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._current_session, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to save server IP in session: {e}")
            return False
    
    def get_server_ip(self) -> Optional[str]:
        """
        Láº¥y server IP tá»?session data
        
        Returns:
            IP mÃ¡y chá»?hoáº·c None náº¿u chÆ°a cÃ³
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("server_ip")
        return None
    
    def save_server_ip_to_file(self, ip: str) -> bool:
        """
        LÆ°u server IP vÃ o file riÃªng biá» t
        
        Args:
            ip: Ä á» a chá»?IP mÃ¡y chá»?
            
        Returns:
            True náº¿u lÆ°u thÃ nh cÃ´ng
        """
        try:
            with open(LAST_IP_FILE, 'w', encoding='utf-8') as f:
                f.write(ip)
            return True
        except Exception as e:
            print(f"[SessionManager] Failed to save server IP to file: {e}")
            return False
    
    def load_server_ip_from_file(self) -> Optional[str]:
        """
        Ä á» c server IP tá»?file riÃªng biá» t
        
        Returns:
            IP mÃ¡y chá»?hoáº·c None náº¿u chÆ°a cÃ³
        """
        try:
            if not os.path.exists(LAST_IP_FILE):
                return None
            with open(LAST_IP_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"[SessionManager] Failed to load server IP from file: {e}")
            return None
    
    # ==================== Role-based Methods ====================
    
    def get_user_role(self) -> Optional[str]:
        """
        Láº¥y role cá»§a user hiá» n táº¡i
        
        Returns:
            Role ('sales', 'engineer', 'admin', 'IT', 'Pur') hoáº·c None
        """
        # Cache role Ä á»?trÃ¡nh gá» i nhiá» u láº§n trong quÃ¡ trÃ¬nh khá» i táº¡o
        if hasattr(self, '_cached_role'):
            return self._cached_role
        
        user_info = self.get_user_info()
        if user_info:
            role = user_info.get('role')
            self._cached_role = role
            return role
        return None
    
    def is_sales(self) -> bool:
        """Kiá» m tra cÃ³ pháº£i sales khÃ´ng"""
        return self.get_user_role() == 'sales'
    
    def is_engineer(self) -> bool:
        """Kiá» m tra cÃ³ pháº£i engineer khÃ´ng"""
        return self.get_user_role() == 'engineer'
    
    def is_admin(self) -> bool:
        """Kiá» m tra cÃ³ pháº£i admin khÃ´ng"""
        return self.get_user_role() == 'admin'
    
    def is_it(self) -> bool:
        """Kiá» m tra cÃ³ pháº£i IT khÃ´ng"""
        return self.get_user_role() == 'IT'
    
    def is_pur(self) -> bool:
        """Kiá» m tra cÃ³ pháº£i Pur khÃ´ng"""
        return self.get_user_role() == 'Pur'
    
    def get_user_id(self) -> Optional[int]:
        """
        Láº¥y user_id tá»?session
        
        Returns:
            user_id hoáº·c None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('user_id')
        return None
    
    def get_full_name(self) -> Optional[str]:
        """
        Láº¥y full_name tá»?session
        
        Returns:
            full_name hoáº·c None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('full_name')
        return None
    
    def get_employee_id(self) -> Optional[str]:
        """
        Láº¥y employee_id tá»?session
        
        Returns:
            employee_id hoáº·c None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('employee_id')
        return None
    
    def can_create_project(self) -> bool:
        """
        Kiá» m tra user cÃ³ thá»?táº¡o project khÃ´ng
        Sales vÃ  Admin cÃ³ thá»?táº¡o
        """
        return self.is_sales() or self.is_admin()
    
    def can_accept_job(self) -> bool:
        """
        Kiá» m tra user cÃ³ thá»?nháº­n job khÃ´ng
        Engineer vÃ  Admin cÃ³ thá»?nháº­n
        """
        return self.is_engineer() or self.is_admin()
    
    def can_accept_job_with_permission(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n job_accept khÃ´ng
        (Dá»±a trÃªn permission, khÃ´ng pháº£i role)
        """
        return self.has_permission('job_accept')
    
    def can_manage_users(self) -> bool:
        """
        Kiá» m tra user cÃ³ thá»?quáº£n lÃ½ users khÃ´ng
        Admin vÃ  IT cÃ³ thá»?quáº£n lÃ½
        """
        return self.is_admin() or self.is_it()
    
    def can_delete_project(self) -> bool:
        """
        Kiá» m tra user cÃ³ thá»?xÃ³a project khÃ´ng
        Chá»?Admin má» i cÃ³ thá»?xÃ³a
        """
        return self.is_admin()
    
    # ==================== Permission-based Methods ====================
    
    def get_user_permissions(self) -> List[str]:
        """
        Láº¥y danh sÃ¡ch permissions tá»?session
        
        Returns:
            List of permissions hoáº·c empty list
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('permissions', [])
        return []
    
    def has_permission(self, permission: str) -> bool:
        """
        Kiá» m tra user cÃ³ má» t permission cá»?thá»?khÃ´ng
        
        Args:
            permission: TÃªn permission cáº§n kiá» m tra
        
        Returns:
            True náº¿u cÃ³ permission
        """
        permissions = self.get_user_permissions()
        return permission in permissions
    
    def can_create_code(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n táº¡o code khÃ´ng
        """
        return self.has_permission('create_code')
    
    def can_view_history(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n xem history khÃ´ng
        """
        return self.has_permission('view_history')
    
    def can_delete_history(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n xÃ³a history khÃ´ng
        """
        return self.has_permission('delete_history')
    
    def can_export(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n export khÃ´ng
        """
        return self.has_permission('export')
    
    def is_super_admin(self) -> bool:
        """
        Kiá» m tra user cÃ³ quyá» n admin khÃ´ng
        """
        return self.has_permission('admin')


# Global instance
session_manager = SessionManager()


# =============================================================================
# HÃ m tiá» n Ã­ch (convenience functions)
# =============================================================================

def get_session_manager() -> SessionManager:
    """Láº¥y instance global cá»§a SessionManager"""
    return session_manager


def is_user_logged_in() -> bool:
    """Kiá» m tra user Ä ang Ä Ä ng nháº­p"""
    return session_manager.is_logged_in()


def get_logged_in_username() -> Optional[str]:
    """Láº¥y username cá»§a user Ä ang Ä Ä ng nháº­p"""
    return session_manager.get_current_user()


def login_user(username: str, password: str, remember: bool = True,
               server_ip: Optional[str] = None) -> bool:
    """
    Ä Ä ng nháº­p user
    
    Args:
        username: TÃªn Ä Ä ng nháº­p
        password: Máº­t kháº©u
        remember: True = lÆ°u credentials
        server_ip: Ä á» a chá»?IP mÃ¡y chá»?(optional)
        
    Returns:
        True náº¿u Ä Ä ng nháº­p thÃ nh cÃ´ng
    """
    # LÆ°u credentials náº¿u cáº§n
    session_manager.save_credentials(username, password, remember)
    # Táº¡o session vá» i server_ip
    return session_manager.create_session(username, server_ip=server_ip)


def logout_user() -> bool:
    """Ä Ä ng xuáº¥t user"""
    return session_manager.end_session()


def get_server_ip() -> Optional[str]:
    """
    Láº¥y server IP tá»?session
    
    Returns:
        IP mÃ¡y chá»?hoáº·c None náº¿u chÆ°a cÃ³
    """
    return session_manager.get_server_ip()


def save_server_ip_to_file(ip: str) -> bool:
    """
    LÆ°u server IP vÃ o file riÃªng biá» t
    
    Args:
        ip: Ä á» a chá»?IP mÃ¡y chá»?
        
    Returns:
        True náº¿u lÆ°u thÃ nh cÃ´ng
    """
    return session_manager.save_server_ip_to_file(ip)


def load_server_ip_from_file() -> Optional[str]:
    """
    Ä á» c server IP tá»?file riÃªng biá» t
    
    Returns:
        IP mÃ¡y chá»?hoáº·c None náº¿u chÆ°a cÃ³
    """
    return session_manager.load_server_ip_from_file()


# ==================== Role-based Convenience Functions ====================

def get_user_role() -> Optional[str]:
    """Láº¥y role cá»§a user hiá» n táº¡i"""
    return session_manager.get_user_role()


def is_sales() -> bool:
    """Kiá» m tra cÃ³ pháº£i sales khÃ´ng"""
    return session_manager.is_sales()


def is_engineer() -> bool:
    """Kiá» m tra cÃ³ pháº£i engineer khÃ´ng"""
    return session_manager.is_engineer()


def is_admin() -> bool:
    """Kiá» m tra cÃ³ pháº£i admin khÃ´ng"""
    return session_manager.is_admin()


def is_it() -> bool:
    """Kiá» m tra cÃ³ pháº£i IT khÃ´ng"""
    return session_manager.is_it()


def is_pur() -> bool:
    """Kiá» m tra cÃ³ pháº£i Pur khÃ´ng"""
    return session_manager.is_pur()


def get_user_id() -> Optional[int]:
    """Láº¥y user_id tá»?session"""
    return session_manager.get_user_id()


def get_full_name() -> Optional[str]:
    """Láº¥y full_name tá»?session"""
    return session_manager.get_full_name()


def get_employee_id() -> Optional[str]:
    """Láº¥y employee_id tá»?session"""
    return session_manager.get_employee_id()


def can_create_project() -> bool:
    """Kiá» m tra user cÃ³ thá»?táº¡o project khÃ´ng"""
    return session_manager.can_create_project()


def can_accept_job() -> bool:
    """Kiá» m tra user cÃ³ thá»?nháº­n job khÃ´ng"""
    return session_manager.can_accept_job()


def can_accept_job_with_permission() -> bool:
    """Kiá» m tra user cÃ³ quyá» n job_accept khÃ´ng"""
    return session_manager.can_accept_job_with_permission()


def can_manage_users() -> bool:
    """Kiá» m tra user cÃ³ thá»?quáº£n lÃ½ users khÃ´ng"""
    return session_manager.can_manage_users()


def can_delete_project() -> bool:
    """Kiá» m tra user cÃ³ thá»?xÃ³a project khÃ´ng"""
    return session_manager.can_delete_project()


# ==================== Permission-based Convenience Functions ====================

def get_user_permissions() -> List[str]:
    """Láº¥y danh sÃ¡ch permissions tá»?session"""
    return session_manager.get_user_permissions()


def has_permission(permission: str) -> bool:
    """Kiá» m tra user cÃ³ má» t permission cá»?thá»?khÃ´ng"""
    return session_manager.has_permission(permission)


def can_create_code() -> bool:
    """Kiá» m tra user cÃ³ quyá» n táº¡o code khÃ´ng"""
    return session_manager.can_create_code()


def can_view_history() -> bool:
    """Kiá» m tra user cÃ³ quyá» n xem history khÃ´ng"""
    return session_manager.can_view_history()


def can_delete_history() -> bool:
    """Kiá» m tra user cÃ³ quyá» n xÃ³a history khÃ´ng"""
    return session_manager.can_delete_history()


def can_export() -> bool:
    """Kiá» m tra user cÃ³ quyá» n export khÃ´ng"""
    return session_manager.can_export()


def is_super_admin() -> bool:
    """Kiá» m tra user cÃ³ quyá» n admin khÃ´ng"""
    return session_manager.is_super_admin()
