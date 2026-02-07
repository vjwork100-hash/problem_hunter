import requests
import time
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from sources.base_source import BaseSource

class GitHubSource(BaseSource):
    """GitHub Issues data source using GitHub API."""
    
    def __init__(self, token: str = None):
        load_dotenv()
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def get_source_name(self) -> str:
        return "github"
    
    def fetch_posts(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch GitHub issues from popular repositories.
        Focuses on feature requests and enhancement issues.
        """
        all_posts = []
        
        # Search across all public repos
        search_terms = keywords if keywords else ["automation", "workflow", "manual process"]
        
        for keyword in search_terms[:3]:  # Limit searches
            try:
                issues = self._search_issues(keyword, limit_per_query=limit//3)
                all_posts.extend(issues)
                
                # Respect rate limits
                time.sleep(2)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching from GitHub for '{keyword}': {e}")
                continue
        
        return all_posts[:limit]
    
    def _search_issues(self, query: str, limit_per_query: int = 20) -> List[Dict[str, Any]]:
        """Search GitHub issues."""
        url = f"{self.api_base}/search/issues"
        params = {
            "q": f"{query} is:issue is:open label:enhancement,feature-request",
            "sort": "reactions",
            "order": "desc",
            "per_page": min(limit_per_query, 100)
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for item in data.get("items", []):
            normalized = self.normalize_data(item)
            if normalized:
                posts.append(normalized)
        
        return posts
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GitHub API response to standard format."""
        # Skip pull requests
        if "pull_request" in raw_data:
            return None
        
        # Calculate engagement score (reactions + comments)
        reactions = raw_data.get("reactions", {}).get("total_count", 0)
        comments = raw_data.get("comments", 0)
        engagement = reactions + comments
        
        return {
            "id": f"gh_{raw_data.get('id', '')}",
            "title": raw_data.get("title", ""),
            "text": raw_data.get("body", "")[:1000] if raw_data.get("body") else "",
            "url": raw_data.get("html_url", ""),
            "source": "github",
            "created_utc": self._parse_github_date(raw_data.get("created_at", "")),
            "score": engagement,
            "num_comments": comments,
            "repository": raw_data.get("repository_url", "").split("/")[-1] if raw_data.get("repository_url") else "unknown"
        }
    
    def _parse_github_date(self, date_str: str) -> int:
        """Convert GitHub ISO date to Unix timestamp."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except:
            return 0
