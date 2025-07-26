# agents/project_manager.py
from typing import Dict, Any
from .base_agent import BaseAgent
from .prompt_ask_engineer import PromptAskEngineer
from .prompt_code_engineer import PromptCodeEngineer
from .code_agent import CodeAgent
from .github_manager import GitHubManager
from .pr_manager import PRManager

class ProjectManager(BaseAgent):
    def __init__(self):
        super().__init__("project_manager")

        # Instantiate once; share across app
        self.prompt_ask_engineer  = PromptAskEngineer()
        self.prompt_code_engineer = PromptCodeEngineer()
        self.code_agent           = CodeAgent()
        self.github_manager       = GitHubManager()
        self.pr_manager           = PRManager()

        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}

        self.log_message("Project Manager initialized")

    def handle_pr_request(self, user_input: str, repo_url: str) -> Dict[str, Any]:
        """
        Entry used by Flask worker. Returns a UI-ready result.
        """
        self.log_message(f"Starting PR workflow for {repo_url}")
        result = self.pr_manager.process_pr_request(
            user_request=user_input,
            repo_url=repo_url,
            options={}
        )
        self.log_message("PR workflow finished")
        return result

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base.update({
            "subagents": {
                "prompt_ask_engineer":    self.prompt_ask_engineer.status(),
                "prompt_code_engineer":   self.prompt_code_engineer.status(),
                "code_agent":             self.code_agent.status(),
                "github_manager":         self.github_manager.status(),
                "pr_manager":             self.pr_manager.status(),
            }
        })
        return base

    def get_project_status(self) -> Dict[str, Any]:
        return {
            "project_manager": self.status(),
            "current_tasks":   len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
        }
