# main.py
import os
import logging
import threading
from uuid import uuid4
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

# Agents
from agents.project_manager      import ProjectManager
from agents.prompt_ask_engineer  import PromptAskEngineer
from agents.prompt_code_engineer import PromptCodeEngineer
from agents.code_agent           import CodeAgent
from agents.github_manager       import GitHubManager
from agents.pr_manager           import PRManager

# Utils / validation
from models.validation   import validate_pr_request, validate_repository_url

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE  = os.getenv("LOG_FILE", "logs/app.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Instantiate agents ONCE and wire them up
# ──────────────────────────────────────────────────────────────
project_manager      = ProjectManager()
prompt_ask_engineer  = project_manager.prompt_ask_engineer
prompt_code_engineer = project_manager.prompt_code_engineer
code_agent           = project_manager.code_agent
github_manager       = project_manager.github_manager
pr_manager           = project_manager.pr_manager

AGENT_MAP = {
    "project_manager":      project_manager,
    "prompt_ask_engineer":  prompt_ask_engineer,
    "prompt_code_engineer": prompt_code_engineer,
    "code_agent":           code_agent,
    "github_manager":       github_manager,
    "pr_manager":           pr_manager,
}

# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html', default_repo=os.getenv("GITHUB_REPO_URL", ""))

@app.route('/api/status')
def api_status():
    return jsonify({
        "system": {"max_messages": int(os.getenv("MAX_MESSAGES", 100))},
        "openai": {"api_key_valid": bool(os.getenv("OPENAI_API_KEY"))},
        "github": {"token_configured": bool(os.getenv("GITHUB_TOKEN"))}
    })

@app.route('/api/agents/<agent_name>/status')
def agent_status(agent_name):
    agent = AGENT_MAP.get(agent_name)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    data = agent.status()
    data.update({
        'message_count': getattr(agent, 'message_count', 0),
        'temperature':   getattr(agent, 'temperature', None),
    })
    return jsonify(data)

@app.route('/api/agents/<agent_name>/reset', methods=['POST'])
def agent_reset(agent_name):
    agent = AGENT_MAP.get(agent_name)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    if hasattr(agent, 'message_history'):
        agent.message_history = []
        agent.message_count   = 0
    return jsonify({'status': 'success', 'agent': agent_name})

@app.route('/logs')
def view_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({'error': 'No log file found'}), 404
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    return jsonify(lines)

# ──────────────────────────────────────────────────────────────
# Async task worker
# ──────────────────────────────────────────────────────────────
background_tasks = {}
task_results     = {}

def execute_background_task(task_id, task_type, task_data):
    background_tasks[task_id] = {
        'status':     'processing',
        'task_type':  task_type,
        'started_at': datetime.now().isoformat(),
        'progress':   0
    }
    try:
        if task_type == 'pr_creation':
            result = project_manager.handle_pr_request(
                user_input=task_data['user_request'],
                repo_url=task_data['repo_url']
            )
            background_tasks[task_id].update({'progress': 100, 'status': 'completed'})
            task_results[task_id] = result
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    except Exception as e:
        background_tasks[task_id].update({
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })
        logger.exception(f"Background task {task_id} failed")

@app.route('/api/async/task/<task_id>/status')
def task_status(task_id):
    data = background_tasks.get(task_id)
    if not data:
        return jsonify({'error': 'Task not found'}), 404
    response = dict(data)
    if data.get('status') == 'completed':
        response['result'] = task_results.get(task_id, {})
    return jsonify(response)

# ──────────────────────────────────────────────────────────────
# PR creation API
# ──────────────────────────────────────────────────────────────
@app.route('/api/pr/create', methods=['POST'])
def create_pr():
    data = request.get_json() or {}
    repo_url = data.get('repo_url') or os.getenv("GITHUB_REPO_URL", "")

    valid, msg = validate_repository_url(repo_url)
    if not valid:
        return jsonify({'error': msg}), 400

    valid, msg = validate_pr_request(data)
    if not valid:
        return jsonify({'error': msg}), 400

    task_id = f"task-{uuid4().hex}"
    background_tasks[task_id] = {
        'status': 'queued',
        'task_type': 'pr_creation',
        'progress': 0,
        'queued_at': datetime.now().isoformat()
    }
    threading.Thread(
        target=execute_background_task,
        args=(task_id, 'pr_creation', {'user_request': data['user_request'], 'repo_url': repo_url}),
        daemon=True
    ).start()
    return jsonify({'task_id': task_id, 'status': 'processing'})

# ──────────────────────────────────────────────────────────────
# Session utilities
# ──────────────────────────────────────────────────────────────
@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    try:
        session.clear()
        return jsonify({'message': 'Session cleared'})
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({'error': str(e)}), 500

# ──────────────────────────────────────────────────────────────
# Run app
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    logger.info("AI Agents Project starting up…")
    app.run(
        host='0.0.0.0',
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("DEBUG", "False").lower() == "true"
    )
