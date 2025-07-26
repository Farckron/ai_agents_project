# utils/base_agent.py
import os
from openai import OpenAI

class BaseAgent:
    """
    Base class for all agents handling OpenAI client initialization,
    and providing a unified call_openai & status interface.
    """
    def __init__(self, model: str = None, temperature: float = 0.2):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable")
        self.client = OpenAI(api_key=api_key)
        self.model = model or "gpt-3.5-turbo"
        self.temperature = temperature

    def call_openai(self, messages: list) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return resp.choices[0].message.content.strip()

    def status(self) -> dict:
        return {"status": "ready", "model": self.model, "temperature": self.temperature}