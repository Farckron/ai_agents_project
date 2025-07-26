# Troubleshooting Guide - GitHub PR Automation System

This guide helps you diagnose and resolve common issues with the GitHub PR Automation System.

## Table of Contents

1. [System Health Check](#system-health-check)
2. [Authentication Issues](#authentication-issues)
3. [Repository Access Problems](#repository-access-problems)
4. [PR Creation Failures](#pr-creation-failures)
5. [Performance Issues](#performance-issues)
6. [API Errors](#api-errors)
7. [Logging and Monitoring](#logging-and-monitoring)
8. [Configuration Problems](#configuration-problems)
9. [Network and Connectivity](#network-and-connectivity)
10. [Advanced Debugging](#advanced-debugging)

---

## System Health Check

### Quick Health Check

First, verify the system is running and healthy:

```bash
curl http://localhost:5000/api/status
```

**Expected Response:**
```json
{
  "system": {
    "status": "online",
    "timestamp": "2024-12-26T14:30:22.123456"
  },
  "agents": {
    "project_manager": {"status": "ready"},
    "github_manager": {"status": "ready"},
    "pr_manager": {"status": "ready"}
  },
  "openai": {
    "api_key_configured": true,
    "api_key_valid": true
  },
  "github": {
    "token_configured": true,
    "repo_configured": true
  }
}
```

### System Health Analysis

Check detailed system health using the log analyzer:

```python
from utils.log_analyzer import get_system_health

health = get_system_health()
print(f"System Status: {health['overall_status']}")

if health['issues']:
    print("Issues found:")
    for issue in health['issues']:
        print(f"  - {issue}")

if health['warnings']:
    print("Warnings:")
    for warning in health['warnings']:
        print(f"  - {warning}")
```

---

## Authentication Issues

### Problem: "GitHub authentication failed"

**Symptoms:**
- HTTP 401 errors
- "authentication_error" in API responses
- "api_key_valid": false in status check

**Solutions:**

1. **Check GitHub Token Configuration:**
   ```bash
   # Verify token is set
   echo $GITHUB_TOKEN
   
   # Check token format (should start with ghp_, gho_, etc.)
   echo $GITHUB_TOKEN | cut -c1-4
   ```

2. **Validate Token Permissions:**
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

3. **Check Token Scopes:**
   ```bash
   curl -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   # Look for X-OAuth-Scopes header
   ```

4. **Required Scopes:**
   - `repo` - Full repository access
   - `read:user` - Read user profile
   - `user:email` - Access user email

**Fix:**
1. Generate a new Personal Access Token at https://github.com/settings/tokens
2. Select required scopes: `repo`, `read:user`, `user:email`
3. Update environment variable:
   ```bash
   export GITHUB_TOKEN="your_new_token_here"
   ```
4. Restart the application

### Problem: "Token expired"

**Symptoms:**
- Intermittent authentication failures
- Previously working requests now fail

**Solutions:**
1. Check token expiration in GitHub settings
2. Generate a new token with the same scopes
3. Update the environment variable
4. Consider using GitHub Apps for long-term authentication

---

## Repository Access Problems

### Problem: "Repository not found" (404 Error)

**Symptoms:**
- HTTP 404 errors
- "resource_not_found" error code

**Diagnostic Steps:**

1. **Verify Repository URL:**
   ```bash
   # Test repository access manually
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/owner/repository
   ```

2. **Check Repository Visibility:**
   - Ensure repository is public OR your token has access to private repos
   - Verify you're a collaborator on private repositories

3. **Test Repository URL Format:**
   ```python
   from models.validation import validate_repository_url
   
   result = validate_repository_url("https://github.com/owner/repo")
   print(f"Valid: {result['is_valid']}")
   if not result['is_valid']:
       print(f"Error: {result['message']}")
   ```

**Common URL Issues:**
- ❌ `https://github.com/owner/repo.git` (includes .git)
- ❌ `https://github.com/owner/repo/` (trailing slash)
- ✅ `https://github.com/owner/repo` (correct format)

### Problem: "Permission denied" (403 Error)

**Symptoms:**
- HTTP 403 errors
- "permission_denied" error code

**Solutions:**

1. **Check Repository Permissions:**
   ```bash
   # Check if you can access the repository
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/owner/repository/collaborators/your-username
   ```

2. **Verify Organization Permissions:**
   - Check if organization requires SSO
   - Ensure token is authorized for organization access

3. **Check Branch Protection:**
   - Verify target branch allows direct pushes or PR creation
   - Check if branch protection rules block the operation

---

## PR Creation Failures

### Problem: PR Creation Hangs or Times Out

**Symptoms:**
- Requests take very long to complete
- Timeout errors
- Status remains "processing" indefinitely

**Diagnostic Steps:**

1. **Check Workflow Status:**
   ```bash
   curl http://localhost:5000/api/pr/status/your_request_id
   ```

2. **Monitor Performance Logs:**
   ```python
   from utils.log_analyzer import LogAnalyzer
   
   analyzer = LogAnalyzer()
   performance = analyzer.get_performance_metrics(hours=1)
   
   print("Slow operations:")
   for op in performance['slowest_operations']:
       print(f"  {op['operation']}: {op['max_duration_ms']}ms")
   ```

3. **Check System Resources:**
   ```bash
   # Check memory usage
   ps aux | grep python
   
   # Check disk space
   df -h
   ```

**Solutions:**

1. **Use Async Endpoints:**
   ```bash
   curl -X POST http://localhost:5000/api/async/pr/create \
     -H "Content-Type: application/json" \
     -d '{"user_request": "...", "repo_url": "..."}'
   ```

2. **Simplify Requests:**
   - Break complex changes into smaller PRs
   - Be more specific in user requests
   - Avoid very large repositories

3. **Increase Timeouts:**
   ```python
   # In config/settings.py
   GITHUB_API_SETTINGS = {
       'timeout': 60,  # Increase from 30 to 60 seconds
       # ...
   }
   ```

### Problem: "Branch already exists"

**Symptoms:**
- Error message about existing branch
- PR creation fails at branch creation step

**Solutions:**

1. **Use Unique Branch Names:**
   ```json
   {
     "options": {
       "branch_name": "feature/fix-login-$(date +%s)"
     }
   }
   ```

2. **Let System Generate Names:**
   ```json
   {
     "user_request": "Fix login issue",
     "repo_url": "...",
     // Don't specify branch_name - system will generate unique name
   }
   ```

3. **Delete Existing Branch:**
   ```bash
   # Via GitHub API
   curl -X DELETE \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/owner/repo/git/refs/heads/branch-name
   ```

### Problem: "No changes detected"

**Symptoms:**
- PR workflow completes but no actual changes made
- Empty commits or PRs

**Diagnostic Steps:**

1. **Check Repository Analysis:**
   ```bash
   curl "http://localhost:5000/api/repository/analyze?repo_url=https://github.com/owner/repo"
   ```

2. **Review User Request Clarity:**
   - Ensure request is specific and actionable
   - Include file paths or specific functions when possible

**Solutions:**

1. **Improve Request Specificity:**
   ```json
   // Instead of:
   {"user_request": "Fix bugs"}
   
   // Use:
   {"user_request": "Fix the null pointer exception in src/auth/login.py line 45 by adding proper null checks"}
   ```

2. **Provide Context:**
   ```json
   {
     "user_request": "Add error handling to the login function in src/auth/login.py. The function should catch exceptions and return appropriate error messages to the user.",
     "repo_url": "..."
   }
   ```

---

## Performance Issues

### Problem: Slow API Response Times

**Symptoms:**
- API calls take longer than 10 seconds
- Timeouts in client applications

**Diagnostic Steps:**

1. **Check Performance Metrics:**
   ```python
   from utils.log_analyzer import LogAnalyzer
   
   analyzer = LogAnalyzer()
   metrics = analyzer.get_performance_metrics(hours=24)
   
   for operation, stats in metrics['average_response_times'].items():
       print(f"{operation}: {stats['average_ms']:.2f}ms avg, {stats['max_ms']:.2f}ms max")
   ```

2. **Monitor System Resources:**
   ```bash
   # CPU usage
   top -p $(pgrep -f "python.*main.py")
   
   # Memory usage
   ps -o pid,vsz,rss,comm -p $(pgrep -f "python.*main.py")
   ```

**Solutions:**

1. **Enable Caching:**
   ```python
   # In agents/github_manager.py
   # Implement repository analysis caching
   ```

2. **Use Async Operations:**
   ```bash
   # For long-running operations
   curl -X POST http://localhost:5000/api/async/pr/create
   ```

3. **Optimize Database Queries:**
   - Add indexes to frequently queried fields
   - Use connection pooling
   - Implement query result caching

### Problem: High Memory Usage

**Symptoms:**
- System becomes unresponsive
- Out of memory errors

**Solutions:**

1. **Limit Concurrent Operations:**
   ```python
   # In config/settings.py
   MAX_CONCURRENT_WORKFLOWS = 5
   ```

2. **Clear Caches Periodically:**
   ```python
   # Add to scheduled tasks
   def cleanup_caches():
       github_manager.repo_cache.clear()
   ```

3. **Monitor Memory Usage:**
   ```python
   import psutil
   
   def log_memory_usage():
       process = psutil.Process()
       memory_mb = process.memory_info().rss / 1024 / 1024
       print(f"Memory usage: {memory_mb:.2f} MB")
   ```

---

## API Errors

### Problem: Rate Limit Exceeded (429 Error)

**Symptoms:**
- HTTP 429 responses
- "rate_limit_exceeded" error code
- Temporary API failures

**Solutions:**

1. **Check Rate Limit Status:**
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/rate_limit
   ```

2. **Implement Retry Logic:**
   ```python
   import time
   
   def api_call_with_retry(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise
               
               wait_time = e.reset_time - time.time()
               print(f"Rate limited. Waiting {wait_time} seconds...")
               time.sleep(wait_time)
   ```

3. **Use Authenticated Requests:**
   - Authenticated requests have higher rate limits (5,000/hour vs 60/hour)
   - Ensure GitHub token is properly configured

### Problem: Validation Errors (400 Error)

**Symptoms:**
- HTTP 400 responses
- "validation_error" error code
- Request rejected before processing

**Common Validation Issues:**

1. **Missing Required Fields:**
   ```json
   // ❌ Missing user_request
   {
     "repo_url": "https://github.com/owner/repo"
   }
   
   // ✅ All required fields
   {
     "user_request": "Fix login bug",
     "repo_url": "https://github.com/owner/repo"
   }
   ```

2. **Invalid Repository URL:**
   ```json
   // ❌ Invalid format
   {
     "repo_url": "github.com/owner/repo"
   }
   
   // ✅ Correct format
   {
     "repo_url": "https://github.com/owner/repo"
   }
   ```

3. **Invalid Options:**
   ```json
   // ❌ Invalid branch name
   {
     "options": {
       "branch_name": "feature/fix bug"  // Spaces not allowed
     }
   }
   
   // ✅ Valid branch name
   {
     "options": {
       "branch_name": "feature/fix-bug"
     }
   }
   ```

---

## Logging and Monitoring

### Enable Debug Logging

1. **Set Log Level:**
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. **Check Log Files:**
   ```bash
   # Main application logs
   tail -f logs/agent_logs.txt
   
   # PR operation logs
   tail -f logs/pr_operations.log
   
   # Performance logs
   tail -f logs/performance.log
   
   # Security logs
   tail -f logs/security.log
   ```

3. **Analyze Logs Programmatically:**
   ```python
   from utils.log_analyzer import LogAnalyzer
   
   analyzer = LogAnalyzer()
   
   # Get PR operation summary
   pr_summary = analyzer.get_pr_operation_summary(hours=24)
   print(f"Success rate: {pr_summary['success_rate']:.2f}%")
   
   # Check for security events
   security = analyzer.get_security_events(hours=24)
   if security['high_severity_events']:
       print("High severity security events detected!")
   ```

### Monitor System Health

1. **Automated Health Checks:**
   ```python
   from utils.log_analyzer import get_system_health
   
   def health_check():
       health = get_system_health()
       
       if health['overall_status'] != 'healthy':
           # Send alert
           print(f"System unhealthy: {health['issues']}")
           
       return health
   ```

2. **Performance Monitoring:**
   ```python
   from utils.structured_logger import get_structured_logger
   
   logger = get_structured_logger("monitoring")
   
   with logger.performance_timer("api_call"):
       # Your API call here
       result = make_api_call()
   ```

---

## Configuration Problems

### Problem: Environment Variables Not Loaded

**Symptoms:**
- Configuration values are None or default
- Authentication failures despite correct tokens

**Solutions:**

1. **Check .env File:**
   ```bash
   # Verify .env file exists and has correct format
   cat .env
   
   # Should contain:
   GITHUB_TOKEN=your_token_here
   OPENAI_API_KEY=your_key_here
   GITHUB_REPO_URL=https://github.com/owner/repo
   ```

2. **Verify Environment Loading:**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   print(f"GitHub Token: {'Set' if os.getenv('GITHUB_TOKEN') else 'Not Set'}")
   print(f"OpenAI Key: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not Set'}")
   ```

3. **Check File Permissions:**
   ```bash
   ls -la .env
   # Should be readable by the application user
   ```

### Problem: Invalid Configuration Values

**Symptoms:**
- Configuration validation errors on startup
- Unexpected behavior

**Solutions:**

1. **Run Configuration Validation:**
   ```python
   from config.settings import validate_all_config
   
   results = validate_all_config()
   
   if not results['overall_valid']:
       print("Configuration issues found:")
       for category, data in results.items():
           if not data.get('valid', True):
               print(f"  {category}: {data.get('errors', data.get('error'))}")
   ```

2. **Fix Common Issues:**
   ```bash
   # GitHub token format
   echo $GITHUB_TOKEN | grep -E '^gh[pous]_[A-Za-z0-9_]{36,}$'
   
   # Repository URL format
   echo $GITHUB_REPO_URL | grep -E '^https://github\.com/[^/]+/[^/]+$'
   ```

---

## Network and Connectivity

### Problem: Cannot Connect to GitHub API

**Symptoms:**
- Connection timeout errors
- DNS resolution failures
- Network unreachable errors

**Diagnostic Steps:**

1. **Test Basic Connectivity:**
   ```bash
   # Test DNS resolution
   nslookup api.github.com
   
   # Test HTTP connectivity
   curl -I https://api.github.com
   
   # Test with timeout
   curl --connect-timeout 10 https://api.github.com/rate_limit
   ```

2. **Check Proxy Settings:**
   ```bash
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   echo $NO_PROXY
   ```

3. **Test from Application:**
   ```python
   import requests
   
   try:
       response = requests.get('https://api.github.com/rate_limit', timeout=10)
       print(f"Status: {response.status_code}")
   except requests.exceptions.ConnectTimeout:
       print("Connection timeout")
   except requests.exceptions.ConnectionError:
       print("Connection error")
   ```

**Solutions:**

1. **Configure Proxy (if needed):**
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

2. **Increase Timeouts:**
   ```python
   # In config/settings.py
   GITHUB_API_SETTINGS = {
       'timeout': 60,  # Increase timeout
       'max_retries': 5,  # Increase retry attempts
   }
   ```

3. **Check Firewall Rules:**
   ```bash
   # Ensure outbound HTTPS (443) is allowed
   telnet api.github.com 443
   ```

---

## Advanced Debugging

### Enable Detailed Request Logging

1. **HTTP Request Logging:**
   ```python
   import logging
   import http.client as http_client
   
   # Enable HTTP debugging
   http_client.HTTPConnection.debuglevel = 1
   
   logging.basicConfig()
   logging.getLogger().setLevel(logging.DEBUG)
   requests_log = logging.getLogger("requests.packages.urllib3")
   requests_log.setLevel(logging.DEBUG)
   requests_log.propagate = True
   ```

2. **GitHub API Request Tracing:**
   ```python
   from github import Github
   
   # Enable GitHub library debugging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   g = Github(token, per_page=100)
   # All API calls will now be logged
   ```

### Database Query Debugging

1. **Enable SQL Logging:**
   ```python
   import logging
   
   # Enable SQLAlchemy logging (if using database)
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

2. **Monitor Database Connections:**
   ```python
   # Check connection pool status
   def check_db_connections():
       # Implementation depends on your database setup
       pass
   ```

### Memory and Performance Profiling

1. **Memory Profiling:**
   ```python
   import tracemalloc
   
   # Start tracing
   tracemalloc.start()
   
   # Your code here
   
   # Get memory usage
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
   print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
   
   tracemalloc.stop()
   ```

2. **Performance Profiling:**
   ```python
   import cProfile
   import pstats
   
   # Profile a function
   profiler = cProfile.Profile()
   profiler.enable()
   
   # Your code here
   
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(10)  # Top 10 functions
   ```

---

## Getting Help

### Collect Diagnostic Information

When reporting issues, include:

1. **System Information:**
   ```bash
   python --version
   pip list | grep -E "(requests|github|flask)"
   uname -a
   ```

2. **Configuration (sanitized):**
   ```python
   from config.settings import Config
   
   print(f"GitHub Token: {'Set' if Config.GITHUB_TOKEN else 'Not Set'}")
   print(f"OpenAI Key: {'Set' if Config.OPENAI_API_KEY else 'Not Set'}")
   print(f"Log Level: {Config.LOG_LEVEL}")
   ```

3. **Recent Logs:**
   ```bash
   tail -n 100 logs/agent_logs.txt
   tail -n 50 logs/pr_operations.log
   ```

4. **Error Details:**
   - Full error message
   - Request that caused the error
   - Steps to reproduce

### Support Channels

1. **Check Documentation:**
   - [API Documentation](API_DOCUMENTATION.md)
   - [Usage Examples](PR_USAGE_EXAMPLES.md)

2. **Review Logs:**
   - Use the log analyzer for insights
   - Check for patterns in errors

3. **Community Support:**
   - GitHub Issues
   - Stack Overflow (tag: github-pr-automation)

### Emergency Procedures

1. **System Recovery:**
   ```bash
   # Stop the application
   pkill -f "python.*main.py"
   
   # Clear temporary data
   rm -rf /tmp/pr_automation_*
   
   # Restart with clean state
   python main.py
   ```

2. **Database Recovery (if applicable):**
   ```bash
   # Backup current state
   cp database.db database.db.backup
   
   # Reset to clean state if needed
   rm database.db
   python -c "from models import init_db; init_db()"
   ```

Remember: Always backup your configuration and data before making significant changes!