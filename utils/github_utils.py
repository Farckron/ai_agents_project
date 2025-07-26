import re
import requests
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import logging

class GitHubUtils:
    """Utility functions for GitHub operations"""
    
    def __init__(self):
        self.logger = logging.getLogger("GitHubUtils")
    
    @staticmethod
    def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
        """
        Parse GitHub URL to extract owner and repository name
        
        Args:
            url: GitHub repository URL
        
        Returns:
            Tuple of (owner, repo) or None if invalid
        """
        try:
            # Remove .git suffix if present
            url = url.rstrip('.git')
            
            # Handle different URL formats
            patterns = [
                r'https://github\.com/([^/]+)/([^/]+)',
                r'git@github\.com:([^/]+)/([^/]+)',
                r'github\.com/([^/]+)/([^/]+)'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, url)
                if match:
                    return match.group(1), match.group(2)
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        """
        Check if URL is a valid GitHub repository URL
        
        Args:
            url: URL to validate
        
        Returns:
            True if valid GitHub URL, False otherwise
        """
        return GitHubUtils.parse_github_url(url) is not None
    
    @staticmethod
    def get_repository_api_url(repo_url: str) -> Optional[str]:
        """
        Convert repository URL to GitHub API URL
        
        Args:
            repo_url: GitHub repository URL
        
        Returns:
            API URL or None if invalid
        """
        parsed = GitHubUtils.parse_github_url(repo_url)
        if parsed:
            owner, repo = parsed
            return f"https://api.github.com/repos/{owner}/{repo}"
        return None
    
    @staticmethod
    def get_raw_file_url(repo_url: str, file_path: str, branch: str = "main") -> Optional[str]:
        """
        Get raw file URL for GitHub file
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to file in repository
            branch: Branch name (default: main)
        
        Returns:
            Raw file URL or None if invalid
        """
        parsed = GitHubUtils.parse_github_url(repo_url)
        if parsed:
            owner, repo = parsed
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        return None
    
    def check_repository_exists(self, repo_url: str) -> bool:
        """
        Check if GitHub repository exists and is accessible
        
        Args:
            repo_url: GitHub repository URL
        
        Returns:
            True if repository exists, False otherwise
        """
        try:
            api_url = self.get_repository_api_url(repo_url)
            if not api_url:
                return False
            
            response = requests.get(api_url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error checking repository existence: {str(e)}")
            return False
    
    def get_repository_info(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Get basic repository information from GitHub API
        
        Args:
            repo_url: GitHub repository URL
        
        Returns:
            Repository information dictionary or None if error
        """
        try:
            api_url = self.get_repository_api_url(repo_url)
            if not api_url:
                return None
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Repository API returned {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching repository info: {str(e)}")
            return None
    
    def get_file_content(self, repo_url: str, file_path: str, branch: str = "main") -> Optional[str]:
        """
        Get file content from GitHub repository
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to file in repository
            branch: Branch name (default: main)
        
        Returns:
            File content as string or None if error
        """
        try:
            raw_url = self.get_raw_file_url(repo_url, file_path, branch)
            if not raw_url:
                return None
            
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"File fetch returned {response.status_code} for {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching file content: {str(e)}")
            return None
    
    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 10) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories
        
        Args:
            query: Search query
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Results per page
        
        Returns:
            List of repository dictionaries
        """
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': query,
                'sort': sort,
                'order': order,
                'per_page': per_page
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                self.logger.warning(f"Repository search returned {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching repositories: {str(e)}")
            return []
    
    def get_repository_languages(self, repo_url: str) -> Dict[str, int]:
        """
        Get programming languages used in repository
        
        Args:
            repo_url: GitHub repository URL
        
        Returns:
            Dictionary of languages and their byte counts
        """
        try:
            api_url = self.get_repository_api_url(repo_url)
            if not api_url:
                return {}
            
            languages_url = f"{api_url}/languages"
            response = requests.get(languages_url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching repository languages: {str(e)}")
            return {}
    
    def get_repository_contributors(self, repo_url: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """
        Get repository contributors
        
        Args:
            repo_url: GitHub repository URL
            per_page: Number of contributors to fetch
        
        Returns:
            List of contributor dictionaries
        """
        try:
            api_url = self.get_repository_api_url(repo_url)
            if not api_url:
                return []
            
            contributors_url = f"{api_url}/contributors"
            response = requests.get(contributors_url, params={'per_page': per_page}, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching contributors: {str(e)}")
            return []
    
    def get_repository_releases(self, repo_url: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        Get repository releases
        
        Args:
            repo_url: GitHub repository URL
            per_page: Number of releases to fetch
        
        Returns:
            List of release dictionaries
        """
        try:
            api_url = self.get_repository_api_url(repo_url)
            if not api_url:
                return []
            
            releases_url = f"{api_url}/releases"
            response = requests.get(releases_url, params={'per_page': per_page}, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching releases: {str(e)}")
            return []
    
    @staticmethod
    def format_repository_summary(repo_data: Dict[str, Any]) -> str:
        """
        Format repository data into a readable summary
        
        Args:
            repo_data: Repository data from GitHub API
        
        Returns:
            Formatted summary string
        """
        try:
            summary_lines = [
                f"Repository: {repo_data.get('full_name', 'Unknown')}",
                f"Description: {repo_data.get('description', 'No description')}"
            ]
            
            if repo_data.get('language'):
                summary_lines.append(f"Main Language: {repo_data['language']}")
            
            stats = []
            if repo_data.get('stargazers_count'):
                stats.append(f"⭐ {repo_data['stargazers_count']}")
            if repo_data.get('forks_count'):
                stats.append(f"🍴 {repo_data['forks_count']}")
            if repo_data.get('open_issues_count'):
                stats.append(f"🐛 {repo_data['open_issues_count']} issues")
            
            if stats:
                summary_lines.append(f"Stats: {' | '.join(stats)}")
            
            if repo_data.get('updated_at'):
                summary_lines.append(f"Last Updated: {repo_data['updated_at']}")
            
            return '\n'.join(summary_lines)
            
        except Exception:
            return "Unable to format repository summary"
    
    def validate_github_token(self, token: str) -> bool:
        """
        Validate GitHub token
        
        Args:
            token: GitHub personal access token
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {'Authorization': f'token {token}'}
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return False
    
    @staticmethod
    def extract_issue_number(text: str) -> List[int]:
        """
        Extract GitHub issue numbers from text
        
        Args:
            text: Text to search for issue numbers
        
        Returns:
            List of issue numbers found
        """
        pattern = r'#(\d+)'
        matches = re.findall(pattern, text)
        return [int(match) for match in matches]
    
    @staticmethod
    def create_github_link(repo_url: str, path: str = "", line: int = None) -> str:
        """
        Create a GitHub link to a file or line
        
        Args:
            repo_url: GitHub repository URL
            path: File path (optional)
            line: Line number (optional)
        
        Returns:
            Complete GitHub URL
        """
        base_url = repo_url.rstrip('/')
        
        if path:
            link = f"{base_url}/blob/main/{path}"
            if line:
                link += f"#L{line}"
            return link
        
        return base_url