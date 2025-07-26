import os
import requests
import logging
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # GitHub Configuration
    GITHUB_REPO_URL = os.getenv('GITHUB_REPO_URL')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_OWNER = os.getenv('GITHUB_OWNER')
    GITHUB_REPO = os.getenv('GITHUB_REPO')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Agent Configuration
    MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 5))
    DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/agent_logs.txt')

# PR Default Settings
PR_DEFAULT_SETTINGS = {
    'branch_prefix': os.getenv('PR_BRANCH_PREFIX', 'ai-agent'),
    'base_branch': os.getenv('PR_BASE_BRANCH', 'main'),
    'auto_merge': os.getenv('PR_AUTO_MERGE', 'False').lower() == 'true',
    'delete_branch_after_merge': os.getenv('PR_DELETE_BRANCH_AFTER_MERGE', 'True').lower() == 'true',
    'pr_template': {
        'title_prefix': os.getenv('PR_TITLE_PREFIX', '[AI Agent]'),
        'description_template': """
## Зміни
{changes_summary}

## Файли змінено
{files_changed}

## Тип змін
{change_type}

## Тестування
{testing_notes}

---
*Цей PR був створений автоматично AI агентом*
        """.strip(),
        'labels': os.getenv('PR_DEFAULT_LABELS', 'ai-generated,automated').split(',')
    },
    'commit_message_template': os.getenv('PR_COMMIT_MESSAGE_TEMPLATE', '{change_type}: {summary}'),
    'max_files_per_pr': int(os.getenv('PR_MAX_FILES_PER_PR', 20)),
    'max_file_size_kb': int(os.getenv('PR_MAX_FILE_SIZE_KB', 1024))
}

# GitHub API Settings
GITHUB_API_SETTINGS = {
    'base_url': os.getenv('GITHUB_API_BASE_URL', 'https://api.github.com'),
    'timeout': int(os.getenv('GITHUB_API_TIMEOUT', 30)),
    'max_retries': int(os.getenv('GITHUB_API_MAX_RETRIES', 3)),
    'retry_delay': float(os.getenv('GITHUB_API_RETRY_DELAY', 1.0)),
    'rate_limit': {
        'requests_per_hour': int(os.getenv('GITHUB_API_RATE_LIMIT', 5000)),
        'check_interval': int(os.getenv('GITHUB_API_RATE_CHECK_INTERVAL', 60))
    },
    'required_scopes': [
        'repo',
        'read:user',
        'user:email'
    ],
    'optional_scopes': [
        'write:repo_hook',
        'read:org'
    ],
    'user_agent': os.getenv('GITHUB_API_USER_AGENT', 'AI-Agent-PR-System/1.0'),
    'accept_header': 'application/vnd.github.v3+json'
}

# Security Settings
SECURITY_SETTINGS = {
    'allowed_file_extensions': [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
        '.json', '.yaml', '.yml', '.xml', '.md', '.txt', '.sql', '.sh', '.bat',
        '.dockerfile', '.gitignore', '.env.example', '.toml', '.ini', '.cfg'
    ],
    'blocked_file_patterns': [
        '*.key', '*.pem', '*.p12', '*.pfx', '*.jks',
        '.env', '.env.local', '.env.production',
        'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
        '*.log', '*.tmp', '*.cache'
    ],
    'max_repository_size_mb': int(os.getenv('SECURITY_MAX_REPO_SIZE_MB', 500)),
    'max_file_size_mb': int(os.getenv('SECURITY_MAX_FILE_SIZE_MB', 10)),
    'allowed_domains': os.getenv('SECURITY_ALLOWED_DOMAINS', 'github.com,api.github.com').split(','),
    'require_https': os.getenv('SECURITY_REQUIRE_HTTPS', 'True').lower() == 'true',
    'token_validation': {
        'check_on_startup': os.getenv('SECURITY_CHECK_TOKEN_ON_STARTUP', 'True').lower() == 'true',
        'cache_validation_minutes': int(os.getenv('SECURITY_TOKEN_CACHE_MINUTES', 60))
    },
    'input_sanitization': {
        'max_request_length': int(os.getenv('SECURITY_MAX_REQUEST_LENGTH', 10000)),
        'allowed_html_tags': [],
        'strip_dangerous_chars': True
    },
    'audit_logging': {
        'enabled': os.getenv('SECURITY_AUDIT_LOGGING', 'True').lower() == 'true',
        'log_file': os.getenv('SECURITY_AUDIT_LOG_FILE', 'logs/security_audit.log'),
        'log_sensitive_operations': True
    }
}

