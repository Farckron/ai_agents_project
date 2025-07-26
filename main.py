from flask import Flask, render_template, request, jsonify, session
import logging
import os
import threading
import time
from datetime import datetime
from config.settings import Config
from agents.project_manager import ProjectManager
from utils.openai_utils import OpenAIUtils
from utils.github_utils import GitHubUtils
from models.pr_request import PRRequest, PRRequestOptions, RequestStatus
from models.validation import validate_pr_request, validate_repository_url
from utils.error_handler import ErrorHandler
from utils.structured_logger import get_structured_logger, log_user_request, log_security_violation, LogLevel

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

def execute_background_task(task_id, task_type, task_data):
    """Execute a background task and store the result"""
    try:
        background_tasks[task_id] = {
            'status': 'processing',
            'task_type': task_type,
            'started_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        if task_type == 'pr_creation':
            # Simulate PR creation process with progress updates
            background_tasks[task_id]['progress'] = 25
            time.sleep(1)  # Simulate work
            
            # Process PR request
            result = project_manager.pr_manager.process_pr_request(
                user_request=task_data['user_request'],
                repo_url=task_data['repo_url'],
                options=task_data.get('options', {})
            )
            
            background_tasks[task_id]['progress'] = 75
            time.sleep(0.5)  # Simulate more work
            
            background_tasks[task_id]['progress'] = 100
            background_tasks[task_id]['status'] = 'completed'
            background_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            task_results[task_id] = result
            
        elif task_type == 'repository_analysis':
            # Simulate repository analysis
            background_tasks[task_id]['progress'] = 50
            
            result = project_manager.github_manager.process_task({
                'action': 'get_repo_summary',
                'repo_url': task_data['repo_url']
            })
            
            background_tasks[task_id]['progress'] = 100
            background_tasks[task_id]['status'] = 'completed'
            background_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            task_results[task_id] = result
            
        elif task_type == 'code_generation':
            # Simulate code generation
            background_tasks[task_id]['progress'] = 30
            time.sleep(0.5)
            
            result = project_manager.code_agent.generate_code_from_spec(
                task_data['specification'],
                task_data.get('file_type', 'python')
            )
            
            background_tasks[task_id]['progress'] = 100
            background_tasks[task_id]['status'] = 'completed'
            background_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            task_results[task_id] = result
            
    except Exception as e:
        background_tasks[task_id]['status'] = 'failed'
        background_tasks[task_id]['error'] = str(e)
        background_tasks[task_id]['failed_at'] = datetime.now().isoformat()
        logger.error(f"Background task {task_id} failed: {str(e)}")

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize components
project_manager = ProjectManager()
openai_utils = OpenAIUtils()
github_utils = GitHubUtils()

# Initialize structured logger for main app
app_logger = get_structured_logger("main_app")

# In-memory storage for PR requests (in production, use a database)
pr_requests_storage = {}

# Background task storage for async operations
background_tasks = {}
task_results = {}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Agent dashboard page"""
    return render_template('dashboard.html')

# ============================================================================
# PR API Endpoints
# ============================================================================

@app.route('/api/pr/create', methods=['POST'])
def create_pr():
    """Create a new Pull Request with automated changes"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_request = data.get('user_request', '').strip()
        repo_url = data.get('repo_url', '').strip()
        
        if not user_request:
            return jsonify({'error': 'user_request is required'}), 400
        
        if not repo_url:
            return jsonify({'error': 'repo_url is required'}), 400
        
        # Validate repository URL
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        # Create PR request options
        options_data = data.get('options', {})
        options = PRRequestOptions(
            branch_name=options_data.get('branch_name'),
            pr_title=options_data.get('pr_title'),
            pr_description=options_data.get('pr_description'),
            base_branch=options_data.get('base_branch', 'main'),
            auto_merge=options_data.get('auto_merge', False)
        )
        
        # Create PR request
        pr_request = PRRequest(
            user_request=user_request,
            repo_url=repo_url,
            options=options
        )
        
        # Validate PR request
        validation_result = validate_pr_request(pr_request.to_dict())
        if not validation_result['is_valid']:
            return jsonify({'error': f'Invalid PR request: {validation_result["message"]}'}), 400
        
        # Store PR request
        pr_requests_storage[pr_request.request_id] = pr_request
        
        # Update status to processing
        pr_request.update_status(RequestStatus.PROCESSING)
        
        logger.info(f"Creating PR for request: {pr_request.request_id}")
        
        # Process through PR manager
        result = project_manager.pr_manager.process_pr_request(
            user_request=user_request,
            repo_url=repo_url,
            options=options.to_dict()
        )
        
        # Update PR request based on result
        if result.get('status') == 'ready_for_changes':
            # PR workflow is prepared, waiting for code changes
            response_data = {
                'status': 'success',
                'request_id': pr_request.request_id,
                'workflow_id': result.get('workflow_id'),
                'message': 'PR request created successfully. Workflow prepared for code changes.',
                'pr_request': pr_request.to_dict(),
                'workflow_details': result
            }
        elif result.get('status') == 'completed':
            pr_request.mark_completed(result.get('pr_url', ''))
            response_data = {
                'status': 'success',
                'request_id': pr_request.request_id,
                'message': 'PR created successfully',
                'pr_request': pr_request.to_dict(),
                'pr_url': result.get('pr_url')
            }
        else:
            # Handle error case
            error_message = result.get('message', 'Unknown error occurred')
            pr_request.mark_failed(error_message)
            response_data = {
                'status': 'error',
                'request_id': pr_request.request_id,
                'message': error_message,
                'pr_request': pr_request.to_dict()
            }
        
        # Log performance metric
        duration_ms = (time.time() - start_time) * 1000
        app_logger.log_performance_metric(
            metric_name="create_pr_duration",
            value=duration_ms,
            unit="ms",
            operation="create_pr",
            status=response_data.get('status', 'unknown'),
            request_id=pr_request.request_id
        )
        
        return jsonify(response_data)
        
    except Exception as e:
        # Log performance metric for failed request
        duration_ms = (time.time() - start_time) * 1000
        app_logger.log_performance_metric(
            metric_name="create_pr_duration",
            value=duration_ms,
            unit="ms",
            operation="create_pr",
            status="error"
        )
        
        error_msg = f"Error creating PR: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "PR creation failed")

@app.route('/api/pr/status/<request_id>')
def get_pr_status(request_id):
    """Get the status of a specific PR request"""
    try:
        # Check if request exists
        if request_id not in pr_requests_storage:
            return jsonify({'error': 'PR request not found'}), 404
        
        pr_request = pr_requests_storage[request_id]
        
        # Get workflow status from PR manager if available
        workflow_status = None
        if hasattr(project_manager, 'pr_manager'):
            workflow_result = project_manager.pr_manager.get_workflow_status(request_id)
            if workflow_result.get('status') == 'success':
                workflow_status = workflow_result.get('workflow')
        
        response_data = {
            'status': 'success',
            'request_id': request_id,
            'pr_request': pr_request.to_dict(),
            'workflow_status': workflow_status
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Error getting PR status: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to get PR status")

@app.route('/api/repository/analyze')
def analyze_repository():
    """Analyze a repository structure and provide insights"""
    try:
        repo_url = request.args.get('repo_url', '').strip()
        
        if not repo_url:
            return jsonify({'error': 'repo_url parameter is required'}), 400
        
        # Validate repository URL
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        logger.info(f"Analyzing repository: {repo_url}")
        
        # Get repository analysis from GitHub manager
        analysis_result = project_manager.github_manager.process_task({
            'action': 'get_repo_summary',
            'repo_url': repo_url
        })
        
        if analysis_result.get('status') == 'success':
            # Get additional repository information
            repo_info = github_utils.get_repository_info(repo_url)
            
            response_data = {
                'status': 'success',
                'repository_url': repo_url,
                'analysis': analysis_result,
                'repository_info': repo_info,
                'analyzed_at': datetime.now().isoformat()
            }
        else:
            response_data = {
                'status': 'error',
                'repository_url': repo_url,
                'message': analysis_result.get('error', 'Analysis failed'),
                'analyzed_at': datetime.now().isoformat()
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Error analyzing repository: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Repository analysis failed")

@app.route('/api/async/pr/create', methods=['POST'])
def create_pr_async():
    """Create a PR asynchronously for long-running operations"""
    try:
        data = request.get_json()
        
        # Validate required fields (same as sync version)
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_request = data.get('user_request', '').strip()
        repo_url = data.get('repo_url', '').strip()
        
        if not user_request or not repo_url:
            return jsonify({'error': 'user_request and repo_url are required'}), 400
        
        # Validate repository URL
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        # Generate task ID
        task_id = f"pr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(background_tasks)}"
        
        # Prepare task data
        task_data = {
            'user_request': user_request,
            'repo_url': repo_url,
            'options': data.get('options', {})
        }
        
        # Start background task
        thread = threading.Thread(
            target=execute_background_task,
            args=(task_id, 'pr_creation', task_data)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'accepted',
            'task_id': task_id,
            'message': 'PR creation started in background',
            'status_url': f'/api/async/task/{task_id}/status'
        }), 202
        
    except Exception as e:
        error_msg = f"Error starting async PR creation: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to start async PR creation")

@app.route('/api/async/task/<task_id>/status')
def get_async_task_status(task_id):
    """Get the status of an async background task"""
    try:
        if task_id not in background_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task_info = background_tasks[task_id].copy()
        
        # Add result if task is completed
        if task_info['status'] == 'completed' and task_id in task_results:
            task_info['result'] = task_results[task_id]
        
        return jsonify({
            'status': 'success',
            'task_id': task_id,
            'task_info': task_info
        })
        
    except Exception as e:
        error_msg = f"Error getting async task status: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to get task status")

