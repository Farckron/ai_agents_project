# API Documentation - GitHub PR Automation System

## Overview

This document provides comprehensive documentation for the GitHub PR Automation System API endpoints. The system allows automated creation of Pull Requests with AI-generated code changes.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, the system uses GitHub tokens configured via environment variables. No additional API authentication is required for local development.

## Content Type

All API endpoints expect and return JSON data:
```
Content-Type: application/json
```

---

## PR Management Endpoints

### Create Pull Request

Creates a new Pull Request with automated code changes.

**Endpoint:** `POST /pr/create`

**Request Body:**
```json
{
  "user_request": "string (required) - Description of changes to make",
  "repo_url": "string (required) - GitHub repository URL",
  "options": {
    "branch_name": "string (optional) - Custom branch name",
    "pr_title": "string (optional) - Custom PR title",
    "pr_description": "string (optional) - Custom PR description",
    "base_branch": "string (optional, default: main) - Target branch",
    "auto_merge": "boolean (optional, default: false) - Auto-merge PR"
  }
}
```

**Response:**
```json
{
  "status": "success|error",
  "request_id": "string - Unique request identifier",
  "workflow_id": "string - Workflow tracking ID",
  "message": "string - Status message",
  "pr_request": {
    "request_id": "string",
    "user_request": "string",
    "repo_url": "string",
    "status": "pending|processing|completed|failed",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
  },
  "workflow_details": {
    "branch_name": "string",
    "pr_title": "string",
    "pr_description": "string",
    "next_steps": ["array of strings"]
  }
}
```

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add error handling to the login function",
    "repo_url": "https://github.com/username/repository",
    "options": {
      "branch_name": "feature/add-error-handling",
      "pr_title": "Improve login error handling"
    }
  }'
