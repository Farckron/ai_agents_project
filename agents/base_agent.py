# agents/base_agent.py

import os
import logging
from abc import ABC
from typing import Dict, Any, List
from datetime import datetime
from openai import OpenAI
from config.settings import AGENT_CONFIGS

# Global OpenAI client loaded from the environment
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class BaseAgent(ABC):
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        # Load per‑agent settings (temperature, prompts, model)
        self.config      = AGENT_CONFIGS.get(agent_type, {})

        # Temperature: env DEFAULT_TEMPERATURE fallback to 0.7
        default_temp     = float(os.getenv("DEFAULT_TEMPERATURE", 0.7))
        self.temperature = self.config.get("temperature", default_temp)

        # System prompt, max_tokens, model
        self.system_prompt = self.config.get("system_prompt", "")
        self.max_tokens    = self.config.get("max_tokens", 1000)
        self.model         = self.config.get("model", "gpt-4")

        # ────────────────────────────────────────────────────
        # Logging: read LOG_LEVEL/LOG_FILE from environment
        # ────────────────────────────────────────────────────
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level  = getattr(logging, level_name, logging.INFO)

        self.logger = logging.getLogger(f"Agent.{agent_type}")
        self.logger.setLevel(log_level)

        # Only add handlers once
        if not self.logger.handlers:
            fmt = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            # File handler
            log_file = os.getenv("LOG_FILE", "logs/app.log")
            fh = logging.FileHandler(log_file)
            fh.setFormatter(fmt)
            # Console handler
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)

            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        # For chat‐style agents
        self.message_history: List[Dict[str, str]] = []
        self.message_count   = 0

    def log_message(self, msg: str, level: str = "INFO") -> None:
        """
        Helper to uniform logging across agents.
        """
        fn = getattr(self.logger, level.lower(), self.logger.info)
        fn(f"[{self.agent_type}] {msg}")

    def status(self) -> Dict[str, Any]:
        """
        Report basic health / readiness.
        """
        return {
            "agent": self.agent_type,
            "ready": True,
            "timestamp": datetime.now().isoformat(),
        }
