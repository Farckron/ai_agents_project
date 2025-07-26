#!/usr/bin/env python3
"""
Test runner script for the GitHub PR automation system tests.
"""

import unittest
import sys
import os
from io import StringIO

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_unit_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/integration', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_specific_test(test_module, test_class=None, test_method=None):
    """Run a specific test module, class, or method"""
    if test_method and test_class:
        suite = unittest.TestSuite()
        suite.addTest(test_class(test_method))
    elif test_class:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    else:
        suite = unittest.TestLoader().loadTestsFromModule(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for GitHub PR automation system')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--module', help='Run tests from specific module (e.g., test_pr_manager)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    success = True
    
    if args.module:
        # Run specific module
        try:
            if args.module.startswith('test_'):
                module_name = args.module
            else:
                module_name = f'test_{args.module}'
            
            # Try unit tests first
            try:
                module = __import__(f'tests.unit.{module_name}', fromlist=[module_name])
                print(f"Running unit tests from {module_name}")
                success = run_specific_test(module)
            except ImportError:
                # Try integration tests
                try:
                    module = __import__(f'tests.integration.{module_name}', fromlist=[module_name])
                    print(f"Running integration tests from {module_name}")
                    success = run_specific_test(module)
                except ImportError:
                    print(f"Could not find test module: {module_name}")
                    success = False
        except Exception as e:
            print(f"Error running specific module: {e}")
            success = False
    
    elif args.unit:
        # Run only unit tests
        success = run_unit_tests()
    
    elif args.integration:
        # Run only integration tests
        success = run_integration_tests()
    
    else:
        # Run all tests
        print("Running all tests...")
        unit_success = run_unit_tests()
        integration_success = run_integration_tests()
        success = unit_success and integration_success
    
    # Print summary
    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED! ✅")
    else:
        print("SOME TESTS FAILED! ❌")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()