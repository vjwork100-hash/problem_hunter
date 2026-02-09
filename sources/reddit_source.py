import praw
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from cache import Cache
from sources.base_source import BaseSource
from utils import get_expanded_pain_keywords, get_pain_score, format_timestamp

class RedditSource(BaseSource):
    """Reddit data source using PRAW."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        load_dotenv()
        self.reddit = praw.Reddit(
            client_id=client_id or os.getenv("REDDIT_CLIENT_ID"),
            client_secret=client_secret or os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=user_agent or os.getenv("REDDIT_USER_AGENT", "ProblemHunter/0.1")
        )
        self.cache = Cache()
        self.pain_keywords = get_expanded_pain_keywords()
        
        # Expanded list of high-signal subreddits for pain point discovery
        self.subreddits = [
            # Entrepreneurship & Business
            "Entrepreneur", "smallbusiness", "startups", "SideProject", "EntrepreneurRideAlong",
            # SaaS & Tech
            "SaaS", "microsaas", "indiehackers", "webdev", "programming",
            # Productivity & Tools
            "productivity", "selfimprovement", "GetMotivated", "LifeProTips",
            # Freelancing & Remote Work
            "freelance", "digitalnomad", "remotework", "WorkOnline",
            # Finance & Accounting
            "Accounting", "Bookkeeping", "personalfinance", "smallbusinessfinance",
            # Marketing & Sales
            "marketing", "sales", "SEO", "socialmedia",
            # Design & Creative
            "graphic_design", "UI_Design", "UXDesign",
            # Industry-Specific
            "realestate", "ecommerce", "Shopify", "AmazonFBA"
        ]

    def get_source_name(self) -> str:
        return "reddit"

    def fetch_posts(
        self, 
        keywords: Optional[List[str]] = None, 
        limit: int = 50,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from multiple subreddits.
        
        Args:
            keywords: Search terms (if None, uses pain keywords)
            limit: Maximum posts to return
            browse_mode: If True, browse top posts without keyword filtering
            sort_by: Sort order - 'hot', 'new', or 'top'
            
        Returns:
            List of normalized posts with pain_score
        """
        all_posts = []
        
        if browse_mode:
            # Browse mode: Get top posts from each subreddit
            all_posts = self._browse_reddit(limit, sort_by)
        else:
            # Keyword mode: Search for specific terms
            search_terms = keywords if keywords else self.pain_keywords[:5]
            query = " OR ".join(search_terms)
            all_posts = self._search_reddit(query, limit)
        
        return all_posts[:limit]
    
    def _browse_reddit(self, limit: int, sort_by: str = 'hot') -> List[Dict[str, Any]]:
        """Browse top posts from subreddits without keyword filtering."""
        all_posts = []
        posts_per_sub = max(2, limit // len(self.subreddits[:10]))  # Limit to top 10 subreddits
        
        for sub_name in self.subreddits[:10]:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                
                # Get posts based on sort_by
                if sort_by == 'hot':
                    posts = subreddit.hot(limit=posts_per_sub)
                elif sort_by == 'new':
                    posts = subreddit.new(limit=posts_per_sub)
                elif sort_by == 'top':
                    posts = subreddit.top(time_filter='week', limit=posts_per_sub)
                else:
                    posts = subreddit.hot(limit=posts_per_sub)
                
                for post in posts:
                    normalized = self.normalize_data(post)
                    if normalized:
                        all_posts.append(normalized)
                    
                    if len(all_posts) >= limit:
                        break
                
                # Rate limiting
                time.sleep(1.0)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error browsing r/{sub_name}: {e}")
                continue
        
        return all_posts
    
    def _search_reddit(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Reddit with keyword query."""
        all_posts = []
        search_limit = limit * 2  # Fetch more to account for filtering
        
        for sub_name in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                
                # Search within the subreddit
                search_results = subreddit.search(query, sort='new', limit=search_limit)
                
                for post in search_results:
                    # Check cache first
                    post_id = post.id
                    cached_post = self.cache.get_post(post_id)
                    if cached_post:
                        all_posts.append(cached_post)
                        if len(all_posts) >= limit:
                            break
                        continue
                    
                    normalized = self.normalize_data(post)
                    if normalized:
                        self.cache.save_post(post_id, normalized)
                        all_posts.append(normalized)
                    
                    if len(all_posts) >= limit:
                        break
                
                # Rate limiting
                time.sleep(1.0)
                
                if len(all_posts) >= limit:
                    break
                        
            except Exception as e:
                print(f"Error fetching from r/{sub_name}: {e}")
                continue
                
        return all_posts
    
    def normalize_data(self, post) -> Optional[Dict[str, Any]]:
        """Convert Reddit post to standard format with pain_score."""
        try:
            # Skip if no title
            if not post.title:
                return None
            
            # Get text content
            text = post.selftext if hasattr(post, 'selftext') else ""
            
            # Calculate pain score
            combined_text = f"{post.title} {text}"
            pain_score = get_pain_score(combined_text)
            
            # Format date
            created_utc = int(post.created_utc) if hasattr(post, 'created_utc') else 0
            date_str = format_timestamp(created_utc)
            
            return {
                "id": f"reddit_{post.id}",
                "title": post.title,
                "text": text,
                "url": f"https://reddit.com{post.permalink}" if hasattr(post, 'permalink') else post.url,
                "source": "reddit",
                "subreddit": post.subreddit.display_name if hasattr(post, 'subreddit') else "unknown",
                "created_utc": created_utc,
                "date": date_str,  # Human-readable date
                "score": post.score if hasattr(post, 'score') else 0,
                "num_comments": post.num_comments if hasattr(post, 'num_comments') else 0,
                "pain_score": pain_score  # NEW: Pain intensity score
            }
        except Exception as e:
            print(f"Error normalizing Reddit post: {e}")
            return None
