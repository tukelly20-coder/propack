# src/security.py
"""
Security Configuration and Utilities Module
- CORS configuration with restrictive origins
- Rate limiting helpers
- Authentication decorators
- Input sanitization
"""
from typing import Optional, List, Dict, Any, Callable, Tuple
from functools import wraps
import re
import secrets
import time

from flask import Flask, request, jsonify, Response
from flask_cors import CORS


class SecurityConfig:
    """Security configuration container"""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        session_timeout: int = 86400,
        rate_limit_enabled: bool = True,
        rate_limit_max_attempts: int = 5,
        rate_limit_window_seconds: int = 300,
        cors_origins: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        strict_cors: bool = True
    ):
        self.secret_key = secret_key
        self.session_timeout = session_timeout
        self.rate_limit_enabled = rate_limit_enabled
        self.rate_limit_max_attempts = rate_limit_max_attempts
        self.rate_limit_window_seconds = rate_limit_window_seconds
        
        # CORS configuration
        self.cors_origins = cors_origins or self._default_origins()
        self.allowed_origins = allowed_origins or self._default_allow_origins()
        self.strict_cors = strict_cors
    
    @staticmethod
    def _default_origins() -> List[str]:
        """Default CORS allowed origins"""
        return [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:12345",
            "http://127.0.0.1:8001",
            "http://127.0.0.1:8002",
            "http://127.0.0.1:12345",
            "https://propackvp.duckdns.org",
            "https://vp.szsunqit.cn",
            "https://vp.sunqit.cn",
        ]
    
    @staticmethod
    def _default_allow_origins() -> List[str]:
        """Default origins that always allow wildcard in development"""
        return [
            "http://localhost:*",
            "http://127.0.0.1:*",
        ]


class RateLimiter:
    """Rate limiting helper for authentication attempts"""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, List[Tuple[float, bool]]] = {}
        self._lock = __import__('threading').Lock()
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if the identifier is rate limited.
        
        Args:
            identifier: IP address or user identifier
        
        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        current_time = time.time()
        
        with self._lock:
            if identifier not in self._attempts:
                self._attempts[identifier] = []
            
            # Clean up old attempts
            self._attempts[identifier] = [
                (timestamp, success) 
                for timestamp, success in self._attempts[identifier]
                if current_time - timestamp < self.window_seconds
            ]
            
            # Check if rate limited
            failed_attempts = sum(
                1 for timestamp, success in self._attempts[identifier]
                if not success
            )
            
            if failed_attempts >= self.max_attempts:
                return False, 0
            
            remaining = self.max_attempts - failed_attempts
            return True, remaining
    
    def record_attempt(self, identifier: str, success: bool) -> None:
        """
        Record a login attempt.
        
        Args:
            identifier: IP address or user identifier
            success: Whether the attempt was successful
        """
        with self._lock:
            if identifier not in self._attempts:
                self._attempts[identifier] = []
            self._attempts[identifier].append((time.time(), success))
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for an identifier"""
        with self._lock:
            if identifier in self._attempts:
                del self._attempts[identifier]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_attempts: int = 5, window_seconds: int = 300) -> RateLimiter:
    """Get or create the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_attempts, window_seconds)
    return _rate_limiter


def configure_cors(
    app: Flask,
    config: Optional[SecurityConfig] = None,
    development_mode: bool = False
) -> None:
    """
    Configure CORS for the Flask application.
    
    Args:
        app: Flask application instance
        config: Security configuration
        development_mode: Enable less restrictive CORS for development
    """
    if config is None:
        config = SecurityConfig()
    
    if development_mode:
        # Less restrictive in development
        CORS(
            app,
            resources={
                r"/api/*": {
                    "origins": "*",
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"],
                }
            },
            supports_credentials=True
        )
        return
    
    # Production - restrictive CORS
    if config.strict_cors:
        CORS(
            app,
            resources={
                r"/api/*": {
                    "origins": config.cors_origins,
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"],
                    "supports_credentials": False,
                }
            }
        )
    else:
        # Semi-restrictive - allow local development
        combined_origins = list(config.cors_origins)
        for origin in config.allowed_origins:
            if origin not in combined_origins:
                combined_origins.append(origin)
        
        CORS(
            app,
            resources={
                r"/api/*": {
                    "origins": combined_origins,
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"],
                }
            },
            supports_credentials=False
        )


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            return jsonify({'message': 'Protected content'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        
        # Check Authorization header first (Bearer token)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Chưa đăng nhập',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        # Token validation would happen here
        # For now, just pass through
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*allowed_roles: str) -> Callable:
    """
    Decorator to require specific roles for an endpoint.
    
    Usage:
        @app.route('/api/admin-only')
        @require_auth
        @require_role('admin', 'IT')
        def admin_endpoint():
            return jsonify({'message': 'Admin content'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would check the user's role from the session/token
            # For now, just pass through
            return f(*args, **kwargs)
        
        decorated_function._allowed_roles = allowed_roles
        return decorated_function
    
    return decorator


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username không được để trống"
    
    if len(username) < 3:
        return False, "Username phải có ít nhất 3 ký tự"
    
    if len(username) > 50:
        return False, "Username không được quá 50 ký tự"
    
    # Only allow alphanumeric, underscore, hyphen, and some special chars
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
        return False, "Username chỉ được chứa chữ, số, _, -, và ."
    
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Mật khẩu không được để trống"
    
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    
    if len(password) > 100:
        return False, "Mật khẩu không được quá 100 ký tự"
    
    return True, None


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes (output will be hex, so 2x length)
    
    Returns:
        Secure random token as hex string
    """
    return secrets.token_hex(length)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2.
    
    Args:
        password: Password to hash
        salt: Optional salt (will be generated if not provided)
    
    Returns:
        Tuple of (hashed_password, salt)
    """
    import hashlib
    
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Simple hash for now (in production, use bcrypt or argon2)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    
    return key.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Password to verify
        hashed: Expected hash
        salt: Salt used in hashing
    
    Returns:
        True if password matches
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, hashed)


def get_client_ip() -> str:
    """Get the real client IP address, accounting for proxies"""
    # Check for X-Forwarded-For header (from proxy/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to remote_addr
    return request.remote_addr or 'unknown'


class SecurityHeaders:
    """Middleware to add security headers to responses"""
    
    @staticmethod
    def add_headers(response: Response) -> Response:
        """Add security headers to a response"""
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Strict transport security (force HTTPS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


def add_security_headers_to_app(app: Flask) -> None:
    """
    Add security headers middleware to Flask app.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def add_security_headers(response: Response) -> Response:
        return SecurityHeaders.add_headers(response)