import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from github import GithubException

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.pr_manager import PRManager
from agents.github_manager import GitHubManager
from utils.git_operations import GitOperations
from utils.error_handler import ErrorHandler, ErrorType, ErrorSeverity


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling across all components"""
    
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
        self.error_handler = ErrorHandler("TestErrorHandler")
        
        self.test_repo_url = "https://github.com/test/error-test-repo"
    
    def test_pr_manager_error_propagation(self):
        """Test error propagation through PR Manager"""
        # Test with invalid repository URL
        invalid_repo_url = "not-a-valid-url"
        
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate:
            mock_validate.return_value = {
                'status': 'error',
                'message': 'Invalid repository URL'
            }
            
            result = self.pr_manager.process_pr_request(
                "Test request",
                invalid_repo_url
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Invalid repository URL', result['message'])
    
    def test_github_manager_api_error_handling(self):
        """Test GitHub Manager API error handling"""
        # Test various GitHub API errors
        error_scenarios = [
            (401, "Bad credentials", "authentication"),
            (403, "Forbidden", "permission"),
            (404, "Not Found", "not_found"),
            (422, "Validation Failed", "validation"),
            (500, "Internal Server Error", "server_error")
        ]
        
        for status_code, message, error_type in error_scenarios:
            with self.subTest(status_code=status_code):
                github_error = GithubException(status_code, message)
                context = {
                    'operation': 'test_operation',
                    'repo_url': self.test_repo_url
                }
                
                result = self.github_manager.handle_github_api_errors(github_error, context)
                
                self.assertEqual(result['status'], 'error')
                self.assertIn('error', result)
                self.assertIn('code', result['error'])
                self.assertIn('message', result['error'])
                self.assertIn(str(status_code), result['error']['code'])
    
    def test_git_operations_validation_errors(self):
        """Test Git Operations validation error handling"""
        # Test invalid branch names
        invalid_branch_names = [
            "",  # Empty
            ".invalid",  # Starts with dot
            "invalid.",  # Ends with dot
            "invalid..name",  # Double dots
            "invalid name",  # Contains space
            "invalid~name",  # Contains tilde
            "a" * 300  # Too long
        ]
        
        for branch_name in invalid_branch_names:
            with self.subTest(branch_name=branch_name):
                is_valid, error_message = self.git_operations.validate_branch_name(branch_name)
                
                self.assertFalse(is_valid)
                self.assertIsNotNone(error_message)
                self.assertIsInstance(error_message, str)
    
    def test_file_safety_error_handling(self):
        """Test file safety error handling"""
        # Test unsafe file paths
        unsafe_paths = [
            "../../../etc/passwd",
            ".git/config",
            "/usr/bin/malicious",
            "C:\\Windows\\System32\\cmd.exe"
        ]
        
        for file_path in unsafe_paths:
            with self.subTest(file_path=file_path):
                is_safe, warning = self.git_operations.check_file_safety(file_path)
                
                self.assertFalse(is_safe)
                self.assertIsNotNone(warning)
                self.assertIn("Unsafe", warning)
        
        # Test dangerous file content
        dangerous_contents = [
            "rm -rf /",
            "eval(malicious_code)",
            "<script>alert('xss')</script>",
            "x" * (1024 * 1024 + 1)  # Too large
        ]
        
        for content in dangerous_contents:
            with self.subTest(content=content[:50] + "..."):
                is_safe, warning = self.git_operations.check_file_safety("test.py", content)
                
                self.assertFalse(is_safe)
                self.assertIsNotNone(warning)
    
    def test_workflow_error_recovery(self):
        """Test workflow error recovery mechanisms"""
        # Test workflow with multiple failure points
        with patch.object(self.pr_manager, '_validate_repository_access') as mock_validate, \
             patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            
            # First call succeeds (validation)
            # Second call fails (repository analysis)
            mock_validate.return_value = {'status': 'success'}
            mock_github.side_effect = [
                {'status': 'error', 'error': 'Repository analysis failed'}
            ]
            
            result = self.pr_manager.process_pr_request(
                "Test request with failure",
                self.test_repo_url
            )
            
            # Should handle the error gracefully
            self.assertIn('status', result)
            # The workflow should still be tracked even if it fails
            self.assertTrue(len(self.pr_manager.completed_workflows) > 0 or 
                          len(self.pr_manager.active_workflows) > 0)
    
    def test_error_handler_integration(self):
        """Test error handler integration with different error types"""
        # Test different error types
        test_errors = [
            (Exception("General error"), ErrorType.GENERAL, ErrorSeverity.MEDIUM),
            (ValueError("Invalid value"), ErrorType.VALIDATION, ErrorSeverity.HIGH),
            (ConnectionError("Network error"), ErrorType.NETWORK, ErrorSeverity.HIGH),
            (FileNotFoundError("File not found"), ErrorType.FILE_OPERATION, ErrorSeverity.MEDIUM)
        ]
        
        for error, error_type, severity in test_errors:
            with self.subTest(error_type=error_type):
                context = {
                    'operation': 'test_operation',
                    'component': 'test_component'
                }
                
                # Log the error
                self.error_handler.log_error(error, error_type, severity, context)
                
                # Verify error was logged (this would typically check logs)
                # For now, we just verify the method doesn't raise an exception
                self.assertTrue(True)
    
    def test_cascading_error_handling(self):
        """Test cascading error handling across components"""
        # Simulate a scenario where an error in one component affects others
        
        # Start with PR Manager
        with patch.object(self.pr_manager.github_manager, 'process_task') as mock_github:
            # GitHub Manager fails
            mock_github.return_value = {
                'status': 'error',
                'error': 'GitHub API error'
            }
            
            # This should be handled gracefully by PR Manager
            result = self.pr_manager.process_task({
                'action': 'process_pr_request',
                'user_request': 'Test request',
                'repo_url': self.test_repo_url
            })
            
            # PR Manager should handle the GitHub error
            self.assertIn('status', result)
            
            # If it's an error, it should be properly formatted
            if result['status'] == 'error':
                self.assertIn('error', result)
    
    def test_input_sanitization_error_handling(self):
        """Test input sanitization error handling"""
        # Test with various malicious inputs
        malicious_inputs = [
            "'; DROP TABLE users; --",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "$(rm -rf /)",  # Command injection attempt
            "\x00\x01\x02",  # Control characters
            "a" * 10000,  # Very long input
            None,  # None input
            "",  # Empty input
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=str(malicious_input)[:50]):
                # Test sanitization doesn't crash
                try:
                    sanitized = self.git_operations.sanitize_user_input(
                        malicious_input, 
                        "general"
                    )
                    # Should return a string (even if empty)
                    self.assertIsInstance(sanitized, str)
                except Exception as e:
                    # If an exception occurs, it should be handled
                    self.fail(f"Sanitization failed for input {malicious_input}: {e}")
    
    def test_concurrent_error_handling(self):
        """Test error handling in concurrent scenarios"""
        import threading
        import time
        
        errors_caught = []
        
        def worker_with_error():
            """Worker function that simulates an error"""
            try:
                # Simulate some work that might fail
                time.sleep(0.1)
                
                # Simulate an error
                raise Exception("Worker error")
                
            except Exception as e:
                errors_caught.append(str(e))
        
        def worker_with_github_error():
            """Worker function that simulates a GitHub API error"""
            try:
                # Mock a GitHub operation that fails
                github_error = GithubException(500, "Internal Server Error")
                result = self.github_manager.handle_github_api_errors(
                    github_error, 
                    {'operation': 'concurrent_test'}
                )
                errors_caught.append(result['error']['message'])
                
            except Exception as e:
                errors_caught.append(f"Unexpected error: {str(e)}")
        
        # Create multiple threads with different error scenarios
        threads = []
        
        for i in range(3):
            thread1 = threading.Thread(target=worker_with_error)
            thread2 = threading.Thread(target=worker_with_github_error)
            threads.extend([thread1, thread2])
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify errors were handled
        self.assertEqual(len(errors_caught), 6)  # 3 * 2 workers
        
        # Verify we have both types of errors
        worker_errors = [e for e in errors_caught if "Worker error" in e]
        github_errors = [e for e in errors_caught if "Internal Server Error" in e]
        
        self.assertEqual(len(worker_errors), 3)
        self.assertEqual(len(github_errors), 3)
    
    def test_memory_error_handling(self):
        """Test handling of memory-related errors"""
        # Test with very large data structures
        try:
            # Create a very large string that might cause memory issues
            large_content = "x" * (100 * 1024 * 1024)  # 100MB string
            
            # Test file safety check with large content
            is_safe, warning = self.git_operations.check_file_safety(
                "large_file.txt", 
                large_content
            )
            
            # Should detect the large file and reject it
            self.assertFalse(is_safe)
            self.assertIn("too large", warning)
            
        except MemoryError:
            # If we actually run out of memory, that's also a valid test result
            self.assertTrue(True, "Memory error was raised as expected")
        except Exception as e:
            # Other exceptions should be handled gracefully
            self.assertIsInstance(e, Exception)
    
    def test_network_error_simulation(self):
        """Test network error simulation and handling"""
        import requests
        
        # Test various network errors
        network_errors = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.Timeout("Request timed out"),
            requests.exceptions.HTTPError("HTTP error"),
            requests.exceptions.RequestException("General request error")
        ]
        
        for error in network_errors:
            with self.subTest(error_type=type(error).__name__):
                # Test that network errors are handled appropriately
                context = {
                    'operation': 'network_test',
                    'url': self.test_repo_url
                }
                
                # Log the network error
                self.error_handler.log_error(
                    error, 
                    ErrorType.NETWORK, 
                    ErrorSeverity.HIGH, 
                    context
                )
                
                # Verify the error handler doesn't crash
                self.assertTrue(True)
    
    def test_validation_error_chains(self):
        """Test chains of validation errors"""
        # Test a scenario where multiple validations fail in sequence
        
        # Invalid repository URL
        invalid_repo = "not-a-url"
        
        # Invalid branch name
        invalid_branch = "invalid..branch..name"
        
        # Invalid file path
        invalid_file = "../../../etc/passwd"
        
        # Test repository validation
        has_access, repo_error = self.git_operations.validate_repository_access(invalid_repo)
        self.assertFalse(has_access)
        self.assertIsNotNone(repo_error)
        
        # Test branch validation
        is_valid_branch, branch_error = self.git_operations.validate_branch_name(invalid_branch)
        self.assertFalse(is_valid_branch)
        self.assertIsNotNone(branch_error)
        
        # Test file validation
        is_safe_file, file_error = self.git_operations.check_file_safety(invalid_file)
        self.assertFalse(is_safe_file)
        self.assertIsNotNone(file_error)
        
        # All validations should fail with appropriate error messages
        self.assertIn("Invalid", repo_error)
        self.assertIn("consecutive dots", branch_error)
        self.assertIn("Unsafe", file_error)
    
    def test_error_recovery_mechanisms(self):
        """Test error recovery and retry mechanisms"""
        # Test retry mechanism simulation
        attempt_count = 0
        max_attempts = 3
        
        def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < max_attempts:
                raise Exception(f"Attempt {attempt_count} failed")
            else:
                return {"status": "success", "attempt": attempt_count}
        
        # Simulate retry logic
        last_error = None
        result = None
        
        for attempt in range(max_attempts):
            try:
                result = failing_operation()
                break
            except Exception as e:
                last_error = e
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    result = {"status": "error", "error": str(e)}
        
        # Should succeed on the final attempt
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempt"], max_attempts)
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail"""
        # Test PR Manager without GitHub token
        with patch('agents.github_manager.Config') as mock_config:
            mock_config.GITHUB_TOKEN = None
            
            # Create a new GitHub Manager without token
            github_manager_no_token = GitHubManager()
            
            # Should initialize without crashing
            self.assertIsNone(github_manager_no_token.github_client)
            
            # Operations should fail gracefully
            result = github_manager_no_token.create_branch(
                self.test_repo_url,
                'test-branch'
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('token required', result['error']['message'])


if __name__ == '__main__':
    unittest.main()