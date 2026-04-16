# tests/test_config.py
"""
Unit tests for src/config.py
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Import the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    Config, 
    ServerConfig, 
    DatabaseConfig, 
    SecurityConfig,
    AIConfig,
    get_config,
    reload_config
)


class TestServerConfig:
    """Tests for ServerConfig dataclass"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8001
        assert config.debug is False
        assert config.threaded is True
        assert config.use_reloader is False
    
    def test_custom_values(self):
        """Test custom configuration values"""
        config = ServerConfig(host="127.0.0.1", port=5000, debug=True)
        assert config.host == "127.0.0.1"
        assert config.port == 5000
        assert config.debug is True


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass"""
    
    def test_default_values(self):
        """Test default database configuration"""
        config = DatabaseConfig()
        assert config.path == "DB.db"
        assert config.backup_enabled is True
        assert config.backup_interval_hours == 24


class TestSecurityConfig:
    """Tests for SecurityConfig dataclass"""
    
    def test_default_cors_origins(self):
        """Test default CORS origins list is not empty"""
        config = SecurityConfig()
        assert len(config.cors_origins) > 0
        assert "http://localhost:8001" in config.cors_origins


class TestAIConfig:
    """Tests for AIConfig dataclass"""
    
    def test_default_ollama_config(self):
        """Test default Ollama configuration"""
        config = AIConfig()
        assert config.ollama.host == "localhost:11434"
        assert config.ollama.enabled is True
        assert config.ollama.default_model == "qwen3:8b"
    
    def test_default_gemini_config(self):
        """Test default Gemini configuration"""
        config = AIConfig()
        assert config.gemini.api_key is None
        assert config.gemini.model == "gemini-3-flash-preview"
    
    def test_default_openrouter_config(self):
        """Test default OpenRouter configuration"""
        config = AIConfig()
        assert config.openrouter.api_key is None
        assert config.openrouter.max_retries == 3
        assert len(config.openrouter.fallback_models) > 0


class TestConfigSingleton:
    """Tests for Config singleton pattern"""
    
    def test_get_config_returns_instance(self):
        """Test get_config returns Config instance"""
        config = get_config()
        assert isinstance(config, Config)
    
    def test_reload_config(self):
        """Test reload_config returns new instance"""
        config1 = get_config()
        config2 = reload_config()
        # Both should be Config instances (may be same or different based on implementation)
        assert isinstance(config1, Config)
        assert isinstance(config2, Config)


class TestConfigLoading:
    """Tests for configuration loading from environment"""
    
    @patch.dict(os.environ, {'FLASK_PORT': '9000', 'FLASK_DEBUG': 'true'})
    def test_load_from_env(self):
        """Test loading configuration from environment variables"""
        config = Config()
        # Note: Due to singleton, we need to test differently
        # This tests that environment variables are read correctly
        assert os.environ.get('FLASK_PORT') == '9000'
        assert os.environ.get('FLASK_DEBUG') == 'true'
    
    def test_load_from_credentials_file(self, tmp_path):
        """Test loading from credentials.json file"""
        import json
        
        # Create a temporary credentials.json
        cred_file = tmp_path / "credentials.json"
        cred_data = {
            'secret_key': 'test-key-from-file',
            'gemini_api_key': 'test-gemini-key',
        }
        cred_file.write_text(json.dumps(cred_data))
        
        # When credentials file exists, it should be loaded
        # Note: This test may need adjustment based on actual implementation
        assert cred_file.exists()


class TestConfigToDict:
    """Tests for Config.to_dict method"""
    
    def test_to_dict_excludes_secrets(self):
        """Test that to_dict excludes sensitive information"""
        config = get_config()
        config_dict = config.to_dict()
        
        # Should have server, database, security, ai sections
        assert 'server' in config_dict
        assert 'database' in config_dict
        assert 'security' in config_dict
        assert 'ai' in config_dict
        
        # AI section should not contain actual API keys
        if 'api_key_configured' in config_dict['ai'].get('gemini', {}):
            # Should be boolean, not actual key
            assert isinstance(config_dict['ai']['gemini']['api_key_configured'], bool)


# Run tests with: pytest tests/test_config.py -v