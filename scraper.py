import praw
import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from cache import Cache

class RedditClient:
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        load_dotenv()
        self.reddit = praw.Reddit(
            client_id=client_id or os.getenv("REDDIT_CLIENT_ID"),
            client_secret=client_secret or os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=user_agent or os.getenv("REDDIT_USER_AGENT", "ProblemHunter/0.1")
        )
        self.cache = Cache()
        
        # Regex patterns for high-signal pain points
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
            r"broken",
            r"cant believe",
            r"can't believe"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.pain_patterns]

    def _matches_patterns(self, text: str) -> bool:
        """Check if text matches any of the pain point patterns."""
        if not text:
            return False
        return any(p.search(text) for p in self.compiled_patterns)

    def fetch_posts(self, subreddits: List[str], keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch posts from subreddits that match keywords and pain patterns.
        """
        all_posts = []
        # Combine keywords for search query, or use a general query if no keywords
        query = " OR ".join(keywords) if keywords else "pain OR problem OR solution"
        
        for sub_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                # Search within the subreddit
                # We fetch more than limit because we will filter them
                search_limit = limit * 3 
                
                # Fetch recent posts matching query
                searchResults = subreddit.search(query, sort='new', limit=search_limit)
                
                for post in searchResults:
                    post_id = post.id
                    
                    # Check cache first
                    cached_post = self.cache.get_post(post_id)
                    if cached_post:
                        all_posts.append(cached_post)
                        if len(all_posts) >= limit:
                             break
                        continue

                    # Text for filtering: Title + Selftext
                    content = f"{post.title} {post.selftext}"
                    
                    # 1. Regex Pre-filter
                    if self._matches_patterns(content):
                        post_data = {
                            "id": post.id,
                            "title": post.title,
                            "text": post.selftext,
                            "url": post.url,
                            "subreddit": post.subreddit.display_name,
                            "created_utc": post.created_utc,
                            "score": post.score,
                            "num_comments": post.num_comments
                        }
                        self.cache.save_post(post_id, post_data)
                        all_posts.append(post_data)
                    
                    if len(all_posts) >= limit:
                        break
                        
            except Exception as e:
                print(f"Error fetching from r/{sub_name}: {e}")
                continue
                
        return all_posts[:limit]
