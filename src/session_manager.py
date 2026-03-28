"""
Session Manager - Quản lý Session và Credentials
Module riêng biệt cho việc lưu tr�?và quản lý thông tin đăng nhập
"""

import json
import os
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


# File lưu credentials
CREDENTIALS_FILE = "credentials.json"
SESSION_FILE = "session.json"
LAST_IP_FILE = "last_ip.txt"

# Thời gian session hết hạn mặc định (24 gi�?
DEFAULT_SESSION_TIMEOUT = 24 * 60 * 60  # seconds


class SessionManager:
    """
    Quản lý session và credentials cho ứng dụng SOFFT
    
    Features:
    - Lưu/đọc credentials (đã mã hóa base64)
    - Tạo/xóa session
    - Kiểm tra session còn hiệu lực
    - H�?tr�?ghi nh�?đăng nhập
    """
    
    def __init__(self):
        self._current_session: Optional[Dict[str, Any]] = None
        self._is_logged_in = False
    
    def _generate_key(self, data: str) -> str:
        """
        Tạo khóa đơn giản t�?data (s�?dụng MD5 hash)
        Đ�?mã hóa/giải mã credentials
        """
        return hashlib.md5(data.encode()).hexdigest()
    
    def _encode(self, text: str) -> str:
        """Mã hóa text thành base64"""
        return base64.b64encode(text.encode()).decode()
    
    def _decode(self, encoded: str) -> str:
        """Giải mã base64 thành text"""
        return base64.b64decode(encoded.encode()).decode()
    
    def save_credentials(self, username: str, password: str, remember: bool = True) -> bool:
        """
        Lưu credentials vào file
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu (s�?được mã hóa)
            remember: True = lưu credentials, False = xóa credentials cũ
            
        Returns:
            True nếu lưu thành công, False nếu có lỗi
        """
        try:
            if not remember:
                # Xóa credentials nếu không muốn ghi nh�?
                if os.path.exists(CREDENTIALS_FILE):
                    os.remove(CREDENTIALS_FILE)
                return True
            
            # Tạo d�?liệu credentials (username + password đã mã hóa)
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
            print(f"[SessionManager] Lỗi khi lưu credentials: {e}")
            return False
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Đọc credentials t�?file
        
        Returns:
            Dict chứa 'username' và 'password' nếu có lưu, None nếu chưa lưu
        """
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                credentials_data = json.load(f)
            
            # Giải mã
            username = self._decode(credentials_data.get("username", ""))
            password = self._decode(credentials_data.get("password", ""))
            remember = credentials_data.get("remember", False)
            
            return {"username": username, "password": password, "remember": remember}
        except Exception as e:
            print(f"[SessionManager] Lỗi khi đọc credentials: {e}")
            return None
    
    def clear_credentials(self) -> bool:
        """
        Xóa credentials đã lưu
        
        Returns:
            True nếu xóa thành công
        """
        try:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
            return True
        except Exception as e:
            print(f"[SessionManager] Lỗi khi xóa credentials: {e}")
            return False
    
    def create_session(self, username: str, user_info: Optional[Dict[str, Any]] = None, 
                       timeout: int = DEFAULT_SESSION_TIMEOUT,
                       server_ip: Optional[str] = None) -> bool:
        """
        Tạo session mới sau khi đăng nhập thành công
        
        Args:
            username: Tên đăng nhập
            user_info: Thông tin b�?sung v�?user
            timeout: Thời gian session hết hạn (giây)
            server_ip: Địa ch�?IP máy ch�?(optional)
            
        Returns:
            True nếu tạo thành công
        """
        try:
            session_data = {
                "username": username,
                "user_info": user_info or {},
                "login_time": datetime.now().isoformat(),
                "expire_time": (datetime.now() + timedelta(seconds=timeout)).isoformat(),
                "is_valid": True
            }
            
            # Thêm server_ip nếu có
            if server_ip:
                session_data["server_ip"] = server_ip
            
            with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self._current_session = session_data
            self._is_logged_in = True
            # Xóa cache role cũ đ�?force đọc role mới
            if hasattr(self, '_cached_role'):
                delattr(self, '_cached_role')
            
            return True
        except Exception as e:
            print(f"[SessionManager] Lỗi khi tạo session: {e}")
            return False
    
    def validate_session(self) -> bool:
        """
        Kiểm tra session còn hiệu lực không
        
        Returns:
            True nếu session hợp l�?và chưa hết hạn
        """
        try:
            if not os.path.exists(SESSION_FILE):
                self._is_logged_in = False
                return False
            
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Kiểm tra session còn hiệu lực
            if not session_data.get("is_valid", False):
                self._is_logged_in = False
                return False
            
            # Kiểm tra thời gian hết hạn
            expire_time = datetime.fromisoformat(session_data.get("expire_time", ""))
            if datetime.now() > expire_time:
                self.end_session()
                return False
            
            # Cập nhật session hiện tại
            self._current_session = session_data
            self._is_logged_in = True
            return True
            
        except Exception as e:
            print(f"[SessionManager] Lỗi khi kiểm tra session: {e}")
            self._is_logged_in = False
            return False
    
    def validate_session_with_server(self, server_ip: str) -> Dict[str, Any]:
        """
        Xác thực session với server bằng credentials đã lưu
        
        Args:
            server_ip: Địa ch�?IP máy ch�?
            
        Returns:
            Dict chứa 'success', 'user_info', 'error'
        """
        import socket
        import json
        
        # Lấy credentials đã lưu
        credentials = self.load_credentials()
        if not credentials:
            return {"success": False, "user_info": None, "error": "No credentials saved"}
        
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        
        if not username or not password:
            return {"success": False, "user_info": None, "error": "Invalid credentials"}
        
        try:
            # Tạo socket và kết nối đến server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # Timeout 5 giây
            
            client_socket.connect((server_ip, 8001))
            
            # Gửi yêu cầu đăng nhập
            request = {
                "request": "LOGIN",
                "username": username,
                "password": password
            }
            client_socket.send(json.dumps(request).encode('utf-8'))
            
            # Nhận phản hồi
            data = client_socket.recv(4096).decode('utf-8')
            client_socket.close()
            
            # Parse kết qu�?
            result = json.loads(data)
            
            if result.get("success"):
                user_info = result.get("user_info", {})
                # Cập nhật session với thông tin user mới nhất t�?server
                self.create_session(username, user_info, server_ip=server_ip)
                return {"success": True, "user_info": user_info, "error": None}
            else:
                error_msg = result.get("error", "Authentication failed")
                print(f"[SessionManager] Server rejected login: {error_msg}")
                return {"success": False, "user_info": None, "error": error_msg}
                
        except socket.timeout:
            print(f"[SessionManager] Timeout khi kết nối đến {server_ip}")
            return {"success": False, "user_info": None, "error": "Server timeout"}
        except ConnectionRefusedError:
            print(f"[SessionManager] Server t�?chối kết nối t�?{server_ip}")
            return {"success": False, "user_info": None, "error": "Server refused connection"}
        except json.JSONDecodeError as e:
            print(f"[SessionManager] Phản hồi server không hợp l�? {e}")
            return {"success": False, "user_info": None, "error": "Invalid server response"}
        except Exception as e:
            print(f"[SessionManager] Lỗi khi xác thực với server: {e}")
            return {"success": False, "user_info": None, "error": str(e)}
    
    def end_session(self) -> bool:
        """
        Kết thúc session (đăng xuất)
        
        Returns:
            True nếu kết thúc thành công
        """
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            
            self._current_session = None
            self._is_logged_in = False
            # Xóa cache role
            if hasattr(self, '_cached_role'):
                delattr(self, '_cached_role')
            
            # Không xóa credentials khi đăng xuất
            # (user có th�?đăng nhập lại nhanh chóng)
            
            return True
        except Exception as e:
            print(f"[SessionManager] Lỗi khi kết thúc session: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """
        Kiểm tra user đang đăng nhập
        
        Returns:
            True nếu có session hợp l�?
        """
        return self._is_logged_in or self.validate_session()
    
    def get_current_user(self) -> Optional[str]:
        """
        Lấy username của user hiện đang đăng nhập
        
        Returns:
            Username hoặc None
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("username")
        return None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user
        
        Returns:
            Dict chứa thông tin user hoặc None
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("user_info")
        return None
    
    def login_user(self, username: str, password: str, remember: bool = True,
                    server_ip: Optional[str] = None) -> bool:
        """
        Đăng nhập user (wrapper cho save_credentials và create_session)
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
            remember: True = lưu credentials
            server_ip: Địa ch�?IP máy ch�?(optional)
            
        Returns:
            True nếu đăng nhập thành công
        """
        # Lưu credentials nếu cần
        self.save_credentials(username, password, remember)
        # Tạo session với server_ip
        return self.create_session(username, server_ip=server_ip)
    
    def refresh_session(self) -> bool:
        """
        Làm mới thời gian hết hạn của session
        
        Returns:
            True nếu làm mới thành công
        """
        if self.validate_session() and self._current_session:
            username = self._current_session.get("username")
            user_info = self._current_session.get("user_info")
            if username:
                return self.create_session(username, user_info)
        return False
    
    def extend_session(self, additional_seconds: int = DEFAULT_SESSION_TIMEOUT) -> bool:
        """
        Gia hạn thêm thời gian cho session
        
        Args:
            additional_seconds: S�?giây cần gia thêm
            
        Returns:
            True nếu gia hạn thành công
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
                print(f"[SessionManager] Lỗi khi gia hạn session: {e}")
                return False
        return False
    
    def save_server_ip(self, ip: str) -> bool:
        """
        Lưu server IP vào session data
        
        Args:
            ip: Địa ch�?IP máy ch�?
            
        Returns:
            True nếu lưu thành công
        """
        try:
            # Cập nhật session data với IP
            if self.validate_session() and self._current_session:
                self._current_session["server_ip"] = ip
                with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._current_session, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[SessionManager] Lỗi khi lưu server IP: {e}")
            return False
    
    def get_server_ip(self) -> Optional[str]:
        """
        Lấy server IP t�?session data
        
        Returns:
            IP máy ch�?hoặc None nếu chưa có
        """
        if self.validate_session() and self._current_session:
            return self._current_session.get("server_ip")
        return None
    
    def save_server_ip_to_file(self, ip: str) -> bool:
        """
        Lưu server IP vào file riêng biệt
        
        Args:
            ip: Địa ch�?IP máy ch�?
            
        Returns:
            True nếu lưu thành công
        """
        try:
            with open(LAST_IP_FILE, 'w', encoding='utf-8') as f:
                f.write(ip)
            return True
        except Exception as e:
            print(f"[SessionManager] Lỗi khi lưu IP: {e}")
            return False
    
    def load_server_ip_from_file(self) -> Optional[str]:
        """
        Đọc server IP t�?file riêng biệt
        
        Returns:
            IP máy ch�?hoặc None nếu chưa có
        """
        try:
            if not os.path.exists(LAST_IP_FILE):
                return None
            with open(LAST_IP_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"[SessionManager] Lỗi khi đọc IP: {e}")
            return None
    
    # ==================== Role-based Methods ====================
    
    def get_user_role(self) -> Optional[str]:
        """
        Lấy role của user hiện tại
        
        Returns:
            Role ('sales', 'engineer', 'admin', 'IT', 'Pur') hoặc None
        """
        # Cache role đ�?tránh gọi nhiều lần trong quá trình khởi tạo
        if hasattr(self, '_cached_role'):
            return self._cached_role
        
        user_info = self.get_user_info()
        if user_info:
            role = user_info.get('role')
            self._cached_role = role
            return role
        return None
    
    def is_sales(self) -> bool:
        """Kiểm tra có phải sales không"""
        return self.get_user_role() == 'sales'
    
    def is_engineer(self) -> bool:
        """Kiểm tra có phải engineer không"""
        return self.get_user_role() == 'engineer'
    
    def is_admin(self) -> bool:
        """Kiểm tra có phải admin không"""
        return self.get_user_role() == 'admin'
    
    def is_it(self) -> bool:
        """Kiểm tra có phải IT không"""
        return self.get_user_role() == 'IT'
    
    def is_pur(self) -> bool:
        """Kiểm tra có phải Pur không"""
        return self.get_user_role() == 'Pur'
    
    def get_user_id(self) -> Optional[int]:
        """
        Lấy user_id t�?session
        
        Returns:
            user_id hoặc None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('user_id')
        return None
    
    def get_full_name(self) -> Optional[str]:
        """
        Lấy full_name t�?session
        
        Returns:
            full_name hoặc None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('full_name')
        return None
    
    def get_employee_id(self) -> Optional[str]:
        """
        Lấy employee_id t�?session
        
        Returns:
            employee_id hoặc None
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('employee_id')
        return None
    
    def can_create_project(self) -> bool:
        """
        Kiểm tra user có th�?tạo project không
        Sales và Admin có th�?tạo
        """
        return self.is_sales() or self.is_admin()
    
    def can_accept_job(self) -> bool:
        """
        Kiểm tra user có th�?nhận job không
        Engineer và Admin có th�?nhận
        """
        return self.is_engineer() or self.is_admin()
    
    def can_accept_job_with_permission(self) -> bool:
        """
        Kiểm tra user có quyền job_accept không
        (Dựa trên permission, không phải role)
        """
        return self.has_permission('job_accept')
    
    def can_manage_users(self) -> bool:
        """
        Kiểm tra user có th�?quản lý users không
        Admin và IT có th�?quản lý
        """
        return self.is_admin() or self.is_it()
    
    def can_delete_project(self) -> bool:
        """
        Kiểm tra user có th�?xóa project không
        Ch�?Admin mới có th�?xóa
        """
        return self.is_admin()
    
    # ==================== Permission-based Methods ====================
    
    def get_user_permissions(self) -> List[str]:
        """
        Lấy danh sách permissions t�?session
        
        Returns:
            List of permissions hoặc empty list
        """
        user_info = self.get_user_info()
        if user_info:
            return user_info.get('permissions', [])
        return []
    
    def has_permission(self, permission: str) -> bool:
        """
        Kiểm tra user có một permission c�?th�?không
        
        Args:
            permission: Tên permission cần kiểm tra
        
        Returns:
            True nếu có permission
        """
        permissions = self.get_user_permissions()
        return permission in permissions
    
    def can_create_code(self) -> bool:
        """
        Kiểm tra user có quyền tạo code không
        """
        return self.has_permission('create_code')
    
    def can_view_history(self) -> bool:
        """
        Kiểm tra user có quyền xem history không
        """
        return self.has_permission('view_history')
    
    def can_delete_history(self) -> bool:
        """
        Kiểm tra user có quyền xóa history không
        """
        return self.has_permission('delete_history')
    
    def can_export(self) -> bool:
        """
        Kiểm tra user có quyền export không
        """
        return self.has_permission('export')
    
    def is_super_admin(self) -> bool:
        """
        Kiểm tra user có quyền admin không
        """
        return self.has_permission('admin')


