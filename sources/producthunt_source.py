import requests
import time
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from sources.base_source import BaseSource

class ProductHuntSource(BaseSource):
    """Product Hunt data source using Product Hunt API v2 (GraphQL)."""
    
    def __init__(self, token: str = None):
        load_dotenv()
        self.token = token or os.getenv("PRODUCTHUNT_TOKEN")
        self.api_base = "https://api.producthunt.com/v2/api/graphql"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def get_source_name(self) -> str:
        return "producthunt"
    
    def fetch_posts(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch Product Hunt posts and comments.
        Focuses on comments expressing pain points.
        """
        if not self.token:
            print("Warning: Product Hunt API token not found. Skipping.")
            return []
        
        all_posts = []
        
        try:
            # Fetch recent posts
            posts = self._fetch_recent_posts(limit=20)
            
            # Extract comments from posts
            for post in posts:
                comments = self._extract_comments(post, keywords)
                all_posts.extend(comments)
                
                if len(all_posts) >= limit:
                    break
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error fetching from Product Hunt: {e}")
        
        return all_posts[:limit]
    
    def _fetch_recent_posts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent Product Hunt posts using GraphQL."""
        query = """
        query {
          posts(first: %d) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                createdAt
                comments(first: 10) {
                  edges {
                    node {
                      id
                      body
                      createdAt
                      votesCount
                    }
                  }
                }
              }
            }
          }
        }
        """ % limit
        
        response = requests.post(
            self.api_base,
            headers=self.headers,
            json={"query": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return [edge["node"] for edge in data.get("data", {}).get("posts", {}).get("edges", [])]
    
    def _extract_comments(self, post: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """Extract relevant comments from a post."""
        comments = []
        post_title = post.get("name", "")
        
        for comment_edge in post.get("comments", {}).get("edges", []):
            comment = comment_edge["node"]
            body = comment.get("body", "").lower()
            
            # Check if comment contains pain keywords
            if any(kw.lower() in body for kw in keywords):
                comments.append(self.normalize_data(post, comment))
        
        return comments
    
    def normalize_data(self, post: Dict[str, Any], comment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Product Hunt data to standard format."""
        return {
            "id": f"ph_{comment.get('id', '')}",
            "title": f"Comment on: {post.get('name', '')}",
            "text": comment.get("body", ""),
            "url": post.get("url", ""),
            "source": "producthunt",
            "created_utc": self._parse_ph_date(comment.get("createdAt", "")),
            "score": comment.get("votesCount", 0),
            "num_comments": 0,
            "product": post.get("name", "")
        }
    
    def _parse_ph_date(self, date_str: str) -> int:
        """Convert Product Hunt ISO date to Unix timestamp."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except:
            return 0
