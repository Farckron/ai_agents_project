"""
Validation functions for data models.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from .pr_request import PRRequest, PRRequestOptions
from .change_set import ChangeSet, ChangeOperation
from .pr_workflow import PRWorkflow


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class ValidationResult:
    """Result of validation with errors and warnings."""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.is_valid: bool = True
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0


def validate_github_url(url: str) -> bool:
    """Validate if URL is a valid GitHub repository URL."""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        if parsed.netloc not in ['github.com', 'www.github.com']:
            return False
        
        # Check if path looks like a repository path (owner/repo)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            return False
        
        # Basic validation of owner and repo names
        owner, repo = path_parts[0], path_parts[1]
        if not owner or not repo:
            return False
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        # GitHub username/repo name validation (simplified)
        github_name_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_])*[a-zA-Z0-9]$|^[a-zA-Z0-9]$'
        if not re.match(github_name_pattern, owner) or not re.match(github_name_pattern, repo):
            return False
        
        return True
    except Exception:
        return False


def validate_branch_name(branch_name: str) -> bool:
    """Validate Git branch name according to Git naming rules."""
    if not branch_name:
        return False
    
    # Git branch name rules (simplified)
    # - Cannot start or end with /
    # - Cannot contain consecutive slashes
    # - Cannot contain certain special characters
    # - Cannot be empty
    
    if branch_name.startswith('/') or branch_name.endswith('/'):
        return False
    
    if '//' in branch_name:
        return False
    
    # Check for invalid characters
    invalid_chars = [' ', '~', '^', ':', '?', '*', '[', '\\', '\x7f']
    for char in invalid_chars:
        if char in branch_name:
            return False
    
    # Cannot be just dots
    if branch_name in ['.', '..']:
        return False
    
    # Cannot contain @{
    if '@{' in branch_name:
        return False
    
    return True


def validate_file_path(file_path: str) -> bool:
    """Validate file path for safety and correctness."""
    if not file_path:
        return False
    
    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return False
    
    # Check for invalid characters (Windows and Unix)
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in invalid_chars:
        if char in file_path:
            return False
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                     'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                     'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    
    path_parts = file_path.split('/')
    for part in path_parts:
        if part.upper() in reserved_names:
            return False
    
    return True


def validate_repository_url(repo_url: str) -> Dict[str, Any]:
    """
    Validate repository URL and return validation result.
    
    Args:
        repo_url: Repository URL to validate
        
    Returns:
        Dictionary with validation result
    """
    if not repo_url or not repo_url.strip():
        return {
            'is_valid': False,
            'message': 'Repository URL cannot be empty'
        }
    
    if not validate_github_url(repo_url):
        return {
            'is_valid': False,
            'message': 'Invalid GitHub repository URL format'
        }
    
    return {
        'is_valid': True,
        'message': 'Valid repository URL'
    }


def validate_pr_request(pr_request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate PR request data dictionary.
    
    Args:
        pr_request_data: Dictionary containing PR request data
        
    Returns:
        Dictionary with validation result
    """
    if not isinstance(pr_request_data, dict):
        return {
            'is_valid': False,
            'message': 'PR request data must be a dictionary'
        }
    
    # Check required fields
    required_fields = ['user_request', 'repo_url', 'request_id']
    for field in required_fields:
        if field not in pr_request_data:
            return {
                'is_valid': False,
                'message': f'Missing required field: {field}'
            }
    
    # Validate user_request
    user_request = pr_request_data.get('user_request', '').strip()
    if not user_request:
        return {
            'is_valid': False,
            'message': 'User request cannot be empty'
        }
    
    if len(user_request) > 10000:
        return {
            'is_valid': False,
            'message': 'User request is too long (max 10000 characters)'
        }
    
    # Validate repo_url
    repo_url_validation = validate_repository_url(pr_request_data.get('repo_url', ''))
    if not repo_url_validation['is_valid']:
        return repo_url_validation
    
    # Validate request_id format
    try:
        import uuid
        uuid.UUID(pr_request_data.get('request_id', ''))
    except (ValueError, TypeError):
        return {
            'is_valid': False,
            'message': 'Invalid request_id format (must be UUID)'
        }
    
    return {
        'is_valid': True,
        'message': 'Valid PR request'
    }


