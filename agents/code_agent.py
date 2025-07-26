# agents/code_agent.py
import logging
from typing import Dict, List, Any
from utils.base_agent import BaseAgent

class CodeAgent(BaseAgent):
    """
    Agent that generates code files directly from user-provided instruction tasks.
    """
    def __init__(self, strict_file_output: bool = True, model: str = None, temperature: float = 0.2):
        super().__init__(model=model, temperature=temperature)
        self.strict_file_output = strict_file_output
        logging.info("[code_agent] Code Agent initialized (strict file output=%s)", strict_file_output)

    def generate_code(self, instructions: str) -> Dict[str, str]:
        """
        Ask the model to generate code files for the given instruction.
        """
        system = (
            "You are an expert developer. "
            "Given the user's instruction below, output all necessary code files for a complete solution. "
            "For each file, use a markdown fence starting with ```file=<relative_path>``` and ending with ```."
        )
        messages = [
            {"role": "system",  "content": system},
            {"role": "user",    "content": instructions},
        ]
        raw = self.call_openai(messages)

        files: Dict[str, str] = {}
        current = None
        buffer: List[str] = []

        for line in raw.splitlines():
            if line.startswith("```file="):
                if current:
                    files[current] = "\n".join(buffer).rstrip()
                current = line[len("```file="):].strip()
                buffer = []
            elif line.strip() == "```":
                if current:
                    files[current] = "\n".join(buffer).rstrip()
                current = None
                buffer = []
            elif current:
                buffer.append(line)

        return files

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload['tasks'] contains a single item: the user instruction
        tasks = payload.get("tasks", [])
        instruction = tasks[0] if tasks else ""
        files = self.generate_code(instruction)

        md_fences = []
        for path, content in files.items():
            md_fences.append(f"```file={path}\n{content}\n```")

        return {"task_results": [{"generated_code": "\n\n".join(md_fences)}]}
