# tests/test_routes.py
"""
Unit tests for routes modules
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuthRoutes:
    """Tests for authentication routes"""
    
    @pytest.fixture
    def auth_bp(self):
        """Get auth blueprint"""
        from routes.auth_routes import auth_bp
        return auth_bp
    
    def test_auth_bp_exists(self, auth_bp):
        """Test that auth blueprint exists"""
        assert auth_bp is not None
        assert auth_bp.name == 'auth'
    
    def test_auth_bp_url_prefix(self, auth_bp):
        """Test auth blueprint has correct URL prefix"""
        assert auth_bp.url_prefix == '/api'


class TestApiRoutes:
    """Tests for API routes"""
    
    @pytest.fixture
    def api_bp(self):
        """Get API blueprint"""
        from routes.api_routes import api_bp
        return api_bp
    
    def test_api_bp_exists(self, api_bp):
        """Test that API blueprint exists"""
        assert api_bp is not None
        assert api_bp.name == 'api'
    
    def test_api_bp_url_prefix(self, api_bp):
        """Test API blueprint has correct URL prefix"""
        assert api_bp.url_prefix == '/api'


class TestAiRoutes:
    """Tests for AI routes"""
    
    @pytest.fixture
    def ai_bp(self):
        """Get AI blueprint"""
        from routes.ai_routes import ai_bp
        return ai_bp
    
    def test_ai_bp_exists(self, ai_bp):
        """Test that AI blueprint exists"""
        assert ai_bp is not None
        assert ai_bp.name == 'ai'
    
    def test_ai_bp_url_prefix(self, ai_bp):
        """Test AI blueprint has correct URL prefix"""
        assert ai_bp.url_prefix == '/api'


class TestSocketRoutes:
    """Tests for Socket routes"""
    
    @pytest.fixture
    def socket_bp(self):
        """Get socket blueprint"""
        from routes.socket_routes import socket_bp
        return socket_bp
    
    def test_socket_bp_exists(self, socket_bp):
        """Test that socket blueprint exists"""
        assert socket_bp is not None
        assert socket_bp.name == 'socket'
    
    def test_socket_bp_url_prefix(self, socket_bp):
        """Test socket blueprint has correct URL prefix"""
        assert socket_bp.url_prefix == '/api'


class TestToolRoutes:
    """Tests for Tool routes"""
    
    @pytest.fixture
    def tool_bp(self):
        """Get tool blueprint"""
        from routes.tool_routes import tool_bp
        return tool_bp
    
    def test_tool_bp_exists(self, tool_bp):
        """Test that tool blueprint exists"""
        assert tool_bp is not None
        assert tool_bp.name == 'tool'
    
    def test_tool_bp_url_prefix(self, tool_bp):
        """Test tool blueprint has correct URL prefix"""
        assert tool_bp.url_prefix == '/api'


class TestRoutesRegistration:
    """Tests for blueprint registration"""
    
    def test_register_all_blueprints(self, app):
        """Test registering all blueprints"""
        from routes import register_all_blueprints
        
        registered = register_all_blueprints(app)
        
        assert 'auth' in registered
        assert 'api' in registered
        assert 'ai' in registered
        assert 'socket' in registered
        assert 'tool' in registered


# Run tests with: pytest tests/test_routes.py -v