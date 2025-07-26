import re
import difflib
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os
import subprocess
from urllib.parse import urlparse

class GitOperations:
    """Utility class for Git operations and repository management"""
    
    def __init__(self):
        self.logger = logging.getLogger("GitOperations")
    
    def calculate_file_diff(self, original_content: str, new_content: str, 
                           file_path: str = "file") -> Dict[str, Any]:
        """
        Calculate the difference between two file contents
        
        Args:
            original_content: Original file content
            new_content: New file content
            file_path: File path for context (optional)
        
        Returns:
            Dictionary containing diff information
        """
        try:
            # Split content into lines for diff calculation
            original_lines = original_content.splitlines(keepends=True) if original_content else []
            new_lines = new_content.splitlines(keepends=True) if new_content else []
            
            # Generate unified diff
            diff_lines = list(difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=""
            ))
            
            # Calculate statistics
            additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
            
            # Determine change type
            if not original_content and new_content:
                change_type = "create"
            elif original_content and not new_content:
                change_type = "delete"
            elif original_content != new_content:
                change_type = "modify"
            else:
                change_type = "no_change"
            
            return {
                "file_path": file_path,
                "change_type": change_type,
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
                "diff_lines": diff_lines,
                "diff_text": "".join(diff_lines),
                "has_changes": len(diff_lines) > 0,
                "original_size": len(original_content) if original_content else 0,
                "new_size": len(new_content) if new_content else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating file diff for {file_path}: {str(e)}")
            return {
                "file_path": file_path,
                "change_type": "error",
                "error": str(e),
                "has_changes": False
            }
    
    def create_commit_message(self, changes_summary: Dict[str, Any], 
                            custom_message: Optional[str] = None) -> str:
        """
        Generate a commit message based on changes summary
        
        Args:
            changes_summary: Dictionary containing information about changes
            custom_message: Custom commit message (optional)
        
        Returns:
            Generated commit message
        """
        try:
            if custom_message:
                return custom_message
            
            # Extract information from changes summary
            files_changed = changes_summary.get("files_changed", [])
            total_additions = changes_summary.get("total_additions", 0)
            total_deletions = changes_summary.get("total_deletions", 0)
            change_types = changes_summary.get("change_types", {})
            
            # Determine primary action
            if change_types.get("create", 0) > 0 and change_types.get("modify", 0) == 0:
                action = "Add"
            elif change_types.get("delete", 0) > 0 and change_types.get("create", 0) == 0:
                action = "Remove"
            elif change_types.get("modify", 0) > 0:
                action = "Update"
            else:
                action = "Modify"
            
            # Create subject line
            if len(files_changed) == 1:
                file_name = os.path.basename(files_changed[0])
                subject = f"{action} {file_name}"
            elif len(files_changed) <= 3:
                file_names = [os.path.basename(f) for f in files_changed]
                subject = f"{action} {', '.join(file_names)}"
            else:
                subject = f"{action} {len(files_changed)} files"
            
            # Add change statistics if significant
            if total_additions + total_deletions > 10:
                stats = []
                if total_additions > 0:
                    stats.append(f"+{total_additions}")
                if total_deletions > 0:
                    stats.append(f"-{total_deletions}")
                if stats:
                    subject += f" ({', '.join(stats)})"
            
            return subject
            
        except Exception as e:
            self.logger.error(f"Error creating commit message: {str(e)}")
            return "Update files"
    
    def generate_unique_branch_name(self, base_name: str, repo_url: str, 
                                  existing_branches: Optional[List[str]] = None) -> str:
        """
        Generate a unique branch name based on base name
        
        Args:
            base_name: Base name for the branch
            repo_url: Repository URL for context
            existing_branches: List of existing branch names (optional)
        
        Returns:
            Unique branch name
        """
        try:
            # Sanitize base name
            sanitized_name = self._sanitize_branch_name(base_name)
            
            # If no existing branches provided, return sanitized name with timestamp
            if not existing_branches:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                return f"{sanitized_name}-{timestamp}"
            
            # Check if base name is already unique
            if sanitized_name not in existing_branches:
                return sanitized_name
            
            # Generate unique name with suffix
            counter = 1
            while True:
                candidate = f"{sanitized_name}-{counter}"
                if candidate not in existing_branches:
                    return candidate
                counter += 1
                
                # Safety check to prevent infinite loop
                if counter > 1000:
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    return f"{sanitized_name}-{timestamp}"
                    
        except Exception as e:
            self.logger.error(f"Error generating unique branch name: {str(e)}")
            # Fallback to timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            return f"feature-{timestamp}"
    
    def validate_branch_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Git branch name according to Git naming rules
        
        Args:
            name: Branch name to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not name:
                return False, "Branch name cannot be empty"
            
            # Git branch name rules
            invalid_patterns = [
                (r'^\.', "Branch name cannot start with a dot"),
                (r'\.$', "Branch name cannot end with a dot"),
                (r'\.\.', "Branch name cannot contain consecutive dots"),
                (r'[~^:\s\[\]\\]', "Branch name contains invalid characters"),
                (r'@{', "Branch name cannot contain @{"),
                (r'^-', "Branch name cannot start with a dash"),
                (r'-$', "Branch name cannot end with a dash"),
                (r'/$', "Branch name cannot end with a slash"),
                (r'//', "Branch name cannot contain consecutive slashes"),
            ]
            
            for pattern, message in invalid_patterns:
                if re.search(pattern, name):
                    return False, message
            
            # Check length (Git doesn't have strict limits, but practical limit)
            if len(name) > 250:
                return False, "Branch name is too long (max 250 characters)"
            
            # Check for control characters
            if any(ord(c) < 32 for c in name):
                return False, "Branch name contains control characters"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error validating branch name: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _sanitize_branch_name(self, name: str) -> str:
        """
        Sanitize a string to create a valid Git branch name
        
        Args:
            name: Original name to sanitize
        
        Returns:
            Sanitized branch name
        """
        try:
            # Convert to lowercase and replace spaces with dashes
            sanitized = name.lower().strip()
            sanitized = re.sub(r'\s+', '-', sanitized)
            
            # Remove or replace invalid characters
            sanitized = re.sub(r'[~^:\[\]\\@{}]', '', sanitized)
            sanitized = re.sub(r'\.\.+', '.', sanitized)  # Replace multiple dots with single
            sanitized = re.sub(r'/+', '/', sanitized)     # Replace multiple slashes with single
            
            # Remove leading/trailing dots, dashes, and slashes
            sanitized = sanitized.strip('.-/')
            
            # Ensure it doesn't start with a dash
            sanitized = re.sub(r'^-+', '', sanitized)
            
            # Replace multiple consecutive dashes with single dash
            sanitized = re.sub(r'-+', '-', sanitized)
            
            # If empty after sanitization, provide default
            if not sanitized:
                sanitized = "feature"
            
            # Truncate if too long
            if len(sanitized) > 200:
                sanitized = sanitized[:200].rstrip('-.')
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing branch name: {str(e)}")
            return "feature"    

    def validate_repository_access(self, repo_url: str, token: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate repository access and permissions
        
        Args:
            repo_url: GitHub repository URL
            token: GitHub access token (optional)
        
        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            from .github_utils import GitHubUtils
            github_utils = GitHubUtils()
            
            # Parse repository URL
            parsed = github_utils.parse_github_url(repo_url)
            if not parsed:
                return False, "Invalid GitHub repository URL"
            
            owner, repo = parsed
            
            # Check if repository exists
            if not github_utils.check_repository_exists(repo_url):
                return False, "Repository does not exist or is not accessible"
            
            # If token provided, check write permissions
            if token:
                try:
                    import requests
                    headers = {'Authorization': f'token {token}'}
                    api_url = f"https://api.github.com/repos/{owner}/{repo}"
                    
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        repo_data = response.json()
                        permissions = repo_data.get('permissions', {})
                        
                        # Check for push permissions (needed for creating branches and PRs)
                        if not permissions.get('push', False):
                            return False, "Insufficient permissions: push access required"
                        
                        return True, None
                    else:
                        return False, f"API access failed: {response.status_code}"
                        
                except Exception as e:
                    return False, f"Token validation failed: {str(e)}"
            
            # Basic validation passed
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error validating repository access: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def sanitize_user_input(self, user_input: str, input_type: str = "general") -> str:
        """
        Sanitize user input to prevent injection attacks and ensure safety
        
        Args:
            user_input: Raw user input
            input_type: Type of input (general, branch_name, commit_message, pr_title, pr_description)
        
        Returns:
            Sanitized input string
        """
        try:
            if not user_input:
                return ""
            
            # Remove null bytes and control characters
            sanitized = ''.join(char for char in user_input if ord(char) >= 32 or char in '\n\r\t')
            
            # Trim whitespace
            sanitized = sanitized.strip()
            
            # Type-specific sanitization
            if input_type == "branch_name":
                return self._sanitize_branch_name(sanitized)
            
            elif input_type == "commit_message":
                # Limit length and remove potentially dangerous patterns
                sanitized = sanitized[:500]  # Reasonable commit message length
                # Remove shell command patterns
                sanitized = re.sub(r'[`$(){};&|<>]', '', sanitized)
                
            elif input_type == "pr_title":
                # Limit length for PR titles
                sanitized = sanitized[:200]
                # Remove markdown that could break formatting
                sanitized = re.sub(r'[#*`]', '', sanitized)
                
            elif input_type == "pr_description":
                # Limit length for PR descriptions
                sanitized = sanitized[:5000]
                # Allow basic markdown but remove dangerous patterns
                sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
                
            elif input_type == "file_path":
                # Sanitize file paths
                sanitized = self._sanitize_file_path(sanitized)
                
            else:  # general
                # General sanitization - remove potentially dangerous patterns
                sanitized = re.sub(r'[`$(){};&|<>]', '', sanitized)
                sanitized = sanitized[:1000]  # General length limit
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing user input: {str(e)}")
            return ""
    
    def check_file_safety(self, file_path: str, content: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if a file is safe to modify/create
        
        Args:
            file_path: Path to the file
            content: File content to check (optional)
        
        Returns:
            Tuple of (is_safe, warning_message)
        """
        try:
            # Check for dangerous file paths
            if not self._is_safe_file_path(file_path):
                return False, f"Unsafe file path: {file_path}"
            
            # Check file extension
            file_ext = os.path.splitext(file_path.lower())[1]
            
            # Dangerous file extensions
            dangerous_extensions = {
                '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
                '.vbs', '.js', '.jar', '.app', '.deb', '.rpm',
                '.dmg', '.pkg', '.msi', '.ps1', '.sh'
            }
            
            if file_ext in dangerous_extensions:
                return False, f"Potentially dangerous file type: {file_ext}"
            
            # Check for system/config files that shouldn't be modified
            system_files = {
                '.env', '.env.local', '.env.production',
                'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
                'authorized_keys', 'known_hosts',
                'passwd', 'shadow', 'sudoers'
            }
            
            file_name = os.path.basename(file_path.lower())
            if file_name in system_files:
                return False, f"System/security file should not be modified: {file_name}"
            
            # Check content if provided
            if content:
                # Check for potentially malicious content
                dangerous_patterns = [
                    r'rm\s+-rf\s+/',  # Dangerous rm commands
                    r'sudo\s+rm',     # Sudo rm commands
                    r'eval\s*\(',     # Eval functions
                    r'exec\s*\(',     # Exec functions
                    r'system\s*\(',   # System calls
                    r'shell_exec',    # Shell execution
                    r'<script[^>]*>', # Script tags
                    r'javascript:',   # JavaScript URLs
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return False, f"Potentially dangerous content detected: {pattern}"
                
                # Check for excessive size
                if len(content) > 1024 * 1024:  # 1MB limit
                    return False, "File content too large (>1MB)"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error checking file safety: {str(e)}")
            return False, f"Safety check error: {str(e)}"
    
    def _is_safe_file_path(self, file_path: str) -> bool:
        """
        Check if file path is safe (no directory traversal, etc.)
        
        Args:
            file_path: File path to check
        
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Normalize path
            normalized = os.path.normpath(file_path)
            
            # Check for directory traversal
            if '..' in normalized:
                return False
            
            # Check for absolute paths (should be relative)
            if os.path.isabs(normalized):
                return False
            
            # Check for hidden system directories
            path_parts = normalized.split(os.sep)
            dangerous_dirs = {'.git', '.ssh', '.aws', '.docker', 'node_modules/.bin'}
            
            for part in path_parts:
                if part in dangerous_dirs:
                    return False
                # Check for hidden directories that might contain sensitive data
                if part.startswith('.') and len(part) > 1 and part not in {'.github', '.vscode', '.gitignore'}:
                    return False
            
            # Check path length
            if len(normalized) > 260:  # Windows path limit
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking file path safety: {str(e)}")
            return False
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """
        Sanitize file path to make it safe
        
        Args:
            file_path: Original file path
        
        Returns:
            Sanitized file path
        """
        try:
            # Remove dangerous characters
            sanitized = re.sub(r'[<>:"|?*]', '', file_path)
            
            # Remove directory traversal attempts
            sanitized = sanitized.replace('..', '')
            
            # Normalize separators
            sanitized = sanitized.replace('\\', '/')
            
            # Remove leading slashes (make relative)
            sanitized = sanitized.lstrip('/')
            
            # Remove multiple consecutive slashes
            sanitized = re.sub(r'/+', '/', sanitized)
            
            # Limit length
            if len(sanitized) > 200:
                # Keep the file extension
                name, ext = os.path.splitext(sanitized)
                sanitized = name[:200-len(ext)] + ext
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing file path: {str(e)}")
            return "safe_file.txt"