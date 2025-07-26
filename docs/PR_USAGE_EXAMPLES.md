# GitHub PR Automation - Usage Examples

This document provides practical examples of using the GitHub PR Automation System for various common scenarios.

## Table of Contents

1. [Basic PR Creation](#basic-pr-creation)
2. [Advanced PR Options](#advanced-pr-options)
3. [Repository Analysis](#repository-analysis)
4. [Asynchronous Operations](#asynchronous-operations)
5. [Error Handling](#error-handling)
6. [Integration Examples](#integration-examples)
7. [Best Practices](#best-practices)

---

## Basic PR Creation

### Example 1: Simple Bug Fix

Create a PR to fix a simple bug in your application.

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Fix the null pointer exception in the user authentication method",
    "repo_url": "https://github.com/mycompany/webapp"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "request_id": "pr_20241226_143022_001",
  "workflow_id": "wf_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "PR request created successfully. Workflow prepared for code changes."
}
```

### Example 2: Add New Feature

Create a PR to add a new feature to your application.

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add email validation to the user registration form with proper error messages",
    "repo_url": "https://github.com/mycompany/frontend-app"
  }'
```

### Example 3: Code Refactoring

Create a PR to refactor existing code for better maintainability.

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Refactor the database connection logic to use connection pooling and improve error handling",
    "repo_url": "https://github.com/mycompany/backend-api"
  }'
```

---

## Advanced PR Options

### Example 4: Custom Branch and PR Details

Create a PR with custom branch name, title, and description.

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Implement JWT token refresh mechanism for better security",
    "repo_url": "https://github.com/mycompany/auth-service",
    "options": {
      "branch_name": "feature/jwt-refresh-tokens",
      "pr_title": "[SECURITY] Implement JWT Token Refresh Mechanism",
      "pr_description": "## Overview\n\nThis PR implements JWT token refresh functionality to improve security by:\n\n- Adding refresh token generation\n- Implementing token rotation\n- Adding proper expiration handling\n\n## Testing\n\n- [ ] Unit tests for token refresh logic\n- [ ] Integration tests for auth flow\n- [ ] Security review completed",
      "base_branch": "develop"
    }
  }'
```

### Example 5: Targeting Specific Branch

Create a PR that targets a development branch instead of main.

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add logging to the payment processing module",
    "repo_url": "https://github.com/mycompany/payment-service",
    "options": {
      "base_branch": "develop",
      "branch_name": "feature/payment-logging"
    }
  }'
```

---

## Repository Analysis

### Example 6: Analyze Repository Structure

Before creating a PR, analyze the repository to understand its structure.

```bash
curl "http://localhost:5000/api/repository/analyze?repo_url=https://github.com/mycompany/webapp"
```

**Expected Response:**
```json
{
  "status": "success",
  "repository_url": "https://github.com/mycompany/webapp",
  "analysis": {
    "status": "success",
    "summary": "This is a React-based web application with Node.js backend. The project uses TypeScript, has comprehensive test coverage, and follows modern development practices.",
    "structure": {
      "total_files": 156,
      "languages": ["TypeScript", "JavaScript", "CSS", "HTML"],
      "frameworks": ["React", "Express.js", "Jest"]
    }
  },
  "repository_info": {
    "name": "webapp",
    "description": "Company web application",
    "language": "TypeScript",
    "stars": 23,
    "forks": 5
  },
  "analyzed_at": "2024-12-26T14:30:22.123456"
}
```

---

## Asynchronous Operations

### Example 7: Long-Running PR Creation

For complex changes that might take longer to process, use async operations.

```bash
# Start async PR creation
curl -X POST http://localhost:5000/api/async/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Migrate the entire codebase from JavaScript to TypeScript with proper type definitions",
    "repo_url": "https://github.com/mycompany/legacy-app"
  }'
```

**Response:**
```json
{
  "status": "accepted",
  "task_id": "pr_20241226_143500_async_001",
  "message": "PR creation started in background",
  "status_url": "/api/async/task/pr_20241226_143500_async_001/status"
}
```

**Check Status:**
```bash
curl http://localhost:5000/api/async/task/pr_20241226_143500_async_001/status
```

**Status Response:**
```json
{
  "status": "success",
  "task_id": "pr_20241226_143500_async_001",
  "task_info": {
    "status": "processing",
    "task_type": "pr_creation",
    "started_at": "2024-12-26T14:35:00.123456",
    "progress": 65
  }
}
```

---

## Error Handling

### Example 8: Handling Invalid Repository URL

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add error handling",
    "repo_url": "https://invalid-url.com/repo"
  }'
```

**Error Response:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid repository URL: URL must be a valid GitHub repository",
    "details": {
      "field": "repo_url",
      "provided_value": "https://invalid-url.com/repo"
    },
    "suggestions": [
      "Ensure URL starts with https://github.com/",
      "Check that the repository exists and is accessible",
      "Verify the repository URL format: https://github.com/owner/repo"
    ],
    "retry_possible": false
  },
  "timestamp": "2024-12-26T14:30:22.123456",
  "error_id": "ERR_1703601022_12345"
}
```

### Example 9: Handling Authentication Errors

```bash
# This would happen if GitHub token is invalid or missing
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add new feature",
    "repo_url": "https://github.com/private/repo"
  }'
