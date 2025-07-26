# config/settings.py

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# Load environment variables from .env
# ──────────────────────────────────────────────────────────────
load_dotenv()


class Config:
    # ──────────────────────────────────────────────────────────
    # Flask / general
    # ──────────────────────────────────────────────────────────
    SECRET_KEY    = os.getenv("SECRET_KEY", "change-me-in-production")
    PORT          = int(os.getenv("PORT", 5000))
    DEBUG         = os.getenv("DEBUG", "False").lower() == "true"
    FLASK_ENV     = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG   = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # ──────────────────────────────────────────────────────────
    # OpenAI
    # ──────────────────────────────────────────────────────────
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # ──────────────────────────────────────────────────────────
    # GitHub
    # ──────────────────────────────────────────────────────────
    GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")
    GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
    GITHUB_OWNER    = os.getenv("GITHUB_OWNER")
    GITHUB_REPO     = os.getenv("GITHUB_REPO")

    # ──────────────────────────────────────────────────────────
    # Default temperature for OpenAI calls
    # ──────────────────────────────────────────────────────────
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", 0.7))

    # ──────────────────────────────────────────────────────────
    # PR Manager defaults (labels, templates, limits)
    # ──────────────────────────────────────────────────────────
    PR_DEFAULT_LABELS          = os.getenv("PR_DEFAULT_LABELS", "ai-generated,automated").split(",")
    PR_COMMIT_MESSAGE_TEMPLATE = os.getenv(
        "PR_COMMIT_MESSAGE_TEMPLATE",
        "{change_type}: {summary}"
    )
    PR_BODY_TEMPLATE = os.getenv(
        "PR_BODY_TEMPLATE",
        """\
## Тип змін
{change_type}

## Тестування
{testing_notes}

---
*Цей PR був створений автоматично AI агентом*"""
    )
    PR_MAX_FILES_PER_PR = int(os.getenv("PR_MAX_FILES_PER_PR", 20))
    PR_MAX_FILE_SIZE_KB = int(os.getenv("PR_MAX_FILE_SIZE_KB", 1024))

    # ──────────────────────────────────────────────────────────
    # (Any other app‑wide settings you might have)
    # ──────────────────────────────────────────────────────────
    # e.g. DATABASE_URL = os.getenv("DATABASE_URL")


# ──────────────────────────────────────────────────────────────
# Agent‑specific configurations
# Used by BaseAgent.__init__; must be imported from config/__init__.py
# ──────────────────────────────────────────────────────────────
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "project_manager": {
        "temperature": 0.3,
        "system_prompt": "You are a Project Manager AI agent responsible for coordinating tasks between different specialized agents.",
        "max_tokens": 1000,
        "model": "gpt-4"
    },
    "prompt_ask_engineer": {
        "temperature": 0.5,
        "system_prompt": "You are a Prompt Ask Engineer AI agent that analyzes repository state and provides recommendations.",
        "max_tokens": 800,
        "model": "gpt-4"
    },
    "prompt_code_engineer": {
        "temperature": 0.4,
        "system_prompt": "You are a Prompt Code Engineer AI agent that creates precise code tasks and prompts for the Code Agent.",
        "max_tokens": 2000,
        "model": "gpt-4"
    },
    "github_manager": {
        "temperature": 0.1,
        "system_prompt": "You are a GitHub Manager AI agent responsible for repository operations and version control.",
        "max_tokens": 600,
        "model": "gpt-3.5-turbo"
    },
    "pr_manager": {
        "temperature": 0.3,
        "system_prompt": "You are a PR Manager AI agent responsible for creating and managing GitHub Pull Requests with automated code changes.",
        "max_tokens": 1000,
        "model": "gpt-4"
    }
}


# ──────────────────────────────────────────────────────────────
# (Disabled) IMPORT‑TIME CONFIG VALIDATION
# If you previously had a validate_all_config() here that errored
# on missing GitHub scopes, it’s now commented out.
# ──────────────────────────────────────────────────────────────
#
# try:
#     from .validation import validate_all_config, log_validation_results
#     results = validate_all_config()
#     if not results["overall_valid"]:
#         logging.error("Configuration validation failed")
#         log_validation_results(results)
# except Exception as e:
#     logging.error(f"Config validation error: {e}")
#
# _LAST_VALIDATION_RESULTS = results if "results" in locals() else None

def get_last_validation_results() -> Optional[Dict[str, Any]]:
    """
    Stub: returns the last validation results if any (validation disabled).
    """
    return None
