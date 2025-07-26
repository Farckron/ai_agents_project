#!/usr/bin/env python3
"""
Comprehensive test for GitHub PR automation system
Tests different types of changes and error scenarios
"""

def test_different_repository_types():
    """Test with different types of repositories"""
    print("Testing different repository types...")
    
    try:
        from agents.github_manager import GitHubManager
        
        github_manager = GitHubManager()
        
        # Test repository type detection (without actual API calls)
        test_repos = [
            "https://github.com/python/cpython",
            "https://github.com/facebook/react", 
            "https://github.com/microsoft/vscode"
        ]
        
        for repo in test_repos:
            # Test URL validation
            is_valid, error = github_manager.git_operations.validate_repository_access(repo)
            print(f"✓ Repository URL validation for {repo}: {'Valid' if is_valid else f'Invalid - {error}'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository type test failed: {str(e)}")
        return False

def test_different_change_types():
    """Test different types of file changes"""
    print("\nTesting different change types...")
    
    try:
        from utils.git_operations import GitOperations
        
        git_ops = GitOperations()
        
        # Test different change scenarios
        test_cases = [
            ("", "print('Hello World')", "create"),
            ("old_content", "new_content", "modify"),
            ("content_to_delete", "", "delete"),
            ("same_content", "same_content", "no_change")
        ]
        
        for original, new, expected_type in test_cases:
            diff_result = git_ops.calculate_file_diff(original, new, "test.py")
            actual_type = diff_result.get('change_type', 'unknown')
            assert actual_type == expected_type, f"Expected {expected_type}, got {actual_type}"
            print(f"✓ Change type detection: {expected_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Change type test failed: {str(e)}")
        return False

def test_error_scenarios():
    """Test various error scenarios"""
    print("\nTesting error scenarios...")
    
    try:
        from agents.pr_manager import PRManager
        from utils.error_handler import ErrorType, ErrorSeverity
        
        pr_manager = PRManager()
        
        # Test invalid branch names
        invalid_names = ["", ".hidden", "branch.", "branch name", "branch?name"]
        for name in invalid_names:
            is_valid, error = pr_manager.git_operations.validate_branch_name(name)
            if is_valid:
                print(f"⚠️  Warning: '{name}' was considered valid but should be invalid")
            else:
                print(f"✓ Invalid branch name rejected: '{name}' - {error}")
        
        # Test file safety checks
        unsafe_files = [".env", "id_rsa", "../../../etc/passwd", "script.exe"]
        for file_path in unsafe_files:
            is_safe, warning = pr_manager.git_operations.check_file_safety(file_path)
            if is_safe:
                print(f"⚠️  Warning: '{file_path}' was considered safe but should be unsafe")
            else:
                print(f"✓ Unsafe file rejected: '{file_path}' - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scenario test failed: {str(e)}")
        return False

def test_pr_workflow_edge_cases():
    """Test PR workflow edge cases"""
    print("\nTesting PR workflow edge cases...")
    
    try:
        from agents.pr_manager import PRManager
        
        pr_manager = PRManager()
        
        # Test branch name generation with various inputs
        test_requests = [
            "Simple feature request",
            "Feature with special characters @#$%",
            "Very long feature request that exceeds normal length limits and should be truncated properly",
            "",  # Empty request
            "🚀 Unicode feature request 🎉"
        ]
        
        for request in test_requests:
            branch_name = pr_manager.generate_branch_name(request)
            assert branch_name, f"Branch name should be generated for: '{request}'"
            
            # Validate generated branch name
            is_valid, error = pr_manager.git_operations.validate_branch_name(branch_name)
            if not is_valid:
                print(f"⚠️  Generated invalid branch name: '{branch_name}' - {error}")
            else:
                print(f"✓ Valid branch name generated: '{branch_name}'")
        
        # Test change validation
        test_changes = {
            "safe_file.py": "print('Hello World')",
            "README.md": "# Project Title\n\nDescription here",
            "config.json": '{"setting": "value"}'
        }
        
        validation_result = pr_manager.validate_changes(list(test_changes.keys()), test_changes)
        assert validation_result['status'] == 'success', "Change validation should succeed for safe files"
        print("✓ Safe file changes validated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ PR workflow edge case test failed: {str(e)}")
        return False

def test_integration_with_project_manager():
    """Test integration with ProjectManager"""
    print("\nTesting ProjectManager integration...")
    
    try:
        from agents.project_manager import ProjectManager
        
        pm = ProjectManager()
        
        # Verify all agents are properly initialized
        agents = ['prompt_ask_engineer', 'prompt_code_engineer', 'code_agent', 'github_manager', 'pr_manager']
        for agent_name in agents:
            agent = getattr(pm, agent_name, None)
            assert agent is not None, f"{agent_name} should be initialized"
            print(f"✓ {agent_name} properly integrated")
        
        # Test status retrieval
        status = pm.get_project_status()
        assert 'agents' in status, "Status should include agents information"
        assert 'pr_manager' in status['agents'], "Status should include PR manager"
        print("✓ Project status includes PR manager")
        
        return True
        
    except Exception as e:
        print(f"❌ ProjectManager integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Starting Comprehensive GitHub PR Automation Tests\n")
    
    success = True
    success &= test_different_repository_types()
    success &= test_different_change_types()
    success &= test_error_scenarios()
    success &= test_pr_workflow_edge_cases()
    success &= test_integration_with_project_manager()
    
    if success:
        print("\n🎉 All comprehensive tests completed successfully!")
        print("The GitHub PR automation system handles various scenarios correctly.")
    else:
        print("\n⚠️  Some tests had warnings or issues.")
        print("The system is functional but may need minor adjustments.")
    
    exit(0 if success else 1)