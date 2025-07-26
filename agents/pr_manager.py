from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from .base_agent import BaseAgent
from .github_manager import GitHubManager
from utils.structured_logger import get_structured_logger, log_pr_start, log_pr_step, log_pr_complete, LogLevel
from utils.git_operations import GitOperations
from utils.error_handler import ErrorHandler, ErrorType, ErrorSeverity

class PRManager(BaseAgent):
    def __init__(self):
        super().__init__("pr_manager")
        
        # Initialize GitHub manager for repository operations
        self.github_manager = GitHubManager()
        
        # Initialize Git operations utility
        self.git_operations = GitOperations()
        
        # Initialize error handler
        self.error_handler = ErrorHandler("pr_manager")
        
        # Initialize structured logger
        self.structured_logger = get_structured_logger("pr_manager")
        
        # Track PR workflows
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.completed_workflows: List[Dict[str, Any]] = []
        
        self.log_message("PR Manager initialized")
        try:
            self.structured_logger.log_structured(
                LogLevel.INFO,
                "SYSTEM",
                "PR Manager initialized with GitOperations and ErrorHandler",
                component="pr_manager"
            )
        except Exception as e:
            self.log_message(f"Structured logging failed: {str(e)}", "WARNING")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main task processing method for PR operations
        
        Expected task structure:
        {
            'action': 'create_pr' | 'process_pr_request' | 'get_workflow_status',
            'user_request': str,
            'repo_url': str,
            'options': {
                'branch_name': str (optional),
                'pr_title': str (optional), 
                'pr_description': str (optional),
                'base_branch': str (default: main),
                'auto_merge': bool (default: false)
            }
        }
        """
        try:
            action = task.get('action', 'process_pr_request')
            
            self.log_message(f"Processing PR action: {action}")
            
            if action == 'process_pr_request':
                return self.process_pr_request(
                    user_request=task.get('user_request', ''),
                    repo_url=task.get('repo_url', ''),
                    options=task.get('options', {})
                )
            elif action == 'get_workflow_status':
                return self.get_workflow_status(task.get('workflow_id', ''))
            elif action == 'create_pr':
                return self.create_pull_request(
                    repo_url=task.get('repo_url', ''),
                    branch_name=task.get('branch_name', ''),
                    title=task.get('title', ''),
                    description=task.get('description', ''),
                    base_branch=task.get('base_branch', 'main')
                )
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown PR action: {action}'
                }
                
        except Exception as e:
            error_msg = f"Error in PR Manager: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def process_pr_request(self, user_request: str, repo_url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user request to create a PR with code changes
        
        This is the main workflow method that coordinates the entire PR creation process
        """
        if options is None:
            options = {}
            
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Initialize workflow tracking
        workflow = {
            'workflow_id': workflow_id,
            'user_request': user_request,
            'repo_url': repo_url,
            'options': options,
            'status': 'processing',
            'steps': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Log PR workflow start
        log_pr_start(
            workflow_id=workflow_id,
            repo_url=repo_url,
            user_request=user_request,
            options=options
        )
        
        try:
            # Step 1: Validate repository access
            self.log_message(f"Starting PR workflow {workflow_id}")
            
            with self.structured_logger.performance_timer("validate_repository_access", workflow_id=workflow_id):
                validation_result = self._validate_repository_access(repo_url)
            
            self._add_workflow_step(workflow_id, 'validate_repository', validation_result)
            log_pr_step(
                workflow_id=workflow_id,
                step_name="validate_repository",
                status=validation_result['status'],
                result=validation_result
            )
            
            if validation_result['status'] != 'success':
                log_pr_complete(
                    workflow_id=workflow_id,
                    status='failed',
                    error_message=validation_result['message']
                )
                return self._complete_workflow(workflow_id, 'failed', validation_result['message'])
            
            # Step 2: Generate branch name if not provided
            branch_name = options.get('branch_name')
            if not branch_name:
                branch_name = self.generate_branch_name(user_request)
                self._add_workflow_step(workflow_id, 'generate_branch_name', {
                    'status': 'success',
                    'branch_name': branch_name
                })
            
            # Step 3: Analyze repository context
            with self.structured_logger.performance_timer("analyze_repository", workflow_id=workflow_id):
                repo_analysis = self.github_manager.process_task({
                    'action': 'get_repo_summary',
                    'repo_url': repo_url
                })
            
            self._add_workflow_step(workflow_id, 'analyze_repository', repo_analysis)
            log_pr_step(
                workflow_id=workflow_id,
                step_name="analyze_repository",
                status=repo_analysis.get('status', 'unknown'),
                result=repo_analysis
            )
            
            # Step 4: Generate PR description
            pr_title = options.get('pr_title', f"Automated changes: {user_request[:50]}...")
            pr_description = options.get('pr_description')
            if not pr_description:
                pr_description = self.create_pr_description(user_request, repo_analysis.get('summary', ''))
                self._add_workflow_step(workflow_id, 'generate_pr_description', {
                    'status': 'success',
                    'description': pr_description
                })
            
            # Step 5: Prepare workflow for code generation (this will be handled by other agents)
            workflow_result = {
                'status': 'ready_for_changes',
                'workflow_id': workflow_id,
                'branch_name': branch_name,
                'pr_title': pr_title,
                'pr_description': pr_description,
                'repo_analysis': repo_analysis,
                'message': 'PR workflow prepared. Ready for code changes to be applied.',
                'next_steps': [
                    'Generate code changes using Code Agent',
                    'Create branch and commit changes',
                    'Create Pull Request'
                ]
            }
            
            self._add_workflow_step(workflow_id, 'prepare_workflow', {
                'status': 'success',
                'result': workflow_result
            })
            
            return workflow_result
            
        except Exception as e:
            error_msg = f"Error in PR workflow: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return self._complete_workflow(workflow_id, 'failed', error_msg)
    
    def execute_pr_workflow(self, workflow_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the final steps of PR creation with the provided changes
        
        Args:
            workflow_id: The workflow ID from process_pr_request
            changes: Dictionary containing file changes to commit
        """
        if workflow_id not in self.active_workflows:
            return {
                'status': 'error',
                'message': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.active_workflows[workflow_id]
        
        try:
            repo_url = workflow['repo_url']
            branch_name = None
            pr_title = None
            pr_description = None
            
            # Extract workflow data from steps
            for step in workflow['steps']:
                if step['step_name'] == 'generate_branch_name':
                    branch_name = step['result'].get('branch_name')
                elif step['step_name'] == 'prepare_workflow':
                    result = step['result'].get('result', {})
                    branch_name = result.get('branch_name')
                    pr_title = result.get('pr_title')
                    pr_description = result.get('pr_description')
            
            if not branch_name:
                return self._complete_workflow(workflow_id, 'failed', 'Branch name not found in workflow')
            
            # Step 1: Create branch
            branch_result = self.github_manager.process_task({
                'action': 'create_branch',
                'repo_url': repo_url,
                'branch_name': branch_name
            })
            self._add_workflow_step(workflow_id, 'create_branch', branch_result)
            
            if branch_result['status'] != 'success':
                return self._complete_workflow(workflow_id, 'failed', f"Failed to create branch: {branch_result.get('error', 'Unknown error')}")
            
            # Step 2: Commit changes
            commit_message = f"Automated changes: {workflow['user_request']}"
            commit_result = self.github_manager.process_task({
                'action': 'commit_changes',
                'repo_url': repo_url,
                'files': changes.get('files', {}),
                'message': commit_message
            })
            self._add_workflow_step(workflow_id, 'commit_changes', commit_result)
            
            if commit_result['status'] != 'success':
                return self._complete_workflow(workflow_id, 'failed', f"Failed to commit changes: {commit_result.get('error', 'Unknown error')}")
            
            # Step 3: Create Pull Request
            pr_result = self.create_pull_request(
                repo_url=repo_url,
                branch_name=branch_name,
                title=pr_title,
                description=pr_description,
                base_branch=workflow['options'].get('base_branch', 'main')
            )
            self._add_workflow_step(workflow_id, 'create_pull_request', pr_result)
            
            if pr_result['status'] == 'success':
                return self._complete_workflow(workflow_id, 'completed', 'PR created successfully', pr_result)
            else:
                return self._complete_workflow(workflow_id, 'failed', f"Failed to create PR: {pr_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Error executing PR workflow: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return self._complete_workflow(workflow_id, 'failed', error_msg)
    
    def generate_branch_name(self, request_summary: str) -> str:
        """Generate a unique branch name based on the request summary"""
        try:
            # Sanitize the request summary using GitOperations
            sanitized_summary = self.git_operations.sanitize_user_input(request_summary, "branch_name")
            
            # Generate unique branch name using GitOperations
            base_name = f"automated-{sanitized_summary}"
            branch_name = self.git_operations.generate_unique_branch_name(base_name, "")
            
            # Validate the generated branch name
            is_valid, error_msg = self.git_operations.validate_branch_name(branch_name)
            if not is_valid:
                self.log_message(f"Generated branch name invalid: {error_msg}", "WARNING")
                # Use fallback
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                branch_name = f"automated-changes-{timestamp}"
            
            self.log_message(f"Generated branch name: {branch_name}")
            return branch_name
            
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.GENERAL, ErrorSeverity.MEDIUM,
                {'operation': 'generate_branch_name', 'request_summary': request_summary[:100]}
            )
            # Fallback to timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            fallback_name = f"automated-changes-{timestamp}"
            self.log_message(f"Using fallback branch name: {fallback_name} (Error ID: {error_id})", "WARNING")
            return fallback_name
    
    def create_pr_description(self, user_request: str, repo_context: str = "") -> str:
        """Generate a detailed PR description based on the user request and repository context"""
        try:
            description_prompt = f"""
            Create a professional Pull Request description for the following automated changes:

            USER REQUEST: {user_request}

            REPOSITORY CONTEXT: {repo_context[:500]}...

            The description should include:
            1. A clear summary of what changes were made
            2. Why these changes were necessary
            3. Any relevant technical details
            4. Testing considerations if applicable

            Keep it professional and concise (max 300 words).
            Format it in markdown.
            """
            
            description = self.call_openai(description_prompt)
            
            # Add automated footer
            footer = "\n\n---\n*This PR was created automatically by the AI Agent System*"
            
            return description + footer
            
        except Exception as e:
            self.log_message(f"Error generating PR description: {str(e)}", "ERROR")
            return f"""# Automated Changes

## Summary
{user_request}

## Details
This PR contains automated changes generated by the AI Agent System.

---
*This PR was created automatically by the AI Agent System*
"""
    
    def create_pull_request(self, repo_url: str, branch_name: str, title: str, description: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a Pull Request using the GitHub Manager"""
        try:
            # Note: This method would need to be implemented in GitHubManager
            # For now, we'll return a placeholder response
            self.log_message(f"Creating PR: {title} from {branch_name} to {base_branch}")
            
            # This would be the actual implementation once GitHubManager is extended
            return {
                'status': 'success',
                'pr_url': f"{repo_url}/pull/123",  # Placeholder
                'pr_number': 123,  # Placeholder
                'title': title,
                'description': description,
                'branch_name': branch_name,
                'base_branch': base_branch,
                'message': 'Pull Request created successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to create Pull Request: {str(e)}'
            }
    
    def validate_changes(self, files_to_change: List[str], proposed_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate proposed changes before creating PR using GitOperations"""
        try:
            validation_results = {
                'valid_files': [],
                'invalid_files': [],
                'warnings': [],
                'overall_status': 'valid'
            }
            
            # Validate file paths using GitOperations
            for file_path in files_to_change:
                # Sanitize file path
                sanitized_path = self.git_operations.sanitize_user_input(file_path, "file_path")
                
                # Check file safety
                is_safe, warning = self.git_operations.check_file_safety(
                    sanitized_path, 
                    proposed_changes.get(file_path, "")
                )
                
                if is_safe:
                    validation_results['valid_files'].append(sanitized_path)
                    if warning:
                        validation_results['warnings'].append(f"File {sanitized_path}: {warning}")
                        validation_results['overall_status'] = 'warning'
                else:
                    validation_results['invalid_files'].append(sanitized_path)
                    validation_results['warnings'].append(f"File {sanitized_path}: {warning}")
                    validation_results['overall_status'] = 'invalid'
            
            # Additional content validation for each file
            for file_path, content in proposed_changes.items():
                if isinstance(content, str):
                    # Check file safety with content
                    is_safe, warning = self.git_operations.check_file_safety(file_path, content)
                    if not is_safe and warning:
                        validation_results['warnings'].append(f"Content validation for {file_path}: {warning}")
                        if validation_results['overall_status'] != 'invalid':
                            validation_results['overall_status'] = 'warning'
            
            return {
                'status': 'success',
                'validation': validation_results
            }
            
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.VALIDATION, ErrorSeverity.HIGH,
                {'operation': 'validate_changes', 'files_count': len(files_to_change)}
            )
            return {
                'status': 'error',
                'error': f'Validation failed: {str(e)}',
                'error_id': error_id
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        if workflow_id in self.active_workflows:
            return {
                'status': 'success',
                'workflow': self.active_workflows[workflow_id]
            }
        
        # Check completed workflows
        for workflow in self.completed_workflows:
            if workflow['workflow_id'] == workflow_id:
                return {
                    'status': 'success',
                    'workflow': workflow
                }
        
        return {
            'status': 'error',
            'message': f'Workflow {workflow_id} not found'
        }
    
    def _validate_repository_access(self, repo_url: str) -> Dict[str, Any]:
        """Validate that we have access to the repository using GitOperations"""
        try:
            # First validate repository access using GitOperations
            has_access, access_error = self.git_operations.validate_repository_access(repo_url)
            
            if not has_access:
                return {
                    'status': 'error',
                    'message': f"Repository access validation failed: {access_error}"
                }
            
            # Then use GitHub manager to test actual repository access
            repo_info = self.github_manager.process_task({
                'action': 'get_repo_summary',
                'repo_url': repo_url
            })
            
            if repo_info['status'] == 'success':
                return {
                    'status': 'success',
                    'message': 'Repository access validated successfully',
                    'validation_details': {
                        'git_operations_check': True,
                        'github_manager_check': True
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': f"GitHub Manager validation failed: {repo_info.get('error', 'Unknown error')}",
                    'validation_details': {
                        'git_operations_check': True,
                        'github_manager_check': False
                    }
                }
                
        except Exception as e:
            error_id = self.error_handler.log_error(
                e, ErrorType.GITHUB_API, ErrorSeverity.HIGH,
                {'operation': 'validate_repository_access', 'repo_url': repo_url}
            )
            return {
                'status': 'error',
                'message': f'Repository validation failed: {str(e)}',
                'error_id': error_id
            }
    
    def _add_workflow_step(self, workflow_id: str, step_name: str, result: Dict[str, Any]):
        """Add a step to the workflow tracking"""
        if workflow_id in self.active_workflows:
            step = {
                'step_name': step_name,
                'status': result.get('status', 'unknown'),
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.active_workflows[workflow_id]['steps'].append(step)
            self.active_workflows[workflow_id]['updated_at'] = datetime.now().isoformat()
    
    def _complete_workflow(self, workflow_id: str, status: str, message: str, result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete a workflow and move it to completed workflows"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['status'] = status
            workflow['completion_message'] = message
            workflow['completed_at'] = datetime.now().isoformat()
            
            if result:
                workflow['final_result'] = result
            
            # Move to completed workflows
            self.completed_workflows.append(workflow)
            del self.active_workflows[workflow_id]
            
            self.log_message(f"Workflow {workflow_id} completed with status: {status}")
            
            return {
                'status': status,
                'workflow_id': workflow_id,
                'message': message,
                'result': result
            }
        
        return {
            'status': 'error',
            'message': f'Workflow {workflow_id} not found'
        }
    

    
    def get_active_workflows(self) -> Dict[str, Any]:
        """Get all active workflows"""
        return {
            'status': 'success',
            'active_workflows': list(self.active_workflows.keys()),
            'count': len(self.active_workflows)
        }
    
    def get_completed_workflows(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent completed workflows"""
        return {
            'status': 'success',
            'completed_workflows': self.completed_workflows[-limit:],
            'count': len(self.completed_workflows)
        }