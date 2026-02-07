import json
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

CACHE_DIR = "cache"
DEFAULT_TTL = 86400  # 24 hours in seconds

class Cache:
    """
    Enhanced caching system with TTL, source-specific caching, and statistics.
    """
    
    def __init__(self, cache_dir: str = CACHE_DIR, default_ttl: int = DEFAULT_TTL):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.posts_cache_file = os.path.join(self.cache_dir, "posts_cache.json")
        self.analysis_cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
        self.source_cache_file = os.path.join(self.cache_dir, "source_cache.json")
        
        self.posts_cache = self._load_cache(self.posts_cache_file)
        self.analysis_cache = self._load_cache(self.analysis_cache_file)
        self.source_cache = self._load_cache(self.source_cache_file)
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'expirations': 0,
            'saves': 0
        }

    def _load_cache(self, filepath: str) -> Dict[str, Any]:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self, filepath: str, data: Dict[str, Any]):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _is_expired(self, cached_item: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Check if a cached item has expired."""
        if 'timestamp' not in cached_item:
            return True
        
        ttl = ttl or self.default_ttl
        age = time.time() - cached_item['timestamp']
        return age > ttl
    
    def _create_cache_entry(self, data: Any, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Create a cache entry with timestamp and TTL."""
        return {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl or self.default_ttl
        }

    # Post caching
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a post from cache if not expired."""
        if post_id in self.posts_cache:
            entry = self.posts_cache[post_id]
            if not self._is_expired(entry, entry.get('ttl')):
                self.stats['hits'] += 1
                return entry['data']
            else:
                # Remove expired entry
                del self.posts_cache[post_id]
                self._save_cache(self.posts_cache_file, self.posts_cache)
                self.stats['expirations'] += 1
        
        self.stats['misses'] += 1
        return None

    def save_post(self, post_id: str, post_data: Dict[str, Any], ttl: Optional[int] = None):
        """Save a post to cache with TTL."""
        self.posts_cache[post_id] = self._create_cache_entry(post_data, ttl)
        self._save_cache(self.posts_cache_file, self.posts_cache)
        self.stats['saves'] += 1

    # Analysis caching
    def get_analysis(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis from cache if not expired."""
        if post_id in self.analysis_cache:
            entry = self.analysis_cache[post_id]
            if not self._is_expired(entry, entry.get('ttl')):
                self.stats['hits'] += 1
                return entry['data']
            else:
                del self.analysis_cache[post_id]
                self._save_cache(self.analysis_cache_file, self.analysis_cache)
                self.stats['expirations'] += 1
        
        self.stats['misses'] += 1
        return None

    def save_analysis(self, post_id: str, analysis_data: Dict[str, Any], ttl: Optional[int] = None):
        """Save analysis to cache with TTL."""
        self.analysis_cache[post_id] = self._create_cache_entry(analysis_data, ttl)
        self._save_cache(self.analysis_cache_file, self.analysis_cache)
        self.stats['saves'] += 1
    
    # Source-specific caching
    def get_source_cache(self, source: str, cache_key: str) -> Optional[Any]:
        """
        Get cached data for a specific source.
        
        Args:
            source: Source name (e.g., 'hackernews', 'stackoverflow')
            cache_key: Unique key for this cache entry (e.g., query hash)
        """
        source_key = f"{source}:{cache_key}"
        
        if source_key in self.source_cache:
            entry = self.source_cache[source_key]
            if not self._is_expired(entry, entry.get('ttl')):
                self.stats['hits'] += 1
                return entry['data']
            else:
                del self.source_cache[source_key]
                self._save_cache(self.source_cache_file, self.source_cache)
                self.stats['expirations'] += 1
        
        self.stats['misses'] += 1
        return None
    
    def save_source_cache(
        self,
        source: str,
        cache_key: str,
        data: Any,
        ttl: Optional[int] = None
    ):
        """
        Save data to source-specific cache.
        
        Args:
            source: Source name
            cache_key: Unique key for this cache entry
            data: Data to cache
            ttl: Time to live in seconds (optional)
        """
        source_key = f"{source}:{cache_key}"
        self.source_cache[source_key] = self._create_cache_entry(data, ttl)
        self._save_cache(self.source_cache_file, self.source_cache)
        self.stats['saves'] += 1
    
    def clear_source_cache(self, source: Optional[str] = None):
        """
        Clear cache for a specific source or all sources.
        
        Args:
            source: Source name to clear, or None to clear all
        """
        if source:
            # Clear only entries for this source
            keys_to_delete = [k for k in self.source_cache.keys() if k.startswith(f"{source}:")]
            for key in keys_to_delete:
                del self.source_cache[key]
        else:
            # Clear all source cache
            self.source_cache = {}
        
        self._save_cache(self.source_cache_file, self.source_cache)
    
    # Cache management
    def clear_cache(self):
        """Clear all caches."""
        if os.path.exists(self.posts_cache_file):
            os.remove(self.posts_cache_file)
        if os.path.exists(self.analysis_cache_file):
            os.remove(self.analysis_cache_file)
        if os.path.exists(self.source_cache_file):
            os.remove(self.source_cache_file)
        
        self.posts_cache = {}
        self.analysis_cache = {}
        self.source_cache = {}
        self.reset_stats()
    
    def clear_expired(self):
        """Remove all expired entries from all caches."""
        expired_count = 0
        
        # Clear expired posts
        for post_id in list(self.posts_cache.keys()):
            if self._is_expired(self.posts_cache[post_id], self.posts_cache[post_id].get('ttl')):
                del self.posts_cache[post_id]
                expired_count += 1
        
        # Clear expired analyses
        for post_id in list(self.analysis_cache.keys()):
            if self._is_expired(self.analysis_cache[post_id], self.analysis_cache[post_id].get('ttl')):
                del self.analysis_cache[post_id]
                expired_count += 1
        
        # Clear expired source cache
        for key in list(self.source_cache.keys()):
            if self._is_expired(self.source_cache[key], self.source_cache[key].get('ttl')):
                del self.source_cache[key]
                expired_count += 1
        
        # Save all caches
        self._save_cache(self.posts_cache_file, self.posts_cache)
        self._save_cache(self.analysis_cache_file, self.analysis_cache)
        self._save_cache(self.source_cache_file, self.source_cache)
        
        return expired_count
    
    # Statistics
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate * 100, 2),
            'expirations': self.stats['expirations'],
            'saves': self.stats['saves'],
            'total_entries': len(self.posts_cache) + len(self.analysis_cache) + len(self.source_cache),
            'posts_cached': len(self.posts_cache),
            'analyses_cached': len(self.analysis_cache),
            'source_entries': len(self.source_cache)
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'expirations': 0,
            'saves': 0
        }
