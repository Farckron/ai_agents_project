# agents/prompt_code_engineer.py
from typing import List, Dict, Any
from utils.base_agent import BaseAgent

class PromptCodeEngineer(BaseAgent):
    """
    Agent that directly passes user instructions as code tasks.
    """
    def create_code_tasks(self, instructions: str) -> List[str]:
        # Simply wrap the full instruction as a single task
        return [instructions.strip()]

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_instruction = payload.get("analysis") or payload.get("user_request") or ""
        tasks = self.create_code_tasks(user_instruction)
        return {"code_tasks": tasks}