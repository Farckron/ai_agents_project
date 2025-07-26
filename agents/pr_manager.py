# agents/pr_manager.py
from typing import Dict, Any, List, Optional, Tuple, Callable
import os
import uuid
import re
import base64
import json
from datetime import datetime

# HTTP: prefer requests, fallback to urllib
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None
    import urllib.request
    import urllib.error

from .base_agent import BaseAgent
from .github_manager import GitHubManager
from .prompt_ask_engineer import PromptAskEngineer
from .prompt_code_engineer import PromptCodeEngineer
from .code_agent import CodeAgent

from utils.structured_logger import (
    get_structured_logger, log_pr_start, log_pr_step, log_pr_complete,
    LogLevel, LogCategory
)
from utils.error_handler import ErrorHandler

GITHUB_API = "https://api.github.com"


def _http_json(method: str, url: str, headers: Dict[str, str], payload: Optional[Dict[str, Any]] = None):
    """Send JSON over HTTP. Returns (status_code, json_dict)."""
    if requests is not None:
        resp = requests.request(method, url, headers=headers, json=payload)
        try:
            return resp.status_code, (resp.json() if resp.text else {})
        except Exception:
            return resp.status_code, {}
    else:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, method=method, headers=headers)  # type: ignore
        if data is not None:
            req.data = data  # type: ignore[attr-defined]
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:  # type: ignore
                body = r.read().decode("utf-8")
                return r.getcode(), (json.loads(body) if body else {})
        except urllib.error.HTTPError as e:  # type: ignore
            body = e.read().decode("utf-8")
            try:
                return e.code, json.loads(body)
            except Exception:
                return e.code, {"message": body or str(e)}
        except Exception as e:
            return 0, {"message": str(e)}


