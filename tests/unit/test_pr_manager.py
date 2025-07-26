import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.pr_manager import PRManager


class TestPRManager(unittest.TestCase):
    """Unit tests for PRManager agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pr_manager = PRManager()
        self.test_repo_url = "https://github.com/test/repo"
        self.test_user_request = "Add new feature"
        self.test_options = {
            'branch_name': 'test-branch',
            'pr_title': 'Test PR',
            'pr_description': 'Test description',
            'base_branch': 'main'
        }
    
    def test_initialization(self):
        """Test PRManager initialization"""
        self.assertEqual(self.pr_manager.agent_name, "pr_manager")
        self.assertIsNotNone(self.pr_manager.github_manager)
        self.assertEqual(len(self.pr_manager.active_workflows), 0)
        self.assertEqual(len(self.pr_manager.completed_workflows), 0)
    
    def test_process_task_unknown_action(self):
        """Test process_task with unknown action"""
        task = {'action': 'unknown_action'}
        result = self.pr_manager.process_task(task)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Unknown PR action', result['message'])
    
    def test_process_task_process_pr_request(self):
        """Test process_task with process_pr_request action"""
        task = {
            'action': 'process_pr_request',
            'user_request': self.test_user_request,
            'repo_url': self.test_repo_url,
            'options': self.test_options
        }
        
        with patch.object(self.pr_manager, 'process_pr_request') as mock_process:
            mock_process.return_value = {'status': 'success'}
            result = self.pr_manager.process_task(task)
            
            mock_process.assert_called_once_with(
                user_request=self.test_user_request,
                repo_url=self.test_repo_url,
                options=self.test_options
            )
            self.assertEqual(result['status'], 'success')
    
    def test_process_task_get_workflow_status(self):
        """Test process_task with get_workflow_status action"""
        workflow_id = str(uuid.uuid4())
        task = {
            'action': 'get_workflow_status',
            'workflow_id': workflow_id
        }
        
        with patch.object(self.pr_manager, 'get_workflow_status') as mock_status:
            mock_status.return_value = {'status': 'success', 'workflow': {}}
            result = self.pr_manager.process_task(task)
            
            mock_status.assert_called_once_with(workflow_id)
            self.assertEqual(result['status'], 'success')
    
    def test_process_task_create_pr(self):
        """Test process_task with create_pr action"""
        task = {
            'action': 'create_pr',
            'repo_url': self.test_repo_url,
            'branch_name': 'test-branch',
            'title': 'Test PR',
            'description': 'Test description',
            'base_branch': 'main'
        }
        
        with patch.object(self.pr_manager, 'create_pull_request') as mock_create:
            mock_create.return_value = {'status': 'success'}
            result = self.pr_manager.process_task(task)
            
            mock_create.assert_called_once_with(
                repo_url=self.test_repo_url,
                branch_name='test-branch',
                title='Test PR',
                description='Test description',
                base_branch='main'
            )
            self.assertEqual(result['status'], 'success')
    
    @patch('uuid.uuid4')
    def test_process_pr_request_success(self, mock_uuid):
        """Test successful PR request processing"""
        mock_workflow_id = 'test-workflow-id'
        mock_uuid.return_value = Mock(spec=str)
        mock_uuid.return_value.__str__ = Mock(return_value=mock_workflow_id)
        
        # Mock the validation and GitHub manager calls
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate, \
             patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            
            mock_validate.return_value = {'status': 'success', 'message': 'Valid'}
            mock_github.return_value = {'status': 'success', 'summary': 'Test repo'}
            
            result = self.pr_manager.process_pr_request(
                self.test_user_request, 
                self.test_repo_url, 
                self.test_options
            )
            
            self.assertEqual(result['status'], 'ready_for_changes')
            self.assertEqual(result['workflow_id'], mock_workflow_id)
            self.assertIn('branch_name', result)
            self.assertIn('pr_title', result)
            self.assertIn('pr_description', result)
    
    def test_process_pr_request_validation_failure(self):
        """Test PR request processing with validation failure"""
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate:
            mock_validate.return_value = {
                'status': 'error', 
                'message': 'Repository not accessible'
            }
            
            result = self.pr_manager.process_pr_request(
                self.test_user_request, 
                self.test_repo_url
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Repository not accessible', result['message'])
    
    def test_generate_branch_name(self):
        """Test branch name generation"""
        request_summary = "Add new feature for user authentication"
        
        with patch('agents.pr_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-1200"
            
            branch_name = self.pr_manager.generate_branch_name(request_summary)
            
            self.assertTrue(branch_name.startswith('automated-'))
            self.assertIn('add-new-feature-for-user', branch_name)
            self.assertIn('20240101-1200', branch_name)
    
    def test_generate_branch_name_fallback(self):
        """Test branch name generation with fallback"""
        # Test with empty request
        with patch('agents.pr_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-120000"
            
            branch_name = self.pr_manager.generate_branch_name("")
            
            self.assertEqual(branch_name, "automated-changes-20240101-120000")
    
    def test_create_pr_description(self):
        """Test PR description creation"""
        user_request = "Add authentication system"
        repo_context = "Python Flask application"
        
        with patch.object(self.pr_manager, 'call_openai') as mock_openai:
            mock_openai.return_value = "Generated PR description"
            
            description = self.pr_manager.create_pr_description(user_request, repo_context)
            
            self.assertIn("Generated PR description", description)
            self.assertIn("AI Agent System", description)
            mock_openai.assert_called_once()
    
    def test_create_pr_description_error_fallback(self):
        """Test PR description creation with error fallback"""
        user_request = "Add authentication system"
        
        with patch.object(self.pr_manager, 'call_openai') as mock_openai:
            mock_openai.side_effect = Exception("OpenAI error")
            
            description = self.pr_manager.create_pr_description(user_request)
            
            self.assertIn("Automated Changes", description)
            self.assertIn(user_request, description)
            self.assertIn("AI Agent System", description)
    
    def test_create_pull_request(self):
        """Test pull request creation"""
        result = self.pr_manager.create_pull_request(
            self.test_repo_url,
            'test-branch',
            'Test PR',
            'Test description'
        )
        
        # Since this is a placeholder implementation, check the structure
        self.assertEqual(result['status'], 'success')
        self.assertIn('pr_url', result)
        self.assertIn('pr_number', result)
        self.assertEqual(result['title'], 'Test PR')
        self.assertEqual(result['description'], 'Test description')
    
    def test_validate_changes_valid_files(self):
        """Test change validation with valid files"""
        files_to_change = ['src/main.py', 'README.md', 'requirements.txt']
        proposed_changes = {
            'src/main.py': 'print("Hello World")',
            'README.md': '# Test Project'
        }
        
        result = self.pr_manager.validate_changes(files_to_change, proposed_changes)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['validation']['overall_status'], 'valid')
        self.assertEqual(len(result['validation']['valid_files']), 3)
        self.assertEqual(len(result['validation']['invalid_files']), 0)
    
    def test_validate_changes_invalid_files(self):
        """Test change validation with invalid files"""
        files_to_change = ['.git/config', '../etc/passwd', 'normal_file.py']
        proposed_changes = {}
        
        result = self.pr_manager.validate_changes(files_to_change, proposed_changes)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['validation']['overall_status'], 'invalid')
        self.assertEqual(len(result['validation']['valid_files']), 1)
        self.assertEqual(len(result['validation']['invalid_files']), 2)
    
    def test_validate_changes_sensitive_content(self):
        """Test change validation with sensitive content"""
        files_to_change = ['config.py']
        proposed_changes = {
            'config.py': 'API_KEY = "secret123"\nPASSWORD = "admin"'
        }
        
        result = self.pr_manager.validate_changes(files_to_change, proposed_changes)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['validation']['overall_status'], 'warning')
        self.assertTrue(len(result['validation']['warnings']) > 0)
    
    def test_get_workflow_status_active(self):
        """Test getting status of active workflow"""
        workflow_id = str(uuid.uuid4())
        test_workflow = {
            'workflow_id': workflow_id,
            'status': 'processing',
            'steps': []
        }
        self.pr_manager.active_workflows[workflow_id] = test_workflow
        
        result = self.pr_manager.get_workflow_status(workflow_id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['workflow']['workflow_id'], workflow_id)
    
    def test_get_workflow_status_completed(self):
        """Test getting status of completed workflow"""
        workflow_id = str(uuid.uuid4())
        test_workflow = {
            'workflow_id': workflow_id,
            'status': 'completed',
            'steps': []
        }
        self.pr_manager.completed_workflows.append(test_workflow)
        
        result = self.pr_manager.get_workflow_status(workflow_id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['workflow']['workflow_id'], workflow_id)
    
    def test_get_workflow_status_not_found(self):
        """Test getting status of non-existent workflow"""
        workflow_id = str(uuid.uuid4())
        
        result = self.pr_manager.get_workflow_status(workflow_id)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['message'])
    
    def test_execute_pr_workflow_success(self):
        """Test successful PR workflow execution"""
        workflow_id = str(uuid.uuid4())
        
        # Set up active workflow
        workflow = {
            'workflow_id': workflow_id,
            'repo_url': self.test_repo_url,
            'user_request': self.test_user_request,
            'options': {'base_branch': 'main'},
            'steps': [
                {
                    'step_name': 'prepare_workflow',
                    'result': {
                        'result': {
                            'branch_name': 'test-branch',
                            'pr_title': 'Test PR',
                            'pr_description': 'Test description'
                        }
                    }
                }
            ]
        }
        self.pr_manager.active_workflows[workflow_id] = workflow
        
        changes = {
            'files': {
                'test.py': 'print("test")'
            }
        }
        
        with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github, \
             patch.object(self.pr_manager, 'create_pull_request') as mock_create_pr:
            
            # Mock GitHub operations
            mock_github.side_effect = [
                {'status': 'success'},  # create_branch
                {'status': 'success'}   # commit_changes
            ]
            mock_create_pr.return_value = {'status': 'success', 'pr_url': 'test-url'}
            
            result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
            
            self.assertEqual(result['status'], 'completed')
            self.assertIn('test-url', str(result))
    
    def test_execute_pr_workflow_not_found(self):
        """Test PR workflow execution with non-existent workflow"""
        workflow_id = str(uuid.uuid4())
        changes = {'files': {}}
        
        result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['message'])
    
    def test_is_safe_file_path(self):
        """Test file path safety checks"""
        # Safe paths
        self.assertTrue(self.pr_manager._is_safe_file_path('src/main.py'))
        self.assertTrue(self.pr_manager._is_safe_file_path('README.md'))
        self.assertTrue(self.pr_manager._is_safe_file_path('docs/guide.md'))
        
        # Unsafe paths
        self.assertFalse(self.pr_manager._is_safe_file_path('.git/config'))
        self.assertFalse(self.pr_manager._is_safe_file_path('.env'))
        self.assertFalse(self.pr_manager._is_safe_file_path('../etc/passwd'))
        self.assertFalse(self.pr_manager._is_safe_file_path('/usr/bin/test'))
    
    def test_contains_sensitive_content(self):
        """Test sensitive content detection"""
        # Safe content
        self.assertFalse(self.pr_manager._contains_sensitive_content('print("Hello World")'))
        self.assertFalse(self.pr_manager._contains_sensitive_content('def main(): pass'))
        
        # Sensitive content
        self.assertTrue(self.pr_manager._contains_sensitive_content('password = "secret"'))
        self.assertTrue(self.pr_manager._contains_sensitive_content('API_KEY = "key123"'))
        self.assertTrue(self.pr_manager._contains_sensitive_content('private_key = "rsa"'))
        self.assertTrue(self.pr_manager._contains_sensitive_content('SECRET_TOKEN = "abc"'))
    
    def test_get_active_workflows(self):
        """Test getting active workflows"""
        # Add some test workflows
        workflow1_id = str(uuid.uuid4())
        workflow2_id = str(uuid.uuid4())
        
        self.pr_manager.active_workflows[workflow1_id] = {'status': 'processing'}
        self.pr_manager.active_workflows[workflow2_id] = {'status': 'processing'}
        
        result = self.pr_manager.get_active_workflows()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 2)
        self.assertIn(workflow1_id, result['active_workflows'])
        self.assertIn(workflow2_id, result['active_workflows'])
    
    def test_get_completed_workflows(self):
        """Test getting completed workflows"""
        # Add some test workflows
        for i in range(15):  # Add more than the default limit
            workflow = {'workflow_id': f'workflow-{i}', 'status': 'completed'}
            self.pr_manager.completed_workflows.append(workflow)
        
        result = self.pr_manager.get_completed_workflows(limit=5)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['completed_workflows']), 5)
        self.assertEqual(result['count'], 15)
        
        # Should return the last 5 workflows
        last_workflow = result['completed_workflows'][-1]
        self.assertEqual(last_workflow['workflow_id'], 'workflow-14')


if __name__ == '__main__':
    unittest.main()