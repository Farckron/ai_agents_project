import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime
from enum import Enum
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


class ErrorType(Enum):
    """Enumeration of error types for categorization"""
    GITHUB_API = "github_api"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    VALIDATION = "validation"
    OPENAI_API = "openai_api"
    FILE_OPERATION = "file_operation"
    GENERAL = "general"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """Centralized error handling system with retry mechanisms and detailed logging"""
    
    def __init__(self, logger_name: str = "ErrorHandler"):
        self.logger = logging.getLogger(logger_name)
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Default retry configuration
        self.default_retry_config = {
            'max_attempts': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'exponential_base': 2.0,
            'jitter': True
        }
        
        # Error type specific configurations
        self.error_configs = {
            ErrorType.GITHUB_API: {
                'max_attempts': 5,
                'base_delay': 2.0,
                'max_delay': 120.0,
                'retryable_status_codes': [429, 500, 502, 503, 504]
            },
            ErrorType.RATE_LIMIT: {
                'max_attempts': 3,
                'base_delay': 60.0,
                'max_delay': 300.0,
                'exponential_base': 1.5
            },
            ErrorType.NETWORK: {
                'max_attempts': 4,
                'base_delay': 1.0,
                'max_delay': 30.0
            },
            ErrorType.OPENAI_API: {
                'max_attempts': 3,
                'base_delay': 1.0,
                'max_delay': 60.0
            }
        }
    
    def log_error(self, 
                  error: Exception, 
                  error_type: ErrorType = ErrorType.GENERAL,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  context: Optional[Dict[str, Any]] = None,
                  user_message: Optional[str] = None) -> str:
        """
        Log error with detailed information and context
        
        Args:
            error: The exception that occurred
            error_type: Type of error for categorization
            severity: Severity level of the error
            context: Additional context information
            user_message: User-friendly error message
        
        Returns:
            Error ID for tracking
        """
        error_id = f"ERR_{int(time.time())}_{id(error)}"
        timestamp = datetime.now().isoformat()
        
        error_details = {
            'error_id': error_id,
            'timestamp': timestamp,
            'error_type': error_type.value,
            'severity': severity.value,
            'exception_type': type(error).__name__,
            'exception_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'user_message': user_message
        }
        
        # Add to error history
        self._add_to_history(error_details)
        
        # Log based on severity
        log_message = self._format_log_message(error_details)
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return error_id
    
    def _add_to_history(self, error_details: Dict[str, Any]):
        """Add error to history with size management"""
        self.error_history.append(error_details)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def _format_log_message(self, error_details: Dict[str, Any]) -> str:
        """Format error details into a readable log message"""
        context_str = ""
        if error_details['context']:
            context_items = [f"{k}={v}" for k, v in error_details['context'].items()]
            context_str = f" | Context: {', '.join(context_items)}"
        
        return (f"[{error_details['error_id']}] "
                f"{error_details['error_type'].upper()} ERROR "
                f"({error_details['severity'].upper()}): "
                f"{error_details['exception_type']}: {error_details['exception_message']}"
                f"{context_str}")
    
    def retry_with_backoff(self, 
                          func: Callable,
                          error_type: ErrorType = ErrorType.GENERAL,
                          custom_config: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute function with exponential backoff retry mechanism
        
        Args:
            func: Function to execute
            error_type: Type of error for retry configuration
            custom_config: Custom retry configuration
            context: Additional context for error logging
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        config = self._get_retry_config(error_type, custom_config)
        last_exception = None
        
        for attempt in range(config['max_attempts']):
            try:
                return func()
            
            except Exception as e:
                last_exception = e
                
                # Check if error is retryable
                if not self._is_retryable_error(e, error_type):
                    self.log_error(
                        e, 
                        error_type, 
                        ErrorSeverity.HIGH,
                        {**(context or {}), 'attempt': attempt + 1, 'retryable': False}
                    )
                    raise e
                
                # Log retry attempt
                self.log_error(
                    e, 
                    error_type, 
                    ErrorSeverity.LOW,
                    {**(context or {}), 'attempt': attempt + 1, 'max_attempts': config['max_attempts']}
                )
                
                # Don't sleep on last attempt
                if attempt < config['max_attempts'] - 1:
                    delay = self._calculate_delay(attempt, config)
                    self.logger.info(f"Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{config['max_attempts']})")
                    time.sleep(delay)
        
        # All retries failed
        self.log_error(
            last_exception, 
            error_type, 
            ErrorSeverity.HIGH,
            {**(context or {}), 'all_retries_failed': True}
        )
        raise last_exception
    
    def _get_retry_config(self, error_type: ErrorType, custom_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get retry configuration for error type"""
        config = self.default_retry_config.copy()
        
        # Apply error type specific config
        if error_type in self.error_configs:
            config.update(self.error_configs[error_type])
        
        # Apply custom config
        if custom_config:
            config.update(custom_config)
        
        return config
    
    def _calculate_delay(self, attempt: int, config: Dict[str, Any]) -> float:
        """Calculate delay for exponential backoff with jitter"""
        base_delay = config['base_delay']
        exponential_base = config.get('exponential_base', 2.0)
        max_delay = config['max_delay']
        jitter = config.get('jitter', True)
        
        # Calculate exponential delay
        delay = base_delay * (exponential_base ** attempt)
        delay = min(delay, max_delay)
        
        # Add jitter to prevent thundering herd
        if jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def _is_retryable_error(self, error: Exception, error_type: ErrorType) -> bool:
        """Determine if an error is retryable based on type and content"""
        
        # Network related errors are generally retryable
        if isinstance(error, (ConnectionError, Timeout, RequestException)):
            return True
        
        # HTTP errors with specific status codes
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
            
            if error_type == ErrorType.GITHUB_API:
                retryable_codes = self.error_configs[ErrorType.GITHUB_API].get('retryable_status_codes', [])
                return status_code in retryable_codes
            
            # General retryable HTTP status codes
            return status_code in [429, 500, 502, 503, 504]
        
        # Rate limit errors are retryable
        if error_type == ErrorType.RATE_LIMIT:
            return True
        
        # OpenAI API specific errors
        if error_type == ErrorType.OPENAI_API:
            error_message = str(error).lower()
            retryable_messages = ['rate limit', 'timeout', 'server error', 'service unavailable']
            return any(msg in error_message for msg in retryable_messages)
        
        # Authentication errors are generally not retryable
        if error_type == ErrorType.AUTHENTICATION:
            return False
        
        # Validation errors are not retryable
        if error_type == ErrorType.VALIDATION:
            return False
        
        # Default: retry for unknown errors
        return True
    
    def handle_github_api_errors(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle GitHub API specific errors
        
        Args:
            error: GitHub API exception
            context: Additional context
        
        Returns:
            Error response dictionary
        """
        error_response = {
            'error': {
                'code': 'github_api_error',
                'message': 'GitHub API error occurred',
                'details': {},
                'suggestions': [],
                'retry_possible': True
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
            error_response['error']['details']['status_code'] = status_code
            
            if status_code == 401:
                error_response['error']['code'] = 'authentication_error'
                error_response['error']['message'] = 'GitHub authentication failed'
                error_response['error']['suggestions'] = [
                    'Check if GitHub token is valid',
                    'Verify token has required permissions',
                    'Ensure token is not expired'
                ]
                error_response['error']['retry_possible'] = False
                
            elif status_code == 403:
                error_response['error']['code'] = 'permission_denied'
                error_response['error']['message'] = 'Permission denied or rate limit exceeded'
                error_response['error']['suggestions'] = [
                    'Check repository access permissions',
                    'Wait for rate limit reset if applicable',
                    'Verify token scope includes required permissions'
                ]
                
            elif status_code == 404:
                error_response['error']['code'] = 'resource_not_found'
                error_response['error']['message'] = 'Repository or resource not found'
                error_response['error']['suggestions'] = [
                    'Verify repository URL is correct',
                    'Check if repository is public or token has access',
                    'Ensure branch or file path exists'
                ]
                error_response['error']['retry_possible'] = False
                
            elif status_code == 422:
                error_response['error']['code'] = 'validation_error'
                error_response['error']['message'] = 'GitHub API validation error'
                error_response['error']['suggestions'] = [
                    'Check request parameters are valid',
                    'Verify required fields are provided',
                    'Review GitHub API documentation'
                ]
                error_response['error']['retry_possible'] = False
                
            elif status_code == 429:
                error_response['error']['code'] = 'rate_limit_exceeded'
                error_response['error']['message'] = 'GitHub API rate limit exceeded'
                error_response['error']['suggestions'] = [
                    'Wait for rate limit reset',
                    'Use authenticated requests for higher limits',
                    'Implement request throttling'
                ]
        
        # Log the error
        error_id = self.log_error(
            error, 
            ErrorType.GITHUB_API, 
            ErrorSeverity.HIGH,
            context,
            error_response['error']['message']
        )
        error_response['error']['error_id'] = error_id
        
        return error_response
    
    def handle_authentication_errors(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle authentication specific errors
        
        Args:
            error: Authentication exception
            context: Additional context
        
        Returns:
            Error response dictionary
        """
        error_response = {
            'error': {
                'code': 'authentication_error',
                'message': 'Authentication failed',
                'details': {'error_type': type(error).__name__},
                'suggestions': [
                    'Verify API token is correct and not expired',
                    'Check token permissions and scopes',
                    'Ensure token is properly configured in environment'
                ],
                'retry_possible': False
            },
            'timestamp': datetime.now().isoformat()
        }
        
        error_message = str(error).lower()
        
        if 'token' in error_message:
            error_response['error']['suggestions'].extend([
                'Generate a new personal access token',
                'Ensure token is stored securely in environment variables'
            ])
        
        if 'permission' in error_message or 'scope' in error_message:
            error_response['error']['suggestions'].extend([
                'Check token has required scopes (repo, user, etc.)',
                'Verify organization permissions if applicable'
            ])
        
        # Log the error
        error_id = self.log_error(
            error, 
            ErrorType.AUTHENTICATION, 
            ErrorSeverity.HIGH,
            context,
            error_response['error']['message']
        )
        error_response['error']['error_id'] = error_id
        
        return error_response
    
    def handle_rate_limit_errors(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle rate limit specific errors
        
        Args:
            error: Rate limit exception
            context: Additional context
        
        Returns:
            Error response dictionary
        """
        error_response = {
            'error': {
                'code': 'rate_limit_exceeded',
                'message': 'API rate limit exceeded',
                'details': {},
                'suggestions': [
                    'Wait for rate limit reset',
                    'Use authenticated requests for higher limits',
                    'Implement exponential backoff retry strategy'
                ],
                'retry_possible': True
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to extract rate limit information
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            headers = error.response.headers
            
            if 'X-RateLimit-Reset' in headers:
                reset_time = int(headers['X-RateLimit-Reset'])
                current_time = int(time.time())
                wait_time = max(0, reset_time - current_time)
                
                error_response['error']['details']['reset_time'] = reset_time
                error_response['error']['details']['wait_time_seconds'] = wait_time
                error_response['error']['suggestions'].insert(0, f'Wait {wait_time} seconds for rate limit reset')
            
            if 'X-RateLimit-Remaining' in headers:
                error_response['error']['details']['remaining_requests'] = int(headers['X-RateLimit-Remaining'])
        
        # Log the error
        error_id = self.log_error(
            error, 
            ErrorType.RATE_LIMIT, 
            ErrorSeverity.MEDIUM,
            context,
            error_response['error']['message']
        )
        error_response['error']['error_id'] = error_id
        
        return error_response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics from history"""
        if not self.error_history:
            return {'total_errors': 0}
        
        stats = {
            'total_errors': len(self.error_history),
            'by_type': {},
            'by_severity': {},
            'recent_errors': len([e for e in self.error_history 
                                if (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 3600])
        }
        
        for error in self.error_history:
            error_type = error['error_type']
            severity = error['severity']
            
            stats['by_type'][error_type] = stats['by_type'].get(error_type, 0) + 1
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        return stats
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.logger.info("Error history cleared")
    
    @staticmethod
    def handle_api_error(error: Exception, user_message: str = "An error occurred") -> tuple:
        """
        Handle API errors and return Flask-compatible response
        
        Args:
            error: The exception that occurred
            user_message: User-friendly error message
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        error_handler = ErrorHandler("api_error_handler")
        
        # Determine error type and appropriate response
        if isinstance(error, (ConnectionError, Timeout, requests.exceptions.ConnectionError)):
            error_type = ErrorType.NETWORK
            status_code = 503
            message = "Service temporarily unavailable"
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            if error.response.status_code == 401:
                error_type = ErrorType.AUTHENTICATION
                status_code = 401
                message = "Authentication failed"
            elif error.response.status_code == 403:
                error_type = ErrorType.GITHUB_API
                status_code = 403
                message = "Access forbidden"
            elif error.response.status_code == 404:
                error_type = ErrorType.GITHUB_API
                status_code = 404
                message = "Resource not found"
            elif error.response.status_code == 429:
                error_type = ErrorType.RATE_LIMIT
                status_code = 429
                message = "Rate limit exceeded"
            else:
                error_type = ErrorType.GITHUB_API
                status_code = 500
                message = "External service error"
        else:
            error_type = ErrorType.GENERAL
            status_code = 500
            message = user_message
        
        # Log the error
        error_id = error_handler.log_error(
            error, 
            error_type, 
            ErrorSeverity.HIGH,
            {'api_endpoint': True, 'user_message': user_message}
        )
        
        # Create response
        response = {
            'error': {
                'message': message,
                'details': str(error),
                'error_id': error_id,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return response, status_code


def with_error_handling(error_type: ErrorType = ErrorType.GENERAL, 
                       retry: bool = False,
                       custom_config: Optional[Dict[str, Any]] = None):
    """
    Decorator for automatic error handling and optional retry
    
    Args:
        error_type: Type of error for proper handling
        retry: Whether to enable retry mechanism
        custom_config: Custom retry configuration
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(f"{func.__module__}.{func.__name__}")
            
            if retry:
                return error_handler.retry_with_backoff(
                    lambda: func(*args, **kwargs),
                    error_type,
                    custom_config,
                    {'function': func.__name__, 'module': func.__module__}
                )
            else:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_handler.log_error(
                        e, 
                        error_type, 
                        ErrorSeverity.HIGH,
                        {'function': func.__name__, 'module': func.__module__}
                    )
                    raise
        
        return wrapper
    return decorator