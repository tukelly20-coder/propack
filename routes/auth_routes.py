# auth_routes.py - Authentication and Session Management
# Extracted from server.py for better modularity
"""
Authentication routes:
- POST /api/login    - User login with rate limiting
- POST /api/logout   - User logout
- GET /api/me      - Get current user info
- PUT /api/profile - Update profile
- PUT /api/profile/password - Change password
"""
from flask import Blueprint, request, jsonify, session
from src.db_helper import get_user_with_permissions, get_user_by_username, update_user
import time
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# Session storage (will be passed from main app)
_sessions = None
_sessions_lock = None
_schedule_save_sessions = None
_check_rate_limit = None
_record_login_attempt = None

def register_auth_routes(app, sessions_ref, sessions_lock_ref, schedule_save_ref, check_rate_limit_ref, record_login_attempt_ref):
    """Register auth routes blueprint with Flask app and session manager references"""
    # Initialize with session manager references
    init_auth_routes(sessions_ref, sessions_lock_ref, schedule_save_ref, check_rate_limit_ref, record_login_attempt_ref)
    
    # Register blueprint with app
    app.register_blueprint(auth_bp)


def init_auth_routes(sessions_ref, sessions_lock_ref, schedule_save_ref, check_rate_limit_ref, record_login_attempt_ref):
    """Initialize module-level session manager references"""
    global _sessions, _sessions_lock, _schedule_save_sessions, _check_rate_limit, _record_login_attempt
    _sessions = sessions_ref
    _sessions_lock = sessions_lock_ref
    _schedule_save_sessions = schedule_save_ref
    _check_rate_limit = check_rate_limit_ref
    _record_login_attempt = record_login_attempt_ref


def generate_token():
    """Generate random token"""
    return secrets.token_hex(32)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with session management"""
    from flask import current_app
    
    client_ip = request.remote_addr
    
    # Check rate limit
    allowed, remaining = _check_rate_limit(client_ip) if _check_rate_limit else (True, 5)
    if not allowed:
        return jsonify({
            "success": False, 
            "error": "Quá nhiều lần thử đăng nhập. Vui lòng thử lại sau 5 phút.",
            "code": "RATE_LIMITED"
        }), 429
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        if _record_login_attempt:
            _record_login_attempt(client_ip, False)
        return jsonify({"success": False, "error": "Vui lòng nhập tên đăng nhập và mật khẩu"}), 400
    
    # Authenticate with database
    user_info = get_user_with_permissions(username)
    
    if user_info:
        if user_info.get('status') == 'locked':
            if _record_login_attempt:
                _record_login_attempt(client_ip, False)
            return jsonify({"success": False, "error": "Tài khoản đã bị khóa. Vui lòng liên hệ Admin."}), 401
        elif user_info.get('passwords') != password:
            if _record_login_attempt:
                _record_login_attempt(client_ip, False)
            return jsonify({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401
        else:
            # Record successful login
            if _record_login_attempt:
                _record_login_attempt(client_ip, True)
            
            # Create session token
            token = generate_token()
            with _sessions_lock:
                _sessions[token] = {
                    'user': user_info,
                    'created_at': time.time(),
                    'ip': client_ip
                }
            
            # Schedule save sessions (debounced, non-blocking)
            if _schedule_save_sessions:
                _schedule_save_sessions()
            
            # Remove password from response
            user_info_copy = user_info.copy()
            if 'passwords' in user_info_copy:
                del user_info_copy['passwords']
            
            return jsonify({
                "success": True,
                "token": token,
                "user": user_info_copy,
                "expires_in": 86400  # 24 hours
            })
    else:
        if _record_login_attempt:
            _record_login_attempt(client_ip, False)
        return jsonify({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with _sessions_lock:
            if token in _sessions:
                del _sessions[token]
    
    if _schedule_save_sessions:
        _schedule_save_sessions()
    
    return jsonify({"success": True, "message": "Đăng xuất thành công"})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    SESSION_TIMEOUT = 86400
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"authenticated": False, "user": None, "reason": "no_token"})
    
    token = auth_header[7:]
    with _sessions_lock:
        session_data = _sessions.get(token)
        if not session_data:
            return jsonify({"authenticated": False, "user": None, "reason": "invalid_token"})
        
        # Check expiration
        created_at = session_data.get('created_at', 0)
        elapsed = time.time() - created_at
        remaining = SESSION_TIMEOUT - elapsed
        
        if remaining <= 0:
            del _sessions[token]
            if _schedule_save_sessions:
                _schedule_save_sessions()
            return jsonify({"authenticated": False, "user": None, "reason": "expired"})
        
        # Check if close to expiration (< 5 minutes)
        is_expiring_soon = remaining < 300
        
        return jsonify({
            "authenticated": True,
            "user": session_data.get('user'),
            "expires_in": int(remaining),
            "expiring_soon": is_expiring_soon
        })


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update current user profile"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
    token = auth_header[7:]
    with _sessions_lock:
        session_data = _sessions.get(token)
        if not session_data:
            return jsonify({"success": False, "error": "Token không hợp lệ"}), 401
    
    current_user = session_data.get('user', {})
    user_id = current_user.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "Không tìm thấy user"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    # Map allowed fields
    profile_data = {}
    allowed_fields = ['full_name', 'employee_id', 'department', 'email', 'phone']
    for field in allowed_fields:
        if field in data:
            profile_data[field] = data[field]
    
    if not profile_data:
        return jsonify({"success": False, "error": "Không có thông tin để cập nhật"}), 400
    
    success = update_user(user_id, profile_data)
    
    if success:
        if 'full_name' in profile_data:
            current_user['full_name'] = profile_data['full_name']
        if 'employee_id' in profile_data:
            current_user['employee_id'] = profile_data['employee_id']
        if 'department' in profile_data:
            current_user['department'] = profile_data['department']
        if 'email' in profile_data:
            current_user['email'] = profile_data['email']
        if 'phone' in profile_data:
            current_user['phone'] = profile_data['phone']
        with _sessions_lock:
            _sessions[token]['user'] = current_user
        
        if _schedule_save_sessions:
            _schedule_save_sessions()
        
        return jsonify({
            "success": True,
            "message": "Cập nhật hồ sơ thành công",
            "user": current_user
        })
    else:
        return jsonify({"success": False, "error": "Lỗi khi cập nhật hồ sơ"}), 500


@auth_bp.route('/profile/password', methods=['PUT'])
def change_password():
    """Change current user password"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
    token = auth_header[7:]
    with _sessions_lock:
        session_data = _sessions.get(token)
        if not session_data:
            return jsonify({"success": False, "error": "Token không hợp lệ"}), 401
    
    current_user = session_data.get('user', {})
    user_id = current_user.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "Không tìm thấy user"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "error": "Vui lòng nhập đầy đủ thông tin"}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Mật khẩu mới không khớp"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Mật khẩu mới phải có ít nhất 6 ký tự"}), 400
    
    # Get current user data to verify password
    user_info = get_user_by_username(current_user.get('username'))
    if not user_info:
        return jsonify({"success": False, "error": "Không tìm thấy thông tin user"}), 400
    
    if user_info.get('passwords') != current_password:
        return jsonify({"success": False, "error": "Mật khẩu hiện tại không đúng"}), 400
    
    success = update_user(user_id, {'passwords': new_password})
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đổi mật khẩu thành công"
        })
    else:
        return jsonify({"success": False, "error": "Lỗi khi đổi mật khẩu"}), 500