class PRManager(BaseAgent):
    """
    Canvas flow (screenshot):
      Text → Prompt Ask → (decision) → Prompt Code → Code Agent → PR.
    Only real code files are committed to GitHub. No placeholders.
    """
    def __init__(self):
        super().__init__("pr_manager")

        self.ask_engineer   = PromptAskEngineer()
        self.code_planner   = PromptCodeEngineer()
        self.code_agent     = CodeAgent()

        self.github_manager: GitHubManager = GitHubManager()
        self.error_handler                 = ErrorHandler("PRManager")
        self.structured_logger             = get_structured_logger("pr_manager")

        # ASCII only to avoid Windows console encoding problems
        self.log_message("PR Manager initialized (code-only workflow)")
        try:
            self.structured_logger.log_structured(
                LogLevel.INFO,
                LogCategory.SYSTEM,
                "PR Manager initialized: code-only, commits only CodeAgent outputs",
                component="pr_manager",
            )
        except Exception as e:
            self.log_message(f"Structured logging failed: {str(e)}", "WARNING")

    # ──────────────────────────────────────────────────────────
    # Public entry
    # ──────────────────────────────────────────────────────────
    def process_pr_request(self, user_request: str, repo_url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        log_pr_start(self.structured_logger, "pr_manager", {
            "repo_url": repo_url,
            "user_request": user_request,
            "options": options,
        })

        # 0) minimal repo context (default_branch + README text)
        repo_ctx = self._fetch_repo_context(repo_url)
        repo_ctx_text = repo_ctx.get("readme", "")

        # 1) Ask Engineer: summary + decision (if method absent, assume changes needed)
        summary, requires_changes = self._ask_engineer_decision(user_request, repo_ctx_text)
        if not requires_changes:
            msg = "No important changes required according to Prompt Ask Engineer."
            self.log_message(msg, "INFO")
            return {
                "ok": True,
                "message": msg,
                "generated_files": [],
                "pr_result": {"created": False, "pr_url": None, "branch": None, "base": repo_ctx.get("default_branch"), "error": None},
                "meta": {"timestamp": ts, "repo_url": repo_url, "summary": summary},
            }

        # 2) Code plan/spec
        plan = self._plan_changes(user_request, repo_ctx_text, summary)

        # 3) Code Agent → files
        code_files = self._produce_code_files(user_request, repo_ctx_text, plan)

        if not code_files:
            msg = "Code Agent did not produce any files (no code blocks with paths found)."
            self.log_message(msg, "WARNING")
            return {
                "ok": False,
                "message": msg,
                "generated_files": [],
                "pr_result": {"created": False, "pr_url": None, "branch": None, "base": repo_ctx.get("default_branch"), "error": msg},
                "meta": {"timestamp": ts, "repo_url": repo_url, "summary": summary, "plan": plan},
            }

        # 4) Create PR via REST
        pr_result: Dict[str, Any] = {
            "created": False,
            "pr_url": None,
            "branch": None,
            "base": options.get("base_branch", repo_ctx.get("default_branch") or "main"),
            "error": None,
        }
        try:
            branch = self._safe_generate_branch_name(user_request)
            pr_title = options.get("title") or f"Automated code update: {self._shorten(user_request, 60)}"
            pr_body  = self._compose_pr_body(user_request, code_files, ts, summary, plan)

            created, pr_url = self._create_pr_via_rest(
                repo_url=repo_url,
                branch_name=branch,
                base_branch=pr_result["base"],
                title=pr_title,
                body=pr_body,
                files=code_files,
            )
            pr_result.update({"created": created, "pr_url": pr_url, "branch": branch})
        except Exception as e:
            pr_result["error"] = str(e)
            self.log_message(f"PR creation failed: {e}", level="ERROR")

        log_pr_complete(self.structured_logger, "pr_manager", {
            "repo_url": repo_url,
            "pr_created": pr_result["created"],
            "pr_url": pr_result["pr_url"],
            "branch": pr_result["branch"],
            "base": pr_result["base"],
            "files_len": len(code_files),
        })

        return {
            "ok": True,
            "message": "Workflow complete",
            "generated_files": code_files,
            "pr_result": pr_result,
            "meta": {"timestamp": ts, "repo_url": repo_url, "summary": summary, "plan": plan},
        }

    # ──────────────────────────────────────────────────────────
    # Canvas steps
    # ──────────────────────────────────────────────────────────
    def _ask_engineer_decision(self, user_request: str, repo_ctx_text: str) -> Tuple[str, bool]:
        """Return (summary, requires_changes). Prefer process_task API."""
        # Preferred path
        if hasattr(self.ask_engineer, "process_task"):
            try:
                out = self.ask_engineer.process_task({"request": user_request, "repo_context": repo_ctx_text})
                if isinstance(out, dict):
                    summary = str(out.get("analysis") or out.get("summary") or "")
                    rc = out.get("requires_changes")
                    if isinstance(rc, bool):
                        return summary, rc
                    # If not provided, infer
                    return summary, self._infer_requires_changes(summary or user_request)
            except Exception as e:
                self.log_message(f"PromptAskEngineer.process_task failed: {e}", "WARNING")

        # Fallbacks (best-effort)
        for name in ("summarize_repo", "analyze_repo", "analyze", "summarize"):
            if hasattr(self.ask_engineer, name):
                try:
                    fn = getattr(self.ask_engineer, name)
                    summary = str(fn(repo_ctx_text, user_request)) if name in ("summarize_repo", "analyze_repo") else str(fn(user_request))
                    return summary, self._infer_requires_changes(summary or user_request)
                except Exception as e:
                    self.log_message(f"PromptAskEngineer.{name} failed: {e}", "WARNING")
        # No agent → assume changes needed if prompt looks actionable
        return user_request.strip(), self._infer_requires_changes(user_request)

    def _infer_requires_changes(self, text: str) -> bool:
        if not text: 
            return False
        t = text.lower()
        keywords = ["add","fix","implement","update","create","refactor","додай","виправ","онов","створ","рефактор"]
        return any(k in t for k in keywords) or len(t) > 15

    def _plan_changes(self, user_request: str, repo_ctx_text: str, summary: str) -> Any:
        if hasattr(self.code_planner, "process_task"):
            try:
                out = self.code_planner.process_task({
                    "user_request": user_request,
                    "analysis": summary,
                    "recommendations": "",  # allow empty
                    "repo_context": repo_ctx_text,
                })
                return out if isinstance(out, dict) else {"raw": str(out)}
            except Exception as e:
                self.log_message(f"PromptCodeEngineer.process_task failed: {e}", "WARNING")
        # Fallback: return minimal dict
        return {"targets": [], "notes": "no planner"}

    def _produce_code_files(self, user_request: str, repo_ctx_text: str, plan: Any) -> List[Dict[str, str]]:
        """Call CodeAgent.process_task and extract files from text responses only.
        No placeholders are created if nothing is extracted.
        """
        # Build a single consolidated task for the CodeAgent
        tasks = []
        code_tasks = []
        if isinstance(plan, dict):
            code_tasks = plan.get("code_tasks") or plan.get("tasks") or []
        if not isinstance(code_tasks, list):
            code_tasks = []
        # Ensure every task has a task_id
        for i, t in enumerate(code_tasks, start=1):
            if isinstance(t, dict) and "task_id" not in t:
                t["task_id"] = f"task-{i:03d}"
        tasks = code_tasks

        if hasattr(self.code_agent, "process_task"):
            try:
                out = self.code_agent.process_task({
                    "tasks": tasks,
                    "files_to_change": (plan.get("files_to_change") if isinstance(plan, dict) else []) or [],
                    "context": repo_ctx_text,
                })
                # Expect list of per-task results in 'task_results', each with text
                texts: List[str] = []
                if isinstance(out, dict):
                    if isinstance(out.get("task_results"), list):
                        for r in out.get("task_results") or []:
                            # pick common keys that likely contain code
                            for k in ("generated_code","modifications","fixed_code","review_results","code"):
                                v = r.get(k)
                                if isinstance(v, str) and v.strip():
                                    texts.append(v)
                    # Some implementations also return 'summary' text
                    if isinstance(out.get("summary"), str):
                        texts.append(out["summary"])
                # Extract files from collected text
                files: List[Dict[str,str]] = []
                for txt in texts:
                    files.extend(self._extract_files_from_text(txt))
                # Deduplicate by path, keep last
                uniq: Dict[str,str] = {}
                for f in files:
                    if f.get("path") and f.get("content") is not None:
                        uniq[f["path"]] = f["content"]
                return [{"path": p, "content": c} for p,c in uniq.items()]
            except Exception as e:
                self.log_message(f"CodeAgent.process_task failed: {e}", "WARNING")
        return []

    # ──────────────────────────────────────────────────────────
    # GitHub REST
    # ──────────────────────────────────────────────────────────
    def _create_pr_via_rest(self, repo_url: str, branch_name: str, base_branch: str, title: str, body: str, files: List[Dict[str, str]]):
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GITHUB_TOKEN is not set")
        owner, repo = self._parse_repo_url(repo_url)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-agents-pr-manager",
        }
        base = self._resolve_base_branch(owner, repo, base_branch, headers)
        self._log_step("Creating branch (REST)", {"branch": branch_name, "base": base})
        self._ensure_branch(owner, repo, branch_name, base, headers)
        self._log_step("Committing files (REST)", {"files": [f["path"] for f in files]})
        for f in files:
            self._put_file(owner, repo, f["path"], f["content"], title, branch_name, headers)
        self._log_step("Opening PR (REST)", {"title": title})
        pr_url = self._open_pr(owner, repo, head=branch_name, base=base, title=title, body=body, headers=headers)
        return True, pr_url

    def _resolve_base_branch(self, owner: str, repo: str, requested_base: str, headers: Dict[str, str]) -> str:
        st, _ = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}/branches/{requested_base}", headers)
        if st == 200:
            return requested_base
        st, repo_meta = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}", headers)
        if st != 200:
            raise RuntimeError(f"Failed to read repo meta: HTTP {st}")
        default_branch = repo_meta.get("default_branch") or "main"
        st, _ = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}/branches/{default_branch}", headers)
        if st != 200:
            raise RuntimeError(f"Base branch not found: '{requested_base}', and default '{default_branch}' missing")
        return default_branch

    def _ensure_branch(self, owner: str, repo: str, branch: str, base: str, headers: Dict[str, str]) -> None:
        st, base_data = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}/branches/{base}", headers)
        if st != 200:
            raise RuntimeError(f"Cannot read base branch '{base}': HTTP {st}")
        base_sha = (base_data.get("commit") or {}).get("sha")
        if not base_sha:
            raise RuntimeError("Base branch SHA not found")
        payload = {"ref": f"refs/heads/{branch}", "sha": base_sha}
        st, resp = _http_json("POST", f"{GITHUB_API}/repos/{owner}/{repo}/git/refs", headers, payload)
        if st in (200, 201):
            return
        if st == 422 and "Reference already exists" in (resp.get("message") or ""):
            return
        raise RuntimeError(f"Failed to create branch '{branch}' from '{base}': HTTP {st} {resp.get('message')}")

    def _put_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str, headers: Dict[str, str]) -> None:
        enc = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {"message": message, "content": enc, "branch": branch}
        st, resp = _http_json("PUT", f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}", headers, payload)
        if st not in (200, 201):
            raise RuntimeError(f"Failed to commit {path}: HTTP {st} {resp.get('message')}")

    def _open_pr(self, owner: str, repo: str, head: str, base: str, title: str, body: str, headers: Dict[str, str]) -> Optional[str]:
        payload = {"title": title, "head": head, "base": base, "body": body}
        st, resp = _http_json("POST", f"{GITHUB_API}/repos/{owner}/{repo}/pulls", headers, payload)
        if st in (201, 200):
            return resp.get("html_url")
        if st == 422:
            q = f"is:pr is:open repo:{owner}/{repo} head:{head} base:{base}"
            st2, sresp = _http_json("GET", f"{GITHUB_API}/search/issues?q={q}", headers)
            if st2 == 200:
                items = sresp.get("items") or []
                if items:
                    return items[0].get("html_url")
        raise RuntimeError(f"Failed to open PR: HTTP {st} {resp.get('message')}")

    # ──────────────────────────────────────────────────────────
    # Repo context
    # ──────────────────────────────────────────────────────────
    def _fetch_repo_context(self, repo_url: str) -> Dict[str, Any]:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        owner, repo = self._parse_repo_url(repo_url)
        headers = {
            "Authorization": f"Bearer {token}" if token else "",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-agents-pr-manager",
        }
        ctx: Dict[str, Any] = {"owner": owner, "repo": repo, "default_branch": "main", "readme": ""}

        st, meta = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}", headers)
        if st == 200:
            ctx["default_branch"] = meta.get("default_branch") or "main"

        st, readme = _http_json("GET", f"{GITHUB_API}/repos/{owner}/{repo}/readme", headers)
        if st == 200 and readme.get("content"):
            try:
                ctx["readme"] = base64.b64decode(readme["content"]).decode("utf-8", errors="ignore")
            except Exception:
                ctx["readme"] = ""
        return ctx

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────
    def _compose_pr_body(self, user_request: str, files: List[Dict[str, str]], ts: str, summary: Any, plan: Any) -> str:
        lines = [
            f"Automated code update on {ts}",
            "",
            f"**Request**: {user_request}",
            "",
        ]
        if summary:
            lines += ["### Summary (Prompt Ask Engineer)", "", str(summary), ""]
        if plan:
            try:
                plan_str = json.dumps(plan, ensure_ascii=False, indent=2)
            except Exception:
                plan_str = str(plan)
            lines += ["### Plan (Prompt Code Engineer)", "", f"```json\n{plan_str}\n```", ""]
        lines += ["### Files", *[f"- `{f['path']}`" for f in files], "", "> Generated by AI Agents workflow."]
        return "\n".join(lines)

    def _safe_generate_branch_name(self, user_request: str, prefix: str = "auto") -> str:
        base = re.sub(r"[^a-zA-Z0-9\-]+", "-", user_request.strip().lower())[:30].strip("-") or "change"
        return f"{prefix}/{base}-{uuid.uuid4().hex[:6]}"

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", repo_url)
        if not m:
            raise ValueError(f"Unsupported repo URL: {repo_url}")
        return m.group("owner"), m.group("repo")

    def _shorten(self, text: str, n: int) -> str:
        return text if len(text) <= n else text[: n - 1] + "…"

    def _log_step(self, msg: str, data: Optional[Dict[str, Any]] = None) -> None:
        try:
            log_pr_step(self.structured_logger, "pr_manager", msg, data or {})
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────
    # File extraction
    # ──────────────────────────────────────────────────────────
    def _extract_files_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract files from fenced blocks. Supported formats:
            ```file=path/to/file.py
            <full content>
            ```
            or first line inside block contains '# path: path/to/file.py' (or // path: ...).
        """
        files: List[Dict[str, str]] = []
        if not text:
            return files
        # ```lang [anything possibly including file=path]
        fence_re = re.compile(r"```(?P<info>[^\n]*)\n(?P<code>.*?)(?:```|$)", re.DOTALL)
        for m in fence_re.finditer(text):
            info = m.group("info") or ""
            code = m.group("code") or ""
            path = None
            # Try to read file=path from info string
            m1 = re.search(r"file\s*=\s*([^\s]+)", info)
            if m1:
                path = m1.group(1).strip()
            else:
                # Otherwise, check first non-empty line in code for path header
                lines = code.splitlines()
                first = ""
                for ln in lines:
                    if ln.strip():
                        first = ln.strip()
                        break
                m2 = re.match(r"(?:(?:#|//)\s*)?(?:path|file)\s*[:=]\s*(.+)", first, re.IGNORECASE)
                if m2:
                    path = m2.group(1).strip()
                    code = "\n".join(lines[1:])  # drop header line
            if path:
                files.append({"path": path, "content": code.rstrip() + "\n"})
        return files
