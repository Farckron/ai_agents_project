#!/usr/bin/env python3
"""
Simple test script to verify the new API endpoints work correctly.
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_REPO_URL = "https://github.com/octocat/Hello-World"

def test_pr_create_endpoint():
    """Test the /api/pr/create endpoint"""
    print("Testing /api/pr/create endpoint...")
    
    payload = {
        "user_request": "Add a simple README improvement",
        "repo_url": TEST_REPO_URL,
        "options": {
            "branch_name": "test-branch-123",
            "pr_title": "Test PR Creation",
            "pr_description": "This is a test PR created by the API",
            "base_branch": "main"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/pr/create", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            return response.json().get('request_id')
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return None

def test_pr_status_endpoint(request_id):
    """Test the /api/pr/status/<request_id> endpoint"""
    if not request_id:
        print("Skipping PR status test - no request_id available")
        return
    
    print(f"\nTesting /api/pr/status/{request_id} endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/pr/status/{request_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_repository_analyze_endpoint():
    """Test the /api/repository/analyze endpoint"""
    print("\nTesting /api/repository/analyze endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/repository/analyze", 
                              params={"repo_url": TEST_REPO_URL})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_enhanced_process_request():
    """Test the enhanced /api/process_request endpoint"""
    print("\nTesting enhanced /api/process_request endpoint...")
    
    payload = {
        "request": "Analyze this repository structure",
        "repo_url": TEST_REPO_URL,
        "create_pr": False,
        "pr_options": {
            "branch_name": "analysis-branch",
            "pr_title": "Repository Analysis Results"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/process_request", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_async_endpoints():
    """Test the async endpoints"""
    print("\nTesting async PR creation endpoint...")
    
    payload = {
        "user_request": "Add async functionality test",
        "repo_url": TEST_REPO_URL,
        "options": {
            "branch_name": "async-test-branch",
            "pr_title": "Async Test PR"
        }
    }
    
    try:
        # Start async task
        response = requests.post(f"{BASE_URL}/api/async/pr/create", json=payload)
        print(f"Async PR Create Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 202:
            task_id = response.json().get('task_id')
            if task_id:
                # Check task status
                print(f"\nChecking task status for: {task_id}")
                time.sleep(2)  # Wait a bit for processing
                
                status_response = requests.get(f"{BASE_URL}/api/async/task/{task_id}/status")
                print(f"Task Status Code: {status_response.status_code}")
                print(f"Task Status: {json.dumps(status_response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_validation_errors():
    """Test validation error handling"""
    print("\nTesting validation error handling...")
    
    # Test with invalid repo URL
    payload = {
        "user_request": "Test request",
        "repo_url": "invalid-url",
        "options": {}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/pr/create", json=payload)
        print(f"Invalid URL Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test with missing required fields
    payload = {
        "repo_url": TEST_REPO_URL
        # Missing user_request
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/pr/create", json=payload)
        print(f"\nMissing Field Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Run all API endpoint tests"""
    print("=" * 60)
    print("API Endpoints Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Test repository: {TEST_REPO_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test new PR endpoints
    request_id = test_pr_create_endpoint()
    test_pr_status_endpoint(request_id)
    test_repository_analyze_endpoint()
    
    # Test enhanced existing endpoints
    test_enhanced_process_request()
    
    # Test async endpoints
    test_async_endpoints()
    
    # Test validation
    test_validation_errors()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()