# Agent-specific configurations
AGENT_CONFIGS = {
    'project_manager': {
        'temperature': 0.3,
        'system_prompt': "You are a Project Manager AI agent responsible for coordinating tasks between different specialized agents.",
        'max_tokens': 1000,
        'model': 'gpt-4'
    },
    'prompt_ask_engineer': {
        'temperature': 0.5,
        'system_prompt': "You are a Prompt Ask Engineer AI agent that analyzes repository state and provides recommendations.",
        'max_tokens': 800,
        'model': 'gpt-4'
    },
    'prompt_code_engineer': {
        'temperature': 0.4,
        'system_prompt': "You are a Prompt Code Engineer AI agent that creates precise code tasks and prompts for the Code Agent.",
        'max_tokens': 1200,
        'model': 'gpt-4'
    },
    'code_agent': {
        'temperature': 0.2,
        'system_prompt': "You are a Code Agent AI responsible for writing, fixing, and editing code based on specific instructions.",
        'max_tokens': 2000,
        'model': 'gpt-4'
    },
    'github_manager': {
        'temperature': 0.1,
        'system_prompt': "You are a GitHub Manager AI agent responsible for repository operations and version control.",
        'max_tokens': 600,
        'model': 'gpt-3.5-turbo'
    },
    'pr_manager': {
        'temperature': 0.3,
        'system_prompt': "You are a PR Manager AI agent responsible for creating and managing GitHub Pull Requests with automated code changes.",
        'max_tokens': 1000,
        'model': 'gpt-4'
    }
}

# Configuration Validation Functions
def validate_github_config() -> Tuple[bool, List[str]]:
    """
    Validate GitHub configuration on startup.
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required environment variables
    required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate GitHub token format
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        if not github_token.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_')):
            errors.append("GitHub token format appears invalid (should start with ghp_, gho_, ghu_, ghs_, or ghr_)")
        
        if len(github_token) < 40:
            errors.append("GitHub token appears too short (should be at least 40 characters)")
    
    # Validate repository URL format
    repo_url = os.getenv('GITHUB_REPO_URL')
    if repo_url:
        if not repo_url.startswith('https://github.com/'):
            errors.append("GitHub repository URL should start with 'https://github.com/'")
    
    # Validate security settings
    max_repo_size = SECURITY_SETTINGS.get('max_repository_size_mb', 0)
    if max_repo_size <= 0:
        errors.append("Maximum repository size must be greater than 0")
    
    max_file_size = SECURITY_SETTINGS.get('max_file_size_mb', 0)
    if max_file_size <= 0:
        errors.append("Maximum file size must be greater than 0")
    
    # Validate PR settings
    max_files_per_pr = PR_DEFAULT_SETTINGS.get('max_files_per_pr', 0)
    if max_files_per_pr <= 0:
        errors.append("Maximum files per PR must be greater than 0")
    
    return len(errors) == 0, errors

def check_required_permissions() -> Tuple[bool, List[str]]:
    """
    Check if GitHub token has required permissions.
    Returns: (has_permissions, list_of_missing_permissions)
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        return False, ["GitHub token not configured"]
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': GITHUB_API_SETTINGS['accept_header'],
        'User-Agent': GITHUB_API_SETTINGS['user_agent']
    }
    
    missing_permissions = []
    
    try:
        # Check user permissions
        response = requests.get(
            f"{GITHUB_API_SETTINGS['base_url']}/user",
            headers=headers,
            timeout=GITHUB_API_SETTINGS['timeout']
        )
        
        if response.status_code == 401:
            return False, ["Invalid GitHub token or token expired"]
        elif response.status_code == 403:
            return False, ["GitHub token lacks basic user access permissions"]
        elif response.status_code != 200:
            return False, [f"Unable to verify permissions (HTTP {response.status_code})"]
        
        # Check token scopes from response headers
        token_scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
        token_scopes = [scope.strip() for scope in token_scopes if scope.strip()]
        
        # Check required scopes
        required_scopes = GITHUB_API_SETTINGS['required_scopes']
        for scope in required_scopes:
            if scope not in token_scopes:
                missing_permissions.append(f"Missing required scope: {scope}")
        
        # Check repository access if repo info is configured
        repo_owner = os.getenv('GITHUB_OWNER')
        repo_name = os.getenv('GITHUB_REPO')
        
        if repo_owner and repo_name:
            repo_response = requests.get(
                f"{GITHUB_API_SETTINGS['base_url']}/repos/{repo_owner}/{repo_name}",
                headers=headers,
                timeout=GITHUB_API_SETTINGS['timeout']
            )
            
            if repo_response.status_code == 404:
                missing_permissions.append(f"Repository {repo_owner}/{repo_name} not found or no access")
            elif repo_response.status_code == 403:
                missing_permissions.append(f"No access to repository {repo_owner}/{repo_name}")
            elif repo_response.status_code != 200:
                missing_permissions.append(f"Unable to verify repository access (HTTP {repo_response.status_code})")
    
    except requests.exceptions.RequestException as e:
        return False, [f"Network error while checking permissions: {str(e)}"]
    except Exception as e:
        return False, [f"Unexpected error while checking permissions: {str(e)}"]
    
    return len(missing_permissions) == 0, missing_permissions

