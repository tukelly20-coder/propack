# tests/conftest.py
"""
Pytest configuration and fixtures for Propack VP Server tests
"""
import os
import sys
import pytest
import tempfile
import shutil
from typing import Generator, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration fixture"""
    return {
        'test_mode': True,
        'database_path': ':memory:',
        'secret_key': 'test-secret-key-for-testing-only',
        'ollama_url': 'http://localhost:11434',
        'gemini_api_key': 'test-key',
    }


@pytest.fixture(scope="function")
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_env_file(temp_dir: str) -> str:
    """Create a temporary .env file for testing"""
    env_path = os.path.join(temp_dir, '.env')
    with open(env_path, 'w') as f:
        f.write('FLASK_SECRET_KEY=test-secret-key\n')
        f.write('FLASK_PORT=9999\n')
        f.write('OLLAMA_HOST=localhost:11434\n')
    return env_path


@pytest.fixture(scope="function")
def mock_credentials_file(temp_dir: str) -> str:
    """Create a mock credentials.json file for testing"""
    import json
    cred_path = os.path.join(temp_dir, 'credentials.json')
    creds = {
        'secret_key': 'test-secret-key',
        'gemini_api_key': 'test-gemini-key',
        'openrouter_api_key': 'test-openrouter-key',
    }
    with open(cred_path, 'w') as f:
        json.dump(creds, f)
    return cred_path


@pytest.fixture
def app():
    """Create a test Flask application"""
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Register a simple test route
    @app.route('/test')
    def test_route():
        return {'status': 'ok', 'message': 'test'}
    
    @app.route('/api/test')
    def api_test():
        return {'status': 'ok', 'endpoint': '/api/test'}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create an authenticated test client"""
    # In a real test, you would log in and get a token
    # For now, just return the client
    return client


@pytest.fixture
def sample_project_data() -> Dict[str, Any]:
    """Sample project data for testing"""
    return {
        'khach_hang': 'Test Customer',
        'nhan_vien_kinh_doanh': 'Test Sales',
        'ten_san_pham': 'Test Product',
        'quy_cach': '100x50x30',
        'nguoi_lien_he_kh': 'Contact Person',
        'so_luong': 10,
        'ma_po': 'PO-001',
        'loai_san_pham': 'SJT',
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'passwords': 'testpassword',
        'full_name': 'Test User',
        'role': 'sales',
        'employee_id': '001',
    }


@pytest.fixture
def sample_code_data() -> Dict[str, Any]:
    """Sample code generation data for testing"""
    return {
        'name': 'Test Drawing',
        'category': 'SJT',
        'employee': '001',
    }


@pytest.fixture
def rate_limiter():
    """Create a rate limiter instance for testing"""
    from src.security import RateLimiter
    return RateLimiter(max_attempts=5, window_seconds=60)


@pytest.fixture
def security_config():
    """Create a security config for testing"""
    from src.security import SecurityConfig
    return SecurityConfig(
        secret_key='test-secret-key',
        session_timeout=3600,
        rate_limit_enabled=True,
        cors_origins=['http://localhost:8001'],
    )


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    for item in items:
        # Add markers based on test path
        if 'test_config' in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif 'test_api' in item.nodeid:
            item.add_marker(pytest.mark.api)
            item.add_marker(pytest.mark.integration)
        elif 'test_security' in item.nodeid:
            item.add_marker(pytest.mark.unit)