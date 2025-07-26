# agents/code_agent.py
from typing import Dict, Any, List
import json
from .base_agent import BaseAgent


STRICT_FORMAT_INSTRUCTIONS = """
You MUST output ONLY code fences for full files. For each file, use exactly:

```file=relative/path/to/file.ext
<entire file content>
```

Rules:
- Return full file contents (no diffs, no patches).
- One code fence per file. No explanations or prose before/after.
- UTF-8 text only.
- If NO files need changes, return an empty response (no words).
"""


class CodeAgent(BaseAgent):
    """
    CodeAgent generates READY-TO-COMMIT files.
    It returns raw text that contains ONLY fenced code blocks with explicit file paths.
    No placeholders are produced here; if the model decides no files are needed, it should return an empty string.

    Expected input to process_task():
    {
      "tasks": [ { ... }, ... ],
      "files_to_change": [ "path/one.py", ... ],
      "context": "<repo README or other context>"
    }

    Expected output:
    {
      "status": "success" | "error",
      "task_results": [
        { "status": "success", "generated_code": "<CODE-FENCES-ONLY>" }
      ],
      "summary": "string"
    }
    """

    def __init__(self):
        super().__init__("code_agent")
        # ASCII-only logging to avoid Windows console encoding issues
        self.log_message("Code Agent initialized (strict file output)")

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point used by PR pipeline.
        Builds a single consolidated instruction for the model and returns its raw output.
        No file parsing is done here (parsing happens upstream).
        """
        try:
            tasks: List[Dict[str, Any]] = task.get("tasks") or []
            files_to_change: List[str] = task.get("files_to_change") or []
            context: str = task.get("context") or ""

            prompt = self._build_prompt(tasks, files_to_change, context)
            self.log_message("Requesting code generation from model")
            # BaseAgent.call_openai should return a string with model output
            generated: str = self.call_openai(prompt)

            return {
                "status": "success",
                "task_results": [{
                    "status": "success",
                    "generated_code": generated or ""  # may be empty if no changes needed
                }],
                "summary": f"Generated files for {len(tasks)} task(s)." if generated else "Model returned no files."
            }

        except Exception as e:
            msg = f"CodeAgent error: {e}"
            self.log_message(msg, "ERROR")
            return {"status": "error", "error": msg}

    # ──────────────────────────────────────────────────────────
    # Prompt builder
    # ──────────────────────────────────────────────────────────
    def _build_prompt(self, tasks: List[Dict[str, Any]], files_to_change: List[str], context: str) -> str:
        """
        Compose a deterministic instruction that forces the model
        to output ONLY full-file code fences with explicit file paths.
        """
        return (
            "You are a senior software engineer. Implement ALL requested changes.\n\n"
            "CONTEXT (README / project info):\n"
            f"{context}\n\n"
            "TASKS (implement all):\n"
            f"{json.dumps(tasks, ensure_ascii=False, indent=2)}\n\n"
            "TARGET FILES (if any):\n"
            f"{json.dumps(files_to_change, ensure_ascii=False)}\n\n"
            "DELIVERABLES:\n"
            "- Return ONLY fully rendered files that must be created or replaced.\n"
            "- Provide one fenced block per file, with explicit relative path.\n"
            "- If you determine NO files need changes, return an EMPTY response.\n\n"
            + STRICT_FORMAT_INSTRUCTIONS
        )
