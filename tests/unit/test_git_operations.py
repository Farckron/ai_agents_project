import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.git_operations import GitOperations


class TestGitOperations(unittest.TestCase):
    """Unit tests for GitOperations utility class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.git_ops = GitOperations()
    
    def test_initialization(self):
        """Test GitOperations initialization"""
        self.assertIsNotNone(self.git_ops.logger)
    
    def test_calculate_file_diff_create(self):
        """Test file diff calculation for file creation"""
        original_content = ""
        new_content = "print('Hello World')\nprint('New file')"
        
        result = self.git_ops.calculate_file_diff(
            original_content, 
            new_content, 
            "test.py"
        )
        
        self.assertEqual(result['file_path'], "test.py")
        self.assertEqual(result['change_type'], "create")
        self.assertEqual(result['additions'], 2)
        self.assertEqual(result['deletions'], 0)
        self.assertEqual(result['total_changes'], 2)
        self.assertTrue(result['has_changes'])
        self.assertEqual(result['original_size'], 0)
        self.assertEqual(result['new_size'], len(new_content))
    
    def test_calculate_file_diff_delete(self):
        """Test file diff calculation for file deletion"""
        original_content = "print('Hello World')\nprint('Old file')"
        new_content = ""
        
        result = self.git_ops.calculate_file_diff(
            original_content, 
            new_content, 
            "test.py"
        )
        
        self.assertEqual(result['change_type'], "delete")
        self.assertEqual(result['additions'], 0)
        self.assertEqual(result['deletions'], 2)
        self.assertEqual(result['total_changes'], 2)
        self.assertTrue(result['has_changes'])
    
    def test_calculate_file_diff_modify(self):
        """Test file diff calculation for file modification"""
        original_content = "print('Hello World')\nprint('Old line')"
        new_content = "print('Hello World')\nprint('New line')\nprint('Added line')"
        
        result = self.git_ops.calculate_file_diff(
            original_content, 
            new_content, 
            "test.py"
        )
        
        self.assertEqual(result['change_type'], "modify")
        self.assertEqual(result['additions'], 2)  # One modified + one added
        self.assertEqual(result['deletions'], 1)  # One removed
        self.assertEqual(result['total_changes'], 3)
        self.assertTrue(result['has_changes'])
    
    def test_calculate_file_diff_no_change(self):
        """Test file diff calculation with no changes"""
        content = "print('Hello World')\nprint('Same content')"
        
        result = self.git_ops.calculate_file_diff(content, content, "test.py")
        
        self.assertEqual(result['change_type'], "no_change")
        self.assertEqual(result['additions'], 0)
        self.assertEqual(result['deletions'], 0)
        self.assertEqual(result['total_changes'], 0)
        self.assertFalse(result['has_changes'])
    
    def test_calculate_file_diff_error(self):
        """Test file diff calculation with error"""
        # Simulate an error by passing invalid input
        with patch('difflib.unified_diff', side_effect=Exception("Diff error")):
            result = self.git_ops.calculate_file_diff("content", "new content", "test.py")
            
            self.assertEqual(result['change_type'], "error")
            self.assertIn('error', result)
            self.assertFalse(result['has_changes'])
    
    def test_create_commit_message_custom(self):
        """Test commit message creation with custom message"""
        changes_summary = {}
        custom_message = "Custom commit message"
        
        result = self.git_ops.create_commit_message(changes_summary, custom_message)
        
        self.assertEqual(result, custom_message)
    
    def test_create_commit_message_single_file_add(self):
        """Test commit message creation for single file addition"""
        changes_summary = {
            "files_changed": ["src/main.py"],
            "total_additions": 50,
            "total_deletions": 0,
            "change_types": {"create": 1, "modify": 0, "delete": 0}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Add main.py (+50)")
    
    def test_create_commit_message_single_file_update(self):
        """Test commit message creation for single file update"""
        changes_summary = {
            "files_changed": ["src/main.py"],
            "total_additions": 10,
            "total_deletions": 5,
            "change_types": {"create": 0, "modify": 1, "delete": 0}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Update main.py (+10, -5)")
    
    def test_create_commit_message_single_file_remove(self):
        """Test commit message creation for single file removal"""
        changes_summary = {
            "files_changed": ["src/old.py"],
            "total_additions": 0,
            "total_deletions": 30,
            "change_types": {"create": 0, "modify": 0, "delete": 1}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Remove old.py (-30)")
    
    def test_create_commit_message_multiple_files(self):
        """Test commit message creation for multiple files"""
        changes_summary = {
            "files_changed": ["src/main.py", "src/utils.py", "README.md"],
            "total_additions": 25,
            "total_deletions": 10,
            "change_types": {"create": 1, "modify": 2, "delete": 0}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Update main.py, utils.py, README.md (+25, -10)")
    
    def test_create_commit_message_many_files(self):
        """Test commit message creation for many files"""
        changes_summary = {
            "files_changed": ["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"],
            "total_additions": 100,
            "total_deletions": 50,
            "change_types": {"create": 2, "modify": 3, "delete": 0}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Update 5 files (+100, -50)")
    
    def test_create_commit_message_small_changes(self):
        """Test commit message creation for small changes (no stats)"""
        changes_summary = {
            "files_changed": ["src/main.py"],
            "total_additions": 2,
            "total_deletions": 1,
            "change_types": {"create": 0, "modify": 1, "delete": 0}
        }
        
        result = self.git_ops.create_commit_message(changes_summary)
        
        self.assertEqual(result, "Update main.py")
    
    def test_create_commit_message_error(self):
        """Test commit message creation with error"""
        with patch('os.path.basename', side_effect=Exception("Path error")):
            changes_summary = {"files_changed": ["test.py"]}
            
            result = self.git_ops.create_commit_message(changes_summary)
            
            self.assertEqual(result, "Update files")
    
    def test_generate_unique_branch_name_no_existing(self):
        """Test unique branch name generation without existing branches"""
        base_name = "feature-authentication"
        repo_url = "https://github.com/test/repo"
        
        with patch('utils.git_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-120000"
            
            result = self.git_ops.generate_unique_branch_name(base_name, repo_url)
            
            self.assertEqual(result, "feature-authentication-20240101-120000")
    
    def test_generate_unique_branch_name_with_existing(self):
        """Test unique branch name generation with existing branches"""
        base_name = "feature-test"
        repo_url = "https://github.com/test/repo"
        existing_branches = ["feature-test", "feature-test-1", "feature-test-2"]
        
        result = self.git_ops.generate_unique_branch_name(
            base_name, 
            repo_url, 
            existing_branches
        )
        
        self.assertEqual(result, "feature-test-3")
    
    def test_generate_unique_branch_name_base_available(self):
        """Test unique branch name generation when base name is available"""
        base_name = "feature-new"
        repo_url = "https://github.com/test/repo"
        existing_branches = ["feature-old", "feature-other"]
        
        result = self.git_ops.generate_unique_branch_name(
            base_name, 
            repo_url, 
            existing_branches
        )
        
        self.assertEqual(result, "feature-new")
    
    def test_generate_unique_branch_name_sanitization(self):
        """Test unique branch name generation with sanitization"""
        base_name = "Feature With Spaces & Special@Chars!"
        repo_url = "https://github.com/test/repo"
        
        with patch('utils.git_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-120000"
            
            result = self.git_ops.generate_unique_branch_name(base_name, repo_url)
            
            self.assertEqual(result, "feature-with-spaces-specialchars-20240101-120000")
    
    def test_generate_unique_branch_name_error_fallback(self):
        """Test unique branch name generation with error fallback"""
        with patch.object(self.git_ops, '_sanitize_branch_name', side_effect=Exception("Error")):
            with patch('utils.git_operations.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101-120000"
                
                result = self.git_ops.generate_unique_branch_name("test", "repo")
                
                self.assertEqual(result, "feature-20240101-120000")
    
    def test_validate_branch_name_valid(self):
        """Test branch name validation with valid names"""
        valid_names = [
            "feature-branch",
            "bugfix/issue-123",
            "release-1.0.0",
            "hotfix_urgent",
            "develop",
            "feature/user-auth",
            "fix-bug-123"
        ]
        
        for name in valid_names:
            is_valid, error = self.git_ops.validate_branch_name(name)
            self.assertTrue(is_valid, f"'{name}' should be valid, but got error: {error}")
            self.assertIsNone(error)
    
    def test_validate_branch_name_invalid(self):
        """Test branch name validation with invalid names"""
        invalid_cases = [
            ("", "Branch name cannot be empty"),
            (".hidden", "Branch name cannot start with a dot"),
            ("branch.", "Branch name cannot end with a dot"),
            ("branch..name", "Branch name cannot contain consecutive dots"),
            ("branch name", "Branch name contains invalid characters"),
            ("branch~name", "Branch name contains invalid characters"),
            ("branch^name", "Branch name contains invalid characters"),
            ("branch:name", "Branch name contains invalid characters"),
            ("branch?name", "Branch name contains invalid characters"),
            ("branch*name", "Branch name contains invalid characters"),
            ("branch[name]", "Branch name contains invalid characters"),
            ("branch\\name", "Branch name contains invalid characters"),
            ("branch@{name}", "Branch name cannot contain @{"),
            ("-branch", "Branch name cannot start with a dash"),
            ("branch-", "Branch name cannot end with a dash"),
            ("branch/", "Branch name cannot end with a slash"),
            ("branch//name", "Branch name cannot contain consecutive slashes"),
            ("a" * 251, "Branch name is too long")
        ]
        
        for name, expected_error_type in invalid_cases:
            is_valid, error = self.git_ops.validate_branch_name(name)
            self.assertFalse(is_valid, f"'{name}' should be invalid")
            self.assertIsNotNone(error)
    
    def test_validate_branch_name_control_characters(self):
        """Test branch name validation with control characters"""
        name_with_control = "branch\x00name"
        
        is_valid, error = self.git_ops.validate_branch_name(name_with_control)
        
        self.assertFalse(is_valid)
        self.assertIn("control characters", error)
    
    def test_validate_branch_name_error(self):
        """Test branch name validation with error"""
        with patch('re.search', side_effect=Exception("Regex error")):
            is_valid, error = self.git_ops.validate_branch_name("test")
            
            self.assertFalse(is_valid)
            self.assertIn("Validation error", error)
    
    def test_sanitize_branch_name(self):
        """Test branch name sanitization"""
        test_cases = [
            ("Feature Branch", "feature-branch"),
            ("Bug Fix #123", "bug-fix-123"),
            ("Release v1.0.0", "release-v1.0.0"),
            ("  spaced  name  ", "spaced-name"),
            ("UPPERCASE", "uppercase"),
            ("special@#$%chars", "specialchars"),
            ("multiple---dashes", "multiple-dashes"),
            ("dots..and..more", "dots.and.more"),
            ("slashes//everywhere", "slashes/everywhere"),
            (".leading-dot", "leading-dot"),
            ("trailing-dot.", "trailing-dot"),
            ("-leading-dash", "leading-dash"),
            ("trailing-dash-", "trailing-dash"),
            ("", "feature"),  # Empty fallback
            ("a" * 250, "a" * 200)  # Truncation
        ]
        
        for input_name, expected in test_cases:
            result = self.git_ops._sanitize_branch_name(input_name)
            self.assertEqual(result, expected, f"'{input_name}' should become '{expected}', got '{result}'")
    
    def test_sanitize_branch_name_error(self):
        """Test branch name sanitization with error"""
        with patch('re.sub', side_effect=Exception("Regex error")):
            result = self.git_ops._sanitize_branch_name("test")
            
            self.assertEqual(result, "feature")
    
    def test_validate_repository_access_invalid_url(self):
        """Test repository access validation with invalid URL"""
        with patch('utils.github_utils.GitHubUtils') as mock_utils_class:
            mock_utils = Mock()
            mock_utils_class.return_value = mock_utils
            mock_utils.parse_github_url.return_value = None
            
            has_access, error = self.git_ops.validate_repository_access("invalid-url")
            
            self.assertFalse(has_access)
            self.assertIn("Invalid GitHub repository URL", error)
    
    def test_validate_repository_access_repo_not_exists(self):
        """Test repository access validation when repo doesn't exist"""
        with patch('utils.github_utils.GitHubUtils') as mock_utils_class:
            mock_utils = Mock()
            mock_utils_class.return_value = mock_utils
            mock_utils.parse_github_url.return_value = ("owner", "repo")
            mock_utils.check_repository_exists.return_value = False
            
            has_access, error = self.git_ops.validate_repository_access("https://github.com/owner/repo")
            
            self.assertFalse(has_access)
            self.assertIn("does not exist", error)
    
    def test_validate_repository_access_success_no_token(self):
        """Test repository access validation success without token"""
        with patch('utils.github_utils.GitHubUtils') as mock_utils_class:
            mock_utils = Mock()
            mock_utils_class.return_value = mock_utils
            mock_utils.parse_github_url.return_value = ("owner", "repo")
            mock_utils.check_repository_exists.return_value = True
            
            has_access, error = self.git_ops.validate_repository_access("https://github.com/owner/repo")
            
            self.assertTrue(has_access)
            self.assertIsNone(error)
    
    def test_validate_repository_access_with_token_success(self):
        """Test repository access validation with valid token"""
        with patch('utils.github_utils.GitHubUtils') as mock_utils_class, \
             patch('requests.get') as mock_get:
            
            mock_utils = Mock()
            mock_utils_class.return_value = mock_utils
            mock_utils.parse_github_url.return_value = ("owner", "repo")
            mock_utils.check_repository_exists.return_value = True
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'permissions': {'push': True}
            }
            mock_get.return_value = mock_response
            
            has_access, error = self.git_ops.validate_repository_access(
                "https://github.com/owner/repo", 
                "valid-token"
            )
            
            self.assertTrue(has_access)
            self.assertIsNone(error)
    
    def test_validate_repository_access_insufficient_permissions(self):
        """Test repository access validation with insufficient permissions"""
        with patch('utils.github_utils.GitHubUtils') as mock_utils_class, \
             patch('requests.get') as mock_get:
            
            mock_utils = Mock()
            mock_utils_class.return_value = mock_utils
            mock_utils.parse_github_url.return_value = ("owner", "repo")
            mock_utils.check_repository_exists.return_value = True
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'permissions': {'push': False}
            }
            mock_get.return_value = mock_response
            
            has_access, error = self.git_ops.validate_repository_access(
                "https://github.com/owner/repo", 
                "limited-token"
            )
            
            self.assertFalse(has_access)
            self.assertIn("Insufficient permissions", error)
    
    def test_sanitize_user_input_general(self):
        """Test general user input sanitization"""
        test_input = "Normal input with some $pecial chars & symbols"
        result = self.git_ops.sanitize_user_input(test_input)
        
        self.assertEqual(result, "Normal input with some pecial chars  symbols")
    
    def test_sanitize_user_input_branch_name(self):
        """Test user input sanitization for branch names"""
        test_input = "Feature Branch Name"
        result = self.git_ops.sanitize_user_input(test_input, "branch_name")
        
        self.assertEqual(result, "feature-branch-name")
    
    def test_sanitize_user_input_commit_message(self):
        """Test user input sanitization for commit messages"""
        test_input = "Commit message with `dangerous` $commands and (parentheses)"
        result = self.git_ops.sanitize_user_input(test_input, "commit_message")
        
        self.assertEqual(result, "Commit message with dangerous commands and parentheses")
    
    def test_sanitize_user_input_pr_title(self):
        """Test user input sanitization for PR titles"""
        test_input = "PR Title with *markdown* and #headers"
        result = self.git_ops.sanitize_user_input(test_input, "pr_title")
        
        self.assertEqual(result, "PR Title with markdown and headers")
    
    def test_sanitize_user_input_pr_description(self):
        """Test user input sanitization for PR descriptions"""
        test_input = "PR description with <script>alert('xss')</script> and javascript:void(0)"
        result = self.git_ops.sanitize_user_input(test_input, "pr_description")
        
        self.assertNotIn("<script>", result)
        self.assertNotIn("javascript:", result)
    
    def test_sanitize_user_input_empty(self):
        """Test user input sanitization with empty input"""
        result = self.git_ops.sanitize_user_input("")
        self.assertEqual(result, "")
        
        result = self.git_ops.sanitize_user_input(None)
        self.assertEqual(result, "")
    
    def test_sanitize_user_input_control_characters(self):
        """Test user input sanitization with control characters"""
        test_input = "Text with\x00null\x01and\x02control\x03chars"
        result = self.git_ops.sanitize_user_input(test_input)
        
        self.assertEqual(result, "Text withnullandcontrolchars")
    
    def test_check_file_safety_safe_files(self):
        """Test file safety check with safe files"""
        safe_files = [
            "src/main.py",
            "README.md",
            "docs/guide.txt",
            "config/settings.json",
            "tests/test_file.py"
        ]
        
        for file_path in safe_files:
            is_safe, warning = self.git_ops.check_file_safety(file_path)
            self.assertTrue(is_safe, f"'{file_path}' should be safe, but got warning: {warning}")
            self.assertIsNone(warning)
    
    def test_check_file_safety_unsafe_paths(self):
        """Test file safety check with unsafe file paths"""
        unsafe_files = [
            "../etc/passwd",
            ".git/config",
            "/usr/bin/test",
            "../../sensitive/file.txt"
        ]
        
        for file_path in unsafe_files:
            is_safe, warning = self.git_ops.check_file_safety(file_path)
            self.assertFalse(is_safe, f"'{file_path}' should be unsafe")
            self.assertIsNotNone(warning)
    
    def test_check_file_safety_dangerous_extensions(self):
        """Test file safety check with dangerous file extensions"""
        dangerous_files = [
            "malware.exe",
            "script.bat",
            "command.cmd",
            "virus.scr",
            "trojan.com"
        ]
        
        for file_path in dangerous_files:
            is_safe, warning = self.git_ops.check_file_safety(file_path)
            self.assertFalse(is_safe, f"'{file_path}' should be unsafe")
            self.assertIn("dangerous file type", warning)
    
    def test_check_file_safety_system_files(self):
        """Test file safety check with system files"""
        system_files = [
            ".env",
            "id_rsa",
            "authorized_keys",
            "passwd",
            "sudoers"
        ]
        
        for file_path in system_files:
            is_safe, warning = self.git_ops.check_file_safety(file_path)
            self.assertFalse(is_safe, f"'{file_path}' should be unsafe")
            self.assertIn("System/security file", warning)
    
    def test_check_file_safety_dangerous_content(self):
        """Test file safety check with dangerous content"""
        dangerous_contents = [
            "rm -rf /",
            "sudo rm -rf",
            "eval(user_input)",
            "exec(malicious_code)",
            "system('dangerous_command')",
            "<script>alert('xss')</script>",
            "javascript:void(0)"
        ]
        
        for content in dangerous_contents:
            is_safe, warning = self.git_ops.check_file_safety("test.py", content)
            self.assertFalse(is_safe, f"Content '{content}' should be unsafe")
            self.assertIn("dangerous content", warning)
    
    def test_check_file_safety_large_content(self):
        """Test file safety check with large content"""
        large_content = "x" * (1024 * 1024 + 1)  # > 1MB
        
        is_safe, warning = self.git_ops.check_file_safety("test.py", large_content)
        
        self.assertFalse(is_safe)
        self.assertIn("too large", warning)
    
    def test_check_file_safety_error(self):
        """Test file safety check with error"""
        with patch.object(self.git_ops, '_is_safe_file_path', side_effect=Exception("Path error")):
            is_safe, warning = self.git_ops.check_file_safety("test.py")
            
            self.assertFalse(is_safe)
            self.assertIn("Safety check error", warning)
    
    def test_is_safe_file_path_safe(self):
        """Test safe file path checking with safe paths"""
        safe_paths = [
            "src/main.py",
            "docs/readme.md",
            "config/settings.json",
            ".github/workflows/ci.yml",
            ".vscode/settings.json"
        ]
        
        for path in safe_paths:
            result = self.git_ops._is_safe_file_path(path)
            self.assertTrue(result, f"'{path}' should be safe")
    
    def test_is_safe_file_path_unsafe(self):
        """Test safe file path checking with unsafe paths"""
        unsafe_paths = [
            "../etc/passwd",
            "/usr/bin/test",
            ".git/config",
            ".ssh/id_rsa",
            ".aws/credentials",
            "node_modules/.bin/script",
            ".secret/key"
        ]
        
        for path in unsafe_paths:
            result = self.git_ops._is_safe_file_path(path)
            self.assertFalse(result, f"'{path}' should be unsafe")
    
    def test_is_safe_file_path_long_path(self):
        """Test safe file path checking with very long path"""
        long_path = "a/" * 200 + "file.txt"  # > 260 characters
        
        result = self.git_ops._is_safe_file_path(long_path)
        
        self.assertFalse(result)
    
    def test_sanitize_file_path(self):
        """Test file path sanitization"""
        test_cases = [
            ("normal/path/file.txt", "normal/path/file.txt"),
            ("path\\with\\backslashes.txt", "path/with/backslashes.txt"),
            ("/absolute/path/file.txt", "absolute/path/file.txt"),
            ("path/../traversal/file.txt", "path/traversal/file.txt"),
            ("path//double//slashes.txt", "path/double/slashes.txt"),
            ("path/with<>:\"|?*chars.txt", "path/withchars.txt"),
            ("a" * 250 + ".txt", "a" * 196 + ".txt")  # Truncation with extension
        ]
        
        for input_path, expected in test_cases:
            result = self.git_ops._sanitize_file_path(input_path)
            self.assertEqual(result, expected, f"'{input_path}' should become '{expected}', got '{result}'")
    
    def test_sanitize_file_path_error(self):
        """Test file path sanitization with error"""
        with patch('re.sub', side_effect=Exception("Regex error")):
            result = self.git_ops._sanitize_file_path("test.txt")
            
            self.assertEqual(result, "safe_file.txt")


if __name__ == '__main__':
    unittest.main()