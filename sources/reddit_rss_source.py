import feedparser
import time
import hashlib
from typing import List, Dict, Any, Optional
from sources.base_source import BaseSource
from utils import get_expanded_pain_keywords, get_pain_score, format_timestamp

class RedditRSSSource(BaseSource):
    """
    Reddit RSS fallback source - works without API keys!
    
    Uses public RSS feeds from Reddit. No authentication required.
    Perfect for immediate use while waiting for API approval.
    
    Limitations:
    - Limited to ~25 posts per feed
    - No post body/selftext (title only)
    - Slower than official API
    
    Advantages:
    - ✅ No API keys needed
    - ✅ Works immediately
    - ✅ No rate limits (reasonable usage)
    """
    
    def __init__(self):
        self.pain_keywords = get_expanded_pain_keywords()
        # Default subreddits for SaaS/business pain points
        self.default_subreddits = [
            "SaaS",
            "Entrepreneur",
            "smallbusiness",
            "marketing",
            "productivity",
            "startups",
            "business",
            "freelance",
            "solopreneur"
        ]
    
    def get_source_name(self) -> str:
        return "reddit_rss"
    
    def fetch_posts(
        self,
        keywords: Optional[List[str]] = None,
        limit: int = 50,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from Reddit RSS feeds.
        
        Args:
            keywords: Keywords to filter by (if None, uses pain keywords)
            limit: Maximum posts to return
            browse_mode: If True, browse top posts without keyword filtering
            sort_by: Sort order - 'hot', 'new', or 'top'
            
        Returns:
            List of normalized posts with pain_score
        """
        all_posts = []
        subreddits = self.default_subreddits
        
        # Map sort_by to RSS endpoints
        sort_mapping = {
            'hot': '',  # Default is hot
            'new': '/new',
            'top': '/top'
        }
        sort_path = sort_mapping.get(sort_by, '')
        
        for subreddit in subreddits:
            try:
                # Fetch from RSS feed
                posts = self._fetch_subreddit_rss(subreddit, sort_path, limit_per_sub=limit//len(subreddits))
                
                # Filter by keywords if not in browse mode
                if not browse_mode and keywords:
                    search_terms = keywords if keywords else self.pain_keywords[:10]
                    posts = self._filter_by_keywords(posts, search_terms)
                
                all_posts.extend(posts)
                
                # Rate limiting - be nice to Reddit
                time.sleep(1.0)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching RSS from r/{subreddit}: {e}")
                continue
        
        return all_posts[:limit]
    
    def _fetch_subreddit_rss(self, subreddit: str, sort_path: str = '', limit_per_sub: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch posts from a single subreddit's RSS feed.
        
        Args:
            subreddit: Subreddit name (without r/)
            sort_path: Sort path ('', '/new', or '/top')
            limit_per_sub: Max posts to fetch
            
        Returns:
            List of normalized posts
        """
        # Construct RSS URL
        url = f"https://www.reddit.com/r/{subreddit}{sort_path}.rss"
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            if not feed.entries:
                return []
            
            posts = []
            for entry in feed.entries[:limit_per_sub]:
                normalized = self.normalize_data(entry, subreddit)
                if normalized:
                    posts.append(normalized)
            
            return posts
            
        except Exception as e:
            print(f"Error parsing RSS feed for r/{subreddit}: {e}")
            return []
    
    def _filter_by_keywords(self, posts: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Filter posts by keywords in title.
        
        Args:
            posts: List of posts
            keywords: Keywords to search for
            
        Returns:
            Filtered list of posts
        """
        filtered = []
        keywords_lower = [k.lower() for k in keywords]
        
        for post in posts:
            title = post.get('title', '').lower()
            # Check if any keyword appears in title
            if any(keyword in title for keyword in keywords_lower):
                filtered.append(post)
        
        return filtered
    
    def normalize_data(self, entry: Any, subreddit: str) -> Optional[Dict[str, Any]]:
        """
        Convert RSS feed entry to standard format.
        
        Args:
            entry: feedparser entry object
            subreddit: Subreddit name
            
        Returns:
            Normalized post dict or None if invalid
        """
        try:
            # Extract data from RSS entry
            title = entry.get('title', '')
            link = entry.get('link', '')
            
            # RSS doesn't include selftext, so we only have title
            # This is a limitation of RSS vs API
            text = entry.get('summary', '')[:500] if entry.get('summary') else ''
            
            # Parse published time
            published_parsed = entry.get('published_parsed')
            if published_parsed:
                created_utc = int(time.mktime(published_parsed))
            else:
                created_utc = int(time.time())
            
            # Generate unique ID from link
            post_id = hashlib.md5(link.encode()).hexdigest()[:16]
            
            # Calculate pain score
            combined_text = f"{title} {text}"
            pain_score = get_pain_score(combined_text)
            
            # Format date
            date_str = format_timestamp(created_utc)
            
            # Extract author if available
            author = entry.get('author', 'unknown')
            if author.startswith('/u/'):
                author = author[3:]  # Remove /u/ prefix
            
            return {
                "id": f"rss_{post_id}",
                "title": title,
                "text": text,
                "url": link,
                "source": "reddit_rss",
                "subreddit": subreddit,
                "created_utc": created_utc,
                "date": date_str,
                "score": 0,  # RSS doesn't include score
                "num_comments": 0,  # RSS doesn't include comment count
                "author": author,
                "pain_score": pain_score
            }
            
        except Exception as e:
            print(f"Error normalizing RSS entry: {e}")
            return None
