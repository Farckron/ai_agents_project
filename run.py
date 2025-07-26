#!/usr/bin/env python3
"""
Simple startup script for GitHub PR Automation System (Windows compatible)
"""

import os
import sys
import subprocess

def check_env():
    """Check environment configuration"""
    print("Checking configuration...")
    
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
        missing = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            print(f"ERROR: Missing environment variables: {', '.join(missing)}")
            return False
        
        print("Configuration OK")
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

def run_basic_test():
    """Run basic integration test"""
    print("Running basic test...")
    
    try:
        # Simple import test
        from agents.pr_manager import PRManager
        from agents.github_manager import GitHubManager
        print("Imports OK")
        
        # Simple initialization test
        pm = PRManager()
        print("PRManager OK")
        
        # Test branch name generation
        branch_name = pm.generate_branch_name('test feature')
        if branch_name:
            print(f"Branch generation OK: {branch_name}")
        
        print("Basic test PASSED")
        return True
        
    except Exception as e:
        print(f"Basic test FAILED: {e}")
        return False

def start_flask():
    """Start Flask application"""
    print("Starting Flask server...")
    print("Server will run on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        os.environ['FLASK_APP'] = 'main.py'
        os.environ['FLASK_ENV'] = 'development'
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

def main():
    print("GitHub PR Automation System - Startup")
    print("=" * 50)
    
    # Check configuration
    if not check_env():
        print("\nPlease fix configuration in .env file")
        return
    
    # Run basic test
    if not run_basic_test():
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    print("\n" + "=" * 50)
    print("System ready!")
    print("=" * 50)
    
    # Start Flask server
    start_flask()

if __name__ == "__main__":
    main()