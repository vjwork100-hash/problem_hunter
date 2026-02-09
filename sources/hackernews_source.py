import requests
import time
from typing import List, Dict, Any, Optional
from sources.base_source import BaseSource
from utils import get_expanded_pain_keywords, get_pain_score, format_timestamp

class HackerNewsSource(BaseSource):
    """Hacker News data source using Algolia API (no auth required)."""
    
    def __init__(self):
        self.api_base = "https://hn.algolia.com/api/v1"
        self.pain_keywords = get_expanded_pain_keywords()
    
    def get_source_name(self) -> str:
        return "hackernews"
    
    def fetch_posts(
        self, 
        keywords: Optional[List[str]] = None, 
        limit: int = 50,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from Hacker News.
        
        Args:
            keywords: Search terms (if None, uses pain keywords)
            limit: Maximum posts to return
            browse_mode: If True, browse top posts without keyword filtering
            sort_by: Sort order - 'hot', 'new', or 'top' (maps to HN filters)
            
        Returns:
            List of normalized posts with pain_score
        """
        all_posts = []
        
        if browse_mode:
            # Browse mode: Get top "Ask HN" posts without keyword filtering
            all_posts = self._browse_hn(limit, sort_by)
        else:
            # Keyword mode: Search for specific terms
            search_terms = keywords if keywords else self.pain_keywords[:5]  # Limit to top 5 keywords
            
            for keyword in search_terms[:3]:  # Limit to avoid too many requests
                try:
                    # Search Ask HN posts
                    ask_posts = self._search_hn(f"Ask HN {keyword}", limit_per_query=limit//2)
                    all_posts.extend(ask_posts)
                    
                    # Rate limiting
                    time.sleep(1.0)  # 1 second between requests
                    
                    if len(all_posts) >= limit:
                        break
                        
                except Exception as e:
                    print(f"Error fetching from Hacker News for '{keyword}': {e}")
                    continue
        
        return all_posts[:limit]
    
    def _browse_hn(self, limit: int, sort_by: str = 'hot') -> List[Dict[str, Any]]:
        """Browse top HN posts without keyword filtering."""
        url = f"{self.api_base}/search"
        
        # Map sort_by to HN API parameters
        sort_mapping = {
            'hot': 'search',  # Default search (by relevance/points)
            'new': 'search_by_date',
            'top': 'search'  # Will filter by points
        }
        
        params = {
            "tags": "ask_hn",  # Only Ask HN posts
            "hitsPerPage": min(limit, 50),
            "numericFilters": "points>10,num_comments>5"  # Quality filter
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for hit in data.get("hits", []):
                normalized = self.normalize_data(hit)
                if normalized:
                    posts.append(normalized)
            
            return posts
        except Exception as e:
            print(f"Error browsing Hacker News: {e}")
            return []
    
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
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert HN API response to standard format with pain_score."""
        # Skip if no title or it's a job posting
        title = raw_data.get("title", "")
        if not title or "hiring" in title.lower() or "who is hiring" in title.lower():
            return None
        
        # Get text content
        text = raw_data.get("story_text", "") or raw_data.get("comment_text", "")
        
        # Calculate pain score
        combined_text = f"{title} {text}"
        pain_score = get_pain_score(combined_text)
        
        # Format date
        created_utc = raw_data.get("created_at_i", 0)
        date_str = format_timestamp(created_utc)
        
        return {
            "id": f"hn_{raw_data.get('objectID', '')}",
            "title": title,
            "text": text,
            "url": raw_data.get("url") or f"https://news.ycombinator.com/item?id={raw_data.get('objectID')}",
            "source": "hackernews",
            "created_utc": created_utc,
            "date": date_str,  # Human-readable date
            "score": raw_data.get("points", 0),
            "num_comments": raw_data.get("num_comments", 0),
            "pain_score": pain_score  # NEW: Pain intensity score
        }
