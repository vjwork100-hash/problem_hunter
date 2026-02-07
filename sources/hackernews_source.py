import requests
import time
from typing import List, Dict, Any
from sources.base_source import BaseSource

class HackerNewsSource(BaseSource):
    """Hacker News data source using Algolia API (no auth required)."""
    
    def __init__(self):
        self.api_base = "https://hn.algolia.com/api/v1"
        self.pain_keywords = [
            "hate", "frustrated", "annoying", "tedious", "manual",
            "time-consuming", "difficult", "struggle", "wish there was",
            "looking for", "need help", "problem with"
        ]
    
    def get_source_name(self) -> str:
        return "hackernews"
    
    def fetch_posts(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch posts from Hacker News.
        Searches "Ask HN" and "Show HN" posts for pain points.
        """
        all_posts = []
        
        # Combine user keywords with pain keywords
        search_terms = keywords if keywords else self.pain_keywords
        
        for keyword in search_terms[:3]:  # Limit to avoid too many requests
            try:
                # Search Ask HN posts
                ask_posts = self._search_hn(f"Ask HN {keyword}", limit_per_query=limit//2)
                all_posts.extend(ask_posts)
                
                # Small delay to respect rate limits
                time.sleep(0.5)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching from Hacker News for '{keyword}': {e}")
                continue
        
        return all_posts[:limit]
    
    def _search_hn(self, query: str, limit_per_query: int = 25) -> List[Dict[str, Any]]:
        """Search Hacker News using Algolia API."""
        url = f"{self.api_base}/search"
        params = {
            "query": query,
            "tags": "story",  # Only get stories, not comments
            "hitsPerPage": min(limit_per_query, 50),  # API max is 1000
            "numericFilters": "points>5,num_comments>2"  # Filter low-quality posts
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for hit in data.get("hits", []):
            normalized = self.normalize_data(hit)
            if normalized:
                posts.append(normalized)
        
        return posts
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert HN API response to standard format."""
        # Skip if no title or it's a job posting
        title = raw_data.get("title", "")
        if not title or "hiring" in title.lower() or "who is hiring" in title.lower():
            return None
        
        return {
            "id": f"hn_{raw_data.get('objectID', '')}",
            "title": title,
            "text": raw_data.get("story_text", "") or raw_data.get("comment_text", ""),
            "url": raw_data.get("url") or f"https://news.ycombinator.com/item?id={raw_data.get('objectID')}",
            "source": "hackernews",
            "created_utc": raw_data.get("created_at_i", 0),
            "score": raw_data.get("points", 0),
            "num_comments": raw_data.get("num_comments", 0)
        }
