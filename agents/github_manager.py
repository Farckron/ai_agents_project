# agents/github_manager.py
from github import Github, GithubException
import os

class GitHubManager:
    """
    Handles GitHub interactions: creating branches, pull requests, and committing files.
    """
    def __init__(self, token: str = None):
        token = token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("Please set the GITHUB_TOKEN environment variable")
        self.client = Github(token)

    def commit_files(self, repo_name: str, branch: str, files: dict, message: str):
        repo = self.client.get_repo(repo_name)
        for path, content in files.items():
            try:
                # Try to get existing file to retrieve its SHA
                existing = repo.get_contents(path, ref=branch)
                repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing.sha,
                    branch=branch,
                )
            except GithubException as e:
                if e.status == 404:
                    # File does not exist; create it
                    repo.create_file(
                        path=path,
                        message=message,
                        content=content,
                        branch=branch,
                    )
                else:
                    # Re-raise other errors
                    raise