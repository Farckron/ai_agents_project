from typing import Dict, Any, List
import requests
import json
from github import Github
from .base_agent import BaseAgent
from config.settings import Config

class GitHubManager(BaseAgent):
    def __init__(self):
        super().__init__("github_manager")
        
        # Initialize GitHub client
        if Config.GITHUB_TOKEN:
            self.github_client = Github(Config.GITHUB_TOKEN)
        else:
            self.github_client = None
            self.log_message("GitHub token not provided - some features will be limited", "WARNING")
        
        self.repo_cache = {}
        self.log_message("GitHub Manager initialized")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GitHub repository operations
        
        Input task structure:
        - action: type of GitHub operation
        - repo_url: repository URL
        - additional parameters based on action
        """
        try:
            action = task.get('action', 'get_repo_summary')
            repo_url = task.get('repo_url', Config.GITHUB_REPO_URL)
            
            self.log_message(f"Processing GitHub action: {action}")
            
            if action == 'get_repo_summary':
                return self._get_repository_summary(repo_url)
            elif action == 'get_file_content':
                return self._get_file_content(repo_url, task.get('file_path', ''))
            elif action == 'list_files':
                return self._list_repository_files(repo_url)
            elif action == 'get_recent_commits':
                return self._get_recent_commits(repo_url, task.get('limit', 10))
            elif action == 'get_issues':
                return self._get_repository_issues(repo_url)
            elif action == 'create_branch':
                return self._create_branch(repo_url, task.get('branch_name', ''))
            elif action == 'commit_changes':
                return self._commit_changes(repo_url, task.get('files', {}), task.get('message', ''))
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to fetch commits from public API'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get commits: {str(e)}'
            }
    
    def _get_repository_issues(self, repo_url: str) -> Dict[str, Any]:
        """Get repository issues"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                issues = repo_obj.get_issues(state='open')[:20]  # Limit to 20 issues
                
                issue_data = []
                for issue in issues:
                    issue_data.append({
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body[:200] + '...' if issue.body and len(issue.body) > 200 else issue.body,
                        'state': issue.state,
                        'created_at': issue.created_at.isoformat(),
                        'labels': [label.name for label in issue.labels]
                    })
                
                return {
                    'status': 'success',
                    'issues': issue_data,
                    'total_issues': len(issue_data)
                }
            else:
                return {
                    'status': 'limited',
                    'message': 'Issue listing requires GitHub token',
                    'issues': []
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get issues: {str(e)}'
            }
    
    def _create_branch(self, repo_url: str, branch_name: str) -> Dict[str, Any]:
        """Create a new branch"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Branch creation requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get the default branch
            default_branch = repo_obj.get_branch(repo_obj.default_branch)
            
            # Create new branch
            repo_obj.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=default_branch.commit.sha
            )
            
            return {
                'status': 'success',
                'branch_name': branch_name,
                'message': f'Branch {branch_name} created successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to create branch: {str(e)}'
            }
    
    def _commit_changes(self, repo_url: str, files: Dict[str, str], commit_message: str) -> Dict[str, Any]:
        """Commit changes to repository"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Committing changes requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Create or update files
            committed_files = []
            for file_path, content in files.items():
                try:
                    # Try to get existing file
                    existing_file = repo_obj.get_contents(file_path)
                    
                    # Update existing file
                    repo_obj.update_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        sha=existing_file.sha
                    )
                    committed_files.append(f"Updated: {file_path}")
                    
                except:
                    # Create new file
                    repo_obj.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content
                    )
                    committed_files.append(f"Created: {file_path}")
            
            return {
                'status': 'success',
                'committed_files': committed_files,
                'commit_message': commit_message,
                'message': f'Successfully committed {len(committed_files)} files'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to commit changes: {str(e)}'
            }
    
    def _generate_ai_summary(self, data: Dict[str, Any]) -> str:
        """Generate AI summary of repository data"""
        
        summary_prompt = f"""
        Create a concise summary of this GitHub repository for development planning:

        REPOSITORY DATA:
        {json.dumps(data, indent=2, default=str)}

        Focus on:
        1. Repository purpose and main functionality
        2. Technology stack and languages used
        3. Recent development activity
        4. Project structure and organization
        5. Current state and development status

        Keep it concise but informative (max 300 words).
        """
        
        return self.call_openai(summary_prompt)
    
    def clone_repository(self, repo_url: str, local_path: str) -> Dict[str, Any]:
        """Clone repository to local path (for development)"""
        
        try:
            import git
            
            self.log_message(f"Cloning repository to {local_path}")
            
            # Clone the repository
            repo = git.Repo.clone_from(repo_url, local_path)
            
            return {
                'status': 'success',
                'local_path': local_path,
                'branch': repo.active_branch.name,
                'message': 'Repository cloned successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to clone repository: {str(e)}'
            }
    
    def get_file_diff(self, repo_url: str, file_path: str, commit1: str, commit2: str) -> Dict[str, Any]:
        """Get diff between two commits for a specific file"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'File diff requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get comparison between commits
            comparison = repo_obj.compare(commit1, commit2)
            
            # Find the specific file in the diff
            file_diff = None
            for file in comparison.files:
                if file.filename == file_path:
                    file_diff = file
                    break
            
            if file_diff:
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'changes': file_diff.changes,
                    'additions': file_diff.additions,
                    'deletions': file_diff.deletions,
                    'patch': file_diff.patch
                }
            else:
                return {
                    'status': 'error',
                    'message': f'File {file_path} not found in diff'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get file diff: {str(e)}'
            }
    
    def search_code(self, repo_url: str, query: str) -> Dict[str, Any]:
        """Search for code within the repository"""
        
        if not self.github_client:
            return {
                'status': 'error',
                'message': 'Code search requires GitHub token'
            }
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            # Search code in repository
            search_query = f"{query} repo:{owner}/{repo}"
            results = self.github_client.search_code(search_query)
            
            search_results = []
            for result in results[:10]:  # Limit to 10 results
                search_results.append({
                    'file_path': result.path,
                    'repository': result.repository.full_name,
                    'score': result.score,
                    'url': result.html_url
                })
            
            return {
                'status': 'success',
                'query': query,
                'results': search_results,
                'total_results': len(search_results)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to search code: {e}',
                'message': f'Unknown GitHub action: {action}'
            }

                
        except Exception as e:
            error_msg = f"Error in GitHub Manager: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _get_repository_summary(self, repo_url: str) -> Dict[str, Any]:
        """Get comprehensive repository summary"""
        
        try:
            repo_info = self._get_repo_info(repo_url)
            if not repo_info:
                return {
                    'status': 'error',
                    'message': 'Could not fetch repository information'
                }
            
            # Get additional repository data
            recent_commits = self._get_recent_commits(repo_url, 5)
            file_structure = self._list_repository_files(repo_url)
            
            # Create summary using AI
            summary_data = {
                'repository_info': repo_info,
                'recent_commits': recent_commits.get('commits', []),
                'file_structure': file_structure.get('files', [])
            }
            
            summary = self._generate_ai_summary(summary_data)
            
            return {
                'status': 'success',
                'summary': summary,
                'raw_data': summary_data,
                'repo_info': repo_info
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get repository summary: {str(e)}'
            }
    
    def _get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """Get basic repository information"""
        
        try:
            # Extract owner/repo from URL
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return None
                
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                # Use authenticated API
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                
                return {
                    'name': repo_obj.name,
                    'full_name': repo_obj.full_name,
                    'description': repo_obj.description,
                    'language': repo_obj.language,
                    'languages': dict(repo_obj.get_languages()),
                    'stars': repo_obj.stargazers_count,
                    'forks': repo_obj.forks_count,
                    'open_issues': repo_obj.open_issues_count,
                    'created_at': repo_obj.created_at.isoformat(),
                    'updated_at': repo_obj.updated_at.isoformat(),
                    'default_branch': repo_obj.default_branch,
                    'topics': repo_obj.get_topics(),
                    'size': repo_obj.size
                }
            else:
                # Use public API
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'name': data.get('name'),
                        'full_name': data.get('full_name'),
                        'description': data.get('description'),
                        'language': data.get('language'),
                        'stars': data.get('stargazers_count'),
                        'forks': data.get('forks_count'),
                        'open_issues': data.get('open_issues_count'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'default_branch': data.get('default_branch'),
                        'size': data.get('size')
                    }
                
                return None
                
        except Exception as e:
            self.log_message(f"Error getting repo info: {str(e)}", "ERROR")
            return None
    
    def _get_file_content(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """Get content of a specific file"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                file_content = repo_obj.get_contents(file_path)
                
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'content': file_content.decoded_content.decode('utf-8'),
                    'size': file_content.size,
                    'sha': file_content.sha
                }
            else:
                # Use raw GitHub content
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
                response = requests.get(raw_url)
                
                if response.status_code == 200:
                    return {
                        'status': 'success',
                        'file_path': file_path,
                        'content': response.text,
                        'size': len(response.text)
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'File not found: {file_path}'
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get file content: {str(e)}'
            }
    
    def _list_repository_files(self, repo_url: str) -> Dict[str, Any]:
        """List files in the repository"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                contents = repo_obj.get_contents("")
                
                files = []
                self._collect_files_recursive(repo_obj, contents, files)
                
                return {
                    'status': 'success',
                    'files': files,
                    'total_files': len(files)
                }
            else:
                # Limited functionality without authentication
                return {
                    'status': 'limited',
                    'message': 'File listing requires GitHub token',
                    'files': []
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to list files: {str(e)}'
            }
    
    def _collect_files_recursive(self, repo_obj, contents, files, path=""):
        """Recursively collect all files in repository"""
        
        for content in contents:
            current_path = f"{path}/{content.name}" if path else content.name
            
            if content.type == "dir":
                try:
                    sub_contents = repo_obj.get_contents(content.path)
                    self._collect_files_recursive(repo_obj, sub_contents, files, current_path)
                except:
                    continue  # Skip directories we can't access
            else:
                files.append({
                    'path': content.path,
                    'name': content.name,
                    'size': content.size,
                    'type': content.type
                })
    
    def _get_recent_commits(self, repo_url: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent commits from repository"""
        
        try:
            parts = repo_url.replace('https://github.com/', '').split('/')
            owner, repo = parts[0], parts[1]
            
            if self.github_client:
                repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
                commits = repo_obj.get_commits()[:limit]
                
                commit_data = []
                for commit in commits:
                    commit_data.append({
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author': commit.commit.author.name,
                        'date': commit.commit.author.date.isoformat(),
                        'files_changed': len(commit.files) if commit.files else 0
                    })
                
                return {
                    'status': 'success',
                    'commits': commit_data,
                    'total_commits': len(commit_data)
                }
            else:
                # Use public API
                api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
                response = requests.get(api_url, params={'per_page': limit})
                
                if response.status_code == 200:
                    commits_data = response.json()
                    commit_data = []
                    
                    for commit in commits_data:
                        commit_data.append({
                            'sha': commit['sha'],
                            'message': commit['commit']['message'],
                            'author': commit['commit']['author']['name'],
                            'date': commit['commit']['author']['date']
                        })
                    
                    return {
                        'status': 'success',
                        'commits': commit_data,
                        'total_commits': len(commit_data)
                    }
                
                return {
                    'status': 'error',
                    'message': f'Failed to fetch commits from public API: {response.status_code}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get recent commits: {str(e)}'
            }