```

**Example Response:**
```json
{
  "status": "success",
  "request_id": "pr_20241226_143022_001",
  "workflow_id": "wf_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "PR request created successfully. Workflow prepared for code changes.",
  "pr_request": {
    "request_id": "pr_20241226_143022_001",
    "user_request": "Add error handling to the login function",
    "repo_url": "https://github.com/username/repository",
    "status": "processing",
    "created_at": "2024-12-26T14:30:22.123456",
    "updated_at": "2024-12-26T14:30:22.123456"
  },
  "workflow_details": {
    "branch_name": "feature/add-error-handling",
    "pr_title": "Improve login error handling",
    "pr_description": "# Automated Changes\n\n## Summary\nAdd error handling to the login function\n\n...",
    "next_steps": [
      "Generate code changes using Code Agent",
      "Create branch and commit changes",
      "Create Pull Request"
    ]
  }
}
```

### Get PR Status

Retrieves the current status of a PR request.

**Endpoint:** `GET /pr/status/{request_id}`

**Parameters:**
- `request_id` (path) - The PR request ID

**Response:**
```json
{
  "status": "success|error",
  "request_id": "string",
  "pr_request": {
    "request_id": "string",
    "user_request": "string",
    "repo_url": "string",
    "status": "pending|processing|completed|failed",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime",
    "pr_url": "string (if completed)"
  },
  "workflow_status": {
    "workflow_id": "string",
    "status": "processing|completed|failed",
    "steps": [
      {
        "step_name": "string",
        "status": "pending|completed|failed",
        "timestamp": "ISO datetime"
      }
    ]
  }
}
```

**Example Request:**
```bash
curl http://localhost:5000/api/pr/status/pr_20241226_143022_001
```

---

## Repository Analysis Endpoints

### Analyze Repository

Analyzes a repository structure and provides insights.

**Endpoint:** `GET /repository/analyze`

**Query Parameters:**
- `repo_url` (required) - GitHub repository URL

**Response:**
```json
{
  "status": "success|error",
  "repository_url": "string",
  "analysis": {
    "status": "success",
    "summary": "string - AI-generated repository summary",
    "structure": {
      "total_files": "number",
      "languages": ["array of detected languages"],
      "frameworks": ["array of detected frameworks"]
    }
  },
  "repository_info": {
    "name": "string",
    "description": "string",
    "language": "string",
    "stars": "number",
    "forks": "number"
  },
  "analyzed_at": "ISO datetime"
}
```

**Example Request:**
```bash
curl "http://localhost:5000/api/repository/analyze?repo_url=https://github.com/username/repository"
```

---

## Asynchronous Operations

### Create PR Asynchronously

For long-running PR creation operations.

**Endpoint:** `POST /async/pr/create`

**Request Body:** Same as synchronous PR creation

**Response:**
```json
{
  "status": "accepted",
  "task_id": "string - Background task ID",
  "message": "PR creation started in background",
  "status_url": "string - URL to check task status"
}
```

### Get Async Task Status

**Endpoint:** `GET /async/task/{task_id}/status`

**Response:**
```json
{
  "status": "success",
  "task_id": "string",
  "task_info": {
    "status": "processing|completed|failed",
    "task_type": "pr_creation|repository_analysis|code_generation",
    "started_at": "ISO datetime",
    "progress": "number (0-100)",
    "completed_at": "ISO datetime (if completed)",
    "result": "object (if completed)"
  }
}
```

---

## System Status Endpoints

### Get System Status

**Endpoint:** `GET /status`

**Response:**
```json
{
  "system": {
    "status": "online",
    "timestamp": "ISO datetime",
    "max_messages": "number"
  },
  "agents": {
    "project_manager": {"status": "ready"},
    "github_manager": {"status": "ready"},
    "pr_manager": {"status": "ready"}
  },
  "openai": {
    "api_key_configured": "boolean",
    "api_key_valid": "boolean"
  },
  "github": {
    "token_configured": "boolean",
    "repo_configured": "boolean"
  }
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "string - Error code",
    "message": "string - Human-readable error message",
    "details": "object - Additional error details",
    "suggestions": ["array of strings - Suggested solutions"],
    "retry_possible": "boolean - Whether retry might succeed"
  },
  "timestamp": "ISO datetime",
  "error_id": "string - Unique error identifier for tracking"
}
```

### Common Error Codes

- `validation_error` - Invalid request parameters
- `authentication_error` - GitHub authentication failed
- `permission_denied` - Insufficient permissions
- `resource_not_found` - Repository or resource not found
- `rate_limit_exceeded` - GitHub API rate limit exceeded
- `github_api_error` - General GitHub API error
- `internal_error` - Internal server error

### HTTP Status Codes

- `200` - Success
- `202` - Accepted (for async operations)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication errors)
- `403` - Forbidden (permission errors)
- `404` - Not Found (resource not found)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

---

## Rate Limiting

The system respects GitHub API rate limits:
- **Authenticated requests:** 5,000 requests per hour
- **Unauthenticated requests:** 60 requests per hour

When rate limits are exceeded, the system will:
1. Return HTTP 429 status
2. Include retry-after information in response
3. Automatically retry with exponential backoff

---

## Webhooks (Future Feature)

*Note: Webhook functionality is planned for future releases.*

### PR Status Webhook

**Endpoint:** `POST /webhooks/pr-status`

Will notify external systems when PR status changes.

---

## SDK and Client Libraries

### Python Client Example

```python
import requests

class PRAutomationClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
    
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

# Usage
client = PRAutomationClient()
result = client.create_pr(
    user_request="Add input validation to user registration",
    repo_url="https://github.com/myorg/myrepo",
    options={"branch_name": "feature/input-validation"}
)
```

### JavaScript Client Example

```javascript
class PRAutomationClient {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
    }
    
    async createPR(userRequest, repoUrl, options = {}) {
        const response = await fetch(`${this.baseUrl}/pr/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_request: userRequest,
                repo_url: repoUrl,
                options: options
            })
        });
        
        return await response.json();
    }
    
    async getPRStatus(requestId) {
        const response = await fetch(`${this.baseUrl}/pr/status/${requestId}`);
        return await response.json();
    }
}

// Usage
const client = new PRAutomationClient();
const result = await client.createPR(
    'Add error handling to API endpoints',
    'https://github.com/myorg/myrepo',
    { branch_name: 'feature/error-handling' }
);
```

---

## Testing

### Health Check

```bash
curl http://localhost:5000/api/status
```

### Test PR Creation

```bash
curl -X POST http://localhost:5000/api/pr/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add a simple test function",
    "repo_url": "https://github.com/your-username/test-repo"
  }'
```

---

## Changelog

### Version 1.0.0 (Current)
- Initial API implementation
- PR creation and status endpoints
- Repository analysis
- Asynchronous operations
- Comprehensive error handling
- Structured logging integration

### Planned Features
- Webhook notifications
- Batch PR operations
- Template-based PR creation
- Advanced repository insights
- User authentication and authorization