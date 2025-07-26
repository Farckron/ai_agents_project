import openai
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from config.settings import Config, AGENT_CONFIGS

class BaseAgent(ABC):
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.config = AGENT_CONFIGS.get(agent_type, {})
        self.temperature = self.config.get('temperature', Config.DEFAULT_TEMPERATURE)
        self.system_prompt = self.config.get('system_prompt', '')
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.model = self.config.get('model', 'gpt-4')
        
        # Initialize OpenAI client
        openai.api_key = Config.OPENAI_API_KEY
        
        # Setup logging
        self.logger = logging.getLogger(f"Agent.{agent_type}")
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Message history
        self.message_history: List[Dict[str, str]] = []
        self.message_count = 0
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log agent messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{self.agent_type}] [{level}] {message}"
        
        if level.upper() == "ERROR":
            self.logger.error(log_entry)
        elif level.upper() == "WARNING":
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        if self.message_count >= Config.MAX_MESSAGES:
            self.log_message("Maximum message limit reached!", "WARNING")
            return False
        
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.message_count += 1
        return True
    
    def call_openai(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Make OpenAI API call with agent-specific configuration"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add context if provided
            if context:
                context_message = f"Context: {context}"
                messages.append({"role": "system", "content": context_message})
            
            # Add message history
            for msg in self.message_history[-3:]:  # Last 3 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            ai_response = response.choices[0].message.content
            
            # Log the interaction
            self.add_message("user", user_message)
            self.add_message("assistant", ai_response)
            
            self.log_message(f"Processed message: {user_message[:100]}...")
            
            return ai_response
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return f"Error: {error_msg}"
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.message_history = []
        self.message_count = 0
        self.log_message("Conversation reset")
    
    @abstractmethod
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific task - to be implemented by each agent"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_type": self.agent_type,
            "message_count": self.message_count,
            "max_messages": Config.MAX_MESSAGES,
            "temperature": self.temperature,
            "model": self.model,
            "last_activity": self.message_history[-1]["timestamp"] if self.message_history else None
        }