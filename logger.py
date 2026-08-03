"""
Logging module for File Integrity Checker.
Provides structured logging with file rotation and multiple output handlers.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LoggerSetup:
    """Class for setting up and managing application logging."""
    
    # Log format with timestamp, level, and message
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    SIMPLE_FORMAT = '%(levelname)s: %(message)s'
    
    # Default log rotation settings
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5
    
    def __init__(self, 
                 log_dir: str = 'logs',
                 log_level: str = 'INFO',
                 console_output: bool = True,
                 file_output: bool = True):
        """
        Initialize logging setup.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console output
            file_output: Enable file output
        """
        self.log_dir = Path(log_dir)
        self.log_level = self._parse_log_level(log_level)
        self.console_output = console_output
        self.file_output = file_output
        
        # Create log directory if it doesn't exist
        if self.file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Store created loggers
        self.loggers = {}
    
    def _parse_log_level(self, level: str) -> int:
        """
        Parse log level string to logging constant.
        
        Args:
            level: Log level as string
            
        Returns:
            Logging level constant
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        return level_map.get(level.upper(), logging.INFO)
    
    def get_logger(self, 
                   name: str,
                   log_file: Optional[str] = None,
                   detailed_format: bool = False) -> logging.Logger:
        """
        Get or create a logger with specified configuration.
        
        Args:
            name: Logger name (typically __name__)
            log_file: Optional specific log file name
            detailed_format: Use detailed format with filename and line number
            
        Returns:
            Configured logger instance
        """
        # Return existing logger if already created
        if name in self.loggers:
            return self.loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            logger.handlers.clear()
        
        # Choose format
        log_format = self.DETAILED_FORMAT if detailed_format else self.DEFAULT_FORMAT
        formatter = logging.Formatter(log_format)
        
        # Add console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Add file handler with rotation
        if self.file_output:
            if log_file is None:
                log_file = f"{name.replace('.', '_')}.log"
            
            file_path = self.log_dir / log_file
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=file_path,
                maxBytes=self.DEFAULT_MAX_BYTES,
                backupCount=self.DEFAULT_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        # Store logger
        self.loggers[name] = logger
        
        return logger
    
    def create_rotating_logger(self,
                              name: str,
                              log_file: str,
                              max_bytes: int = DEFAULT_MAX_BYTES,
                              backup_count: int = DEFAULT_BACKUP_COUNT,
                              when: Optional[str] = None) -> logging.Logger:
        """
        Create a logger with rotating file handler.
        
        Args:
            name: Logger name
            log_file: Log file name
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
            when: Time-based rotation ('midnight', 'H', 'D', etc.)
            
        Returns:
            Configured logger with rotation
        """
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        if logger.handlers:
            logger.handlers.clear()
        
        formatter = logging.Formatter(self.DEFAULT_FORMAT)
        file_path = self.log_dir / log_file
        
        # Use time-based or size-based rotation
        if when:
            handler = logging.handlers.TimedRotatingFileHandler(
                filename=file_path,
                when=when,
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            handler = logging.handlers.RotatingFileHandler(
                filename=file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        
        handler.setLevel(self.log_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(self.SIMPLE_FORMAT))
            logger.addHandler(console_handler)
        
        logger.propagate = False
        self.loggers[name] = logger
        
        return logger


# Global logger setup instance
_logger_setup: Optional[LoggerSetup] = None


def setup_logger(log_dir: str = 'logs',
                 log_level: str = 'INFO',
                 console_output: bool = True,
                 file_output: bool = True) -> logging.Logger:
    """
    Setup and return the main application logger.
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_output: Enable console output
        file_output: Enable file output
        
    Returns:
        Main application logger
    """
    global _logger_setup
    
    if _logger_setup is None:
        _logger_setup = LoggerSetup(
            log_dir=log_dir,
            log_level=log_level,
            console_output=console_output,
            file_output=file_output
        )
    
    return _logger_setup.get_logger('file_integrity_checker', 'main.log')


def get_module_logger(module_name: str, 
                     log_file: Optional[str] = None,
                     detailed: bool = False) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Module name (use __name__)
        log_file: Optional custom log file
        detailed: Use detailed format
        
    Returns:
        Module-specific logger
    """
    global _logger_setup
    
    if _logger_setup is None:
        _logger_setup = LoggerSetup()
    
    return _logger_setup.get_logger(module_name, log_file, detailed)


def log_event(logger: logging.Logger,
              level: str,
              message: str,
              **kwargs) -> None:
    """
    Log an event with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context to include in log
    """
    log_method = getattr(logger, level.lower(), logger.info)
    
    if kwargs:
        context = ' | '.join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}"
    else:
        full_message = message
    
    log_method(full_message)


def log_exception(logger: logging.Logger,
                 message: str = "An exception occurred",
                 exc_info: bool = True) -> None:
    """
    Log an exception with traceback.
    
    Args:
        logger: Logger instance
        message: Error message
        exc_info: Include exception info and traceback
    """
    logger.error(message, exc_info=exc_info)


class AuditLogger:
    """Specialized logger for audit trail and integrity events."""
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Audit logs should have detailed format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Daily rotating file handler for audit logs
        audit_file = self.log_dir / 'audit.log'
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=audit_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of audit logs
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def log_baseline_created(self, path: str, file_count: int) -> None:
        """Log baseline creation event."""
        self.logger.info(f"BASELINE_CREATED | path={path} | files={file_count}")
    
    def log_baseline_updated(self, path: str, file_count: int) -> None:
        """Log baseline update event."""
        self.logger.info(f"BASELINE_UPDATED | path={path} | files={file_count}")
    
    def log_verification_started(self, path: str) -> None:
        """Log verification start event."""
        self.logger.info(f"VERIFICATION_STARTED | path={path}")
    
    def log_verification_completed(self, path: str, 
                                   modified: int, 
                                   added: int, 
                                   deleted: int) -> None:
        """Log verification completion event."""
        self.logger.info(
            f"VERIFICATION_COMPLETED | path={path} | "
            f"modified={modified} | added={added} | deleted={deleted}"
        )
    
    def log_file_modified(self, file_path: str, 
                         old_hash: str, 
                         new_hash: str) -> None:
        """Log file modification event."""
        self.logger.warning(
            f"FILE_MODIFIED | file={file_path} | "
            f"old_hash={old_hash[:16]}... | new_hash={new_hash[:16]}..."
        )
    
    def log_file_added(self, file_path: str, file_hash: str) -> None:
        """Log file addition event."""
        self.logger.info(f"FILE_ADDED | file={file_path} | hash={file_hash[:16]}...")
    
    def log_file_deleted(self, file_path: str) -> None:
        """Log file deletion event."""
        self.logger.warning(f"FILE_DELETED | file={file_path}")
    
    def log_error(self, operation: str, error: str) -> None:
        """Log error event."""
        self.logger.error(f"ERROR | operation={operation} | error={error}")


# Convenience function to get audit logger
def get_audit_logger(log_dir: str = 'logs') -> AuditLogger:
    """
    Get or create audit logger instance.
    
    Args:
        log_dir: Directory for audit logs
        
    Returns:
        AuditLogger instance
    """
    return AuditLogger(log_dir)