def validate_pr_request_model(pr_request: PRRequest) -> ValidationResult:
    """
    Validate PRRequest model.
    
    Args:
        pr_request: PRRequest instance to validate
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Validate user_request
    if not pr_request.user_request or not pr_request.user_request.strip():
        result.add_error("User request cannot be empty")
    elif len(pr_request.user_request) > 10000:
        result.add_warning("User request is very long (>10000 characters)")
    
    # Validate repo_url
    if not validate_github_url(pr_request.repo_url):
        result.add_error("Invalid GitHub repository URL")
    
    # Validate options
    if pr_request.options:
        options_result = validate_pr_request_options(pr_request.options)
        result.errors.extend(options_result.errors)
        result.warnings.extend(options_result.warnings)
        if options_result.has_errors():
            result.is_valid = False
    
    # Validate request_id format
    try:
        import uuid
        uuid.UUID(pr_request.request_id)
    except ValueError:
        result.add_error("Invalid request_id format (must be UUID)")
    
    # Validate timestamps
    if pr_request.created_at > pr_request.updated_at:
        result.add_error("created_at cannot be after updated_at")
    
    # Validate status consistency
    if pr_request.status.value == "completed" and not pr_request.pr_url:
        result.add_warning("Completed request should have pr_url")
    
    if pr_request.status.value == "failed" and not pr_request.error_message:
        result.add_warning("Failed request should have error_message")
    
    return result


def validate_pr_request_options(options: PRRequestOptions) -> ValidationResult:
    """
    Validate PRRequestOptions.
    
    Args:
        options: PRRequestOptions instance to validate
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Validate branch_name if provided
    if options.branch_name and not validate_branch_name(options.branch_name):
        result.add_error("Invalid branch name format")
    
    # Validate base_branch
    if not validate_branch_name(options.base_branch):
        result.add_error("Invalid base branch name format")
    
    # Validate pr_title length
    if options.pr_title and len(options.pr_title) > 200:
        result.add_warning("PR title is very long (>200 characters)")
    
    # Validate pr_description length
    if options.pr_description and len(options.pr_description) > 50000:
        result.add_warning("PR description is very long (>50000 characters)")
    
    return result


