"""
Unit tests for aggregator module.
Tests parallel fetching, error handling, and deduplication.
"""

import unittest
from unittest.mock import Mock, patch
from aggregator import Aggregator
from sources.base_source import BaseSource


class MockSource(BaseSource):
    """Mock source for testing."""
    
    def __init__(self, posts_to_return=None, should_fail=False):
        self.posts_to_return = posts_to_return or []
        self.should_fail = should_fail
    
    def fetch_posts(self, keywords, limit=50, **kwargs):
        if self.should_fail:
            raise Exception("Mock source failure")
        return self.posts_to_return


class TestAggregator(unittest.TestCase):
    """Test suite for Aggregator class."""
    
    def setUp(self):
        """Initialize aggregator for testing."""
        self.aggregator = Aggregator(max_workers=3)
    
    def test_single_source_success(self):
        """Test fetching from a single source successfully."""
        mock_posts = [
            {"id": "1", "title": "Post 1", "url": "http://example.com/1", "source": "test"}
        ]
        source = MockSource(posts_to_return=mock_posts)
        
        result = self.aggregator.fetch_from_sources(
            [("test_source", source)],
            ["keyword"],
            limit_per_source=10
        )
        
        self.assertEqual(len(result['posts']), 1)
        self.assertEqual(result['posts'][0]['title'], "Post 1")
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['stats']['successful_fetches'], 1)
    
    def test_multiple_sources_parallel(self):
        """Test parallel fetching from multiple sources."""
        posts1 = [{"id": "1", "title": "Post 1", "url": "http://example.com/1", "source": "source1"}]
        posts2 = [{"id": "2", "title": "Post 2", "url": "http://example.com/2", "source": "source2"}]
        
        source1 = MockSource(posts_to_return=posts1)
        source2 = MockSource(posts_to_return=posts2)
        
        result = self.aggregator.fetch_from_sources(
            [("source1", source1), ("source2", source2)],
            ["keyword"],
            limit_per_source=10
        )
        
        self.assertEqual(len(result['posts']), 2)
        self.assertEqual(result['stats']['successful_fetches'], 2)
        self.assertEqual(result['stats']['failed_fetches'], 0)
    
    def test_graceful_error_handling(self):
        """Test that one source failure doesn't block others."""
        good_posts = [{"id": "1", "title": "Good Post", "url": "http://example.com/1", "source": "good"}]
        
        good_source = MockSource(posts_to_return=good_posts)
        bad_source = MockSource(should_fail=True)
        
        result = self.aggregator.fetch_from_sources(
            [("good_source", good_source), ("bad_source", bad_source)],
            ["keyword"],
            limit_per_source=10
        )
        
        self.assertEqual(len(result['posts']), 1)
        self.assertEqual(result['posts'][0]['title'], "Good Post")
        self.assertIn("bad_source", result['errors'])
        self.assertEqual(result['stats']['successful_fetches'], 1)
        self.assertEqual(result['stats']['failed_fetches'], 1)
    
    def test_post_validation(self):
        """Test that invalid posts are filtered out."""
        posts = [
            {"id": "1", "title": "Valid Post", "url": "http://example.com/1", "source": "test"},
            {"id": "2", "title": "Invalid Post"},  # Missing url and source
            {"title": "No ID", "url": "http://example.com/3", "source": "test"},  # Missing id
        ]
        
        source = MockSource(posts_to_return=posts)
        
        result = self.aggregator.fetch_from_sources(
            [("test_source", source)],
            ["keyword"],
            limit_per_source=10
        )
        
        # Only valid post should be returned
        self.assertEqual(len(result['posts']), 1)
        self.assertEqual(result['posts'][0]['id'], "1")
    
    def test_deduplication(self):
        """Test deduplication of posts with same ID."""
        posts = [
            {"id": "1", "title": "Post 1", "url": "http://example.com/1", "source": "test"},
            {"id": "2", "title": "Post 2", "url": "http://example.com/2", "source": "test"},
            {"id": "1", "title": "Duplicate Post 1", "url": "http://example.com/1", "source": "test"},
        ]
        
        deduplicated = self.aggregator.deduplicate_posts(posts)
        
        self.assertEqual(len(deduplicated), 2)
        self.assertEqual(deduplicated[0]['id'], "1")
        self.assertEqual(deduplicated[1]['id'], "2")
    
    def test_sort_posts(self):
        """Test sorting posts by score."""
        posts = [
            {"id": "1", "score": 5},
            {"id": "2", "score": 10},
            {"id": "3", "score": 3},
        ]
        
        sorted_posts = self.aggregator.sort_posts(posts, sort_by='score', reverse=True)
        
        self.assertEqual(sorted_posts[0]['score'], 10)
        self.assertEqual(sorted_posts[1]['score'], 5)
        self.assertEqual(sorted_posts[2]['score'], 3)
    
    def test_filter_posts(self):
        """Test filtering posts by criteria."""
        posts = [
            {"id": "1", "score": 5, "source": "hackernews"},
            {"id": "2", "score": 10, "source": "stackoverflow"},
            {"id": "3", "score": 3, "source": "hackernews"},
        ]
        
        # Filter by min score
        filtered = self.aggregator.filter_posts(posts, min_score=5)
        self.assertEqual(len(filtered), 2)
        
        # Filter by source
        filtered = self.aggregator.filter_posts(posts, sources=["hackernews"])
        self.assertEqual(len(filtered), 2)
        
        # Combined filters
        filtered = self.aggregator.filter_posts(posts, min_score=5, sources=["hackernews"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['id'], "1")
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        posts = [{"id": "1", "title": "Post 1", "url": "http://example.com/1", "source": "test"}]
        source = MockSource(posts_to_return=posts)
        
        self.aggregator.fetch_from_sources([("test", source)], ["keyword"], 10)
        
        stats = self.aggregator.get_stats()
        self.assertEqual(stats['total_fetches'], 1)
        self.assertEqual(stats['successful_fetches'], 1)
        self.assertEqual(stats['total_posts'], 1)
        self.assertEqual(stats['success_rate'], 1.0)
        self.assertIn('test', stats['fetch_times'])


if __name__ == '__main__':
    unittest.main()