# Global instance
session_manager = SessionManager()


# =============================================================================
# Hàm tiện ích (convenience functions)
# =============================================================================

def get_session_manager() -> SessionManager:
    """Lấy instance global của SessionManager"""
    return session_manager


def is_user_logged_in() -> bool:
    """Kiểm tra user đang đăng nhập"""
    return session_manager.is_logged_in()


def get_logged_in_username() -> Optional[str]:
    """Lấy username của user đang đăng nhập"""
    return session_manager.get_current_user()


def login_user(username: str, password: str, remember: bool = True,
               server_ip: Optional[str] = None) -> bool:
    """
    Đăng nhập user
    
    Args:
        username: Tên đăng nhập
        password: Mật khẩu
        remember: True = lưu credentials
        server_ip: Địa ch�?IP máy ch�?(optional)
        
    Returns:
        True nếu đăng nhập thành công
    """
    # Lưu credentials nếu cần
    session_manager.save_credentials(username, password, remember)
    # Tạo session với server_ip
    return session_manager.create_session(username, server_ip=server_ip)


def logout_user() -> bool:
    """Đăng xuất user"""
    return session_manager.end_session()


def get_server_ip() -> Optional[str]:
    """
    Lấy server IP t�?session
    
    Returns:
        IP máy ch�?hoặc None nếu chưa có
    """
    return session_manager.get_server_ip()


