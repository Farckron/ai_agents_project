from typing import Dict, Any, List
import requests
import json
import time
from github import Github, GithubException
from .base_agent import BaseAgent
from config.settings import Config
from utils.error_handler import ErrorHandler, ErrorType, ErrorSeverity, with_error_handling
from utils.structured_logger import get_structured_logger, log_github_api_call, LogLevel
from utils.git_operations import GitOperations

class GitHubManager(BaseAgent):
    def __init__(self):
        super().__init__("github_manager")
        
        # Initialize error handler
        self.error_handler = ErrorHandler("GitHubManager")
        
        # Initialize Git operations utility
        self.git_operations = GitOperations()
        
        # Initialize structured logger
        self.structured_logger = get_structured_logger("github_manager")
        
        # Initialize GitHub client
        if Config.GITHUB_TOKEN:
            try:
                self.github_client = Github(Config.GITHUB_TOKEN)
                # Test the token
                self.github_client.get_user()
                self.log_message("GitHub client initialized successfully")
            except Exception as e:
                self.error_handler.log_error(
                    e, 
                    ErrorType.AUTHENTICATION, 
                    ErrorSeverity.HIGH,
                    {'token_provided': True}
                )
                self.github_client = None
                self.log_message("GitHub token validation failed - some features will be limited", "WARNING")
        else:
            self.github_client = None
            self.log_message("GitHub token not provided - some features will be limited", "WARNING")
        
        self.repo_cache = {}
        self.log_message("GitHub Manager initialized")
    
    def handle_github_api_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GitHub API specific errors with detailed analysis"""
        return self.error_handler.handle_github_api_errors(error, context)
    
    def handle_authentication_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GitHub authentication errors"""
        return self.error_handler.handle_authentication_errors(error, context)
    
    def handle_rate_limit_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GitHub rate limit errors with retry suggestions"""
        return self.error_handler.handle_rate_limit_errors(error, context)
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GitHub repository operations
        
        Input task structure:
        - action: type of GitHub operation
        - repo_url: repository URL
        - additional parameters based on action
        """
        try:
            action = task.get('action', 'get_repo_summary')
            repo_url = task.get('repo_url', Config.GITHUB_REPO_URL)
            
            self.log_message(f"Processing GitHub action: {action}")
            
            if action == 'get_repo_summary':
                return self._get_repository_summary(repo_url)
            elif action == 'get_file_content':
                return self._get_file_content(repo_url, task.get('file_path', ''))
            elif action == 'list_files':
                return self._list_repository_files(repo_url)
            elif action == 'get_recent_commits':
                return self._get_recent_commits(repo_url, task.get('limit', 10))
            elif action == 'get_issues':
                return self._get_repository_issues(repo_url)
            elif action == 'create_branch':
                return self.create_branch(repo_url, task.get('branch_name', ''), task.get('base_branch', 'main'))
            elif action == 'validate_branch_name':
                return self.validate_branch_name(task.get('branch_name', ''))
            elif action == 'generate_unique_branch_name':
                return self.generate_unique_branch_name(task.get('base_name', ''), repo_url)
            elif action == 'commit_changes':
                return self.commit_multiple_files(repo_url, task.get('branch_name', 'main'), task.get('files', {}), task.get('message', ''))
            elif action == 'commit_multiple_files':
                return self.commit_multiple_files(repo_url, task.get('branch_name', 'main'), task.get('files', {}), task.get('message', ''))
            elif action == 'update_file_content':
                return self.update_file_content(repo_url, task.get('branch_name', 'main'), task.get('file_path', ''), task.get('content', ''), task.get('message', ''))
            elif action == 'delete_file':
                return self.delete_file(repo_url, task.get('branch_name', 'main'), task.get('file_path', ''), task.get('message', ''))
            elif action == 'create_pull_request':
                return self.create_pull_request(repo_url, task.get('branch_name', ''), task.get('title', ''), task.get('description', ''), task.get('base_branch', 'main'))
            elif action == 'generate_pr_description':
                return {'status': 'success', 'description': self.generate_pr_description(repo_url, task.get('branch_name', ''), task.get('base_branch', 'main'))}
            elif action == 'validate_pr_parameters':
                return self.validate_pr_parameters(task.get('title', ''), task.get('description', ''), task.get('head_branch', ''), task.get('base_branch', ''))
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to fetch commits from public API'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get commits: {str(e)}'
            }
    
    def _get_repository_issues(self, repo_url: str) -> Dict[str, Any]:
        """Get repository issues"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                issues = repo_obj.get_issues(state='open')[:20]  # Limit to 20 issues
                
                issue_data = []
                for issue in issues:
                    issue_data.append({
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body[:200] + '...' if issue.body and len(issue.body) > 200 else issue.body,
                        'state': issue.state,
                        'created_at': issue.created_at.isoformat(),
                        'labels': [label.name for label in issue.labels]
                    })
                
                return {
                    'status': 'success',
                    'issues': issue_data,
                    'total_issues': len(issue_data)
                }
            else:
                return {
                    'status': 'limited',
                    'message': 'Issue listing requires GitHub token',
                    'issues': []
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get issues: {str(e)}'
            }
    
    @with_error_handling(ErrorType.GITHUB_API, retry=True)
    def create_branch(self, repo_url: str, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch from base branch"""
        
        if not self.github_client:
            auth_error = Exception("GitHub token required for branch creation")
            return self.handle_authentication_errors(auth_error, {
                'operation': 'create_branch',
                'repo_url': repo_url,
                'branch_name': branch_name
            })
        
        # Validate branch name first
        validation_result = self.validate_branch_name(branch_name)
        if not validation_result['is_valid']:
            return {
                'status': 'error',
                'error': f'Invalid branch name: {validation_result["message"]}'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Check if branch already exists
            try:
                existing_branch = repo_obj.get_branch(branch_name)
                return {
                    'status': 'error',
                    'error': f'Branch {branch_name} already exists'
                }
            except GithubException as e:
                if e.status != 404:  # 404 means branch doesn't exist, which is what we want
                    return self.handle_github_api_errors(e, {
                        'operation': 'check_branch_exists',
                        'repo_url': repo_url,
                        'branch_name': branch_name
                    })
            
            # Get the base branch (default to main if not specified)
            try:
                base_branch_obj = repo_obj.get_branch(base_branch)
            except GithubException as e:
                if e.status == 404:
                    # If base branch doesn't exist, try default branch
                    try:
                        base_branch_obj = repo_obj.get_branch(repo_obj.default_branch)
                        base_branch = repo_obj.default_branch
                    except GithubException as default_error:
                        return self.handle_github_api_errors(default_error, {
                            'operation': 'get_default_branch',
                            'repo_url': repo_url,
                            'requested_base_branch': base_branch
                        })
                else:
                    return self.handle_github_api_errors(e, {
                        'operation': 'get_base_branch',
                        'repo_url': repo_url,
                        'base_branch': base_branch
                    })
            
            # Create new branch
            repo_obj.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_branch_obj.commit.sha
            )
            
            self.log_message(f"Created branch {branch_name} from {base_branch}")
            
            return {
                'status': 'success',
                'branch_name': branch_name,
                'base_branch': base_branch,
                'sha': base_branch_obj.commit.sha,
                'message': f'Branch {branch_name} created successfully from {base_branch}'
            }
            
        except GithubException as e:
            return self.handle_github_api_errors(e, {
                'operation': 'create_branch',
                'repo_url': repo_url,
                'branch_name': branch_name,
                'base_branch': base_branch
            })
        except Exception as e:
            self.error_handler.log_error(
                e, 
                ErrorType.GITHUB_API, 
                ErrorSeverity.HIGH,
                {
                    'operation': 'create_branch',
                    'repo_url': repo_url,
                    'branch_name': branch_name,
                    'base_branch': base_branch
                }
            )
            return {
                'status': 'error',
                'error': f'Failed to create branch: {str(e)}'
            }
    
    def validate_branch_name(self, branch_name: str) -> Dict[str, Any]:
        """Validate branch name according to Git naming rules"""
        
        import re
        
        if not branch_name:
            return {
                'is_valid': False,
                'message': 'Branch name cannot be empty'
            }
        
        # Check length
        if len(branch_name) > 250:
            return {
                'is_valid': False,
                'message': 'Branch name too long (max 250 characters)'
            }
        
        # Check for invalid characters and patterns
        invalid_patterns = [
            r'^\.',           # Cannot start with dot
            r'\.$',           # Cannot end with dot
            r'\.\.',          # Cannot contain double dots
            r'[~^:?*\[\]\\]', # Cannot contain special characters
            r'[ \t]',         # Cannot contain spaces or tabs
            r'@{',            # Cannot contain @{
            r'/$',            # Cannot end with slash
            r'//',            # Cannot contain double slashes
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, branch_name):
                return {
                    'is_valid': False,
                    'message': f'Branch name contains invalid pattern: {pattern}'
                }
        
        # Check for reserved names
        reserved_names = ['HEAD', 'refs', 'remotes']
        if branch_name in reserved_names:
            return {
                'is_valid': False,
                'message': f'Branch name "{branch_name}" is reserved'
            }
        
        return {
            'is_valid': True,
            'message': 'Branch name is valid'
        }
    
    def generate_unique_branch_name(self, base_name: str, repo_url: str) -> Dict[str, Any]:
        """Generate a unique branch name by checking existing branches"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Unique branch name generation requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Clean base name
            import re
            clean_base = re.sub(r'[^a-zA-Z0-9\-_]', '-', base_name.lower())
            clean_base = re.sub(r'-+', '-', clean_base).strip('-')
            
            if not clean_base:
                clean_base = 'feature'
            
            # Check if base name is available
            candidate = clean_base
            counter = 1
            
            while True:
                try:
                    repo_obj.get_branch(candidate)
                    # Branch exists, try next candidate
                    candidate = f"{clean_base}-{counter}"
                    counter += 1
                    
                    # Prevent infinite loop
                    if counter > 1000:
                        return {
                            'status': 'error',
                            'error': 'Could not generate unique branch name after 1000 attempts'
                        }
                except:
                    # Branch doesn't exist, we can use this name
                    break
            
            # Validate the generated name
            validation_result = self.validate_branch_name(candidate)
            if not validation_result['is_valid']:
                return {
                    'status': 'error',
                    'error': f'Generated branch name is invalid: {validation_result["message"]}'
                }
            
            return {
                'status': 'success',
                'branch_name': candidate,
                'base_name': base_name,
                'message': f'Generated unique branch name: {candidate}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to generate unique branch name: {str(e)}'
            }
    
    @with_error_handling(ErrorType.GITHUB_API, retry=True)
    def commit_multiple_files(self, repo_url: str, branch_name: str, files_dict: Dict[str, str], commit_message: str) -> Dict[str, Any]:
        """Commit multiple files to a specific branch simultaneously"""
        
        if not self.github_client:
            auth_error = Exception("GitHub token required for committing changes")
            return self.handle_authentication_errors(auth_error, {
                'operation': 'commit_multiple_files',
                'repo_url': repo_url,
                'branch_name': branch_name
            })
        
        if not files_dict:
            return {
                'status': 'error',
                'error': 'No files provided for commit'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Verify branch exists
            try:
                branch = repo_obj.get_branch(branch_name)
            except GithubException as e:
                return self.handle_github_api_errors(e, {
                    'operation': 'get_branch_for_commit',
                    'repo_url': repo_url,
                    'branch_name': branch_name
                })
            
            # Process each file
            committed_files = []
            failed_files = []
            
            for file_path, content in files_dict.items():
                try:
                    # Check if file exists
                    try:
                        existing_file = repo_obj.get_contents(file_path, ref=branch_name)
                        
                        # Check if content is actually different
                        current_content = existing_file.decoded_content.decode('utf-8')
                        if current_content == content:
                            committed_files.append({
                                'path': file_path,
                                'action': 'unchanged',
                                'sha': existing_file.sha
                            })
                            continue
                        
                        # Update existing file
                        result = repo_obj.update_file(
                            path=file_path,
                            message=commit_message,
                            content=content,
                            sha=existing_file.sha,
                            branch=branch_name
                        )
                        committed_files.append({
                            'path': file_path,
                            'action': 'updated',
                            'sha': result['commit'].sha
                        })
                        
                    except GithubException as file_error:
                        if file_error.status == 404:
                            # Create new file
                            result = repo_obj.create_file(
                                path=file_path,
                                message=commit_message,
                                content=content,
                                branch=branch_name
                            )
                            committed_files.append({
                                'path': file_path,
                                'action': 'created',
                                'sha': result['commit'].sha
                            })
                        else:
                            # Handle other GitHub API errors for this file
                            error_response = self.handle_github_api_errors(file_error, {
                                'operation': 'process_file',
                                'file_path': file_path,
                                'branch_name': branch_name
                            })
                            failed_files.append({
                                'path': file_path,
                                'error': error_response['error']['message'],
                                'error_code': error_response['error']['code']
                            })
                        
                except Exception as file_error:
                    self.error_handler.log_error(
                        file_error, 
                        ErrorType.FILE_OPERATION, 
                        ErrorSeverity.MEDIUM,
                        {'file_path': file_path, 'operation': 'commit_file'}
                    )
                    failed_files.append({
                        'path': file_path,
                        'error': str(file_error)
                    })
            
            self.log_message(f"Committed {len(committed_files)} files to branch {branch_name}")
            
            return {
                'status': 'success' if not failed_files else 'partial',
                'branch_name': branch_name,
                'committed_files': committed_files,
                'failed_files': failed_files,
                'commit_message': commit_message,
                'total_files': len(files_dict),
                'successful_commits': len([f for f in committed_files if f['action'] != 'unchanged']),
                'unchanged_files': len([f for f in committed_files if f['action'] == 'unchanged']),
                'message': f'Successfully processed {len(committed_files)} files to {branch_name}'
            }
            
        except GithubException as e:
            return self.handle_github_api_errors(e, {
                'operation': 'commit_multiple_files',
                'repo_url': repo_url,
                'branch_name': branch_name,
                'file_count': len(files_dict)
            })
        except Exception as e:
            self.error_handler.log_error(
                e, 
                ErrorType.GITHUB_API, 
                ErrorSeverity.HIGH,
                {
                    'operation': 'commit_multiple_files',
                    'repo_url': repo_url,
                    'branch_name': branch_name,
                    'file_count': len(files_dict)
                }
            )
            return {
                'status': 'error',
                'error': f'Failed to commit multiple files: {str(e)}'
            }
    
    def update_file_content(self, repo_url: str, branch_name: str, file_path: str, content: str, commit_message: str) -> Dict[str, Any]:
        """Update content of an existing file"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Updating file content requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Verify branch exists
            try:
                branch = repo_obj.get_branch(branch_name)
            except:
                return {
                    'status': 'error',
                    'error': f'Branch {branch_name} does not exist'
                }
            
            # Get existing file
            try:
                existing_file = repo_obj.get_contents(file_path, ref=branch_name)
            except:
                return {
                    'status': 'error',
                    'error': f'File {file_path} does not exist in branch {branch_name}'
                }
            
            # Check if content is actually different
            current_content = existing_file.decoded_content.decode('utf-8')
            if current_content == content:
                return {
                    'status': 'success',
                    'message': 'File content is already up to date',
                    'file_path': file_path,
                    'branch_name': branch_name,
                    'changed': False
                }
            
            # Update file
            result = repo_obj.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing_file.sha,
                branch=branch_name
            )
            
            self.log_message(f"Updated file {file_path} in branch {branch_name}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'branch_name': branch_name,
                'commit_sha': result['commit'].sha,
                'commit_message': commit_message,
                'changed': True,
                'message': f'Successfully updated {file_path} in {branch_name}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to update file content: {str(e)}'
            }
    
    def delete_file(self, repo_url: str, branch_name: str, file_path: str, commit_message: str) -> Dict[str, Any]:
        """Delete a file from the repository"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Deleting files requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Verify branch exists
            try:
                branch = repo_obj.get_branch(branch_name)
            except:
                return {
                    'status': 'error',
                    'error': f'Branch {branch_name} does not exist'
                }
            
            # Get existing file
            try:
                existing_file = repo_obj.get_contents(file_path, ref=branch_name)
            except:
                return {
                    'status': 'error',
                    'error': f'File {file_path} does not exist in branch {branch_name}'
                }
            
            # Delete file
            result = repo_obj.delete_file(
                path=file_path,
                message=commit_message,
                sha=existing_file.sha,
                branch=branch_name
            )
            
            self.log_message(f"Deleted file {file_path} from branch {branch_name}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'branch_name': branch_name,
                'commit_sha': result['commit'].sha,
                'commit_message': commit_message,
                'message': f'Successfully deleted {file_path} from {branch_name}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to delete file: {str(e)}'
            }
    
    @with_error_handling(ErrorType.GITHUB_API, retry=True)
    def create_pull_request(self, repo_url: str, branch_name: str, title: str, description: str = "", base_branch: str = "main") -> Dict[str, Any]:
        """Create a Pull Request with detailed parameters"""
        
        if not self.github_client:
            auth_error = Exception("GitHub token required for creating Pull Request")
            return self.handle_authentication_errors(auth_error, {
                'operation': 'create_pull_request',
                'repo_url': repo_url,
                'branch_name': branch_name
            })
        
        # Validate PR parameters
        validation_result = self.validate_pr_parameters(title, description, branch_name, base_branch)
        if not validation_result['is_valid']:
            return {
                'status': 'error',
                'error': f'Invalid PR parameters: {validation_result["message"]}'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Verify branches exist
            try:
                head_branch = repo_obj.get_branch(branch_name)
            except GithubException as e:
                return self.handle_github_api_errors(e, {
                    'operation': 'get_head_branch',
                    'repo_url': repo_url,
                    'branch_name': branch_name
                })
            
            try:
                base_branch_obj = repo_obj.get_branch(base_branch)
            except GithubException as e:
                return self.handle_github_api_errors(e, {
                    'operation': 'get_base_branch',
                    'repo_url': repo_url,
                    'base_branch': base_branch
                })
            
            # Check if PR already exists
            try:
                existing_prs = repo_obj.get_pulls(state='open', head=f"{owner}:{branch_name}", base=base_branch)
                if existing_prs.totalCount > 0:
                    existing_pr = existing_prs[0]
                    return {
                        'status': 'error',
                        'error': f'Pull Request already exists: #{existing_pr.number}',
                        'existing_pr_url': existing_pr.html_url
                    }
            except GithubException as e:
                # Log but don't fail - we can still try to create the PR
                self.error_handler.log_error(
                    e, 
                    ErrorType.GITHUB_API, 
                    ErrorSeverity.LOW,
                    {'operation': 'check_existing_pr', 'repo_url': repo_url}
                )
            
            # Generate description if not provided
            if not description:
                try:
                    description = self.generate_pr_description(repo_url, branch_name, base_branch)
                except Exception as desc_error:
                    self.error_handler.log_error(
                        desc_error, 
                        ErrorType.GITHUB_API, 
                        ErrorSeverity.LOW,
                        {'operation': 'generate_pr_description'}
                    )
                    description = f"Automated Pull Request from {branch_name} to {base_branch}"
            
            # Create Pull Request
            pr = repo_obj.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=base_branch
            )
            
            self.log_message(f"Created Pull Request #{pr.number}: {title}")
            
            return {
                'status': 'success',
                'pr_number': pr.number,
                'pr_url': pr.html_url,
                'title': title,
                'description': description,
                'head_branch': branch_name,
                'base_branch': base_branch,
                'state': pr.state,
                'created_at': pr.created_at.isoformat(),
                'message': f'Successfully created Pull Request #{pr.number}'
            }
            
        except GithubException as e:
            # Handle specific GitHub API errors
            if e.status == 422:
                # Validation error - likely no changes between branches
                return {
                    'status': 'error',
                    'error': 'No changes found between branches or validation error',
                    'details': str(e),
                    'suggestions': [
                        'Ensure there are commits in the head branch that are not in the base branch',
                        'Check that branch names are correct',
                        'Verify repository permissions'
                    ]
                }
            else:
                return self.handle_github_api_errors(e, {
                    'operation': 'create_pull_request',
                    'repo_url': repo_url,
                    'branch_name': branch_name,
                    'base_branch': base_branch,
                    'title': title
                })
        except Exception as e:
            self.error_handler.log_error(
                e, 
                ErrorType.GITHUB_API, 
                ErrorSeverity.HIGH,
                {
                    'operation': 'create_pull_request',
                    'repo_url': repo_url,
                    'branch_name': branch_name,
                    'base_branch': base_branch
                }
            )
            return {
                'status': 'error',
                'error': f'Failed to create Pull Request: {str(e)}'
            }
    
    def generate_pr_description(self, repo_url: str, branch_name: str, base_branch: str = "main") -> str:
        """Generate automatic PR description based on changes"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if not self.github_client:
                return "Automated Pull Request - GitHub token required for detailed description"
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get comparison between branches
            comparison = repo_obj.compare(base_branch, branch_name)
            
            # Build description
            description_parts = []
            description_parts.append("## Changes Summary")
            description_parts.append(f"This Pull Request contains {comparison.total_commits} commit(s) with {comparison.files.totalCount} file(s) changed.")
            description_parts.append("")
            
            # Add commit information
            if comparison.commits.totalCount > 0:
                description_parts.append("### Commits")
                for commit in comparison.commits[:5]:  # Limit to 5 commits
                    description_parts.append(f"- {commit.commit.message.split(chr(10))[0]}")  # First line only
                
                if comparison.commits.totalCount > 5:
                    description_parts.append(f"- ... and {comparison.commits.totalCount - 5} more commits")
                description_parts.append("")
            
            # Add file changes
            if comparison.files.totalCount > 0:
                description_parts.append("### Files Changed")
                for file in comparison.files[:10]:  # Limit to 10 files
                    status = "modified"
                    if file.status == "added":
                        status = "added"
                    elif file.status == "removed":
                        status = "deleted"
                    elif file.status == "renamed":
                        status = "renamed"
                    
                    description_parts.append(f"- `{file.filename}` ({status})")
                
                if comparison.files.totalCount > 10:
                    description_parts.append(f"- ... and {comparison.files.totalCount - 10} more files")
                description_parts.append("")
            
            # Add statistics
            description_parts.append("### Statistics")
            description_parts.append(f"- **Additions**: +{comparison.additions}")
            description_parts.append(f"- **Deletions**: -{comparison.deletions}")
            description_parts.append(f"- **Total Changes**: {comparison.additions + comparison.deletions}")
            description_parts.append("")
            
            description_parts.append("---")
            description_parts.append("*This description was automatically generated.*")
            
            return chr(10).join(description_parts)
            
        except Exception as e:
            return f"Automated Pull Request\n\nError generating detailed description: {str(e)}"
    
    def validate_pr_parameters(self, title: str, description: str, head_branch: str, base_branch: str) -> Dict[str, Any]:
        """Validate Pull Request parameters"""
        
        # Validate title
        if not title or not title.strip():
            return {
                'is_valid': False,
                'message': 'PR title cannot be empty'
            }
        
        if len(title) > 256:
            return {
                'is_valid': False,
                'message': 'PR title too long (max 256 characters)'
            }
        
        # Validate branches
        if not head_branch or not head_branch.strip():
            return {
                'is_valid': False,
                'message': 'Head branch cannot be empty'
            }
        
        if not base_branch or not base_branch.strip():
            return {
                'is_valid': False,
                'message': 'Base branch cannot be empty'
            }
        
        if head_branch == base_branch:
            return {
                'is_valid': False,
                'message': 'Head branch and base branch cannot be the same'
            }
        
        # Validate branch names
        head_validation = self.validate_branch_name(head_branch)
        if not head_validation['is_valid']:
            return {
                'is_valid': False,
                'message': f'Invalid head branch name: {head_validation["message"]}'
            }
        
        base_validation = self.validate_branch_name(base_branch)
        if not base_validation['is_valid']:
            return {
                'is_valid': False,
                'message': f'Invalid base branch name: {base_validation["message"]}'
            }
        
        # Validate description length (GitHub limit is ~65536 characters)
        if description and len(description) > 65000:
            return {
                'is_valid': False,
                'message': 'PR description too long (max ~65000 characters)'
            }
        
        return {
            'is_valid': True,
            'message': 'PR parameters are valid'
        }
    
    def _generate_ai_summary(self, data: Dict[str, Any]) -> str:
        """Generate AI summary of repository data"""
        
        summary_prompt = f"""
        Create a concise summary of this GitHub repository for development planning:

        REPOSITORY DATA:
        {json.dumps(data, indent=2, default=str)}

        Focus on:
        1. Repository purpose and main functionality
        2. Technology stack and languages used
        3. Recent development activity
        4. Project structure and organization
        5. Current state and development status

        Keep it concise but informative (max 300 words).
        """
        
        return self.call_openai(summary_prompt)
    
    def clone_repository(self, repo_url: str, local_path: str) -> Dict[str, Any]:
        """Clone repository to local path (for development)"""
        
        try:
            import git
            
            self.log_message(f"Cloning repository to {local_path}")
            
            # Clone the repository
            repo = git.Repo.clone_from(repo_url, local_path)
            
            return {
                'status': 'success',
                'local_path': local_path,
                'branch': repo.active_branch.name,
                'message': 'Repository cloned successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to clone repository: {str(e)}'
            }
    
    def get_file_diff(self, repo_url: str, file_path: str, commit1: str, commit2: str) -> Dict[str, Any]:
        """Get diff between two commits for a specific file"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'File diff requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get comparison between commits
            comparison = repo_obj.compare(commit1, commit2)
            
            # Find the specific file in the diff
            file_diff = None
            for file in comparison.files:
                if file.filename == file_path:
                    file_diff = file
                    break
            
            if file_diff:
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'changes': file_diff.changes,
                    'additions': file_diff.additions,
                    'deletions': file_diff.deletions,
                    'patch': file_diff.patch
                }
            else:
                return {
                    'status': 'error',
                    'message': f'File {file_path} not found in diff'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get file diff: {str(e)}'
            }
    
    def search_code(self, repo_url: str, query: str) -> Dict[str, Any]:
        """Search for code within the repository"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Code search requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            # Search code in repository
            search_query = f"{query} repo:{owner}/{repo}"
            results = self.github_client.search_code(search_query)
            
            search_results = []
            for result in results[:10]:  # Limit to 10 results
                search_results.append({
                    'file_path': result.path,
                    'repository': result.repository.full_name,
                    'score': result.score,
                    'url': result.html_url
                })
            
            return {
                'status': 'success',
                'query': query,
                'results': search_results,
                'total_results': len(search_results)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to search code: {e}',
                'message': f'Unknown GitHub action: {action}'
            }

                
        except Exception as e:
            error_msg = f"Error in GitHub Manager: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _get_repository_summary(self, repo_url: str) -> Dict[str, Any]:
        """Get comprehensive repository summary with enhanced analysis"""
        
        try:
            repo_info = self._get_repo_info(repo_url)
            if not repo_info:
                return {
                    'status': 'error',
                    'message': 'Could not fetch repository information'
                }
            
            # Get additional repository data
            recent_commits = self._get_recent_commits(repo_url, 5)
            file_structure = self._list_repository_files(repo_url)
            
            # Enhanced analysis
            project_type = self.detect_project_type(repo_url)
            code_style = self.analyze_code_style(repo_url)
            frameworks = self.identify_frameworks(repo_url)
            dependencies = self.analyze_dependencies(repo_url)
            improvements = self.suggest_improvements(repo_url)
            
            # Create enhanced summary data
            summary_data = {
                'repository_info': repo_info,
                'recent_commits': recent_commits.get('commits', []),
                'file_structure': file_structure.get('files', []),
                'project_analysis': {
                    'project_type': project_type,
                    'code_style': code_style,
                    'frameworks': frameworks,
                    'dependencies': dependencies,
                    'improvement_suggestions': improvements
                }
            }
            
            summary = self._generate_ai_summary(summary_data)
            
            return {
                'status': 'success',
                'summary': summary,
                'raw_data': summary_data,
                'repo_info': repo_info,
                'project_analysis': summary_data['project_analysis']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get repository summary: {str(e)}'
            }
    
    def _get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """Get basic repository information"""
        
        try:
            # Extract owner/repo from URL
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return None
                
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                # Use authenticated API
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                
                return {
                    'name': repo_obj.name,
                    'full_name': repo_obj.full_name,
                    'description': repo_obj.description,
                    'language': repo_obj.language,
                    'languages': dict(repo_obj.get_languages()),
                    'stars': repo_obj.stargazers_count,
                    'forks': repo_obj.forks_count,
                    'open_issues': repo_obj.open_issues_count,
                    'created_at': repo_obj.created_at.isoformat(),
                    'updated_at': repo_obj.updated_at.isoformat(),
                    'default_branch': repo_obj.default_branch,
                    'topics': repo_obj.get_topics(),
                    'size': repo_obj.size
                }
            else:
                # Use public API
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'name': data.get('name'),
                        'full_name': data.get('full_name'),
                        'description': data.get('description'),
                        'language': data.get('language'),
                        'stars': data.get('stargazers_count'),
                        'forks': data.get('forks_count'),
                        'open_issues': data.get('open_issues_count'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'default_branch': data.get('default_branch'),
                        'size': data.get('size')
                    }
                
                return None
                
        except Exception as e:
            self.log_message(f"Error getting repo info: {str(e)}", "ERROR")
            return None
    
    def _get_file_content(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """Get content of a specific file"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                file_content = repo_obj.get_contents(file_path)
                
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'content': file_content.decoded_content.decode('utf-8'),
                    'size': file_content.size,
                    'sha': file_content.sha
                }
            else:
                # Use raw GitHub content
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
                response = requests.get(raw_url)
                
                if response.status_code == 200:
                    return {
                        'status': 'success',
                        'file_path': file_path,
                        'content': response.text,
                        'size': len(response.text)
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'File not found: {file_path}'
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get file content: {str(e)}'
            }
    
    def _list_repository_files(self, repo_url: str) -> Dict[str, Any]:
        """List files in the repository"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                contents = repo_obj.get_contents("")
                
                files = []
                self._collect_files_recursive(repo_obj, contents, files)
                
                return {
                    'status': 'success',
                    'files': files,
                    'total_files': len(files)
                }
            else:
                # Limited functionality without authentication
                return {
                    'status': 'limited',
                    'message': 'File listing requires GitHub token',
                    'files': []
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to list files: {str(e)}'
            }
    
    def _collect_files_recursive(self, repo_obj, contents, files, path=""):
        """Recursively collect all files in repository"""
        
        for content in contents:
            current_path = f"{path}/{content.name}" if path else content.name
            
            if content.type == "dir":
                try:
                    sub_contents = repo_obj.get_contents(content.path)
                    self._collect_files_recursive(repo_obj, sub_contents, files, current_path)
                except:
                    continue  # Skip directories we can't access
            else:
                files.append({
                    'path': content.path,
                    'name': content.name,
                    'size': content.size,
                    'type': content.type
                })
    
    def _get_recent_commits(self, repo_url: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent commits from repository"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                commits = repo_obj.get_commits()[:limit]
                
                commit_data = []
                for commit in commits:
                    commit_data.append({
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author': commit.commit.author.name,
                        'date': commit.commit.author.date.isoformat(),
                        'files_changed': len(commit.files) if commit.files else 0
                    })
                
                return {
                    'status': 'success',
                    'commits': commit_data,
                    'total_commits': len(commit_data)
                }
            else:
                # Use public API
                api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
                response = requests.get(api_url, params={'per_page': limit})
                
                if response.status_code == 200:
                    commits_data = response.json()
                    commit_data = []
                    
                    for commit in commits_data:
                        commit_data.append({
                            'sha': commit['sha'],
                            'message': commit['commit']['message'],
                            'author': commit['commit']['author']['name'],
                            'date': commit['commit']['author']['date']
                        })
                    
                    return {
                        'status': 'success',
                        'commits': commit_data,
                        'total_commits': len(commit_data)
                    }
                
                return {
                    'status': 'error',
                    'message': f'Failed to fetch commits from public API: {response.status_code}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get recent commits: {str(e)}'
            }
    def detect_project_type(self, repo_url: str) -> Dict[str, Any]:
        """Detect project type based on files and structure"""
        
        try:
            file_structure = self._list_repository_files(repo_url)
            if file_structure.get('status') != 'success':
                return {
                    'status': 'error',
                    'message': 'Could not analyze project structure'
                }
            
            files = file_structure.get('files', [])
            file_names = [f['name'] for f in files]
            file_paths = [f['path'] for f in files]
            
            project_types = []
            confidence_scores = {}
            
            # Python project detection
            python_indicators = [
                'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile',
                'manage.py', '__init__.py', 'main.py'
            ]
            python_score = sum(1 for indicator in python_indicators if indicator in file_names)
            python_files = sum(1 for path in file_paths if path.endswith('.py'))
            
            if python_score > 0 or python_files > 0:
                confidence = min(100, (python_score * 20) + (python_files * 2))
                project_types.append('Python')
                confidence_scores['Python'] = confidence
            
            # JavaScript/Node.js project detection
            js_indicators = [
                'package.json', 'package-lock.json', 'yarn.lock', 'node_modules',
                'webpack.config.js', 'gulpfile.js', 'gruntfile.js'
            ]
            js_score = sum(1 for indicator in js_indicators if indicator in file_names)
            js_files = sum(1 for path in file_paths if path.endswith(('.js', '.jsx', '.ts', '.tsx')))
            
            if js_score > 0 or js_files > 0:
                confidence = min(100, (js_score * 15) + (js_files * 2))
                project_types.append('JavaScript/Node.js')
                confidence_scores['JavaScript/Node.js'] = confidence
            
            # Web project detection
            web_indicators = ['index.html', 'index.htm', 'style.css', 'styles.css']
            web_files = sum(1 for path in file_paths if path.endswith(('.html', '.htm', '.css')))
            web_score = sum(1 for indicator in web_indicators if indicator in file_names)
            
            if web_score > 0 or web_files > 0:
                confidence = min(100, (web_score * 10) + (web_files * 3))
                project_types.append('Web')
                confidence_scores['Web'] = confidence
            
            # Java project detection
            java_indicators = ['pom.xml', 'build.gradle', 'gradlew', 'mvnw']
            java_files = sum(1 for path in file_paths if path.endswith('.java'))
            java_score = sum(1 for indicator in java_indicators if indicator in file_names)
            
            if java_score > 0 or java_files > 0:
                confidence = min(100, (java_score * 20) + (java_files * 2))
                project_types.append('Java')
                confidence_scores['Java'] = confidence
            
            # Docker project detection
            docker_indicators = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore']
            docker_score = sum(1 for indicator in docker_indicators if indicator in file_names)
            
            if docker_score > 0:
                confidence = min(100, docker_score * 25)
                project_types.append('Docker')
                confidence_scores['Docker'] = confidence
            
            # Determine primary project type
            primary_type = 'Unknown'
            if confidence_scores:
                primary_type = max(confidence_scores.keys(), key=lambda k: confidence_scores[k])
            
            return {
                'status': 'success',
                'primary_type': primary_type,
                'all_types': project_types,
                'confidence_scores': confidence_scores,
                'total_files_analyzed': len(files)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to detect project type: {str(e)}'
            }
    
    def analyze_code_style(self, repo_url: str) -> Dict[str, Any]:
        """Analyze code style and conventions used in the project"""
        
        try:
            # Get sample files for analysis
            file_structure = self._list_repository_files(repo_url)
            if file_structure.get('status') != 'success':
                return {
                    'status': 'error',
                    'message': 'Could not analyze code style'
                }
            
            files = file_structure.get('files', [])
            code_files = [f for f in files if f['path'].endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.cs'))]
            
            style_analysis = {
                'indentation': 'unknown',
                'line_endings': 'unknown',
                'naming_convention': 'unknown',
                'file_organization': {},
                'config_files': []
            }
            
            # Analyze a few sample files
            sample_files = code_files[:5]  # Analyze first 5 code files
            indentation_votes = {'spaces': 0, 'tabs': 0}
            
            for file_info in sample_files:
                try:
                    content_result = self._get_file_content(repo_url, file_info['path'])
                    if content_result.get('status') == 'success':
                        content = content_result.get('content', '')
                        
                        # Analyze indentation
                        lines = content.split('\n')
                        for line in lines[:20]:  # Check first 20 lines
                            if line.startswith('    '):  # 4 spaces
                                indentation_votes['spaces'] += 1
                            elif line.startswith('\t'):  # Tab
                                indentation_votes['tabs'] += 1
                                
                except Exception:
                    continue
            
            # Determine indentation style
            if indentation_votes['spaces'] > indentation_votes['tabs']:
                style_analysis['indentation'] = 'spaces (4)'
            elif indentation_votes['tabs'] > indentation_votes['spaces']:
                style_analysis['indentation'] = 'tabs'
            
            # Check for style configuration files
            style_config_files = [
                '.eslintrc', '.eslintrc.js', '.eslintrc.json',
                '.prettierrc', '.prettierrc.js', '.prettierrc.json',
                'pyproject.toml', 'setup.cfg', '.flake8',
                '.editorconfig', 'tslint.json'
            ]
            
            file_names = [f['name'] for f in files]
            found_configs = [config for config in style_config_files if config in file_names]
            style_analysis['config_files'] = found_configs
            
            # Analyze file organization
            directories = {}
            for file_info in files:
                path_parts = file_info['path'].split('/')
                if len(path_parts) > 1:
                    dir_name = path_parts[0]
                    directories[dir_name] = directories.get(dir_name, 0) + 1
            
            style_analysis['file_organization'] = directories
            
            return {
                'status': 'success',
                'style_analysis': style_analysis,
                'files_analyzed': len(sample_files),
                'has_style_config': len(found_configs) > 0
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to analyze code style: {str(e)}'
            }
    
    def identify_frameworks(self, repo_url: str) -> Dict[str, Any]:
        """Identify frameworks and libraries used in the project"""
        
        try:
            file_structure = self._list_repository_files(repo_url)
            if file_structure.get('status') != 'success':
                return {
                    'status': 'error',
                    'message': 'Could not analyze frameworks'
                }
            
            files = file_structure.get('files', [])
            file_names = [f['name'] for f in files]
            frameworks = {}
            
            # Check package.json for JavaScript frameworks
            if 'package.json' in file_names:
                try:
                    package_content = self._get_file_content(repo_url, 'package.json')
                    if package_content.get('status') == 'success':
                        import json
                        package_data = json.loads(package_content.get('content', '{}'))
                        
                        dependencies = {}
                        dependencies.update(package_data.get('dependencies', {}))
                        dependencies.update(package_data.get('devDependencies', {}))
                        
                        js_frameworks = {
                            'React': ['react', 'react-dom'],
                            'Vue.js': ['vue', '@vue/cli'],
                            'Angular': ['@angular/core', '@angular/cli'],
                            'Express.js': ['express'],
                            'Next.js': ['next'],
                            'Nuxt.js': ['nuxt'],
                            'Svelte': ['svelte'],
                            'Gatsby': ['gatsby'],
                            'Webpack': ['webpack'],
                            'Vite': ['vite'],
                            'TypeScript': ['typescript'],
                            'Jest': ['jest'],
                            'Mocha': ['mocha'],
                            'Cypress': ['cypress']
                        }
                        
                        for framework, indicators in js_frameworks.items():
                            for indicator in indicators:
                                if indicator in dependencies:
                                    frameworks[framework] = {
                                        'version': dependencies[indicator],
                                        'type': 'JavaScript/Node.js',
                                        'category': 'framework' if framework in ['React', 'Vue.js', 'Angular', 'Express.js'] else 'tool'
                                    }
                                    break
                                    
                except Exception:
                    pass
            
            # Check requirements.txt for Python frameworks
            if 'requirements.txt' in file_names:
                try:
                    req_content = self._get_file_content(repo_url, 'requirements.txt')
                    if req_content.get('status') == 'success':
                        requirements = req_content.get('content', '').split('\n')
                        
                        python_frameworks = {
                            'Django': ['django', 'Django'],
                            'Flask': ['flask', 'Flask'],
                            'FastAPI': ['fastapi', 'FastAPI'],
                            'Pandas': ['pandas'],
                            'NumPy': ['numpy'],
                            'TensorFlow': ['tensorflow'],
                            'PyTorch': ['torch', 'pytorch'],
                            'Requests': ['requests'],
                            'SQLAlchemy': ['sqlalchemy', 'SQLAlchemy'],
                            'Pytest': ['pytest']
                        }
                        
                        for req_line in requirements:
                            req_line = req_line.strip()
                            if req_line and not req_line.startswith('#'):
                                package_name = req_line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                                
                                for framework, indicators in python_frameworks.items():
                                    if package_name.lower() in [ind.lower() for ind in indicators]:
                                        frameworks[framework] = {
                                            'requirement': req_line,
                                            'type': 'Python',
                                            'category': 'framework' if framework in ['Django', 'Flask', 'FastAPI'] else 'library'
                                        }
                                        break
                                        
                except Exception:
                    pass
            
            # Check for specific framework files
            framework_files = {
                'Django': ['manage.py', 'settings.py'],
                'Flask': ['app.py', 'wsgi.py'],
                'React': ['src/App.js', 'src/App.jsx', 'public/index.html'],
                'Vue.js': ['src/main.js', 'vue.config.js'],
                'Angular': ['angular.json', 'src/main.ts'],
                'Spring Boot': ['pom.xml', 'src/main/java'],
                'Laravel': ['artisan', 'composer.json'],
                'Ruby on Rails': ['Gemfile', 'config/routes.rb']
            }
            
            file_paths = [f['path'] for f in files]
            for framework, indicators in framework_files.items():
                if framework not in frameworks:  # Don't override if already detected
                    for indicator in indicators:
                        if indicator in file_paths or any(path.endswith(indicator) for path in file_paths):
                            frameworks[framework] = {
                                'detected_by': 'file_structure',
                                'indicator_file': indicator,
                                'category': 'framework'
                            }
                            break
            
            return {
                'status': 'success',
                'frameworks': frameworks,
                'total_frameworks': len(frameworks),
                'categories': {
                    'frameworks': [name for name, info in frameworks.items() if info.get('category') == 'framework'],
                    'libraries': [name for name, info in frameworks.items() if info.get('category') == 'library'],
                    'tools': [name for name, info in frameworks.items() if info.get('category') == 'tool']
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to identify frameworks: {str(e)}'
            }
    
    def analyze_dependencies(self, repo_url: str) -> Dict[str, Any]:
        """Analyze project dependencies and their versions"""
        
        try:
            file_structure = self._list_repository_files(repo_url)
            if file_structure.get('status') != 'success':
                return {
                    'status': 'error',
                    'message': 'Could not analyze dependencies'
                }
            
            files = file_structure.get('files', [])
            file_names = [f['name'] for f in files]
            dependencies = {
                'production': {},
                'development': {},
                'total_count': 0,
                'outdated_risk': 'unknown',
                'security_concerns': []
            }
            
            # Analyze package.json dependencies
            if 'package.json' in file_names:
                try:
                    package_content = self._get_file_content(repo_url, 'package.json')
                    if package_content.get('status') == 'success':
                        import json
                        package_data = json.loads(package_content.get('content', '{}'))
                        
                        prod_deps = package_data.get('dependencies', {})
                        dev_deps = package_data.get('devDependencies', {})
                        
                        dependencies['production'].update(prod_deps)
                        dependencies['development'].update(dev_deps)
                        dependencies['total_count'] += len(prod_deps) + len(dev_deps)
                        
                        # Check for potentially outdated or risky packages
                        risky_patterns = ['*', '^0.', '~0.', 'latest', 'beta', 'alpha']
                        for dep, version in {**prod_deps, **dev_deps}.items():
                            for pattern in risky_patterns:
                                if pattern in str(version):
                                    dependencies['security_concerns'].append(f"{dep}@{version} - potentially unstable version")
                                    
                except Exception:
                    pass
            
            # Analyze requirements.txt dependencies
            if 'requirements.txt' in file_names:
                try:
                    req_content = self._get_file_content(repo_url, 'requirements.txt')
                    if req_content.get('status') == 'success':
                        requirements = req_content.get('content', '').split('\n')
                        python_deps = {}
                        
                        for req_line in requirements:
                            req_line = req_line.strip()
                            if req_line and not req_line.startswith('#'):
                                if '==' in req_line:
                                    name, version = req_line.split('==', 1)
                                    python_deps[name.strip()] = version.strip()
                                elif '>=' in req_line:
                                    name, version = req_line.split('>=', 1)
                                    python_deps[name.strip()] = f">={version.strip()}"
                                else:
                                    python_deps[req_line] = 'unspecified'
                        
                        dependencies['production'].update(python_deps)
                        dependencies['total_count'] += len(python_deps)
                        
                except Exception:
                    pass
            
            # Analyze Pipfile dependencies
            if 'Pipfile' in file_names:
                try:
                    pipfile_content = self._get_file_content(repo_url, 'Pipfile')
                    if pipfile_content.get('status') == 'success':
                        content = pipfile_content.get('content', '')
                        # Simple parsing for common patterns
                        lines = content.split('\n')
                        in_packages = False
                        in_dev_packages = False
                        
                        for line in lines:
                            line = line.strip()
                            if line == '[packages]':
                                in_packages = True
                                in_dev_packages = False
                            elif line == '[dev-packages]':
                                in_packages = False
                                in_dev_packages = True
                            elif line.startswith('['):
                                in_packages = False
                                in_dev_packages = False
                            elif '=' in line and (in_packages or in_dev_packages):
                                try:
                                    name, version = line.split('=', 1)
                                    name = name.strip().strip('"\'')
                                    version = version.strip().strip('"\'')
                                    
                                    if in_packages:
                                        dependencies['production'][name] = version
                                    else:
                                        dependencies['development'][name] = version
                                    dependencies['total_count'] += 1
                                except:
                                    pass
                                    
                except Exception:
                    pass
            
            # Analyze pom.xml for Java projects
            if 'pom.xml' in file_names:
                try:
                    pom_content = self._get_file_content(repo_url, 'pom.xml')
                    if pom_content.get('status') == 'success':
                        content = pom_content.get('content', '')
                        # Simple XML parsing for dependencies
                        import re
                        
                        # Find dependency blocks
                        dep_pattern = r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?<version>(.*?)</version>.*?</dependency>'
                        matches = re.findall(dep_pattern, content, re.DOTALL)
                        
                        for group_id, artifact_id, version in matches:
                            dep_name = f"{group_id.strip()}:{artifact_id.strip()}"
                            dependencies['production'][dep_name] = version.strip()
                            dependencies['total_count'] += 1
                            
                except Exception:
                    pass
            
            # Assess overall dependency health
            if dependencies['total_count'] > 50:
                dependencies['outdated_risk'] = 'high'
            elif dependencies['total_count'] > 20:
                dependencies['outdated_risk'] = 'medium'
            else:
                dependencies['outdated_risk'] = 'low'
            
            return {
                'status': 'success',
                'dependencies': dependencies,
                'summary': {
                    'total_dependencies': dependencies['total_count'],
                    'production_count': len(dependencies['production']),
                    'development_count': len(dependencies['development']),
                    'risk_level': dependencies['outdated_risk'],
                    'security_concerns_count': len(dependencies['security_concerns'])
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to analyze dependencies: {str(e)}'
            }
    
    def suggest_improvements(self, repo_url: str) -> Dict[str, Any]:
        """Suggest improvements based on repository analysis"""
        
        try:
            # Gather data for analysis
            file_structure = self._list_repository_files(repo_url)
            project_type = self.detect_project_type(repo_url)
            code_style = self.analyze_code_style(repo_url)
            frameworks = self.identify_frameworks(repo_url)
            dependencies = self.analyze_dependencies(repo_url)
            
            if any(result.get('status') != 'success' for result in [file_structure, project_type, code_style, frameworks, dependencies]):
                return {
                    'status': 'error',
                    'message': 'Could not gather sufficient data for improvement suggestions'
                }
            
            suggestions = {
                'documentation': [],
                'code_quality': [],
                'security': [],
                'performance': [],
                'maintenance': [],
                'testing': []
            }
            
            files = file_structure.get('files', [])
            file_names = [f['name'] for f in files]
            file_paths = [f['path'] for f in files]
            
            # Documentation suggestions
            if 'README.md' not in file_names and 'README.rst' not in file_names:
                suggestions['documentation'].append({
                    'priority': 'high',
                    'suggestion': 'Add a README.md file to document the project',
                    'reason': 'Missing project documentation'
                })
            
            if 'CONTRIBUTING.md' not in file_names:
                suggestions['documentation'].append({
                    'priority': 'medium',
                    'suggestion': 'Add CONTRIBUTING.md to guide contributors',
                    'reason': 'No contribution guidelines found'
                })
            
            if 'LICENSE' not in file_names and 'LICENSE.txt' not in file_names:
                suggestions['documentation'].append({
                    'priority': 'medium',
                    'suggestion': 'Add a LICENSE file to clarify usage rights',
                    'reason': 'No license file found'
                })
            
            # Code quality suggestions
            style_config_files = code_style.get('style_analysis', {}).get('config_files', [])
            if not style_config_files:
                primary_type = project_type.get('primary_type', '')
                if 'Python' in primary_type:
                    suggestions['code_quality'].append({
                        'priority': 'medium',
                        'suggestion': 'Add .flake8 or pyproject.toml for code style configuration',
                        'reason': 'No Python code style configuration found'
                    })
                elif 'JavaScript' in primary_type:
                    suggestions['code_quality'].append({
                        'priority': 'medium',
                        'suggestion': 'Add .eslintrc and .prettierrc for code style configuration',
                        'reason': 'No JavaScript code style configuration found'
                    })
            
            # Security suggestions
            security_concerns = dependencies.get('dependencies', {}).get('security_concerns', [])
            if security_concerns:
                suggestions['security'].append({
                    'priority': 'high',
                    'suggestion': 'Review and fix dependency version constraints',
                    'reason': f'Found {len(security_concerns)} potentially risky dependency versions',
                    'details': security_concerns[:3]  # Show first 3 concerns
                })
            
            if '.env' in file_names:
                suggestions['security'].append({
                    'priority': 'high',
                    'suggestion': 'Ensure .env file is in .gitignore and not committed',
                    'reason': 'Environment file detected - may contain sensitive data'
                })
            
            if '.gitignore' not in file_names:
                suggestions['security'].append({
                    'priority': 'medium',
                    'suggestion': 'Add .gitignore file to exclude sensitive files',
                    'reason': 'No .gitignore file found'
                })
            
            # Testing suggestions
            test_files = [f for f in file_paths if 'test' in f.lower() or f.endswith(('_test.py', '.test.js', '.spec.js'))]
            if not test_files:
                suggestions['testing'].append({
                    'priority': 'high',
                    'suggestion': 'Add unit tests to improve code reliability',
                    'reason': 'No test files detected'
                })
            
            # CI/CD suggestions
            ci_files = ['.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml']
            has_ci = any(ci_file in file_paths for ci_file in ci_files)
            if not has_ci:
                suggestions['maintenance'].append({
                    'priority': 'medium',
                    'suggestion': 'Set up CI/CD pipeline for automated testing and deployment',
                    'reason': 'No CI/CD configuration detected'
                })
            
            # Performance suggestions
            dep_count = dependencies.get('summary', {}).get('total_dependencies', 0)
            if dep_count > 50:
                suggestions['performance'].append({
                    'priority': 'medium',
                    'suggestion': 'Review and optimize dependencies to reduce bundle size',
                    'reason': f'High number of dependencies ({dep_count}) may impact performance'
                })
            
            # Docker suggestions
            if 'Dockerfile' not in file_names:
                suggestions['maintenance'].append({
                    'priority': 'low',
                    'suggestion': 'Consider adding Dockerfile for containerization',
                    'reason': 'No Docker configuration found'
                })
            
            # Calculate priority summary
            priority_counts = {'high': 0, 'medium': 0, 'low': 0}
            total_suggestions = 0
            
            for category, category_suggestions in suggestions.items():
                for suggestion in category_suggestions:
                    priority = suggestion.get('priority', 'low')
                    priority_counts[priority] += 1
                    total_suggestions += 1
            
            return {
                'status': 'success',
                'suggestions': suggestions,
                'summary': {
                    'total_suggestions': total_suggestions,
                    'high_priority': priority_counts['high'],
                    'medium_priority': priority_counts['medium'],
                    'low_priority': priority_counts['low'],
                    'categories_with_suggestions': len([cat for cat, suggs in suggestions.items() if suggs])
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to generate improvement suggestions: {str(e)}'
            } 
   
    def validate_branch_name(self, branch_name: str) -> Dict[str, Any]:
        """Validate branch name using GitOperations"""
        try:
            is_valid, error_message = self.git_operations.validate_branch_name(branch_name)
            
            return {
                'status': 'success' if is_valid else 'error',
                'is_valid': is_valid,
                'branch_name': branch_name,
                'error_message': error_message,
                'message': 'Branch name is valid' if is_valid else f'Invalid branch name: {error_message}'
            }
            
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.VALIDATION, ErrorSeverity.MEDIUM,
                {'operation': 'validate_branch_name', 'branch_name': branch_name}
            )
            return {
                'status': 'error',
                'is_valid': False,
                'error': f'Branch name validation failed: {str(e)}',
                'error_id': error_id
            }
    
    def calculate_changes_diff(self, original_content: str, new_content: str, file_path: str) -> Dict[str, Any]:
        """Calculate file differences using GitOperations"""
        try:
            diff_result = self.git_operations.calculate_file_diff(original_content, new_content, file_path)
            
            return {
                'status': 'success',
                'diff_result': diff_result,
                'has_changes': diff_result.get('has_changes', False),
                'change_summary': {
                    'additions': diff_result.get('additions', 0),
                    'deletions': diff_result.get('deletions', 0),
                    'total_changes': diff_result.get('total_changes', 0),
                    'change_type': diff_result.get('change_type', 'unknown')
                }
            }
            
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.FILE_OPERATION, ErrorSeverity.MEDIUM,
                {'operation': 'calculate_changes_diff', 'file_path': file_path}
            )
            return {
                'status': 'error',
                'error': f'Failed to calculate diff: {str(e)}',
                'error_id': error_id
            }
    
    def generate_commit_message(self, changes_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate commit message using GitOperations"""
        try:
            commit_message = self.git_operations.create_commit_message(changes_summary)
            
            return {
                'status': 'success',
                'commit_message': commit_message,
                'changes_summary': changes_summary
            }
            
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.GENERAL, ErrorSeverity.MEDIUM,
                {'operation': 'generate_commit_message', 'changes_count': len(changes_summary.get('files_changed', []))}
            )
            return {
                'status': 'error',
                'error': f'Failed to generate commit message: {str(e)}',
                'error_id': error_id,
                'fallback_message': 'Update files'
            }