"""
Simplified working tests for Problem Hunter.
Tests core functionality without mocking complex dependencies.
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
        self.cache = Cache(cache_dir=self.test_dir, default_ttl=2)
    
    def tearDown(self):
        """Clean up temporary cache directory."""
        shutil.rmtree(self.test_dir)
    
    def test_post_cache_save_and_get(self):
        """Test saving and retrieving posts from cache."""
        post_data = {"title": "Test Post", "content": "Test content"}
        self.cache.save_post("post_1", post_data)
        
        retrieved = self.cache.get_post("post_1")
        self.assertEqual(retrieved, post_data)
    
    def test_ttl_expiration(self):
        """Test that cached items expire after TTL."""
        post_data = {"title": "Test Post"}
        self.cache.save_post("post_1", post_data, ttl=1)
        
        # Should be available immediately
        retrieved = self.cache.get_post("post_1")
        self.assertEqual(retrieved, post_data)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        retrieved = self.cache.get_post("post_1")
        self.assertIsNone(retrieved)
    
    def test_source_specific_cache(self):
        """Test source-specific caching."""
        data = {"results": [1, 2, 3]}
        self.cache.save_source_cache("hackernews", "query_hash_123", data)
        
        retrieved = self.cache.get_source_cache("hackernews", "query_hash_123")
        self.assertEqual(retrieved, data)
        
        # Different source should not retrieve same data
        retrieved = self.cache.get_source_cache("stackoverflow", "query_hash_123")
        self.assertIsNone(retrieved)


class TestAggregator(unittest.TestCase):
    """Test suite for Aggregator class."""
    
    def test_deduplication(self):
        """Test deduplication of posts with same ID."""
        from aggregator import Aggregator
        
        aggregator = Aggregator()
        posts = [
            {"id": "1", "title": "Post 1"},
            {"id": "2", "title": "Post 2"},
            {"id": "1", "title": "Duplicate Post 1"},
        ]
        
        deduplicated = aggregator.deduplicate_posts(posts)
        
        self.assertEqual(len(deduplicated), 2)
        self.assertEqual(deduplicated[0]['id'], "1")
        self.assertEqual(deduplicated[1]['id'], "2")
    
    def test_sort_posts(self):
        """Test sorting posts by score."""
        from aggregator import Aggregator
        
        aggregator = Aggregator()
        posts = [
            {"id": "1", "score": 5},
            {"id": "2", "score": 10},
            {"id": "3", "score": 3},
        ]
        
        sorted_posts = aggregator.sort_posts(posts, sort_by='score', reverse=True)
        
        self.assertEqual(sorted_posts[0]['score'], 10)
        self.assertEqual(sorted_posts[1]['score'], 5)
        self.assertEqual(sorted_posts[2]['score'], 3)
    
    def test_filter_posts(self):
        """Test filtering posts by criteria."""
        from aggregator import Aggregator
        
        aggregator = Aggregator()
        posts = [
            {"id": "1", "score": 5, "source": "hackernews"},
            {"id": "2", "score": 10, "source": "stackoverflow"},
            {"id": "3", "score": 3, "source": "hackernews"},
        ]
        
        # Filter by min score
        filtered = aggregator.filter_posts(posts, min_score=5)
        self.assertEqual(len(filtered), 2)
        
        # Filter by source
        filtered = aggregator.filter_posts(posts, sources=["hackernews"])
        self.assertEqual(len(filtered), 2)


class TestDatabase(unittest.TestCase):
    """Test suite for Database class."""
    
    def setUp(self):
        """Create temporary database for testing."""
        from database import Database
        
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = Database(db_path=self.db_file.name)
    
    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        os.unlink(self.db_file.name)
    
    def test_save_post(self):
        """Test saving posts."""
        post = {
            "id": "test_1",
            "title": "Test Post",
            "url": "http://example.com",
            "source": "test",
            "text": "Test content"
        }
        
        result = self.db.save_post(post)
        self.assertTrue(result)
    
    def test_save_analysis(self):
        """Test saving analysis results."""
        post = {
            "id": "test_1",
            "title": "Test Post",
            "url": "http://example.com",
            "source": "test"
        }
        
        analysis = {
            "is_pain_point": True,
            "score": 9,
            "solution": "Test solution",
            "reasoning": "Test reasoning",
            "trend_score": 7,
            "market_size": "medium",
            "competitors": "Competitor A",
            "difficulty": 5,
            "time_to_build": "2-3 months"
        }
        
        self.db.save_post(post)
        result = self.db.save_analysis("test_1", analysis)
        self.assertTrue(result)
    
    def test_get_stats(self):
        """Test database statistics."""
        # Add some posts
        for i in range(3):
            post = {
                "id": f"post_{i}",
                "title": f"Post {i}",
                "url": f"http://example.com/{i}",
                "source": "hackernews"
            }
            self.db.save_post(post)
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_posts'], 3)
        self.assertIn('hackernews', stats['posts_by_source'])


class TestTrendAnalyzer(unittest.TestCase):
    """Test suite for TrendAnalyzer class."""
    
    def setUp(self):
        """Create temporary database and trend analyzer."""
        from database import Database
        from trend_analyzer import TrendAnalyzer
        
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = Database(db_path=self.db_file.name)
        self.analyzer = TrendAnalyzer(self.db)
    
    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        os.unlink(self.db_file.name)
    
    def test_normalize_problem(self):
        """Test problem text normalization."""
        solution = "Auto-sync tool"
        reasoning = "Manual syncing is tedious"
        
        normalized = self.analyzer._normalize_problem(solution, reasoning)
        
        # Should return a normalized string
        self.assertIsInstance(normalized, str)
        self.assertGreater(len(normalized), 0)
    
    def test_track_problem(self):
        """Test tracking a problem."""
        post = {
            "id": "test_post_1",
            "title": "Test Post",
            "url": "http://example.com",
            "source": "test"
        }
        self.db.save_post(post)
        
        analysis = {
            "solution": "Auto-sync tool for Stripe and QuickBooks",
            "reasoning": "Manual syncing is time-consuming",
            "score": 9,
            "is_pain_point": True
        }
        self.db.save_analysis("test_post_1", analysis)
        
        result = self.analyzer.track_problem("test_post_1", analysis)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
