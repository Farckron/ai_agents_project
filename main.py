from flask import Flask, render_template, request, jsonify, session
import logging
import os
from datetime import datetime
from config.settings import Config
from agents.project_manager import ProjectManager
from utils.openai_utils import OpenAIUtils
from utils.github_utils import GitHubUtils

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

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

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Agent dashboard page"""
    return render_template('dashboard.html')

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
    """Process user request through the agent system"""
    try:
        data = request.get_json()
        user_request = data.get('request', '')
        repo_url = data.get('repo_url', Config.GITHUB_REPO_URL)
        
        if not user_request:
            return jsonify({'error': 'Request is required'}), 400
        
        logger.info(f"Processing user request: {user_request[:100]}...")
        
        # Process through project manager
        result = project_manager.handle_user_request(user_request, repo_url)
        
        # Store in session for tracking
        if 'requests' not in session:
            session['requests'] = []
        
        session['requests'].append({
            'request': user_request,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    """Get GitHub repository information"""
    try:
        repo_url = request.args.get('url', Config.GITHUB_REPO_URL)
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        # Validate URL
        if not github_utils.is_valid_github_url(repo_url):
            return jsonify({'error': 'Invalid GitHub URL'}), 400
        
        # Get repository info
        repo_info = github_utils.get_repository_info(repo_url)
        
        if repo_info:
            return jsonify({
                'status': 'success',
                'repository': repo_info
            })
        else:
            return jsonify({'error': 'Repository not found or inaccessible'}), 404
            
    except Exception as e:
        logger.error(f"Error getting repo info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/repo/summary')
def get_repo_summary():
    """Get AI-generated repository summary"""
    try:
        repo_url = request.args.get('url', Config.GITHUB_REPO_URL)
        
        result = project_manager.github_manager.process_task({
            'action': 'get_repo_summary',
            'repo_url': repo_url
        })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting repo summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/file/<path:file_path>')
def get_file_content(file_path):
    """Get content of a specific file from repository"""
    try:
        repo_url = request.args.get('repo', Config.GITHUB_REPO_URL)
        
        result = project_manager.github_manager.process_task({
            'action': 'get_file_content',
            'repo_url': repo_url,
            'file_path': file_path
        })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    """Generate code using Code Agent"""
    try:
        data = request.get_json()
        specification = data.get('specification', '')
        file_type = data.get('file_type', 'python')
        
        if not specification:
            return jsonify({'error': 'Specification is required'}), 400
        
        result = project_manager.code_agent.generate_code_from_spec(specification, file_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/review', methods=['POST'])
def review_code():
    """Review code quality using Code Agent"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        result = project_manager.code_agent.review_code_quality(code, language)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error reviewing code: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