```

**Error Response:**
```json
{
  "error": {
    "code": "authentication_error",
    "message": "GitHub authentication failed",
    "details": {
      "status_code": 401
    },
    "suggestions": [
      "Check if GitHub token is valid",
      "Verify token has required permissions",
      "Ensure token is not expired"
    ],
    "retry_possible": false
  },
  "timestamp": "2024-12-26T14:30:22.123456",
  "error_id": "ERR_1703601022_12346"
}
```

---

## Integration Examples

### Example 10: Python Integration

```python
import requests
import time
import json

class PRAutomationClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
    
    def create_pr_and_wait(self, user_request, repo_url, options=None, timeout=300):
        """Create PR and wait for completion"""
        
        # Create PR
        response = self.create_pr(user_request, repo_url, options)
        
        if response.get('status') != 'success':
            raise Exception(f"Failed to create PR: {response}")
        
        request_id = response['request_id']
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_pr_status(request_id)
            
            if status['pr_request']['status'] == 'completed':
                return status
            elif status['pr_request']['status'] == 'failed':
                raise Exception(f"PR creation failed: {status}")
            
            time.sleep(10)  # Wait 10 seconds before next check
        
        raise TimeoutError(f"PR creation timed out after {timeout} seconds")
    
    def create_pr(self, user_request, repo_url, options=None):
        payload = {
            "user_request": user_request,
            "repo_url": repo_url,
            "options": options or {}
        }
        
        response = requests.post(
            f"{self.base_url}/pr/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def get_pr_status(self, request_id):
        response = requests.get(f"{self.base_url}/pr/status/{request_id}")
        return response.json()

# Usage example
if __name__ == "__main__":
    client = PRAutomationClient()
    
    try:
        result = client.create_pr_and_wait(
            user_request="Add input validation to all API endpoints",
            repo_url="https://github.com/mycompany/api-server",
            options={
                "branch_name": "feature/api-validation",
                "pr_title": "Add comprehensive input validation"
            }
        )
        
        print(f"PR created successfully: {result['pr_request'].get('pr_url')}")
        
    except Exception as e:
        print(f"Error: {e}")
```

### Example 11: Node.js Integration

```javascript
const axios = require('axios');

class PRAutomationClient {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async createPR(userRequest, repoUrl, options = {}) {
        try {
            const response = await this.client.post('/pr/create', {
                user_request: userRequest,
                repo_url: repoUrl,
                options: options
            });
            
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`API Error: ${error.response.data.error?.message || error.response.statusText}`);
            }
            throw error;
        }
    }
    
    async getPRStatus(requestId) {
        try {
            const response = await this.client.get(`/pr/status/${requestId}`);
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`API Error: ${error.response.data.error?.message || error.response.statusText}`);
            }
            throw error;
        }
    }
    
    async createPRAndWait(userRequest, repoUrl, options = {}, timeout = 300000) {
        const result = await this.createPR(userRequest, repoUrl, options);
        
        if (result.status !== 'success') {
            throw new Error(`Failed to create PR: ${result.message}`);
        }
        
        const requestId = result.request_id;
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const status = await this.getPRStatus(requestId);
            
            if (status.pr_request.status === 'completed') {
                return status;
            } else if (status.pr_request.status === 'failed') {
                throw new Error(`PR creation failed: ${status.pr_request.error_message}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
        }
        
        throw new Error(`PR creation timed out after ${timeout}ms`);
    }
}

// Usage example
async function main() {
    const client = new PRAutomationClient();
    
    try {
        const result = await client.createPRAndWait(
            'Implement rate limiting for API endpoints',
            'https://github.com/mycompany/api-gateway',
            {
                branch_name: 'feature/rate-limiting',
                pr_title: 'Implement API Rate Limiting'
            }
        );
        
        console.log(`PR created successfully: ${result.pr_request.pr_url}`);
        
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
}

main();
```

### Example 12: GitHub Actions Integration

Create a GitHub Action workflow that uses the PR automation system:

```yaml
# .github/workflows/auto-pr.yml
name: Automated PR Creation

on:
  issues:
    types: [labeled]

jobs:
  create-pr:
    if: contains(github.event.label.name, 'auto-fix')
    runs-on: ubuntu-latest
    
    steps:
    - name: Create Automated PR
      run: |
        curl -X POST ${{ secrets.PR_AUTOMATION_URL }}/api/pr/create \
          -H "Content-Type: application/json" \
          -d '{
            "user_request": "${{ github.event.issue.title }}: ${{ github.event.issue.body }}",
            "repo_url": "${{ github.event.repository.html_url }}",
            "options": {
              "branch_name": "auto-fix/issue-${{ github.event.issue.number }}",
              "pr_title": "Auto-fix: ${{ github.event.issue.title }}",
              "pr_description": "Automated fix for issue #${{ github.event.issue.number }}\n\n${{ github.event.issue.body }}"
            }
          }'
```

---

## Best Practices

### 1. Clear and Specific Requests

**Good:**
```json
{
  "user_request": "Add input validation to the user registration endpoint to check for valid email format, password strength (minimum 8 characters, at least one uppercase, one lowercase, one number), and prevent SQL injection"
}
```

**Avoid:**
```json
{
  "user_request": "Fix the registration"
}
```

### 2. Use Descriptive Branch Names

**Good:**
```json
{
  "options": {
    "branch_name": "feature/user-registration-validation",
    "pr_title": "Add comprehensive input validation to user registration"
  }
}
```

**Avoid:**
```json
{
  "options": {
    "branch_name": "fix",
    "pr_title": "Updates"
  }
}
```

### 3. Monitor PR Status

Always check the status of your PR requests:

```python
# Good practice: Check status periodically
def monitor_pr(client, request_id, max_wait=300):
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = client.get_pr_status(request_id)
        print(f"Status: {status['pr_request']['status']}")
        
        if status['pr_request']['status'] in ['completed', 'failed']:
            return status
        
        time.sleep(30)  # Check every 30 seconds
    
    return None
```

### 4. Handle Errors Gracefully

```python
def create_pr_with_retry(client, user_request, repo_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = client.create_pr(user_request, repo_url)
            
            if result.get('status') == 'success':
                return result
            
            # Handle specific error cases
            if 'rate_limit' in result.get('error', {}).get('code', ''):
                wait_time = result['error']['details'].get('wait_time_seconds', 60)
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            # Non-retryable error
            if not result.get('error', {}).get('retry_possible', True):
                raise Exception(f"Non-retryable error: {result['error']['message']}")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception("Max retries exceeded")
```

### 5. Repository Analysis First

For complex changes, analyze the repository structure first:

```python
def smart_pr_creation(client, user_request, repo_url):
    # Analyze repository first
    analysis = client.analyze_repository(repo_url)
    
    # Adjust request based on analysis
    if 'TypeScript' in analysis['analysis']['structure']['languages']:
        user_request += " Make sure to include proper TypeScript type definitions."
    
    if 'React' in analysis['analysis']['structure']['frameworks']:
        user_request += " Follow React best practices and hooks patterns."
    
    # Create PR with enhanced context
    return client.create_pr(user_request, repo_url)
```

---

## Troubleshooting Common Issues

### Issue 1: "Repository not found"
- Verify the repository URL is correct
- Check that the repository is public or your token has access
- Ensure the repository exists

### Issue 2: "Authentication failed"
- Verify your GitHub token is valid
- Check token permissions include 'repo' scope
- Ensure token is not expired

### Issue 3: "Rate limit exceeded"
- Wait for the rate limit to reset
- Use authenticated requests for higher limits
- Implement proper retry logic with backoff

### Issue 4: "PR creation timeout"
- Complex changes may take longer
- Use async endpoints for long-running operations
- Monitor progress using status endpoints

For more troubleshooting information, see the [Troubleshooting Guide](TROUBLESHOOTING.md).