def test_github_connectivity() -> Tuple[bool, Optional[str]]:
    """
    Test connectivity to GitHub API.
    Returns: (is_connected, error_message)
    """
    try:
        # Test basic connectivity to GitHub API
        response = requests.get(
            f"{GITHUB_API_SETTINGS['base_url']}/rate_limit",
            timeout=GITHUB_API_SETTINGS['timeout']
        )
        
        if response.status_code == 200:
            rate_limit_data = response.json()
            remaining = rate_limit_data.get('rate', {}).get('remaining', 0)
            
            if remaining < 100:
                return True, f"Warning: Low API rate limit remaining ({remaining} requests)"
            
            return True, None
        else:
            return False, f"GitHub API returned HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Timeout connecting to GitHub API"
    except requests.exceptions.ConnectionError:
        return False, "Unable to connect to GitHub API (network error)"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_all_config() -> Dict[str, any]:
    """
    Run all configuration validations and return comprehensive results.
    Returns: Dictionary with validation results
    """
    results = {
        'overall_valid': True,
        'github_config': {'valid': True, 'errors': []},
        'permissions': {'valid': True, 'errors': []},
        'connectivity': {'valid': True, 'error': None},
        'timestamp': None
    }
    
    # Import datetime here to avoid circular imports
    from datetime import datetime
    results['timestamp'] = datetime.now().isoformat()
    
    # Validate GitHub config
    config_valid, config_errors = validate_github_config()
    results['github_config']['valid'] = config_valid
    results['github_config']['errors'] = config_errors
    
    if not config_valid:
        results['overall_valid'] = False
    
    # Check permissions (only if basic config is valid)
    if config_valid:
        perms_valid, perm_errors = check_required_permissions()
        results['permissions']['valid'] = perms_valid
        results['permissions']['errors'] = perm_errors
        
        if not perms_valid:
            results['overall_valid'] = False
    
    # Test connectivity
    conn_valid, conn_error = test_github_connectivity()
    results['connectivity']['valid'] = conn_valid
    results['connectivity']['error'] = conn_error
    
    if not conn_valid:
        results['overall_valid'] = False
    
    return results

def log_validation_results(results: Dict[str, any]) -> None:
    """
    Log validation results to the configured log file.
    """
    logger = logging.getLogger(__name__)
    
    if results['overall_valid']:
        logger.info("Configuration validation passed successfully")
    else:
        logger.error("Configuration validation failed")
        
        if not results['github_config']['valid']:
            for error in results['github_config']['errors']:
                logger.error(f"Config error: {error}")
        
        if not results['permissions']['valid']:
            for error in results['permissions']['errors']:
                logger.error(f"Permission error: {error}")
        
        if not results['connectivity']['valid']:
            logger.error(f"Connectivity error: {results['connectivity']['error']}")

# Initialize validation on import (can be disabled by setting environment variable)
if os.getenv('SKIP_CONFIG_VALIDATION', 'False').lower() != 'true':
    try:
        validation_results = validate_all_config()
        log_validation_results(validation_results)
        
        # Store results for access by other modules
        _LAST_VALIDATION_RESULTS = validation_results
    except Exception as e:
        logging.error(f"Error during configuration validation: {str(e)}")
        _LAST_VALIDATION_RESULTS = None
else:
    _LAST_VALIDATION_RESULTS = None

def get_last_validation_results() -> Optional[Dict[str, any]]:
    """
    Get the results of the last configuration validation.
    """
    return _LAST_VALIDATION_RESULTS