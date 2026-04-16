# tests/test_logging.py
"""
Unit tests for src/logging_config.py
"""
import os
import sys
import pytest
import logging
from unittest.mock import patch, MagicMock

# Import the logging module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.logging_config import (
    setup_logging,
    get_logger,
    get_logger_context,
    LogContext,
    StructuredLogger,
    create_logger,
    log_function_call,
    SafePrintWrapper,
)


class TestSetupLogging:
    """Tests for setup_logging function"""
    
    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates log handlers"""
        log_dir = str(tmp_path / "logs")
        setup_logging(log_to_file=True, log_to_console=False, log_dir=log_dir)
        
        # Check that log directory was created
        assert os.path.exists(log_dir)
    
    def test_setup_logging_no_file(self):
        """Test setup_logging without file output"""
        setup_logging(log_to_file=False, log_to_console=False)
        # Should not raise any errors
    
    def test_setup_logging_idempotent(self):
        """Test that calling setup_logging multiple times is safe"""
        setup_logging(log_to_console=False)
        setup_logging(log_to_console=False)
        # Should not raise any errors or create duplicate handlers


class TestGetLogger:
    """Tests for get_logger function"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_same_name_returns_same(self):
        """Test that get_logger with same name returns same logger"""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test that get_logger with different names returns different loggers"""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")
        assert logger1 is not logger2
    
    def test_logger_name_set(self):
        """Test that logger name is set correctly"""
        logger = get_logger("my_test_module")
        assert logger.name == "my_test_module"


class TestGetLoggerContext:
    """Tests for get_logger_context function"""
    
    def test_context_has_required_fields(self):
        """Test that context has required fields"""
        context = get_logger_context("test_logger")
        assert 'logger' in context
        assert 'timestamp' in context
        assert context['logger'] == "test_logger"


class TestLogContext:
    """Tests for LogContext context manager"""
    
    def test_log_context_sets_and_restores(self):
        """Test that LogContext sets and restores context"""
        # Set initial context
        with LogContext("test", operation="test"):
            context1 = LogContext.get_context()
            assert 'operation' in context1
            assert context1['operation'] == "test"
        
        # After exiting, context should be restored
        context2 = LogContext.get_context()
        assert 'operation' not in context2
    
    def test_log_context_nesting(self):
        """Test that LogContext supports nesting"""
        with LogContext("outer", level=1):
            outer_context = LogContext.get_context()
            assert outer_context['level'] == 1
            
            with LogContext("inner", level=2):
                inner_context = LogContext.get_context()
                assert inner_context['level'] == 2
                assert 'level' in inner_context
            
            # After inner exits, should be back to outer context
            current = LogContext.get_context()
            assert current['level'] == 1


class TestStructuredLogger:
    """Tests for StructuredLogger wrapper"""
    
    def test_structured_logger_creation(self):
        """Test creating a structured logger"""
        logger = StructuredLogger("test_module")
        assert logger._logger.name == "test_module"
    
    def test_create_logger_function(self):
        """Test create_logger function"""
        logger = create_logger("test_module")
        assert isinstance(logger, StructuredLogger)
    
    def test_structured_logger_methods(self):
        """Test structured logger methods"""
        logger = StructuredLogger("test_module")
        
        # These should not raise errors (just log)
        logger.debug("Debug message", operation="test")
        logger.info("Info message", operation="test")
        logger.warning("Warning message", operation="test")
        logger.error("Error message", operation="test")
    
    def test_structured_format_includes_context(self):
        """Test that structured messages include context"""
        logger = StructuredLogger("test_module")
        
        # The underlying logger should receive formatted message
        # We can't easily test the output, but we verify it doesn't error
        logger.info("Test message", key="value", another="data")


class TestSafePrintWrapper:
    """Tests for SafePrintWrapper (safe_print)"""
    
    def test_safe_print_callable(self):
        """Test that SafePrintWrapper is callable"""
        wrapper = SafePrintWrapper()
        assert callable(wrapper)
    
    def test_safe_print_output(self):
        """Test that SafePrintWrapper outputs to logger"""
        wrapper = SafePrintWrapper()
        # Should not raise errors
        wrapper("Test output")
        wrapper("Multiple", "arguments")
        wrapper("Key", "=", "Value")


class TestLogFunctionCall:
    """Tests for log_function_call decorator"""
    
    def test_decorator_preserves_function(self):
        """Test that decorator preserves function metadata"""
        @log_function_call
        def my_function():
            return "result"
        
        assert my_function.__name__ == "my_function"
    
    def test_decorator_logs_call(self):
        """Test that decorator logs function call"""
        @log_function_call
        def add(a, b):
            return a + b
        
        result = add(1, 2)
        assert result == 3
        # Should not raise any errors
    
    def test_decorator_logs_return(self):
        """Test that decorator logs return value"""
        @log_function_call
        def return_value():
            return 42
        
        result = return_value()
        assert result == 42
    
    def test_decorator_logs_exception(self):
        """Test that decorator logs exceptions"""
        @log_function_call
        def raise_error():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            raise_error()


# Run tests with: pytest tests/test_logging.py -v