@app.route('/api/async/repository/analyze', methods=['POST'])
def analyze_repository_async():
    """Analyze repository asynchronously"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        repo_url = data.get('repo_url', '').strip()
        
        if not repo_url:
            return jsonify({'error': 'repo_url is required'}), 400
        
        # Validate repository URL
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        # Generate task ID
        task_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(background_tasks)}"
        
        # Start background task
        thread = threading.Thread(
            target=execute_background_task,
            args=(task_id, 'repository_analysis', {'repo_url': repo_url})
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'accepted',
            'task_id': task_id,
            'message': 'Repository analysis started in background',
            'status_url': f'/api/async/task/{task_id}/status'
        }), 202
        
    except Exception as e:
        error_msg = f"Error starting async repository analysis: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to start async repository analysis")

# ============================================================================
# Existing API Endpoints
# ============================================================================

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        status = {
            'system': {
                'status': 'online',
                'timestamp': datetime.now().isoformat(),
                'max_messages': Config.MAX_MESSAGES
            },
            'agents': project_manager.get_project_status(),
            'openai': {
                'api_key_configured': bool(Config.OPENAI_API_KEY),
                'api_key_valid': openai_utils.validate_api_key()
            },
            'github': {
                'token_configured': bool(Config.GITHUB_TOKEN),
                'repo_configured': bool(Config.GITHUB_REPO_URL)
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_request', methods=['POST'])
def process_request():
    """Process user request through the agent system with enhanced PR support"""
    try:
        data = request.get_json()
        
        # Validate request body
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_request = data.get('request', '').strip()
        repo_url = data.get('repo_url', Config.GITHUB_REPO_URL or '').strip()
        
        # Enhanced validation
        if not user_request:
            return jsonify({'error': 'Request field is required and cannot be empty'}), 400
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        # Validate repository URL format
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        # Check for PR options in request
        pr_options = data.get('pr_options', {})
        create_pr = data.get('create_pr', False)
        
        logger.info(f"Processing user request: {user_request[:100]}... (create_pr: {create_pr})")
        
        # If PR creation is requested, use the PR workflow
        if create_pr:
            # Create PR request options
            options = PRRequestOptions(
                branch_name=pr_options.get('branch_name'),
                pr_title=pr_options.get('pr_title'),
                pr_description=pr_options.get('pr_description'),
                base_branch=pr_options.get('base_branch', 'main'),
                auto_merge=pr_options.get('auto_merge', False)
            )
            
            # Process through PR manager
            result = project_manager.pr_manager.process_pr_request(
                user_request=user_request,
                repo_url=repo_url,
                options=options.to_dict()
            )
            
            # Add PR-specific metadata to result
            result['processing_type'] = 'pr_workflow'
            result['pr_options'] = options.to_dict()
        else:
            # Process through standard project manager workflow
            result = project_manager.handle_user_request(user_request, repo_url)
            result['processing_type'] = 'standard_workflow'
        
        # Enhanced session tracking with more metadata
        if 'requests' not in session:
            session['requests'] = []
        
        session_entry = {
            'request': user_request,
            'repo_url': repo_url,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'processing_type': result.get('processing_type', 'standard_workflow'),
            'create_pr': create_pr
        }
        
        if create_pr:
            session_entry['pr_options'] = pr_options
        
        session['requests'].append(session_entry)
        
        # Limit session history to prevent memory issues
        if len(session['requests']) > 50:
            session['requests'] = session['requests'][-50:]
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Request processing failed")

@app.route('/api/agents/<agent_type>/status')
def get_agent_status(agent_type):
    """Get status of specific agent"""
    try:
        agent_map = {
            'project_manager': project_manager,
            'prompt_ask_engineer': project_manager.prompt_ask_engineer,
            'prompt_code_engineer': project_manager.prompt_code_engineer,
            'code_agent': project_manager.code_agent,
            'github_manager': project_manager.github_manager
        }
        
        agent = agent_map.get(agent_type)
        if not agent:
            return jsonify({'error': f'Unknown agent type: {agent_type}'}), 404
        
        status = agent.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/<agent_type>/reset', methods=['POST'])
def reset_agent(agent_type):
    """Reset specific agent conversation"""
    try:
        agent_map = {
            'project_manager': project_manager,
            'prompt_ask_engineer': project_manager.prompt_ask_engineer,
            'prompt_code_engineer': project_manager.prompt_code_engineer,
            'code_agent': project_manager.code_agent,
            'github_manager': project_manager.github_manager
        }
        
        agent = agent_map.get(agent_type)
        if not agent:
            return jsonify({'error': f'Unknown agent type: {agent_type}'}), 404
        
        agent.reset_conversation()
        return jsonify({'message': f'{agent_type} reset successfully'})
        
    except Exception as e:
        logger.error(f"Error resetting agent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/repo/info')
def get_repo_info():
    """Get GitHub repository information with enhanced validation"""
    try:
        repo_url = request.args.get('url', Config.GITHUB_REPO_URL or '').strip()
        
        # Enhanced validation
        if not repo_url:
            return jsonify({'error': 'Repository URL parameter is required'}), 400
        
        # Validate repository URL format
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        logger.info(f"Getting repository info for: {repo_url}")
        
        # Get repository info
        repo_info = github_utils.get_repository_info(repo_url)
        
        if repo_info:
            return jsonify({
                'status': 'success',
                'repository': repo_info,
                'retrieved_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Repository not found or inaccessible',
                'repository_url': repo_url
            }), 404
            
    except Exception as e:
        error_msg = f"Error getting repo info: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to get repository information")

@app.route('/api/github/repo/summary')
def get_repo_summary():
    """Get AI-generated repository summary with enhanced validation"""
    try:
        repo_url = request.args.get('url', Config.GITHUB_REPO_URL or '').strip()
        
        # Enhanced validation
        if not repo_url:
            return jsonify({'error': 'Repository URL parameter is required'}), 400
        
        # Validate repository URL format
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        logger.info(f"Getting repository summary for: {repo_url}")
        
        result = project_manager.github_manager.process_task({
            'action': 'get_repo_summary',
            'repo_url': repo_url
        })
        
        # Add metadata to response
        if result.get('status') == 'success':
            result['repository_url'] = repo_url
            result['generated_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error getting repo summary: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to get repository summary")

@app.route('/api/github/file/<path:file_path>')
def get_file_content(file_path):
    """Get content of a specific file from repository with enhanced validation"""
    try:
        repo_url = request.args.get('repo', Config.GITHUB_REPO_URL or '').strip()
        branch = request.args.get('branch', 'main').strip()
        
        # Enhanced validation
        if not repo_url:
            return jsonify({'error': 'Repository URL parameter is required'}), 400
        
        if not file_path or file_path.strip() == '':
            return jsonify({'error': 'File path is required'}), 400
        
        # Validate repository URL format
        url_validation = validate_repository_url(repo_url)
        if not url_validation['is_valid']:
            return jsonify({'error': f'Invalid repository URL: {url_validation["message"]}'}), 400
        
        # Basic file path security check
        if '..' in file_path or file_path.startswith('/'):
            return jsonify({'error': 'Invalid file path'}), 400
        
        logger.info(f"Getting file content: {file_path} from {repo_url} (branch: {branch})")
        
        result = project_manager.github_manager.process_task({
            'action': 'get_file_content',
            'repo_url': repo_url,
            'file_path': file_path,
            'branch': branch
        })
        
        # Add metadata to response
        if result.get('status') == 'success':
            result['repository_url'] = repo_url
            result['file_path'] = file_path
            result['branch'] = branch
            result['retrieved_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error getting file content: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Failed to get file content")

@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    """Generate code using Code Agent with enhanced validation"""
    try:
        data = request.get_json()
        
        # Validate request body
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        specification = data.get('specification', '').strip()
        file_type = data.get('file_type', 'python').strip().lower()
        context = data.get('context', {})
        
        # Enhanced validation
        if not specification:
            return jsonify({'error': 'Specification field is required and cannot be empty'}), 400
        
        if len(specification) > 10000:
            return jsonify({'error': 'Specification is too long (max 10000 characters)'}), 400
        
        # Validate file type
        supported_types = ['python', 'javascript', 'typescript', 'html', 'css', 'json', 'yaml', 'markdown']
        if file_type not in supported_types:
            return jsonify({
                'error': f'Unsupported file type: {file_type}',
                'supported_types': supported_types
            }), 400
        
        logger.info(f"Generating {file_type} code from specification: {specification[:100]}...")
        
        # Add enhanced context to the request
        enhanced_context = {
            'file_type': file_type,
            'timestamp': datetime.now().isoformat(),
            'user_context': context
        }
        
        result = project_manager.code_agent.generate_code_from_spec(specification, file_type)
        
        # Add metadata to response
        if result.get('status') == 'success':
            result['generation_context'] = enhanced_context
            result['generated_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error generating code: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Code generation failed")

@app.route('/api/code/review', methods=['POST'])
def review_code():
    """Review code quality using Code Agent with enhanced validation"""
    try:
        data = request.get_json()
        
        # Validate request body
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        code = data.get('code', '').strip()
        language = data.get('language', 'python').strip().lower()
        review_options = data.get('review_options', {})
        
        # Enhanced validation
        if not code:
            return jsonify({'error': 'Code field is required and cannot be empty'}), 400
        
        if len(code) > 50000:
            return jsonify({'error': 'Code is too long for review (max 50000 characters)'}), 400
        
        # Validate language
        supported_languages = ['python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust', 'php']
        if language not in supported_languages:
            return jsonify({
                'error': f'Unsupported language: {language}',
                'supported_languages': supported_languages
            }), 400
        
        logger.info(f"Reviewing {language} code ({len(code)} characters)")
        
        # Add enhanced options
        enhanced_options = {
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'code_length': len(code),
            'review_options': review_options
        }
        
        result = project_manager.code_agent.review_code_quality(code, language)
        
        # Add metadata to response
        if result.get('status') == 'success':
            result['review_context'] = enhanced_options
            result['reviewed_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error reviewing code: {str(e)}"
        logger.error(error_msg)
        return ErrorHandler.handle_api_error(e, "Code review failed")

@app.route('/api/logs')
def get_logs():
    """Get recent system logs"""
    try:
        lines = int(request.args.get('lines', 50))
        
        if os.path.exists(Config.LOG_FILE):
            with open(Config.LOG_FILE, 'r') as f:
                log_lines = f.readlines()
                recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
                
            return jsonify({
                'logs': [line.strip() for line in recent_logs],
                'total_lines': len(log_lines)
            })
        else:
            return jsonify({
                'logs': ['Log file not found'],
                'total_lines': 0
            })
            
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/requests')
def get_session_requests():
    """Get user requests from current session"""
    try:
        requests_history = session.get('requests', [])
        return jsonify({
            'requests': requests_history,
            'total': len(requests_history)
        })
        
    except Exception as e:
        logger.error(f"Error getting session requests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear current session data"""
    try:
        session.clear()
        return jsonify({'message': 'Session cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def startup():
    """Initialize application on startup"""
    logger.info("AI Agents Project starting up...")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    
    # Validate configuration
    if not Config.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured")
    
    if not Config.GITHUB_REPO_URL:
        logger.warning("GitHub repository URL not configured")
    
    logger.info("AI Agents Project startup complete")


if __name__ == '__main__':
    # run your startup tasks once, up front
    startup()
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