def save_server_ip_to_file(ip: str) -> bool:
    """
    Lưu server IP vào file riêng biệt
    
    Args:
        ip: Địa ch�?IP máy ch�?
        
    Returns:
        True nếu lưu thành công
    """
    return session_manager.save_server_ip_to_file(ip)


def load_server_ip_from_file() -> Optional[str]:
    """
    Đọc server IP t�?file riêng biệt
    
    Returns:
        IP máy ch�?hoặc None nếu chưa có
    """
    return session_manager.load_server_ip_from_file()


# ==================== Role-based Convenience Functions ====================

def get_user_role() -> Optional[str]:
    """Lấy role của user hiện tại"""
    return session_manager.get_user_role()


def is_sales() -> bool:
    """Kiểm tra có phải sales không"""
    return session_manager.is_sales()


def is_engineer() -> bool:
    """Kiểm tra có phải engineer không"""
    return session_manager.is_engineer()


def is_admin() -> bool:
    """Kiểm tra có phải admin không"""
    return session_manager.is_admin()


def is_it() -> bool:
    """Kiểm tra có phải IT không"""
    return session_manager.is_it()


def is_pur() -> bool:
    """Kiểm tra có phải Pur không"""
    return session_manager.is_pur()


def get_user_id() -> Optional[int]:
    """Lấy user_id t�?session"""
    return session_manager.get_user_id()


