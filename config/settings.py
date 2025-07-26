import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # GitHub Configuration
    GITHUB_REPO_URL = os.getenv('GITHUB_REPO_URL')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_OWNER = os.getenv('GITHUB_OWNER')
    GITHUB_REPO = os.getenv('GITHUB_REPO')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Agent Configuration
    MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 5))
    DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/agent_logs.txt')

# Agent-specific configurations
AGENT_CONFIGS = {
    'project_manager': {
        'temperature': 0.3,
        'system_prompt': "You are a Project Manager AI agent responsible for coordinating tasks between different specialized agents.",
        'max_tokens': 1000,
        'model': 'gpt-4'
    },
    'prompt_ask_engineer': {
        'temperature': 0.5,
        'system_prompt': "You are a Prompt Ask Engineer AI agent that analyzes repository state and provides recommendations.",
        'max_tokens': 800,
        'model': 'gpt-4'
    },
    'prompt_code_engineer': {
        'temperature': 0.4,
        'system_prompt': "You are a Prompt Code Engineer AI agent that creates precise code tasks and prompts for the Code Agent.",
        'max_tokens': 1200,
        'model': 'gpt-4'
    },
    'code_agent': {
        'temperature': 0.2,
        'system_prompt': "You are a Code Agent AI responsible for writing, fixing, and editing code based on specific instructions.",
        'max_tokens': 2000,
        'model': 'gpt-4'
    },
    'github_manager': {
        'temperature': 0.1,
        'system_prompt': "You are a GitHub Manager AI agent responsible for repository operations and version control.",
        'max_tokens': 600,
        'model': 'gpt-3.5-turbo'
    }
}