# agents/prompt_ask_engineer.py
from utils.base_agent import BaseAgent

class PromptAskEngineer(BaseAgent):
    """
    Agent that analyzes a repo URL and recommends improvements.
    """
    def analyze_and_recommend(self, repo_url: str) -> str:
        system = (
            "You are an expert software architect and code reviewer. "
            "Given the GitHub repository URL below, produce a concise, prioritized list "
            "of architectural or process improvements (e.g., testing, CI/CD, code quality)."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": f"Repository URL: {repo_url}"},
        ]
        return self.call_openai(messages)

    # PRManager hooks
    summarize_repo = analyze_and_recommend
    analyze_repo   = analyze_and_recommend
    analyze        = analyze_and_recommend
    summarize      = analyze_and_recommend
