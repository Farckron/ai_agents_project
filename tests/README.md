# GitHub PR Automation - Test Suite

This directory contains comprehensive tests for the GitHub PR automation system.

## Test Structure

```
tests/
├── __init__.py
├── README.md
├── run_tests.py              # Main test runner
├── unit/                     # Unit tests
│   ├── __init__.py
│   ├── test_pr_manager.py    # Tests for PRManager agent
│   ├── test_github_manager.py # Tests for GitHubManager agent
│   └── test_git_operations.py # Tests for GitOperations utility
└── integration/              # Integration tests
    ├── __init__.py
    ├── test_pr_workflow.py   # Complete PR workflow tests
    ├── test_github_api_mock.py # GitHub API integration with mocks
    └── test_error_handling.py # Error handling integration tests
```

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Only Unit Tests
```bash
python tests/run_tests.py --unit
```

### Run Only Integration Tests
```bash
python tests/run_tests.py --integration
```

### Run Specific Test Module
```bash
python tests/run_tests.py --module test_pr_manager
python tests/run_tests.py --module test_github_api_mock
```

### Run Tests with Verbose Output
```bash
python tests/run_tests.py --verbose
```

## Test Categories

### Unit Tests

#### test_pr_manager.py
Tests for the PRManager agent including:
- Initialization and configuration
- Task processing for different actions
- PR request workflow processing
- Branch name generation
- PR description creation
- Change validation
- Workflow state management
- Error handling

#### test_github_manager.py
Tests for the GitHubManager agent including:
- GitHub client initialization
- Repository operations
- Branch creation and validation
- File operations (create, update, delete)
- Pull request creation
- Error handling for GitHub API errors
- Authentication and rate limiting

#### test_git_operations.py
Tests for the GitOperations utility including:
- File diff calculation
- Commit message generation
- Branch name validation and sanitization
- Repository access validation
- User input sanitization
- File safety checks
- Path validation

### Integration Tests

#### test_pr_workflow.py
Complete workflow integration tests including:
- End-to-end PR creation workflow
- Component interaction testing
- Workflow state management
- Error propagation between components
- File diff and commit message integration
- Change validation across components

#### test_github_api_mock.py
GitHub API integration tests with mocked responses including:
- Various API response scenarios
- Error handling for different HTTP status codes
- Rate limiting and authentication errors
- Concurrent operations simulation
- Large file operations
- Timeout handling

#### test_error_handling.py
Comprehensive error handling integration tests including:
- Error propagation across components
- Cascading error scenarios
- Input validation error chains
- Network error simulation
- Memory error handling
- Graceful degradation testing

## Test Features

### Mocking Strategy
- All tests use mocked GitHub API calls to avoid real API usage
- Comprehensive mocking of GitHub client and responses
- Simulation of various error conditions
- Thread-safe mocking for concurrent tests

### Error Testing
- Comprehensive error scenario coverage
- Authentication and authorization errors
- Network and timeout errors
- Validation and input sanitization errors
- Resource limitation errors

### Edge Cases
- Large file operations
- Concurrent operations
- Memory limitations
- Invalid input handling
- API rate limiting

## Test Data

Tests use controlled test data including:
- Mock repository URLs: `https://github.com/test/repo`
- Test branch names with various validation scenarios
- Sample file contents for diff testing
- Error scenarios with specific HTTP status codes

## Coverage

The test suite covers:
- ✅ All public methods in PRManager
- ✅ All public methods in GitHubManager  
- ✅ All public methods in GitOperations
- ✅ Error handling paths
- ✅ Input validation
- ✅ Workflow state management
- ✅ Component integration
- ✅ Edge cases and error scenarios

## Requirements

Tests require the following packages (already in requirements.txt):
- unittest (built-in)
- unittest.mock (built-in)
- github (PyGithub)
- requests

## Continuous Integration

These tests are designed to run in CI/CD environments:
- No external dependencies (all mocked)
- Deterministic results
- Comprehensive error reporting
- Exit codes for CI integration

## Adding New Tests

When adding new functionality:

1. **Unit Tests**: Add tests to the appropriate `test_*.py` file in `tests/unit/`
2. **Integration Tests**: Add workflow tests to `tests/integration/`
3. **Error Cases**: Add error scenarios to `test_error_handling.py`
4. **Mock Data**: Update mock responses as needed

### Test Naming Convention
- Test files: `test_<component_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<functionality>_<scenario>`

### Example Test Structure
```python
def test_component_method_success(self):
    """Test successful operation of component method"""
    # Arrange
    # Act
    # Assert

def test_component_method_error(self):
    """Test error handling in component method"""
    # Arrange error scenario
    # Act
    # Assert error handling
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Mock Failures**: Check that all external dependencies are properly mocked
3. **Test Isolation**: Ensure tests don't depend on each other's state

### Debug Mode
Run individual test methods for debugging:
```python
python -m unittest tests.unit.test_pr_manager.TestPRManager.test_specific_method -v
```