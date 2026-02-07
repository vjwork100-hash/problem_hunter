from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSource(ABC):
    """Abstract base class for all data sources."""
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source."""
        pass
    
    @abstractmethod
    def fetch_posts(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch posts from this source.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of posts to return
            
        Returns:
            List of normalized post dictionaries with standard fields:
            - id: Unique identifier
            - title: Post title
            - text: Post body/content
            - url: Link to original post
            - source: Source name (e.g., "hackernews", "reddit")
            - created_utc: Unix timestamp
            - score: Upvotes/likes/engagement metric
            - num_comments: Number of comments/replies
        """
        pass
    
    def normalize_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        Convert source-specific data format to standard format.
        Override this if needed for complex transformations.
        """
        return raw_data
