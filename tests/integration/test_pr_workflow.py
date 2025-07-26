import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid
import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.pr_manager import PRManager
from agents.github_manager import GitHubManager
from utils.git_operations import GitOperations


class TestPRWorkflowIntegration(unittest.TestCase):
    """Integration tests for the complete PR workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock GitHub client to avoid real API calls
        with patch('agents.github_manager.Config') as mock_config:
            mock_config.GITHUB_TOKEN = 'test-token'
            with patch('github.Github') as mock_github_class:
                mock_github_client = Mock()
                mock_github_class.return_value = mock_github_client
                mock_github_client.get_user.return_value = Mock()
                
                self.pr_manager = PRManager()
                self.github_manager = GitHubManager()
                self.git_operations = GitOperations()
        
        self.test_repo_url = "https://github.com/test/integration-repo"
        self.test_user_request = "Add integration test feature"
        self.test_options = {
            'branch_name': 'integration-test-branch',
            'pr_title': 'Integration Test PR',
            'pr_description': 'This PR adds integration test functionality',
            'base_branch': 'main'
        }
    
    def test_complete_pr_workflow_success(self):
        """Test the complete PR workflow from request to PR creation"""
        # Mock all GitHub API interactions
        with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github_task, \
             patch.object(self.pr_manager, 'create_pull_request') as mock_create_pr:
            
            # Mock GitHub manager responses
            mock_github_task.side_effect = [
                # Repository validation
                {'status': 'success', 'summary': 'Test repository'},
                # Branch creation
                {'status': 'success', 'branch_name': 'integration-test-branch'},
                # Commit changes
                {'status': 'success', 'committed_files': ['test.py']}
            ]
            
            # Mock PR creation
            mock_create_pr.return_value = {
                'status': 'success',
                'pr_url': 'https://github.com/test/integration-repo/pull/1',
                'pr_number': 1
            }
            
            # Step 1: Process PR request
            workflow_result = self.pr_manager.process_pr_request(
                self.test_user_request,
                self.test_repo_url,
                self.test_options
            )
            
            self.assertEqual(workflow_result['status'], 'ready_for_changes')
            self.assertIn('workflow_id', workflow_result)
            workflow_id = workflow_result['workflow_id']
            
            # Step 2: Execute PR workflow with changes
            changes = {
                'files': {
                    'integration_test.py': 'def test_integration():\n    pass\n',
                    'README.md': '# Integration Test\nThis is a test.'
                }
            }
            
            final_result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
            
            self.assertEqual(final_result['status'], 'completed')
            self.assertIn('pr_url', str(final_result))
            
            # Verify workflow was tracked properly
            workflow_status = self.pr_manager.get_workflow_status(workflow_id)
            self.assertEqual(workflow_status['status'], 'success')
            completed_workflow = workflow_status['workflow']
            self.assertEqual(completed_workflow['status'], 'completed')
    
    def test_pr_workflow_with_validation_failure(self):
        """Test PR workflow when repository validation fails"""
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate:
            mock_validate.return_value = {
                'status': 'error',
                'message': 'Repository not accessible'
            }
            
            result = self.pr_manager.process_pr_request(
                self.test_user_request,
                "https://github.com/invalid/repo"
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Repository not accessible', result['message'])
    
    def test_pr_workflow_with_branch_creation_failure(self):
        """Test PR workflow when branch creation fails"""
        workflow_id = str(uuid.uuid4())
        
        # Set up workflow
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
        
        changes = {'files': {'test.py': 'print("test")'}}
        
        with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            # Mock branch creation failure
            mock_github.return_value = {
                'status': 'error',
                'error': 'Branch already exists'
            }
            
            result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Failed to create branch', result['message'])
    
    def test_pr_workflow_with_commit_failure(self):
        """Test PR workflow when commit fails"""
        workflow_id = str(uuid.uuid4())
        
        # Set up workflow
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
        
        changes = {'files': {'test.py': 'print("test")'}}
        
        with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            mock_github.side_effect = [
                {'status': 'success'},  # Branch creation succeeds
                {'status': 'error', 'error': 'Commit failed'}  # Commit fails
            ]
            
            result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Failed to commit changes', result['message'])
    
    def test_github_manager_integration_with_git_operations(self):
        """Test integration between GitHubManager and GitOperations"""
        # Test branch name validation integration
        branch_name = "feature/user-authentication-system"
        
        # Test through GitHubManager
        github_result = self.github_manager.validate_branch_name(branch_name)
        
        # Test through GitOperations
        git_ops_result = self.git_operations.validate_branch_name(branch_name)
        
        # Both should agree on validity
        self.assertEqual(github_result['is_valid'], git_ops_result[0])
        
        # Test with invalid branch name
        invalid_branch = "invalid..branch..name"
        
        github_invalid = self.github_manager.validate_branch_name(invalid_branch)
        git_ops_invalid = self.git_operations.validate_branch_name(invalid_branch)
        
        self.assertFalse(github_invalid['is_valid'])
        self.assertFalse(git_ops_invalid[0])
    
    def test_file_diff_calculation_integration(self):
        """Test file diff calculation in the context of PR workflow"""
        original_content = """def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""
        
        new_content = """def hello_world():
    print("Hello, World!")
    print("This is an updated version!")

def goodbye_world():
    print("Goodbye, World!")

if __name__ == "__main__":
    hello_world()
    goodbye_world()
"""
        
        # Calculate diff using GitOperations
        diff_result = self.git_operations.calculate_file_diff(
            original_content,
            new_content,
            "hello.py"
        )
        
        self.assertEqual(diff_result['change_type'], 'modify')
        self.assertTrue(diff_result['has_changes'])
        self.assertGreater(diff_result['additions'], 0)
        self.assertGreater(diff_result['total_changes'], 0)
        
        # Test commit message generation based on diff
        changes_summary = {
            "files_changed": ["hello.py"],
            "total_additions": diff_result['additions'],
            "total_deletions": diff_result['deletions'],
            "change_types": {"modify": 1}
        }
        
        commit_message = self.git_operations.create_commit_message(changes_summary)
        
        self.assertIn("hello.py", commit_message)
        self.assertTrue(commit_message.startswith("Update"))
    
    def test_error_handling_integration(self):
        """Test error handling across components"""
        # Test with invalid repository URL
        invalid_repo_url = "not-a-valid-url"
        
        result = self.pr_manager.process_pr_request(
            "Test request",
            invalid_repo_url
        )
        
        # Should handle the error gracefully
        self.assertIn('status', result)
        
        # Test with invalid branch name through the workflow
        invalid_options = {
            'branch_name': 'invalid..branch..name'
        }
        
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate:
            mock_validate.return_value = {'status': 'success'}
            
            result = self.pr_manager.process_pr_request(
                "Test request",
                self.test_repo_url,
                invalid_options
            )
            
            # Should still work because PR manager generates its own branch name
            # if validation fails
            self.assertIn('status', result)
    
    def test_workflow_state_management(self):
        """Test workflow state management across operations"""
        # Start a workflow
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate, \
             patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            
            mock_validate.return_value = {'status': 'success'}
            mock_github.return_value = {'status': 'success', 'summary': 'Test repo'}
            
            result = self.pr_manager.process_pr_request(
                self.test_user_request,
                self.test_repo_url
            )
            
            workflow_id = result['workflow_id']
            
            # Check workflow is in active state
            active_workflows = self.pr_manager.get_active_workflows()
            self.assertIn(workflow_id, active_workflows['active_workflows'])
            
            # Complete the workflow
            changes = {'files': {'test.py': 'print("test")'}}
            
            with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github_exec, \
                 patch.object(self.pr_manager, 'create_pull_request') as mock_create_pr:
                
                mock_github_exec.side_effect = [
                    {'status': 'success'},  # create_branch
                    {'status': 'success'}   # commit_changes
                ]
                mock_create_pr.return_value = {'status': 'success'}
                
                final_result = self.pr_manager.execute_pr_workflow(workflow_id, changes)
                
                self.assertEqual(final_result['status'], 'completed')
                
                # Check workflow moved to completed state
                active_workflows_after = self.pr_manager.get_active_workflows()
                self.assertNotIn(workflow_id, active_workflows_after['active_workflows'])
                
                completed_workflows = self.pr_manager.get_completed_workflows()
                completed_ids = [w['workflow_id'] for w in completed_workflows['completed_workflows']]
                self.assertIn(workflow_id, completed_ids)
    
    def test_change_validation_integration(self):
        """Test change validation integration across components"""
        # Test with safe changes
        safe_files = ['src/main.py', 'README.md', 'tests/test_main.py']
        safe_changes = {
            'src/main.py': 'def main():\n    print("Hello")',
            'README.md': '# Test Project\nThis is a test.',
            'tests/test_main.py': 'import unittest\n\nclass TestMain(unittest.TestCase):\n    pass'
        }
        
        validation_result = self.pr_manager.validate_changes(safe_files, safe_changes)
        
        self.assertEqual(validation_result['status'], 'success')
        self.assertEqual(validation_result['validation']['overall_status'], 'valid')
        
        # Test file safety through GitOperations
        for file_path, content in safe_changes.items():
            is_safe, warning = self.git_operations.check_file_safety(file_path, content)
            self.assertTrue(is_safe, f"File {file_path} should be safe")
        
        # Test with unsafe changes
        unsafe_files = ['.git/config', '../etc/passwd']
        unsafe_changes = {
            '.git/config': '[core]\n    repositoryformatversion = 0',
            '../etc/passwd': 'root:x:0:0:root:/root:/bin/bash'
        }
        
        validation_result = self.pr_manager.validate_changes(unsafe_files, unsafe_changes)
        
        self.assertEqual(validation_result['status'], 'success')
        self.assertEqual(validation_result['validation']['overall_status'], 'invalid')
        
        # Test file safety through GitOperations
        for file_path, content in unsafe_changes.items():
            is_safe, warning = self.git_operations.check_file_safety(file_path, content)
            self.assertFalse(is_safe, f"File {file_path} should be unsafe")
    
    def test_branch_name_generation_integration(self):
        """Test branch name generation integration"""
        test_requests = [
            "Add user authentication system",
            "Fix bug in payment processing",
            "Update documentation for API",
            "Refactor database connection logic",
            "Implement OAuth2 integration"
        ]
        
        for request in test_requests:
            # Generate branch name through PR Manager
            pr_branch_name = self.pr_manager.generate_branch_name(request)
            
            # Validate through GitHubManager
            validation_result = self.github_manager.validate_branch_name(pr_branch_name)
            
            self.assertTrue(validation_result['is_valid'], 
                          f"Generated branch name '{pr_branch_name}' should be valid")
            
            # Validate through GitOperations
            is_valid, error = self.git_operations.validate_branch_name(pr_branch_name)
            
            self.assertTrue(is_valid, 
                          f"Generated branch name '{pr_branch_name}' should be valid in GitOperations")
    
    def test_pr_description_generation_integration(self):
        """Test PR description generation integration"""
        user_request = "Add comprehensive logging system"
        repo_context = "Python Flask web application with SQLAlchemy database"
        
        with patch.object(self.pr_manager, 'call_openai') as mock_openai:
            mock_openai.return_value = """# Add Comprehensive Logging System

## Summary
This PR implements a comprehensive logging system for the Flask application.

## Changes Made
- Added structured logging configuration
- Implemented log rotation
- Added request/response logging middleware
- Created log analysis utilities

## Testing
- Unit tests for logging utilities
- Integration tests for log middleware
- Manual testing of log output formats
"""
            
            description = self.pr_manager.create_pr_description(user_request, repo_context)
            
            # Verify description contains expected elements
            self.assertIn("Comprehensive Logging System", description)
            self.assertIn("AI Agent System", description)  # Footer
            
            # Test input sanitization
            sanitized_request = self.git_operations.sanitize_user_input(
                user_request, 
                "pr_description"
            )
            self.assertEqual(sanitized_request, user_request)  # Should be unchanged for safe input
    
    def test_mock_github_api_integration(self):
        """Test integration with mocked GitHub API calls"""
        # This test simulates the full workflow with mocked GitHub API
        mock_repo_data = {
            'name': 'integration-repo',
            'full_name': 'test/integration-repo',
            'description': 'Test repository for integration tests',
            'language': 'Python',
            'default_branch': 'main'
        }
        
        with patch.object(self.github_manager.github_client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.name = mock_repo_data['name']
            mock_repo.full_name = mock_repo_data['full_name']
            mock_repo.description = mock_repo_data['description']
            mock_repo.language = mock_repo_data['language']
            mock_repo.default_branch = mock_repo_data['default_branch']
            
            # Mock branch operations
            mock_main_branch = Mock()
            mock_main_branch.commit.sha = 'abc123'
            mock_repo.get_branch.return_value = mock_main_branch
            mock_repo.create_git_ref.return_value = Mock()
            
            # Mock file operations
            mock_repo.get_contents.side_effect = Exception("File not found")  # New file
            mock_repo.create_file.return_value = {'commit': Mock(sha='def456')}
            
            mock_get_repo.return_value = mock_repo
            
            # Test branch creation
            branch_result = self.github_manager.create_branch(
                self.test_repo_url,
                'integration-test-branch',
                'main'
            )
            
            self.assertEqual(branch_result['status'], 'success')
            self.assertEqual(branch_result['branch_name'], 'integration-test-branch')
            
            # Test file commit
            files_dict = {
                'integration_test.py': 'def test_integration():\n    assert True'
            }
            
            commit_result = self.github_manager.commit_multiple_files(
                self.test_repo_url,
                'integration-test-branch',
                files_dict,
                'Add integration test'
            )
            
            self.assertEqual(commit_result['status'], 'success')
            self.assertEqual(len(commit_result['committed_files']), 1)


if __name__ == '__main__':
    unittest.main()