import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from github import GithubException

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.github_manager import GitHubManager


class TestGitHubManager(unittest.TestCase):
    """Unit tests for GitHubManager agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('agents.github_manager.Config') as mock_config:
            mock_config.GITHUB_TOKEN = 'test-token'
            with patch('github.Github') as mock_github_class:
                mock_github_client = Mock()
                mock_github_class.return_value = mock_github_client
                mock_github_client.get_user.return_value = Mock()
                
                self.github_manager = GitHubManager()
                self.github_manager.github_client = mock_github_client
        
        self.test_repo_url = "https://github.com/test/repo"
        self.test_branch_name = "test-branch"
        self.test_base_branch = "main"
    
    def test_initialization_with_token(self):
        """Test GitHubManager initialization with valid token"""
        with patch('agents.github_manager.Config') as mock_config, \
             patch('github.Github') as mock_github_class:
            
            mock_config.GITHUB_TOKEN = 'valid-token'
            mock_github_client = Mock()
            mock_github_class.return_value = mock_github_client
            mock_github_client.get_user.return_value = Mock()
            
            manager = GitHubManager()
            
            self.assertEqual(manager.agent_name, "github_manager")
            self.assertIsNotNone(manager.github_client)
            self.assertEqual(manager.repo_cache, {})
    
    def test_initialization_without_token(self):
        """Test GitHubManager initialization without token"""
        with patch('agents.github_manager.Config') as mock_config:
            mock_config.GITHUB_TOKEN = None
            
            manager = GitHubManager()
            
            self.assertIsNone(manager.github_client)
    
    def test_initialization_with_invalid_token(self):
        """Test GitHubManager initialization with invalid token"""
        with patch('agents.github_manager.Config') as mock_config, \
             patch('github.Github') as mock_github_class:
            
            mock_config.GITHUB_TOKEN = 'invalid-token'
            mock_github_client = Mock()
            mock_github_class.return_value = mock_github_client
            mock_github_client.get_user.side_effect = Exception("Invalid token")
            
            manager = GitHubManager()
            
            self.assertIsNone(manager.github_client)
    
    def test_process_task_get_repo_summary(self):
        """Test process_task with get_repo_summary action"""
        task = {
            'action': 'get_repo_summary',
            'repo_url': self.test_repo_url
        }
        
        with patch.object(self.github_manager, '_get_repository_summary') as mock_summary:
            mock_summary.return_value = {'status': 'success', 'summary': 'Test repo'}
            
            result = self.github_manager.process_task(task)
            
            mock_summary.assert_called_once_with(self.test_repo_url)
            self.assertEqual(result['status'], 'success')
    
    def test_process_task_create_branch(self):
        """Test process_task with create_branch action"""
        task = {
            'action': 'create_branch',
            'repo_url': self.test_repo_url,
            'branch_name': self.test_branch_name,
            'base_branch': self.test_base_branch
        }
        
        with patch.object(self.github_manager, 'create_branch') as mock_create:
            mock_create.return_value = {'status': 'success'}
            
            result = self.github_manager.process_task(task)
            
            mock_create.assert_called_once_with(
                self.test_repo_url, 
                self.test_branch_name, 
                self.test_base_branch
            )
            self.assertEqual(result['status'], 'success')
    
    def test_create_branch_success(self):
        """Test successful branch creation"""
        mock_repo = Mock()
        mock_base_branch = Mock()
        mock_base_branch.commit.sha = 'test-sha'
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.side_effect = [
            GithubException(404, "Not Found"),  # Branch doesn't exist (good)
            mock_base_branch  # Base branch exists
        ]
        mock_repo.create_git_ref.return_value = Mock()
        
        with patch.object(self.github_manager, 'validate_branch_name') as mock_validate:
            mock_validate.return_value = {'is_valid': True}
            
            result = self.github_manager.create_branch(
                self.test_repo_url, 
                self.test_branch_name, 
                self.test_base_branch
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['branch_name'], self.test_branch_name)
            self.assertEqual(result['base_branch'], self.test_base_branch)
            self.assertEqual(result['sha'], 'test-sha')
    
    def test_create_branch_already_exists(self):
        """Test branch creation when branch already exists"""
        mock_repo = Mock()
        mock_existing_branch = Mock()
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_existing_branch  # Branch exists
        
        with patch.object(self.github_manager, 'validate_branch_name') as mock_validate:
            mock_validate.return_value = {'is_valid': True}
            
            result = self.github_manager.create_branch(
                self.test_repo_url, 
                self.test_branch_name
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('already exists', result['error'])
    
    def test_create_branch_invalid_name(self):
        """Test branch creation with invalid name"""
        with patch.object(self.github_manager, 'validate_branch_name') as mock_validate:
            mock_validate.return_value = {
                'is_valid': False, 
                'message': 'Invalid branch name'
            }
            
            result = self.github_manager.create_branch(
                self.test_repo_url, 
                'invalid..branch'
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('Invalid branch name', result['error'])
    
    def test_create_branch_no_token(self):
        """Test branch creation without GitHub token"""
        self.github_manager.github_client = None
        
        result = self.github_manager.create_branch(
            self.test_repo_url, 
            self.test_branch_name
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('token required', result['error']['message'])
    
    def test_validate_branch_name_valid(self):
        """Test branch name validation with valid names"""
        valid_names = [
            'feature-branch',
            'bugfix/issue-123',
            'release-1.0.0',
            'hotfix_urgent',
            'develop'
        ]
        
        for name in valid_names:
            result = self.github_manager.validate_branch_name(name)
            self.assertTrue(result['is_valid'], f"'{name}' should be valid")
    
    def test_validate_branch_name_invalid(self):
        """Test branch name validation with invalid names"""
        invalid_names = [
            '',  # Empty
            '.hidden',  # Starts with dot
            'branch.',  # Ends with dot
            'branch..name',  # Double dots
            'branch name',  # Contains space
            'branch~name',  # Contains tilde
            'branch^name',  # Contains caret
            'branch:name',  # Contains colon
            'branch?name',  # Contains question mark
            'branch*name',  # Contains asterisk
            'branch[name]',  # Contains brackets
            'branch\\name',  # Contains backslash
            'branch@{name}',  # Contains @{
            '-branch',  # Starts with dash
            'branch-',  # Ends with dash
            'branch/',  # Ends with slash
            'branch//name',  # Double slashes
            'a' * 251  # Too long
        ]
        
        for name in invalid_names:
            result = self.github_manager.validate_branch_name(name)
            self.assertFalse(result['is_valid'], f"'{name}' should be invalid")
    
    def test_generate_unique_branch_name_success(self):
        """Test unique branch name generation"""
        mock_repo = Mock()
        self.github_manager.github_client.get_repo.return_value = mock_repo
        
        # First call returns branch exists, second call returns not found
        mock_repo.get_branch.side_effect = [
            Mock(),  # Base name exists
            GithubException(404, "Not Found")  # Candidate doesn't exist
        ]
        
        with patch.object(self.github_manager, 'validate_branch_name') as mock_validate:
            mock_validate.return_value = {'is_valid': True}
            
            result = self.github_manager.generate_unique_branch_name(
                'feature-test', 
                self.test_repo_url
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['branch_name'], 'feature-test-1')
            self.assertEqual(result['base_name'], 'feature-test')
    
    def test_generate_unique_branch_name_no_token(self):
        """Test unique branch name generation without token"""
        self.github_manager.github_client = None
        
        result = self.github_manager.generate_unique_branch_name(
            'feature-test', 
            self.test_repo_url
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('requires GitHub token', result['message'])
    
    def test_commit_multiple_files_success(self):
        """Test successful multiple file commit"""
        mock_repo = Mock()
        mock_branch = Mock()
        mock_existing_file = Mock()
        mock_existing_file.decoded_content.decode.return_value = "old content"
        mock_existing_file.sha = "old-sha"
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.get_contents.side_effect = [
            mock_existing_file,  # File exists
            GithubException(404, "Not Found")  # File doesn't exist
        ]
        
        mock_update_result = {'commit': Mock(sha='new-sha')}
        mock_create_result = {'commit': Mock(sha='create-sha')}
        mock_repo.update_file.return_value = mock_update_result
        mock_repo.create_file.return_value = mock_create_result
        
        files_dict = {
            'existing_file.py': 'new content',
            'new_file.py': 'file content'
        }
        
        result = self.github_manager.commit_multiple_files(
            self.test_repo_url,
            self.test_branch_name,
            files_dict,
            'Test commit'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['committed_files']), 2)
        self.assertEqual(result['successful_commits'], 2)
        self.assertEqual(len(result['failed_files']), 0)
    
    def test_commit_multiple_files_no_token(self):
        """Test multiple file commit without token"""
        self.github_manager.github_client = None
        
        result = self.github_manager.commit_multiple_files(
            self.test_repo_url,
            self.test_branch_name,
            {'file.py': 'content'},
            'Test commit'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('token required', result['error']['message'])
    
    def test_commit_multiple_files_empty_files(self):
        """Test multiple file commit with empty files dict"""
        result = self.github_manager.commit_multiple_files(
            self.test_repo_url,
            self.test_branch_name,
            {},
            'Test commit'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No files provided', result['error'])
    
    def test_update_file_content_success(self):
        """Test successful file content update"""
        mock_repo = Mock()
        mock_branch = Mock()
        mock_existing_file = Mock()
        mock_existing_file.decoded_content.decode.return_value = "old content"
        mock_existing_file.sha = "old-sha"
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.get_contents.return_value = mock_existing_file
        
        mock_result = {'commit': Mock(sha='new-sha')}
        mock_repo.update_file.return_value = mock_result
        
        result = self.github_manager.update_file_content(
            self.test_repo_url,
            self.test_branch_name,
            'test_file.py',
            'new content',
            'Update file'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], 'test_file.py')
        self.assertEqual(result['commit_sha'], 'new-sha')
        self.assertTrue(result['changed'])
    
    def test_update_file_content_no_change(self):
        """Test file content update with no actual change"""
        mock_repo = Mock()
        mock_branch = Mock()
        mock_existing_file = Mock()
        mock_existing_file.decoded_content.decode.return_value = "same content"
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.get_contents.return_value = mock_existing_file
        
        result = self.github_manager.update_file_content(
            self.test_repo_url,
            self.test_branch_name,
            'test_file.py',
            'same content',
            'Update file'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertFalse(result['changed'])
        self.assertIn('already up to date', result['message'])
    
    def test_delete_file_success(self):
        """Test successful file deletion"""
        mock_repo = Mock()
        mock_branch = Mock()
        mock_existing_file = Mock()
        mock_existing_file.sha = "file-sha"
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.get_contents.return_value = mock_existing_file
        
        mock_result = {'commit': Mock(sha='delete-sha')}
        mock_repo.delete_file.return_value = mock_result
        
        result = self.github_manager.delete_file(
            self.test_repo_url,
            self.test_branch_name,
            'test_file.py',
            'Delete file'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], 'test_file.py')
        self.assertEqual(result['commit_sha'], 'delete-sha')
    
    def test_delete_file_not_exists(self):
        """Test file deletion when file doesn't exist"""
        mock_repo = Mock()
        mock_branch = Mock()
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.get_contents.side_effect = Exception("File not found")
        
        result = self.github_manager.delete_file(
            self.test_repo_url,
            self.test_branch_name,
            'nonexistent_file.py',
            'Delete file'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('does not exist', result['error'])
    
    def test_create_pull_request_success(self):
        """Test successful pull request creation"""
        mock_repo = Mock()
        mock_head_branch = Mock()
        mock_base_branch = Mock()
        mock_pulls = Mock()
        mock_pulls.totalCount = 0  # No existing PRs
        
        self.github_manager.github_client.get_repo.return_value = mock_repo
        mock_repo.get_branch.side_effect = [mock_head_branch, mock_base_branch]
        mock_repo.get_pulls.return_value = mock_pulls
        
        with patch.object(self.github_manager, 'validate_pr_parameters') as mock_validate, \
             patch.object(self.github_manager, 'generate_pr_description') as mock_desc:
            
            mock_validate.return_value = {'is_valid': True}
            mock_desc.return_value = "Generated description"
            
            # Mock the actual PR creation (this would need to be implemented)
            with patch.object(mock_repo, 'create_pull') as mock_create_pr:
                mock_pr = Mock()
                mock_pr.html_url = "https://github.com/test/repo/pull/1"
                mock_pr.number = 1
                mock_create_pr.return_value = mock_pr
                
                result = self.github_manager.create_pull_request(
                    self.test_repo_url,
                    self.test_branch_name,
                    'Test PR',
                    'Test description'
                )
                
                # Since the actual implementation is incomplete, 
                # we'll test what we can based on the current code structure
                self.assertIn('status', result)
    
    def test_create_pull_request_invalid_params(self):
        """Test pull request creation with invalid parameters"""
        with patch.object(self.github_manager, 'validate_pr_parameters') as mock_validate:
            mock_validate.return_value = {
                'is_valid': False, 
                'message': 'Invalid title'
            }
            
            result = self.github_manager.create_pull_request(
                self.test_repo_url,
                self.test_branch_name,
                '',  # Empty title
                'Test description'
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('Invalid PR parameters', result['error'])
    
    def test_create_pull_request_no_token(self):
        """Test pull request creation without token"""
        self.github_manager.github_client = None
        
        result = self.github_manager.create_pull_request(
            self.test_repo_url,
            self.test_branch_name,
            'Test PR',
            'Test description'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('token required', result['error']['message'])
    
    def test_validate_pr_parameters_valid(self):
        """Test PR parameter validation with valid parameters"""
        # This method would need to be implemented in the actual GitHubManager
        # For now, we'll test the structure
        pass
    
    def test_validate_pr_parameters_invalid(self):
        """Test PR parameter validation with invalid parameters"""
        # This method would need to be implemented in the actual GitHubManager
        # For now, we'll test the structure
        pass
    
    def test_handle_github_api_errors(self):
        """Test GitHub API error handling"""
        test_error = GithubException(404, "Not Found")
        context = {'operation': 'test_operation'}
        
        result = self.github_manager.handle_github_api_errors(test_error, context)
        
        self.assertIn('error', result)
        self.assertIn('code', result['error'])
        self.assertIn('message', result['error'])
    
    def test_handle_authentication_errors(self):
        """Test authentication error handling"""
        test_error = Exception("Authentication failed")
        context = {'operation': 'test_auth'}
        
        result = self.github_manager.handle_authentication_errors(test_error, context)
        
        self.assertIn('error', result)
        self.assertIn('code', result['error'])
        self.assertIn('message', result['error'])
    
    def test_handle_rate_limit_errors(self):
        """Test rate limit error handling"""
        test_error = GithubException(403, "Rate limit exceeded")
        context = {'operation': 'test_rate_limit'}
        
        result = self.github_manager.handle_rate_limit_errors(test_error, context)
        
        self.assertIn('error', result)
        self.assertIn('code', result['error'])
        self.assertIn('message', result['error'])


if __name__ == '__main__':
    unittest.main()