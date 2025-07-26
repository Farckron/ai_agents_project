"""
Structured logging system for PR operations, audit logging, and performance monitoring
"""

import json
import logging
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
import uuid
import os


class LogLevel(Enum):
    """Log levels for structured logging"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Categories for different types of logs"""
    PR_OPERATION = "pr_operation"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    SECURITY = "security"
    API_CALL = "api_call"
    USER_ACTION = "user_action"
    SYSTEM = "system"


class StructuredLogger:
    """
    Enhanced structured logger for PR operations, audit logging, and performance monitoring
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Thread-local storage for context
        self._local = threading.local()
        
        # Initialize different log files
        self._setup_loggers()
        
        # Performance tracking
        self._performance_data = {}
        self._active_operations = {}
    
    def _setup_loggers(self):
        """Setup different loggers for different categories"""
        
        # PR Operations Logger
        self.pr_logger = self._create_logger(
            "pr_operations",
            self.log_dir / "pr_operations.log"
        )
        
        # Audit Logger
        self.audit_logger = self._create_logger(
            "audit",
            self.log_dir / "audit.log"
        )
        
        # Performance Logger
        self.performance_logger = self._create_logger(
            "performance",
            self.log_dir / "performance.log"
        )
        
        # Security Logger
        self.security_logger = self._create_logger(
            "security",
            self.log_dir / "security.log"
        )
        
        # General structured logger
        self.structured_logger = self._create_logger(
            "structured",
            self.log_dir / "structured.log"
        )
    
    def _create_logger(self, name: str, log_file: Path) -> logging.Logger:
        """Create a logger with JSON formatting"""
        logger = logging.getLogger(f"{self.name}.{name}")
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # File handler with JSON formatting
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # JSON formatter
        formatter = JsonFormatter()
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.propagate = False
        
        return logger
    
    def set_context(self, **context):
        """Set context for current thread"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(context)
    
    def clear_context(self):
        """Clear context for current thread"""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current thread context"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        return self._local.context.copy()
    
    @contextmanager
    def context(self, **context):
        """Context manager for temporary context"""
        old_context = self.get_context()
        try:
            self.set_context(**context)
            yield
        finally:
            self.clear_context()
            self.set_context(**old_context)
    
    def _create_log_entry(self, 
                         level: LogLevel,
                         category: LogCategory,
                         message: str,
                         **kwargs) -> Dict[str, Any]:
        """Create a structured log entry"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'logger': self.name,
            'message': message,
            'thread_id': threading.get_ident(),
            'context': self.get_context()
        }
        
        # Add any additional fields
        entry.update(kwargs)
        
        return entry
    
    def log_pr_operation(self, 
                        operation: str,
                        status: str,
                        level: LogLevel = LogLevel.INFO,
                        **details):
        """Log PR operation with structured data"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.PR_OPERATION,
            message=f"PR Operation: {operation}",
            operation=operation,
            status=status,
            details=details
        )
        
        self._log_to_logger(self.pr_logger, level, entry)
    
    def log_audit_event(self,
                       event_type: str,
                       user_id: Optional[str] = None,
                       resource: Optional[str] = None,
                       action: Optional[str] = None,
                       result: str = "success",
                       level: LogLevel = LogLevel.INFO,
                       **details):
        """Log audit event for security tracking"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.AUDIT,
            message=f"Audit Event: {event_type}",
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            details=details
        )
        
        self._log_to_logger(self.audit_logger, level, entry)
    
    def log_performance_metric(self,
                              metric_name: str,
                              value: Union[int, float],
                              unit: str = "ms",
                              operation: Optional[str] = None,
                              level: LogLevel = LogLevel.INFO,
                              **metadata):
        """Log performance metric"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.PERFORMANCE,
            message=f"Performance Metric: {metric_name}",
            metric_name=metric_name,
            value=value,
            unit=unit,
            operation=operation,
            metadata=metadata
        )
        
        self._log_to_logger(self.performance_logger, level, entry)
    
    def log_security_event(self,
                          event_type: str,
                          severity: str = "medium",
                          source_ip: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          level: LogLevel = LogLevel.WARNING,
                          **details):
        """Log security event"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.SECURITY,
            message=f"Security Event: {event_type}",
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details
        )
        
        self._log_to_logger(self.security_logger, level, entry)
    
    def log_api_call(self,
                    method: str,
                    url: str,
                    status_code: int,
                    duration_ms: float,
                    request_size: Optional[int] = None,
                    response_size: Optional[int] = None,
                    level: LogLevel = LogLevel.INFO,
                    **details):
        """Log API call with performance data"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.API_CALL,
            message=f"API Call: {method} {url}",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            request_size=request_size,
            response_size=response_size,
            details=details
        )
        
        self._log_to_logger(self.structured_logger, level, entry)
    
    def log_user_action(self,
                       action: str,
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       level: LogLevel = LogLevel.INFO,
                       **details):
        """Log user action"""
        
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.USER_ACTION,
            message=f"User Action: {action}",
            action=action,
            user_id=user_id,
            session_id=session_id,
            details=details
        )
        
        self._log_to_logger(self.structured_logger, level, entry)
    
    def _log_to_logger(self, logger: logging.Logger, level: LogLevel, entry: Dict[str, Any]):
        """Log entry to specific logger"""
        
        log_method = getattr(logger, level.value)
        log_method(json.dumps(entry, ensure_ascii=False, default=str))
    
    @contextmanager
    def performance_timer(self, operation_name: str, **metadata):
        """Context manager for timing operations"""
        
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Store operation start
        self._active_operations[operation_id] = {
            'name': operation_name,
            'start_time': start_time,
            'metadata': metadata
        }
        
        try:
            yield operation_id
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Log performance metric
            self.log_performance_metric(
                metric_name=f"{operation_name}_duration",
                value=duration_ms,
                unit="ms",
                operation=operation_name,
                operation_id=operation_id,
                **metadata
            )
            
            # Clean up
            if operation_id in self._active_operations:
                del self._active_operations[operation_id]
    
    def log_structured(self,
                      level: LogLevel,
                      category: LogCategory,
                      message: str,
                      **kwargs):
        """General structured logging method"""
        
        entry = self._create_log_entry(level, category, message, **kwargs)
        self._log_to_logger(self.structured_logger, level, entry)
    
    def get_performance_summary(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for operations"""
        
        # This would typically read from the performance log file
        # For now, return active operations
        summary = {
            'active_operations': len(self._active_operations),
            'operations': []
        }
        
        for op_id, op_data in self._active_operations.items():
            current_duration = (time.time() - op_data['start_time']) * 1000
            summary['operations'].append({
                'id': op_id,
                'name': op_data['name'],
                'duration_ms': current_duration,
                'metadata': op_data['metadata']
            })
        
        return summary


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        # If the message is already JSON, return it as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # If not JSON, create a structured entry
            entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname.lower(),
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            if record.exc_info:
                entry['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(entry, ensure_ascii=False, default=str)


# Global logger instances
_loggers = {}

def get_structured_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger instance"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


# Convenience functions for common logging patterns
def log_pr_start(workflow_id: str, repo_url: str, user_request: str, **details):
    """Log PR workflow start"""
    logger = get_structured_logger("pr_manager")
    logger.set_context(workflow_id=workflow_id, repo_url=repo_url)
    logger.log_pr_operation(
        operation="workflow_start",
        status="started",
        level=LogLevel.INFO,
        user_request=user_request,
        **details
    )

def log_pr_step(workflow_id: str, step_name: str, status: str, **details):
    """Log PR workflow step"""
    logger = get_structured_logger("pr_manager")
    logger.set_context(workflow_id=workflow_id)
    logger.log_pr_operation(
        operation=f"step_{step_name}",
        status=status,
        level=LogLevel.INFO if status == "success" else LogLevel.ERROR,
        step_name=step_name,
        **details
    )

def log_pr_complete(workflow_id: str, status: str, pr_url: Optional[str] = None, **details):
    """Log PR workflow completion"""
    logger = get_structured_logger("pr_manager")
    logger.set_context(workflow_id=workflow_id)
    logger.log_pr_operation(
        operation="workflow_complete",
        status=status,
        level=LogLevel.INFO if status == "success" else LogLevel.ERROR,
        pr_url=pr_url,
        **details
    )

def log_github_api_call(method: str, url: str, status_code: int, duration_ms: float, **details):
    """Log GitHub API call"""
    logger = get_structured_logger("github_manager")
    logger.log_api_call(
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
        **details
    )

def log_security_violation(event_type: str, severity: str = "high", **details):
    """Log security violation"""
    logger = get_structured_logger("security")
    logger.log_security_event(
        event_type=event_type,
        severity=severity,
        level=LogLevel.WARNING if severity == "medium" else LogLevel.ERROR,
        **details
    )

def log_user_request(user_id: str, action: str, **details):
    """Log user request"""
    logger = get_structured_logger("api")
    logger.log_user_action(
        action=action,
        user_id=user_id,
        **details
    )