def get_full_name() -> Optional[str]:
    """Lấy full_name t�?session"""
    return session_manager.get_full_name()


def get_employee_id() -> Optional[str]:
    """Lấy employee_id t�?session"""
    return session_manager.get_employee_id()


def can_create_project() -> bool:
    """Kiểm tra user có th�?tạo project không"""
    return session_manager.can_create_project()


def can_accept_job() -> bool:
    """Kiểm tra user có th�?nhận job không"""
    return session_manager.can_accept_job()


def can_accept_job_with_permission() -> bool:
    """Kiểm tra user có quyền job_accept không"""
    return session_manager.can_accept_job_with_permission()


def can_manage_users() -> bool:
    """Kiểm tra user có th�?quản lý users không"""
    return session_manager.can_manage_users()


def can_delete_project() -> bool:
    """Kiểm tra user có th�?xóa project không"""
    return session_manager.can_delete_project()


# ==================== Permission-based Convenience Functions ====================

def get_user_permissions() -> List[str]:
    """Lấy danh sách permissions t�?session"""
    return session_manager.get_user_permissions()


def has_permission(permission: str) -> bool:
    """Kiểm tra user có một permission c�?th�?không"""
    return session_manager.has_permission(permission)


def can_create_code() -> bool:
    """Kiểm tra user có quyền tạo code không"""
    return session_manager.can_create_code()


def can_view_history() -> bool:
    """Kiểm tra user có quyền xem history không"""
    return session_manager.can_view_history()


def can_delete_history() -> bool:
    """Kiểm tra user có quyền xóa history không"""
    return session_manager.can_delete_history()


def can_export() -> bool:
    """Kiểm tra user có quyền export không"""
    return session_manager.can_export()


def is_super_admin() -> bool:
    """Kiểm tra user có quyền admin không"""
    return session_manager.is_super_admin()
