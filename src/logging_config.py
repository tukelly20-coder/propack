# src/logging_config.py
"""
Centralized Logging Configuration Module
- Replaces print() statements with structured logging
- Supports multiple log levels and output formats
- Thread-safe logging with rotation
"""
import logging
import os
import sys
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


# Log levels configuration
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log file settings
LOG_DIR = 'logs'
LOG_FILE = 'app.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Loggers registry for clean management
_loggers: Dict[str, logging.Logger] = {}
_loggers_lock = threading.Lock()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',
    }
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color for console handler
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class SafePrintWrapper:
    """
    Thread-safe print wrapper that can replace print() statements.
    Outputs to the 'general' logger instead.
    """
    _lock = threading.Lock()
    
    def __call__(self, *args, **kwargs):
        with self._lock:
            logger = get_logger('general')
            msg = ' '.join(str(arg) for arg in args)
            logger.info(msg)


# Global safe_print replacement
safe_print = SafePrintWrapper()


def setup_logging(
    log_level: int = LOG_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = LOG_DIR,
    log_file: str = LOG_FILE
) -> None:
    """
    Set up the root logger with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
        log_to_console: Whether to output to console
        log_dir: Directory for log files
        log_file: Base name for log file
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        LOG_DATE_FORMAT
    )
    
    # Console handler with colors
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_path = os.path.join(log_dir, log_file)
        
        # Use RotatingFileHandler for size-based rotation
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Also create a daily rotating log for easy archival
        daily_log_path = os.path.join(log_dir, f'server_{datetime.now().strftime("%Y%m%d")}.log')
        daily_handler = RotatingFileHandler(
            daily_log_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=3,
            encoding='utf-8'
        )
        daily_handler.setLevel(log_level)
        daily_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(daily_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a named logger.
    
    Args:
        name: Logger name (typically module name)
    
    Returns:
        Configured logger instance
    """
    global _loggers
    
    with _loggers_lock:
        if name in _loggers:
            return _loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(LOG_LEVEL)
        
        _loggers[name] = logger
        return logger


def get_logger_context(name: str) -> Dict[str, Any]:
    """
    Get context dictionary for structured logging.
    
    Args:
        name: Logger name
    
    Returns:
        Dictionary with logger context info
    """
    return {
        'logger': name,
        'timestamp': datetime.now().isoformat(),
        'level': 'DEBUG'
    }


class LogContext:
    """
    Context manager for structured logging with extra context.
    
    Usage:
        with LogContext('database', operation='query', table='users'):
            logger.info('Executing query')
    """
    
    _context_locals = threading.local()
    
    def __init__(self, logger_name: str, **context):
        self.logger_name = logger_name
        self.context = context
        self._previous_context = None
    
    def __enter__(self):
        # Store previous context
        self._previous_context = getattr(self._context_locals, 'current', {})
        # Set new context
        self._context_locals.current = {
            **self._previous_context,
            **self.context
        }
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        self._context_locals.current = self._previous_context
        return False
    
    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get current log context"""
        return getattr(cls._context_locals, 'current', {})


class StructuredLogger:
    """
    Logger wrapper that adds structured logging capabilities.
    """
    
    def __init__(self, name: str):
        self._logger = get_logger(name)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context"""
        if kwargs:
            context_str = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} [{context_str}]"
        return message
    
    def debug(self, message: str, **kwargs) -> None:
        self._logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs) -> None:
        self._logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        self._logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs) -> None:
        self._logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs) -> None:
        self._logger.critical(self._format_message(message, **kwargs))
    
    def exception(self, message: str, **kwargs) -> None:
        self._logger.exception(self._format_message(message, **kwargs))


def create_logger(name: str) -> StructuredLogger:
    """Create a structured logger"""
    return StructuredLogger(name)


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with arguments and return values.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    logger = get_logger(func.__module__)
    
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func_name} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


def log_api_request(logger_name: str = 'api') -> Callable:
    """
    Decorator to log API requests and responses.
    
    Usage:
        @log_api_request('projects')
        def api_projects():
            return jsonify(...)
    """
    logger = get_logger(logger_name)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            from flask import request
            
            request_id = id(request)
            method = getattr(request, 'method', 'UNKNOWN')
            path = getattr(request, 'path', 'UNKNOWN')
            
            logger.info(f"Request started: {method} {path} [ID: {request_id}]")
            
            try:
                response = func(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                logger.info(f"Request completed: {method} {path} [ID: {request_id}] -> {status_code}")
                return response
            except Exception as e:
                logger.error(f"Request failed: {method} {path} [ID: {request_id}] - {e}")
                raise
        
        return wrapper
    
    return decorator


# Initialize default logging on module import
def _init_logging():
    """Initialize logging with default settings"""
    # Check if logging is already configured
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    
    setup_logging()


_init_logging()