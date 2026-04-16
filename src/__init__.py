# src/__init__.py
"""
Propack VP Server - Core Package

Main modules:
- config: Configuration management with environment variables
- logging_config: Centralized logging setup
- security: Security utilities (CORS, authentication helpers)
- db_helper: Database operations (existing)
- chat_service: AI chat service (existing)
- ai_memory: AI long-term memory system (existing)
"""

__version__ = "8.0.0"
__author__ = "Propack VP Team"

# Import core modules
from . import config
from . import logging_config
from . import security

# Export commonly used utilities
from .config import Config, get_config
from .logging_config import setup_logging, get_logger
from .security import (
    SecurityConfig,
    RateLimiter,
    get_rate_limiter,
    sanitize_input,
    generate_secure_token,
)

__all__ = [
    # Version info
    '__version__',
    # Core modules
    'config',
    'logging_config',
    'security',
    # Config exports
    'Config',
    'get_config',
    # Logging exports
    'setup_logging',
    'get_logger',
    # Security exports
    'SecurityConfig',
    'RateLimiter',
    'get_rate_limiter',
    'sanitize_input',
    'generate_secure_token',
]