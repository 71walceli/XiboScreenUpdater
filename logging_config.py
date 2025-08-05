"""
Logging configuration and utilities for Xibo Screen Updater.

Provides structured logging with timestamps, levels, and component identification.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Create main logger
    logger = logging.getLogger('xibo_screen_updater')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_component_logger(component: str, parent_logger: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        component: Component name (e.g., 'nextcloud', 'xibo', 'processor')
        parent_logger: Parent logger instance
        
    Returns:
        Component-specific logger
    """
    if parent_logger:
        return parent_logger.getChild(component)
    else:
        return logging.getLogger(f'xibo_screen_updater.{component}')


class LogContext:
    """Context manager for structured logging with additional context."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        context_str = ', '.join(f"{k}={v}" for k, v in self.context.items())
        self.logger.info(f"Starting {self.operation}" + (f" ({context_str})" if context_str else ""))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.utcnow() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed {self.operation} in {duration.total_seconds():.2f}s")
        else:
            self.logger.error(f"Failed {self.operation} after {duration.total_seconds():.2f}s: {exc_val}")
    
    def update_context(self, **kwargs):
        """Update context information."""
        self.context.update(kwargs)
    
    def log_progress(self, message: str, level: str = "INFO"):
        """Log a progress message."""
        getattr(self.logger, level.lower())(f"{self.operation}: {message}")
