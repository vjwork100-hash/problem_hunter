import requests
import time
from typing import List, Dict, Any, Optional
from sources.base_source import BaseSource
from utils import get_expanded_pain_keywords, get_pain_score, format_timestamp

class StackOverflowSource(BaseSource):
    """Stack Overflow data source using Stack Exchange API (no auth required)."""
    
    def __init__(self):
        self.api_base = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"
        self.pain_keywords = get_expanded_pain_keywords()
    
    def get_source_name(self) -> str:
        return "stackoverflow"
    
    def fetch_posts(
        self, 
        keywords: Optional[List[str]] = None, 
        limit: int = 50,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> List[Dict[str, Any]]:
        """
        Fetch questions from Stack Overflow.
        
        Args:
            keywords: Search terms (if None, uses pain keywords)
            limit: Maximum posts to return
            browse_mode: If True, browse top questions without keyword filtering
            sort_by: Sort order - 'hot', 'new', or 'top' (votes)
            
        Returns:
            List of normalized posts with pain_score
        """
        all_posts = []
        
        if browse_mode:
            # Browse mode: Get top questions
            all_posts = self._browse_questions(limit, sort_by)
        else:
            # Keyword mode: Search for specific terms
            search_terms = keywords if keywords else self.pain_keywords[:3]
            
            for keyword in search_terms[:3]:  # Limit to avoid rate limits
                try:
                    questions = self._search_questions(keyword, limit_per_query=limit//3)
                    all_posts.extend(questions)
                    
                    # Rate limiting
                    time.sleep(1.0)
                    
                    if len(all_posts) >= limit:
                        break
                        
                except Exception as e:
                    print(f"Error fetching from Stack Overflow for '{keyword}': {e}")
                    continue
        
        return all_posts[:limit]
    
    def _browse_questions(self, limit: int, sort_by: str = 'hot') -> List[Dict[str, Any]]:
        """Browse top Stack Overflow questions."""
        url = f"{self.api_base}/questions"
        
        # Map sort_by
        sort_mapping = {
            'hot': 'hot',
            'new': 'creation',
            'top': 'votes'
        }
        
        params = {
            "site": self.site,
            "pagesize": min(limit, 100),
            "order": "desc",
            "sort": sort_mapping.get(sort_by, 'hot'),
            "filter": "withbody",
            "min_views": 100
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for item in data.get("items", []):
                normalized = self.normalize_data(item)
                if normalized:
                    posts.append(normalized)
            
            return posts
        except Exception as e:
            print(f"Error browsing Stack Overflow: {e}")
            return []
    
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
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Stack Overflow API response to standard format with pain_score."""
        # Skip if already has accepted answer (problem is solved)
        if raw_data.get("is_answered", False):
            return None
        
        # Extract tags for context
        tags = raw_data.get("tags", [])
        title = raw_data.get("title", "")
        body = raw_data.get("body", "")[:1000]  # Truncate long bodies
        
        # Calculate pain score
        combined_text = f"{title} {body}"
        pain_score = get_pain_score(combined_text)
        
        # Format date
        created_utc = raw_data.get("creation_date", 0)
        date_str = format_timestamp(created_utc)
        
        return {
            "id": f"so_{raw_data.get('question_id', '')}",
            "title": title,
            "text": body,
            "url": raw_data.get("link", ""),
            "source": "stackoverflow",
            "created_utc": created_utc,
            "date": date_str,  # Human-readable date
            "score": raw_data.get("score", 0),
            "num_comments": raw_data.get("answer_count", 0),
            "tags": ", ".join(tags[:5]),  # Include tags for context
            "pain_score": pain_score  # NEW: Pain intensity score
        }
