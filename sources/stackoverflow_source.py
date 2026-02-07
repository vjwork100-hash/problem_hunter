import requests
import time
from typing import List, Dict, Any
from sources.base_source import BaseSource

class StackOverflowSource(BaseSource):
    """Stack Overflow data source using Stack Exchange API (no auth required)."""
    
    def __init__(self):
        self.api_base = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"
    
    def get_source_name(self) -> str:
        return "stackoverflow"
    
    def fetch_posts(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch questions from Stack Overflow.
        Focuses on high-view, low-answer questions indicating pain points.
        """
        all_posts = []
        
        # Combine keywords into search query
        search_terms = keywords if keywords else ["automation", "workflow", "manual"]
        
        for keyword in search_terms[:3]:  # Limit to avoid rate limits
            try:
                questions = self._search_questions(keyword, limit_per_query=limit//3)
                all_posts.extend(questions)
                
                # Respect rate limits
                time.sleep(1)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching from Stack Overflow for '{keyword}': {e}")
                continue
        
        return all_posts[:limit]
    
    def _search_questions(self, query: str, limit_per_query: int = 20) -> List[Dict[str, Any]]:
        """Search Stack Overflow questions."""
        url = f"{self.api_base}/search/advanced"
        params = {
            "q": query,
            "site": self.site,
            "pagesize": min(limit_per_query, 100),  # API max is 100
            "order": "desc",
            "sort": "votes",
            "filter": "withbody",  # Include question body
            "min_views": 100,  # Filter low-quality questions
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for item in data.get("items", []):
            normalized = self.normalize_data(item)
            if normalized:
                posts.append(normalized)
        
        return posts
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Stack Overflow API response to standard format."""
        # Skip if already has accepted answer (problem is solved)
        if raw_data.get("is_answered", False):
            return None
        
        # Extract tags for context
        tags = raw_data.get("tags", [])
        
        return {
            "id": f"so_{raw_data.get('question_id', '')}",
            "title": raw_data.get("title", ""),
            "text": raw_data.get("body", "")[:1000],  # Truncate long bodies
            "url": raw_data.get("link", ""),
            "source": "stackoverflow",
            "created_utc": raw_data.get("creation_date", 0),
            "score": raw_data.get("score", 0),
            "num_comments": raw_data.get("answer_count", 0),
            "tags": ", ".join(tags[:5])  # Include tags for context
        }
