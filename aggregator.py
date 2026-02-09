import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from datetime import datetime
from sources.base_source import BaseSource

class Aggregator:
    """
    Multi-source orchestrator for parallel data fetching.
    Handles graceful error handling and result normalization.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize aggregator.
        
        Args:
            max_workers: Maximum number of parallel workers for fetching
        """
        self.max_workers = max_workers
        self.fetch_stats = {
            'total_fetches': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'total_posts': 0,
            'fetch_times': {}
        }
    
    def fetch_from_sources(
        self,
        sources: List[tuple[str, BaseSource]],
        keywords: List[str],
        limit_per_source: int = 50,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> Dict[str, Any]:
        """
        Fetch posts from multiple sources in parallel.
        
        Args:
            sources: List of (source_name, source_instance) tuples
            keywords: Keywords to search for (ignored if browse_mode=True)
            limit_per_source: Max posts per source
            browse_mode: If True, browse top posts without keyword filtering
            sort_by: Sort order - 'hot', 'new', or 'top'
            
        Returns:
            Dictionary with 'posts' (list) and 'errors' (dict)
        """
        all_posts = []
        errors = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all fetch tasks
            future_to_source = {
                executor.submit(
                    self._fetch_with_error_handling,
                    source_name,
                    source_instance,
                    keywords,
                    limit_per_source,
                    browse_mode,
                    sort_by
                ): source_name
                for source_name, source_instance in sources
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    result = future.result()
                    if result['success']:
                        all_posts.extend(result['posts'])
                        self.fetch_stats['successful_fetches'] += 1
                        self.fetch_stats['total_posts'] += len(result['posts'])
                        self.fetch_stats['fetch_times'][source_name] = result['fetch_time']
                    else:
                        errors[source_name] = result['error']
                        self.fetch_stats['failed_fetches'] += 1
                except Exception as e:
                    errors[source_name] = str(e)
                    self.fetch_stats['failed_fetches'] += 1
                
                self.fetch_stats['total_fetches'] += 1
        
        return {
            'posts': all_posts,
            'errors': errors,
            'stats': self.get_stats()
        }
    
    def _fetch_with_error_handling(
        self,
        source_name: str,
        source: BaseSource,
        keywords: List[str],
        limit: int,
        browse_mode: bool = False,
        sort_by: str = 'hot'
    ) -> Dict[str, Any]:
        """
        Fetch from a single source with error handling and timing.
        
        Returns:
            Dictionary with 'success', 'posts', 'error', 'fetch_time'
        """
        start_time = time.time()
        
        try:
            # Pass browse_mode and sort_by to source
            posts = source.fetch_posts(
                keywords=keywords, 
                limit=limit,
                browse_mode=browse_mode,
                sort_by=sort_by
            )
            fetch_time = time.time() - start_time
            
            # Validate posts
            if not isinstance(posts, list):
                return {
                    'success': False,
                    'posts': [],
                    'error': f"Invalid return type: expected list, got {type(posts)}",
                    'fetch_time': fetch_time
                }
            
            # Normalize all posts
            normalized_posts = []
            for post in posts:
                if self._validate_post(post):
                    normalized_posts.append(post)
                else:
                    print(f"Warning: Invalid post from {source_name}: {post.get('id', 'unknown')}")
            
            return {
                'success': True,
                'posts': normalized_posts,
                'error': None,
                'fetch_time': fetch_time
            }
            
        except Exception as e:
            fetch_time = time.time() - start_time
            return {
                'success': False,
                'posts': [],
                'error': str(e),
                'fetch_time': fetch_time
            }
    
    def _validate_post(self, post: Dict[str, Any]) -> bool:
        """
        Validate that a post has all required fields.
        
        Required fields: id, title, url, source
        """
        required_fields = ['id', 'title', 'url', 'source']
        return all(field in post for field in required_fields)
    
    def deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate posts based on ID.
        Keeps the first occurrence of each unique ID.
        """
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            post_id = post.get('id')
            if post_id and post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        return unique_posts
    
    def sort_posts(
        self,
        posts: List[Dict[str, Any]],
        sort_by: str = 'score',
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sort posts by a given field.
        
        Args:
            posts: List of posts
            sort_by: Field to sort by (score, created_utc, num_comments, pain_score)
            reverse: Sort descending if True
        """
        return sorted(
            posts,
            key=lambda p: p.get(sort_by, 0),
            reverse=reverse
        )
    
    def filter_posts(
        self,
        posts: List[Dict[str, Any]],
        min_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        after_timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter posts based on criteria.
        
        Args:
            posts: List of posts
            min_score: Minimum score threshold
            sources: List of allowed sources
            after_timestamp: Only posts after this timestamp
        """
        filtered = posts
        
        if min_score is not None:
            filtered = [p for p in filtered if p.get('score', 0) >= min_score]
        
        if sources:
            filtered = [p for p in filtered if p.get('source') in sources]
        
        if after_timestamp is not None:
            filtered = [p for p in filtered if p.get('created_utc', 0) >= after_timestamp]
        
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        return {
            'total_fetches': self.fetch_stats['total_fetches'],
            'successful_fetches': self.fetch_stats['successful_fetches'],
            'failed_fetches': self.fetch_stats['failed_fetches'],
            'total_posts': self.fetch_stats['total_posts'],
            'success_rate': (
                self.fetch_stats['successful_fetches'] / self.fetch_stats['total_fetches']
                if self.fetch_stats['total_fetches'] > 0 else 0
            ),
            'fetch_times': self.fetch_stats['fetch_times']
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.fetch_stats = {
            'total_fetches': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'total_posts': 0,
            'fetch_times': {}
        }
