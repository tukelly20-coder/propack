# src/config.py
"""
Configuration Management Module
- Loads configuration from environment variables and .env file
- Provides type-safe configuration access
- Supports .env file parsing for local development
"""
import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    threaded: bool = True
    use_reloader: bool = False


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "DB.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: Optional[str] = None
    session_timeout: int = 86400  # 24 hours in seconds
    rate_limit_enabled: bool = True
    rate_limit_max_attempts: int = 5
    rate_limit_window_seconds: int = 300  # 5 minutes
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:12345",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:12345",
        "https://propackvp.duckdns.org",
        "https://vp.szsunqit.cn",
        "https://vp.sunqit.cn",
    ])


@dataclass
class OllamaConfig:
    """Ollama AI configuration"""
    host: str = "localhost:11434"
    enabled: bool = True
    default_model: str = "qwen3:8b"
    timeout: int = 120


@dataclass
class GeminiConfig:
    """Google Gemini AI configuration"""
    api_key: Optional[str] = None
    model: str = "gemini-3-flash-preview"
    timeout: int = 60


@dataclass
class OpenRouterConfig:
    """OpenRouter AI configuration"""
    api_key: Optional[str] = None
    default_model: str = "google/gemini-2.0-flash-exp:free"
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 10000
    fallback_models: List[str] = field(default_factory=lambda: [
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-1.5-flash-8b:free",
        "meta-llama/llama-3.1-8b-instruct"
    ])
    timeout: int = 60


@dataclass
class AIConfig:
    """AI configuration container"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    openrouter: OpenRouterConfig = field(default_factory=OpenRouterConfig)


class Config:
    """
    Central configuration management class.
    Loads settings from environment variables and credentials.json.
    """
    
    _instance: Optional['Config'] = None
    
    def __new__(cls) -> 'Config':
        """Singleton pattern for global config access"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._initialized = True
        self.server = ServerConfig()
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.ai = AIConfig()
        
        self._load_from_env()
        self._load_from_credentials()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        # Server settings
        self.server.host = os.environ.get('FLASK_HOST', self.server.host)
        self.server.port = int(os.environ.get('FLASK_PORT', self.server.port))
        self.server.debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        
        # Security settings
        self.security.secret_key = os.environ.get('FLASK_SECRET_KEY')
        session_timeout = os.environ.get('SESSION_TIMEOUT')
        if session_timeout:
            self.security.session_timeout = int(session_timeout)
        
        # Ollama settings
        self.ai.ollama.host = os.environ.get('OLLAMA_HOST', self.ai.ollama.host)
        self.ai.ollama.enabled = os.environ.get('OLLAMA_ENABLED', 'true').lower() == 'true'
        
        # Database settings
        self.database.path = os.environ.get('DB_PATH', self.database.path)
        
        # Load .env file if exists
        self._load_env_file()
    
    def _load_env_file(self) -> None:
        """Load .env file for local development"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if not os.path.exists(env_path):
            # Also check current directory
            env_path = '.env'
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
    
    def _load_from_credentials(self) -> None:
        """Load sensitive credentials from credentials.json"""
        cred_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if not os.path.exists(cred_path):
            return
        
        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
            
            # Load secret key
            if not self.security.secret_key:
                self.security.secret_key = creds.get('secret_key')
            
            # Load Gemini config
            if 'gemini_api_key' in creds:
                self.ai.gemini.api_key = creds['gemini_api_key']
            if 'gemini_model' in creds:
                self.ai.gemini.model = creds['gemini_model']
            
            # Load OpenRouter config
            if 'openrouter_api_key' in creds:
                self.ai.openrouter.api_key = creds['openrouter_api_key']
            if 'ai_retry' in creds:
                retry_config = creds['ai_retry']
                if 'max_retries' in retry_config:
                    self.ai.openrouter.max_retries = retry_config['max_retries']
                if 'initial_delay_ms' in retry_config:
                    self.ai.openrouter.initial_delay_ms = retry_config['initial_delay_ms']
                if 'max_delay_ms' in retry_config:
                    self.ai.openrouter.max_delay_ms = retry_config['max_delay_ms']
            if 'fallback_models' in creds:
                self.ai.openrouter.fallback_models = creds['fallback_models']
                
        except (json.JSONDecodeError, IOError) as e:
            import sys
            print(f"[Config] Warning: Could not load credentials.json: {e}", file=sys.stderr)
    
    def reload(self) -> None:
        """Reload configuration from sources"""
        self._initialized = False
        self.__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excludes secrets)"""
        return {
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'debug': self.server.debug,
            },
            'database': {
                'path': self.database.path,
            },
            'security': {
                'session_timeout': self.security.session_timeout,
                'rate_limit_enabled': self.security.rate_limit_enabled,
                'cors_origins_count': len(self.security.cors_origins),
            },
            'ai': {
                'ollama': {
                    'host': self.ai.ollama.host,
                    'enabled': self.ai.ollama.enabled,
                    'default_model': self.ai.ollama.default_model,
                },
                'gemini': {
                    'api_key_configured': bool(self.ai.gemini.api_key),
                    'model': self.ai.gemini.model,
                },
                'openrouter': {
                    'api_key_configured': bool(self.ai.openrouter.api_key),
                    'default_model': self.ai.openrouter.default_model,
                    'max_retries': self.ai.openrouter.max_retries,
                }
            }
        }


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload and return the global configuration"""
    global _config
    _config = Config()
    return _config