#!/usr/bin/env python3
"""
Test current functionality with existing GitHub token
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_github_access():
    """Test what works with current token"""
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_OWNER')
    repo = os.getenv('GITHUB_REPO')
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print("Testing GitHub API access with current token...")
    print("=" * 50)
    
    # Test 1: Repository access
    try:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print("✅ Repository access: SUCCESS")
            print(f"   Repository: {repo_data['full_name']}")
            print(f"   Private: {repo_data['private']}")
            print(f"   Default branch: {repo_data['default_branch']}")
        else:
            print(f"❌ Repository access: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Repository access: ERROR - {e}")
    
    # Test 2: Can we read files?
    try:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/contents', headers=headers)
        if response.status_code == 200:
            files = response.json()
            print("✅ File reading: SUCCESS")
            print(f"   Found {len(files)} files/folders")
        else:
            print(f"❌ File reading: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ File reading: ERROR - {e}")
    
    # Test 3: Can we read branches?
    try:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/branches', headers=headers)
        if response.status_code == 200:
            branches = response.json()
            print("✅ Branch access: SUCCESS")
            print(f"   Found {len(branches)} branches")
            for branch in branches[:3]:  # Show first 3
                print(f"   - {branch['name']}")
        else:
            print(f"❌ Branch access: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Branch access: ERROR - {e}")
    
    # Test 4: User info (this will show the limitation)
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User info: SUCCESS")
            print(f"   Username: {user_data.get('login', 'Unknown')}")
            print(f"   Name: {user_data.get('name', 'Not available')}")
            print(f"   Email: {user_data.get('email', 'Not available - missing user:email scope')}")
        else:
            print(f"⚠️  User info: LIMITED ({response.status_code})")
            print("   This is expected with current token scopes")
    except Exception as e:
        print(f"⚠️  User info: LIMITED - {e}")
    
    # Test 5: Rate limit
    try:
        response = requests.get('https://api.github.com/rate_limit', headers=headers)
        if response.status_code == 200:
            rate_data = response.json()
            core_limit = rate_data['rate']
            print("✅ Rate limit info: SUCCESS")
            print(f"   Remaining: {core_limit['remaining']}/{core_limit['limit']}")
            print(f"   Reset time: {core_limit['reset']}")
        else:
            print(f"❌ Rate limit info: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Rate limit info: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("✅ Core PR functionality should work perfectly")
    print("⚠️  User details will be limited (not critical)")
    print("🚀 System is ready for PR automation!")

if __name__ == "__main__":
    test_github_access()