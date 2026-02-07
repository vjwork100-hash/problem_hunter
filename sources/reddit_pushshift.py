import requests
import time
import re
from typing import List, Dict, Any
from sources.base_source import BaseSource

class RedditPushshiftSource(BaseSource):
    """Reddit data source using Pushshift.io API (no auth required)."""
    
    def __init__(self):
        self.api_base = "https://api.pushshift.io/reddit/search/submission"
        
        # Regex patterns for pain points (same as Reddit source)
        self.pain_patterns = [
            r"hate (manually|doing|when)",
            r"takes? (too long|forever|hours)",
            r"wish (there was|I could)",
            r"tired of",
            r"struggle with",
            r"hard to find",
            r"expensive",
            r"complicated",
            r"annoying",
            r"frustrating",
            r"tedious",
            r"repetitive",
            r"manual work",
            r"waste of time",
            r"no good solution",
            r"sucks",
            r"broken"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.pain_patterns]
    
    def get_source_name(self) -> str:
        return "reddit_pushshift"
    
    def _matches_patterns(self, text: str) -> bool:
        """Check if text matches pain point patterns."""
        if not text:
            return False
        return any(p.search(text) for p in self.compiled_patterns)
    
    def fetch_posts(self, keywords: List[str], limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch posts from Reddit via Pushshift.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of posts to return
            subreddits: List of subreddit names (optional)
        """
        if subreddits is None:
            subreddits = ["Entrepreneur", "smallbusiness", "SaaS", "startups"]
        
        all_posts = []
        query = " OR ".join(keywords) if keywords else "pain OR problem OR solution"
        
        for subreddit in subreddits:
            try:
                posts = self._search_subreddit(subreddit, query, limit_per_sub=limit//len(subreddits))
                all_posts.extend(posts)
                
                # Respect rate limits
                time.sleep(1)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching from r/{subreddit} via Pushshift: {e}")
                continue
        
        return all_posts[:limit]
    
    def _search_subreddit(self, subreddit: str, query: str, limit_per_sub: int = 25) -> List[Dict[str, Any]]:
        """Search a subreddit using Pushshift."""
        params = {
            "subreddit": subreddit,
            "q": query,
            "size": min(limit_per_sub, 100),  # API max
            "sort": "desc",
            "sort_type": "created_utc",
            "selftext:not": "[removed]",  # Exclude removed posts
            "selftext:not": "[deleted]"
        }
        
        response = requests.get(self.api_base, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for item in data.get("data", []):
            # Apply regex pre-filter
            content = f"{item.get('title', '')} {item.get('selftext', '')}"
            if self._matches_patterns(content):
                normalized = self.normalize_data(item)
                if normalized:
                    posts.append(normalized)
        
        return posts
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Pushshift API response to standard format."""
        return {
            "id": f"reddit_ps_{raw_data.get('id', '')}",
            "title": raw_data.get("title", ""),
            "text": raw_data.get("selftext", ""),
            "url": f"https://reddit.com{raw_data.get('permalink', '')}",
            "source": "reddit_pushshift",
            "subreddit": raw_data.get("subreddit", ""),
            "created_utc": raw_data.get("created_utc", 0),
            "score": raw_data.get("score", 0),
            "num_comments": raw_data.get("num_comments", 0)
        }
