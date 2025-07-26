#!/usr/bin/env python3
"""
Детальне тестування створення PR для діагностики проблем
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_api_endpoints():
    """Тестуємо різні API endpoints для діагностики"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 Діагностика API endpoints...")
    print("=" * 50)
    
    # Test 1: System status
    try:
        response = requests.get(f"{base_url}/api/status")
        print(f"✅ System Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   GitHub token configured: {data.get('github', {}).get('token_configured', 'Unknown')}")
            print(f"   OpenAI configured: {data.get('openai', {}).get('api_key_configured', 'Unknown')}")
    except Exception as e:
        print(f"❌ System Status Error: {e}")
    
    # Test 2: Repository analysis
    repo_url = f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}"
    try:
        response = requests.get(f"{base_url}/api/repository/analyze", params={"repo_url": repo_url})
        print(f"✅ Repository Analysis: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Repository Analysis Error: {e}")
    
    # Test 3: Simple process request (without PR creation)
    try:
        simple_request = {
            "request": "Analyze this repository structure",
            "repo_url": repo_url,
            "create_pr": False
        }
        
        response = requests.post(
            f"{base_url}/api/process_request",
            headers={"Content-Type": "application/json"},
            json=simple_request,
            timeout=30
        )
        
        print(f"✅ Simple Process Request: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Processing type: {data.get('processing_type', 'Unknown')}")
        else:
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Simple Process Request Error: {e}")

def test_direct_pr_creation():
    """Тестуємо пряме створення PR з мінімальними даними"""
    
    print("\n🚀 Тестування прямого створення PR...")
    print("=" * 50)
    
    # Мінімальний запит
    minimal_request = {
        "user_request": "Add simple hello.py file with print('Hello World')",
        "repo_url": f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}.git"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/pr/create",
            headers={"Content-Type": "application/json"},
            json=minimal_request,
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PR Creation Response:")
            print(json.dumps(result, indent=2))
        else:
            print("❌ PR Creation Failed:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Direct PR Creation Error: {e}")

def test_github_connectivity():
    """Тестуємо підключення до GitHub напряму"""
    
    print("\n🔗 Тестування GitHub підключення...")
    print("=" * 50)
    
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_OWNER')
    repo = os.getenv('GITHUB_REPO')
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Test repository access
    try:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
        print(f"✅ GitHub Repository Access: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"   Repository: {repo_data['full_name']}")
            print(f"   Permissions: {repo_data.get('permissions', {})}")
        else:
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ GitHub Repository Access Error: {e}")

if __name__ == "__main__":
    print("🔧 Детальна діагностика PR створення")
    print("=" * 60)
    
    test_api_endpoints()
    test_github_connectivity()
    test_direct_pr_creation()
    
    print("\n" + "=" * 60)
    print("Діагностика завершена!")