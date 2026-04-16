# tests/test_security.py
"""
Unit tests for src/security.py
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Import the security module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.security import (
    SecurityConfig,
    RateLimiter,
    get_rate_limiter,
    sanitize_input,
    validate_username,
    validate_password,
    generate_secure_token,
    hash_password,
    verify_password,
)


class TestSecurityConfig:
    """Tests for SecurityConfig class"""
    
    def test_default_origins(self):
        """Test default CORS origins are set correctly"""
        config = SecurityConfig()
        assert len(config.cors_origins) > 0
        assert "http://localhost:8001" in config.cors_origins
    
    def test_custom_origins(self):
        """Test custom CORS origins"""
        custom_origins = ["http://example.com", "https://example.org"]
        config = SecurityConfig(cors_origins=custom_origins)
        assert config.cors_origins == custom_origins
    
    def test_rate_limit_defaults(self):
        """Test default rate limit settings"""
        config = SecurityConfig()
        assert config.rate_limit_max_attempts == 5
        assert config.rate_limit_window_seconds == 300
    
    def test_session_timeout_default(self):
        """Test default session timeout"""
        config = SecurityConfig()
        assert config.session_timeout == 86400  # 24 hours


class TestRateLimiter:
    """Tests for RateLimiter class"""
    
    def test_initial_check_allows(self, rate_limiter):
        """Test that initial check allows requests"""
        is_allowed, remaining = rate_limiter.check_rate_limit("test-ip")
        assert is_allowed is True
        assert remaining == 5
    
    def test_multiple_failed_attempts(self, rate_limiter):
        """Test that multiple failed attempts eventually block"""
        ip = "test-ip-block"
        
        # Use up all attempts
        for i in range(5):
            rate_limiter.record_attempt(ip, success=False)
        
        is_allowed, remaining = rate_limiter.check_rate_limit(ip)
        assert is_allowed is False
        assert remaining == 0
    
    def test_successful_attempt_resets_failure_count(self, rate_limiter):
        """Test that successful attempt doesn't affect failure count"""
        ip = "test-ip-success"
        
        # Record some failures
        rate_limiter.record_attempt(ip, success=False)
        rate_limiter.record_attempt(ip, success=False)
        
        # Record a success
        rate_limiter.record_attempt(ip, success=True)
        
        # Should still have some attempts remaining
        is_allowed, remaining = rate_limiter.check_rate_limit(ip)
        assert is_allowed is True
        assert remaining > 0
    
    def test_reset(self, rate_limiter):
        """Test reset functionality"""
        ip = "test-ip-reset"
        
        # Use up attempts
        for i in range(5):
            rate_limiter.record_attempt(ip, success=False)
        
        # Reset
        rate_limiter.reset(ip)
        
        # Should be allowed again
        is_allowed, remaining = rate_limiter.check_rate_limit(ip)
        assert is_allowed is True
        assert remaining == 5


class TestSanitizeInput:
    """Tests for input sanitization"""
    
    def test_normal_text_unchanged(self):
        """Test that normal text remains unchanged"""
        text = "Hello World"
        result = sanitize_input(text)
        assert result == text
    
    def test_control_characters_removed(self):
        """Test that control characters are removed"""
        text = "Hello\x00World\x07"
        result = sanitize_input(text)
        assert "\x00" not in result
        assert "\x07" not in result
        assert "HelloWorld" in result
    
    def test_max_length_truncation(self):
        """Test that text is truncated to max length"""
        text = "A" * 2000
        result = sanitize_input(text, max_length=100)
        assert len(result) == 100
    
    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed"""
        text = "  Hello World  "
        result = sanitize_input(text)
        assert result == "Hello World"
    
    def test_empty_string(self):
        """Test that empty string returns empty"""
        result = sanitize_input("")
        assert result == ""
    
    def test_none_returns_empty(self):
        """Test that None returns empty string"""
        result = sanitize_input(None)
        assert result == ""


class TestValidateUsername:
    """Tests for username validation"""
    
    def test_valid_username(self):
        """Test valid usernames"""
        valid_usernames = ["user123", "test_user", "admin", "john.doe"]
        for username in valid_usernames:
            is_valid, error = validate_username(username)
            assert is_valid is True
            assert error is None
    
    def test_empty_username(self):
        """Test empty username is rejected"""
        is_valid, error = validate_username("")
        assert is_valid is False
        assert error is not None
    
    def test_short_username(self):
        """Test username too short is rejected"""
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "ít nhất 3 ký tự" in error
    
    def test_username_with_invalid_chars(self):
        """Test username with invalid characters is rejected"""
        invalid_usernames = ["user@name", "test name", "user\nname", "user<>name"]
        for username in invalid_usernames:
            is_valid, error = validate_username(username)
            assert is_valid is False


class TestValidatePassword:
    """Tests for password validation"""
    
    def test_valid_password(self):
        """Test valid passwords"""
        valid_passwords = ["password123", "Abc123!@#", "test"]
        for password in valid_passwords:
            is_valid, error = validate_password(password)
            assert is_valid is True
            assert error is None
    
    def test_empty_password(self):
        """Test empty password is rejected"""
        is_valid, error = validate_password("")
        assert is_valid is False
        assert error is not None
    
    def test_short_password(self):
        """Test password too short is rejected"""
        is_valid, error = validate_password("abc")
        assert is_valid is False
        assert "ít nhất 6 ký tự" in error


class TestSecureToken:
    """Tests for secure token generation"""
    
    def test_token_length(self):
        """Test token has expected length"""
        token = generate_secure_token(32)
        assert len(token) == 64  # hex string is 2x bytes
    
    def test_tokens_are_unique(self):
        """Test that generated tokens are unique"""
        tokens = [generate_secure_token() for _ in range(100)]
        assert len(set(tokens)) == 100
    
    def test_custom_length(self):
        """Test custom token length"""
        token = generate_secure_token(16)
        assert len(token) == 32


class TestPasswordHashing:
    """Tests for password hashing functions"""
    
    def test_hash_password(self):
        """Test password hashing produces a hash"""
        password = "test_password"
        hashed, salt = hash_password(password)
        assert hashed is not None
        assert len(hashed) > 0
        assert salt is not None
    
    def test_same_password_different_hash(self):
        """Test same password produces different hashes with different salts"""
        password = "test_password"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)
        assert hash1 != hash2  # Different salts should produce different hashes
        assert salt1 != salt2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password"
        hashed, salt = hash_password(password)
        assert verify_password(password, hashed, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password"
        hashed, salt = hash_password(password)
        assert verify_password("wrong_password", hashed, salt) is False


# Run tests with: pytest tests/test_security.py -v