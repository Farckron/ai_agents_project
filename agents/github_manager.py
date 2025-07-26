from typing import Dict, Any, List
import requests
import json
import time
from github import Github, GithubException, UnknownObjectException
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
        token = Config.GITHUB_TOKEN
        if token:
            try:
                self.github_client = Github(token)
                # Test the token (this will require read:user & user:email)
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
                self.log_message("GitHub token validation failed – some features limited", "WARNING")
        else:
            self.github_client = None
            self.log_message("No GitHub token provided – some features limited", "WARNING")
        
        self.repo_cache = {}
        self.log_message("GitHub Manager initialized")
    
    def handle_github_api_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        return self.error_handler.handle_github_api_errors(error, context)
    
    def handle_authentication_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        return self.error_handler.handle_authentication_errors(error, context)
    
    def handle_rate_limit_errors(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        return self.error_handler.handle_rate_limit_errors(error, context)
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GitHub repository operations
        """
        try:
            action  = task.get('action', 'get_repo_summary')
            raw_url = task.get('repo_url', Config.GITHUB_REPO_URL or "").rstrip("/")
            owner, repo = raw_url.rsplit("/", 1)
            # strip a trailing “.git” if present
            if repo.lower().endswith(".git"):
                repo = repo[:-4]

            # fetch the repo object
            gh_repo = self.github_client.get_repo(f"{owner}/{repo}")

            self.log_message(f"Processing GitHub action: {action}")
            
            if action == 'get_repo_summary':
                return self._get_repository_summary(raw_url)
            elif action == 'get_file_content':
                return self._get_file_content(raw_url, task.get('file_path', ''))
            elif action == 'list_files':
                return self._list_repository_files(raw_url)
            elif action == 'get_recent_commits':
                return self._get_recent_commits(raw_url, task.get('limit', 10))
            elif action == 'get_issues':
                return self._get_repository_issues(raw_url)
            elif action == 'create_branch':
                return self.create_branch(raw_url, task.get('branch_name', ''), task.get('base_branch', 'main'))
            elif action == 'validate_branch_name':
                return self.validate_branch_name(task.get('branch_name', ''))
            elif action == 'generate_unique_branch_name':
                return self.generate_unique_branch_name(task.get('base_name', ''), raw_url)
            elif action in ('commit_changes', 'commit_multiple_files'):
                return self.commit_multiple_files(
                    raw_url,
                    task.get('branch_name', 'main'),
                    task.get('files', {}),
                    task.get('message', '')
                )
            elif action == 'update_file_content':
                return self.update_file_content(
                    raw_url,
                    task.get('branch_name', 'main'),
                    task.get('file_path', ''),
                    task.get('content', ''),
                    task.get('message', '')
                )
            elif action == 'delete_file':
                return self.delete_file(
                    raw_url,
                    task.get('branch_name', 'main'),
                    task.get('file_path', ''),
                    task.get('message', '')
                )
            elif action == 'create_pull_request':
                return self.create_pull_request(
                    raw_url,
                    task.get('branch_name', ''),
                    task.get('title', ''),
                    task.get('description', ''),
                    task.get('base_branch', 'main')
                )
            elif action == 'generate_pr_description':
                return {
                    'status': 'success',
                    'description': self.generate_pr_description(
                        raw_url,
                        task.get('branch_name', ''),
                        task.get('base_branch', 'main')
                    )
                }
            elif action == 'validate_pr_parameters':
                return self.validate_pr_parameters(
                    task.get('title', ''),
                    task.get('description', ''),
                    task.get('head_branch', ''),
                    task.get('base_branch', '')
                )
            else:
                return {'status': 'error', 'message': f'Unknown GitHub action: {action}'}
                
        except Exception as e:
            return {'status': 'error', 'error': f'Failed to process GitHub task: {str(e)}'}
    
    # …all other methods (create_branch, commit_multiple_files, etc.) remain unchanged…
