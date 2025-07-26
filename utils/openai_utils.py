from openai import OpenAI

client = OpenAI(api_key=Config.OPENAI_API_KEY)
import logging
from typing import Dict, Any, List, Optional
from config.settings import Config

class OpenAIUtils:
    """Utility class for OpenAI API operations"""

    def __init__(self):
        self.logger = logging.getLogger("OpenAIUtils")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[str]:
        """
        Make a chat completion request to OpenAI
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for OpenAI API
        
        Returns:
            Response content or None if error
        """
        try:
            response = client.chat.completions.create(model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs)

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return None

    def create_system_message(self, content: str) -> Dict[str, str]:
        """Create a system message dictionary"""
        return {"role": "system", "content": content}

    def create_user_message(self, content: str) -> Dict[str, str]:
        """Create a user message dictionary"""
        return {"role": "user", "content": content}

    def create_assistant_message(self, content: str) -> Dict[str, str]:
        """Create an assistant message dictionary"""
        return {"role": "assistant", "content": content}

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count
        (Actual implementation would use tiktoken library)
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def truncate_conversation(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 3000,
        preserve_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Truncate conversation history to fit within token limit
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to keep
            preserve_system: Whether to always keep system messages
        
        Returns:
            Truncated list of messages
        """
        if not messages:
            return messages

        # Separate system messages if preserving them
        system_messages = []
        other_messages = []

        for msg in messages:
            if msg.get("role") == "system" and preserve_system:
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # Calculate tokens for system messages
        system_tokens = sum(self.estimate_tokens(msg["content"]) for msg in system_messages)
        available_tokens = max_tokens - system_tokens

        if available_tokens <= 0:
            return system_messages  # Only system messages fit

        # Add other messages from most recent, working backwards
        truncated_messages = []
        current_tokens = 0

        for msg in reversed(other_messages):
            msg_tokens = self.estimate_tokens(msg["content"])
            if current_tokens + msg_tokens <= available_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        return system_messages + truncated_messages

    def batch_process(
        self,
        prompts: List[str],
        system_prompt: str = "",
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> List[Optional[str]]:
        """
        Process multiple prompts in batch
        
        Args:
            prompts: List of prompts to process
            system_prompt: System prompt to use for all requests
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
        
        Returns:
            List of responses (None for failed requests)
        """
        results = []

        for prompt in prompts:
            messages = []
            if system_prompt:
                messages.append(self.create_system_message(system_prompt))
            messages.append(self.create_user_message(prompt))

            response = self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            results.append(response)

        return results

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """
        Get text embedding from OpenAI
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector or None if error
        """
        try:
            response = client.embeddings.create(model=model,
            input=text)

            return response.data[0].embedding

        except Exception as e:
            self.logger.error(f"Embedding API error: {str(e)}")
            return None

    def moderate_content(self, text: str) -> Dict[str, Any]:
        """
        Check content using OpenAI's moderation API
        
        Args:
            text: Text to moderate
        
        Returns:
            Moderation results dictionary
        """
        try:
            response = client.moderations.create(input=text)

            return {
                'flagged': response.results[0].flagged,
                'categories': response.results[0].categories,
                'category_scores': response.results[0].category_scores
            }

        except Exception as e:
            self.logger.error(f"Moderation API error: {str(e)}")
            return {
                'flagged': False,
                'categories': {},
                'category_scores': {},
                'error': str(e)
            }

    def create_prompt_template(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Create a prompt from a template with variables
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variables to substitute
        
        Returns:
            Formatted prompt string
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            return template

    def validate_api_key(self) -> bool:
        """
        Validate that the OpenAI API key is working
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a simple API call to test the key
            response = client.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1)
            return True

        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            return False

    def count_conversation_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count total tokens in a conversation
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Total estimated token count
        """
        total_tokens = 0
        for message in messages:
            total_tokens += self.estimate_tokens(message.get("content", ""))
            total_tokens += 4  # Overhead per message

        return total_tokens

    def optimize_prompt(self, prompt: str, max_length: int = 2000) -> str:
        """
        Optimize prompt length while preserving meaning
        
        Args:
            prompt: Original prompt
            max_length: Maximum character length
        
        Returns:
            Optimized prompt
        """
        if len(prompt) <= max_length:
            return prompt

        # Simple truncation with ellipsis
        # In a real implementation, would use more sophisticated techniques
        return prompt[:max_length-3] + "..."