def validate_change_set(change_set: ChangeSet) -> ValidationResult:
    """
    Validate ChangeSet model.
    
    Args:
        change_set: ChangeSet instance to validate
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Validate request_id format
    try:
        import uuid
        uuid.UUID(change_set.request_id)
    except ValueError:
        result.add_error("Invalid request_id format (must be UUID)")
    
    # Validate change_id format
    try:
        import uuid
        uuid.UUID(change_set.change_id)
    except ValueError:
        result.add_error("Invalid change_id format (must be UUID)")
    
    # Validate file_path
    if not validate_file_path(change_set.file_path):
        result.add_error("Invalid or unsafe file path")
    
    # Validate change_summary
    if not change_set.change_summary or not change_set.change_summary.strip():
        result.add_error("Change summary cannot be empty")
    elif len(change_set.change_summary) > 1000:
        result.add_warning("Change summary is very long (>1000 characters)")
    
    # Validate operation-specific requirements
    if change_set.operation == ChangeOperation.CREATE:
        if not change_set.new_content:
            result.add_error("CREATE operation requires new_content")
        if change_set.original_content is not None:
            result.add_warning("CREATE operation should not have original_content")
    
    elif change_set.operation == ChangeOperation.DELETE:
        if not change_set.original_content:
            result.add_error("DELETE operation requires original_content")
        if change_set.new_content is not None:
            result.add_warning("DELETE operation should not have new_content")
    
    elif change_set.operation == ChangeOperation.MODIFY:
        if not change_set.original_content:
            result.add_error("MODIFY operation requires original_content")
        if not change_set.new_content:
            result.add_error("MODIFY operation requires new_content")
        if change_set.original_content == change_set.new_content:
            result.add_warning("MODIFY operation has identical original and new content")
    
    # Validate content size
    max_content_size = 1024 * 1024  # 1MB
    if change_set.original_content and len(change_set.original_content) > max_content_size:
        result.add_warning("Original content is very large (>1MB)")
    if change_set.new_content and len(change_set.new_content) > max_content_size:
        result.add_warning("New content is very large (>1MB)")
    
    # Validate timestamps
    if change_set.applied_at and change_set.applied_at < change_set.created_at:
        result.add_error("applied_at cannot be before created_at")
    
    return result


def validate_pr_workflow(workflow: PRWorkflow) -> ValidationResult:
    """
    Validate PRWorkflow model.
    
    Args:
        workflow: PRWorkflow instance to validate
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Validate request_id format
    try:
        import uuid
        uuid.UUID(workflow.request_id)
    except ValueError:
        result.add_error("Invalid request_id format (must be UUID)")
    
    # Validate workflow_id format
    try:
        import uuid
        uuid.UUID(workflow.workflow_id)
    except ValueError:
        result.add_error("Invalid workflow_id format (must be UUID)")
    
    # Validate branch_name if provided
    if workflow.branch_name and not validate_branch_name(workflow.branch_name):
        result.add_error("Invalid branch name format")
    
    # Validate pr_url if provided
    if workflow.pr_url and not workflow.pr_url.startswith('https://github.com/'):
        result.add_warning("PR URL should be a GitHub URL")
    
    # Validate steps
    if not workflow.steps:
        result.add_warning("Workflow has no steps")
    else:
        step_names = [step.step_name for step in workflow.steps]
        if len(step_names) != len(set(step_names)):
            result.add_error("Workflow has duplicate step names")
        
        for i, step in enumerate(workflow.steps):
            if not step.step_name or not step.step_name.strip():
                result.add_error(f"Step {i} has empty name")
    
    # Validate timestamps
    if workflow.completed_at and workflow.completed_at < workflow.created_at:
        result.add_error("completed_at cannot be before created_at")
    
    # Validate completion status consistency
    if workflow.is_completed():
        if workflow.completion_status.value == "success" and workflow.has_failed_steps():
            result.add_warning("Workflow marked as success but has failed steps")
        elif workflow.completion_status.value == "failed" and not workflow.has_failed_steps():
            result.add_warning("Workflow marked as failed but has no failed steps")
    
    return result


def validate_all_models(pr_request: PRRequest, change_sets: List[ChangeSet], 
                       workflow: PRWorkflow) -> ValidationResult:
    """
    Validate all models together for consistency.
    
    Args:
        pr_request: PRRequest instance
        change_sets: List of ChangeSet instances
        workflow: PRWorkflow instance
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Validate individual models first
    pr_result = validate_pr_request(pr_request)
    workflow_result = validate_pr_workflow(workflow)
    
    result.errors.extend(pr_result.errors)
    result.warnings.extend(pr_result.warnings)
    result.errors.extend(workflow_result.errors)
    result.warnings.extend(workflow_result.warnings)
    
    if pr_result.has_errors() or workflow_result.has_errors():
        result.is_valid = False
    
    for change_set in change_sets:
        cs_result = validate_change_set(change_set)
        result.errors.extend(cs_result.errors)
        result.warnings.extend(cs_result.warnings)
        if cs_result.has_errors():
            result.is_valid = False
    
    # Cross-model validation
    # Check if request_ids match
    if pr_request.request_id != workflow.request_id:
        result.add_error("PRRequest and PRWorkflow have different request_ids")
    
    for change_set in change_sets:
        if change_set.request_id != pr_request.request_id:
            result.add_error(f"ChangeSet {change_set.change_id} has different request_id")
    
    # Check if workflow branch matches PR options
    if (workflow.branch_name and pr_request.options.branch_name and 
        workflow.branch_name != pr_request.options.branch_name):
        result.add_warning("Workflow branch name differs from PR request options")
    
    # Check if completed workflow has PR URL matching request
    if (workflow.is_completed() and workflow.pr_url and pr_request.pr_url and
        workflow.pr_url != pr_request.pr_url):
        result.add_warning("Workflow and PR request have different PR URLs")
    
    return result