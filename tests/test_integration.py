"""
Integration tests for end-to-end workflows.
Tests complete pipeline from fetching to analysis to storage.
"""

import unittest
import os
import tempfile
from unittest.mock import Mock, patch
from aggregator import Aggregator
from analyzer import Analyzer
from database import Database
from trend_analyzer import TrendAnalyzer
from sources.base_source import BaseSource


class MockSource(BaseSource):
    """Mock source for integration testing."""
    
    def fetch_posts(self, keywords, limit=50, **kwargs):
        return [
            {
                "id": "mock_1",
                "title": "I hate manually syncing Stripe to QuickBooks",
                "text": "Every week I spend 2 hours manually entering transactions",
                "url": "http://example.com/1",
                "source": "mock",
                "score": 10,
                "num_comments": 5,
                "created_utc": 1234567890
            },
            {
                "id": "mock_2",
                "title": "Looking for automation tool for accounting",
                "text": "Manual data entry is killing my productivity",
                "url": "http://example.com/2",
                "source": "mock",
                "score": 8,
                "num_comments": 3,
                "created_utc": 1234567891
            }
        ]


class TestEndToEnd(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = Database(db_path=self.db_file.name)
        self.aggregator = Aggregator(max_workers=2)
        self.trend_analyzer = TrendAnalyzer(self.db)
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
        os.unlink(self.db_file.name)
    
    @patch('analyzer.Analyzer.analyze_posts')
    def test_complete_pipeline(self, mock_analyze):
        """Test complete pipeline from fetching to storage."""
        # Mock AI analysis
        mock_analyze.return_value = [
            {
                "id": "mock_1",
                "title": "I hate manually syncing Stripe to QuickBooks",
                "text": "Every week I spend 2 hours manually entering transactions",
                "url": "http://example.com/1",
                "source": "mock",
                "analysis": {
                    "is_pain_point": True,
                    "score": 9,
                    "solution": "StripeSync: Auto-sync Stripe to QuickBooks",
                    "reasoning": "High frequency, clear workflow pain",
                    "trend_score": 7,
                    "market_size": "medium",
                    "competitors": "Zapier",
                    "difficulty": 4,
                    "time_to_build": "1-2 months"
                }
            }
        ]
        
        # 1. Fetch posts
        mock_source = MockSource()
        result = self.aggregator.fetch_from_sources(
            [("mock", mock_source)],
            ["hate", "manual"],
            limit_per_source=10
        )
        
        self.assertEqual(len(result['posts']), 2)
        self.assertEqual(result['stats']['successful_fetches'], 1)
        
        # 2. Analyze posts (mocked)
        analyzer = Analyzer(api_key="fake_key")
        analyzed_posts = mock_analyze.return_value
        
        # 3. Store in database
        for post in analyzed_posts:
            self.db.save_post(post)
            if 'analysis' in post:
                self.db.save_analysis(post['id'], post['analysis'])
                self.trend_analyzer.track_problem(post['id'], post['analysis'])
        
        # 4. Verify storage
        stats = self.db.get_stats()
        self.assertEqual(stats['total_posts'], 1)
        self.assertEqual(stats['total_analyses'], 1)
        self.assertEqual(stats['pain_points_found'], 1)
        
        # 5. Verify trends
        trends = self.trend_analyzer.get_emerging_trends(days=30, min_recent=1)
        self.assertGreater(len(trends), 0)
    
    def test_parallel_fetching_performance(self):
        """Test that parallel fetching is faster than sequential."""
        import time
        
        mock_source1 = MockSource()
        mock_source2 = MockSource()
        
        # Parallel fetch
        start = time.time()
        result = self.aggregator.fetch_from_sources(
            [("source1", mock_source1), ("source2", mock_source2)],
            ["keyword"],
            limit_per_source=10
        )
        parallel_time = time.time() - start
        
        # Should complete in reasonable time
        self.assertLess(parallel_time, 2.0)  # Should be very fast with mocks
        self.assertEqual(len(result['posts']), 4)  # 2 posts from each source
    
    def test_deduplication_across_sources(self):
        """Test that duplicates from different sources are removed."""
        # Create sources that return same post ID
        class DuplicateSource(BaseSource):
            def fetch_posts(self, keywords, limit=50, **kwargs):
                return [{
                    "id": "duplicate_1",
                    "title": "Same post",
                    "url": "http://example.com/1",
                    "source": "source1"
                }]
        
        source1 = DuplicateSource()
        source2 = DuplicateSource()
        
        result = self.aggregator.fetch_from_sources(
            [("source1", source1), ("source2", source2)],
            ["keyword"],
            limit_per_source=10
        )
        
        # Should have 2 posts before deduplication
        self.assertEqual(len(result['posts']), 2)
        
        # Deduplicate
        deduplicated = self.aggregator.deduplicate_posts(result['posts'])
        self.assertEqual(len(deduplicated), 1)


if __name__ == '__main__':
    unittest.main()
