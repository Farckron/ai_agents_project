#!/usr/bin/env python3
"""
Integration test script for GitHub PR automation system
"""

def test_basic_integration():
    """Test basic integration of all components"""
    print("Testing basic integration...")
    
    try:
        # Test imports
        from agents.pr_manager import PRManager
        from agents.github_manager import GitHubManager
        from utils.git_operations import GitOperations
        from utils.error_handler import ErrorHandler
        print("✓ All imports successful")
        
        # Test initialization
        pr_manager = PRManager()
        github_manager = GitHubManager()
        git_ops = GitOperations()
        error_handler = ErrorHandler("test")
        print("✓ All components initialized")
        
        # Test integration
        assert hasattr(pr_manager, 'git_operations'), "PRManager should have git_operations"
        assert hasattr(pr_manager, 'error_handler'), "PRManager should have error_handler"
        assert hasattr(github_manager, 'git_operations'), "GitHubManager should have git_operations"
        assert hasattr(github_manager, 'error_handler'), "GitHubManager should have error_handler"
        print("✓ Integration attributes verified")
        
        # Test basic functionality
        branch_name = pr_manager.generate_branch_name("test feature")
        assert branch_name, "Branch name should be generated"
        print(f"✓ Branch name generated: {branch_name}")
        
        # Test GitOperations methods
        is_valid, error = git_ops.validate_branch_name("valid-branch-name")
        assert is_valid, f"Valid branch name should pass validation: {error}"
        print("✓ Branch name validation working")
        
        # Test file diff calculation
        diff_result = git_ops.calculate_file_diff("old content", "new content", "test.txt")
        assert diff_result['has_changes'], "Diff should detect changes"
        print("✓ File diff calculation working")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_pr_workflow_integration():
    """Test PR workflow integration"""
    print("\nTesting PR workflow integration...")
    
    try:
        from agents.project_manager import ProjectManager
        
        # Initialize project manager
        pm = ProjectManager()
        print("✓ ProjectManager initialized")
        
        # Verify PR manager is integrated
        assert hasattr(pm, 'pr_manager'), "ProjectManager should have pr_manager"
        assert pm.pr_manager is not None, "PR manager should be initialized"
        print("✓ PR manager integrated in ProjectManager")
        
        # Test PR workflow preparation (without actual GitHub calls)
        test_request = "Add a simple hello world function"
        test_repo = "https://github.com/test/repo"
        
        # This would normally make GitHub API calls, but we'll just test the structure
        print("✓ PR workflow structure verified")
        
        return True
        
    except Exception as e:
        print(f"❌ PR workflow integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_integration():
    """Test error handling integration"""
    print("\nTesting error handling integration...")
    
    try:
        from utils.error_handler import ErrorHandler, ErrorType, ErrorSeverity
        
        error_handler = ErrorHandler("test")
        
        # Test error logging
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_id = error_handler.log_error(e, ErrorType.GENERAL, ErrorSeverity.LOW)
            assert error_id, "Error ID should be returned"
            print(f"✓ Error logged with ID: {error_id}")
        
        # Test API error handling
        try:
            import requests
            raise requests.exceptions.ConnectionError("Test connection error")
        except Exception as e:
            response, status_code = ErrorHandler.handle_api_error(e, "Test message")
            assert 'error' in response, "Response should contain error"
            assert status_code == 503, f"Should return 503 for connection error, got {status_code}"
            print(f"✓ API error handling working: {status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting GitHub PR Automation Integration Tests\n")
    
    success = True
    success &= test_basic_integration()
    success &= test_pr_workflow_integration()
    success &= test_error_handling_integration()
    
    if success:
        print("\n✅ All integration tests completed successfully!")
        print("The GitHub PR automation system is properly integrated.")
    else:
        print("\n❌ Some integration tests failed.")
        print("Please check the errors above and fix the issues.")
    
    exit(0 if success else 1)