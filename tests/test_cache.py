"""
Unit tests for cache module.
Tests TTL expiration, source-specific caching, and statistics.
"""

import unittest
import time
import os
import tempfile
import shutil
from cache import Cache


class TestCache(unittest.TestCase):
    """Test suite for Cache class."""
    
    def setUp(self):
        """Create temporary cache directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.cache = Cache(cache_dir=self.test_dir, default_ttl=2)  # 2 second TTL for testing
    
    def tearDown(self):
        """Clean up temporary cache directory."""
        shutil.rmtree(self.test_dir)
    
    def test_post_cache_save_and_get(self):
        """Test saving and retrieving posts from cache."""
        post_data = {"title": "Test Post", "content": "Test content"}
        self.cache.save_post("post_1", post_data)
        
        retrieved = self.cache.get_post("post_1")
        self.assertEqual(retrieved, post_data)
        self.assertEqual(self.cache.stats['saves'], 1)
        self.assertEqual(self.cache.stats['hits'], 1)
    
    def test_post_cache_miss(self):
        """Test cache miss for non-existent post."""
        retrieved = self.cache.get_post("non_existent")
        self.assertIsNone(retrieved)
        self.assertEqual(self.cache.stats['misses'], 1)
    
    def test_ttl_expiration(self):
        """Test that cached items expire after TTL."""
        post_data = {"title": "Test Post"}
        self.cache.save_post("post_1", post_data, ttl=1)  # 1 second TTL
        
        # Should be available immediately
        retrieved = self.cache.get_post("post_1")
        self.assertEqual(retrieved, post_data)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        retrieved = self.cache.get_post("post_1")
        self.assertIsNone(retrieved)
        self.assertEqual(self.cache.stats['expirations'], 1)
    
    def test_analysis_cache(self):
        """Test analysis caching."""
        analysis_data = {"score": 9, "is_pain_point": True}
        self.cache.save_analysis("post_1", analysis_data)
        
        retrieved = self.cache.get_analysis("post_1")
        self.assertEqual(retrieved, analysis_data)
    
    def test_source_specific_cache(self):
        """Test source-specific caching."""
        data = {"results": [1, 2, 3]}
        self.cache.save_source_cache("hackernews", "query_hash_123", data)
        
        retrieved = self.cache.get_source_cache("hackernews", "query_hash_123")
        self.assertEqual(retrieved, data)
        
        # Different source should not retrieve same data
        retrieved = self.cache.get_source_cache("stackoverflow", "query_hash_123")
        self.assertIsNone(retrieved)
    
    def test_clear_source_cache(self):
        """Test clearing source-specific cache."""
        self.cache.save_source_cache("hackernews", "key1", {"data": 1})
        self.cache.save_source_cache("hackernews", "key2", {"data": 2})
        self.cache.save_source_cache("stackoverflow", "key1", {"data": 3})
        
        # Clear only hackernews
        self.cache.clear_source_cache("hackernews")
        
        self.assertIsNone(self.cache.get_source_cache("hackernews", "key1"))
        self.assertIsNone(self.cache.get_source_cache("hackernews", "key2"))
        self.assertIsNotNone(self.cache.get_source_cache("stackoverflow", "key1"))
    
    def test_clear_expired(self):
        """Test clearing expired entries."""
        self.cache.save_post("post_1", {"data": 1}, ttl=1)
        self.cache.save_post("post_2", {"data": 2}, ttl=10)
        
        time.sleep(1.5)
        
        expired_count = self.cache.clear_expired()
        self.assertEqual(expired_count, 1)
        
        self.assertIsNone(self.cache.get_post("post_1"))
        self.assertIsNotNone(self.cache.get_post("post_2"))
    
    def test_statistics(self):
        """Test cache statistics tracking."""
        self.cache.save_post("post_1", {"data": 1})
        self.cache.get_post("post_1")  # Hit
        self.cache.get_post("post_2")  # Miss
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['saves'], 1)
        self.assertAlmostEqual(stats['hit_rate'], 50.0, places=1)


if __name__ == '__main__':
    unittest.main()
