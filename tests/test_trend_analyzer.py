"""
Unit tests for trend_analyzer module.
Tests hash-based similarity, emerging/declining trend detection.
"""

import unittest
import os
import tempfile
from database import Database
from trend_analyzer import TrendAnalyzer


class TestTrendAnalyzer(unittest.TestCase):
    """Test suite for TrendAnalyzer class."""
    
    def setUp(self):
        """Create temporary database and trend analyzer."""
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
        text1 = "I hate manually syncing data between systems"
        text2 = "I HATE manually SYNCING data between SYSTEMS"
        
        normalized1 = self.analyzer._normalize_problem(text1)
        normalized2 = self.analyzer._normalize_problem(text2)
        
        # Should be case-insensitive and remove common words
        self.assertEqual(normalized1, normalized2)
    
    def test_problem_hash(self):
        """Test problem hash generation."""
        solution = "Auto-sync tool"
        reasoning = "Manual syncing is tedious"
        
        hash1 = self.analyzer._get_problem_hash(solution, reasoning)
        hash2 = self.analyzer._get_problem_hash(solution, reasoning)
        
        # Same input should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different input should produce different hash
        hash3 = self.analyzer._get_problem_hash("Different solution", reasoning)
        self.assertNotEqual(hash1, hash3)
    
    def test_track_problem(self):
        """Test tracking a problem."""
        post_id = "test_post_1"
        analysis = {
            "solution": "Auto-sync tool for Stripe and QuickBooks",
            "reasoning": "Manual syncing is time-consuming",
            "score": 9,
            "is_pain_point": True
        }
        
        self.analyzer.track_problem(post_id, analysis)
        
        # Verify problem was tracked
        trends = self.analyzer.get_emerging_trends(days=30, min_recent=1)
        self.assertGreater(len(trends), 0)
    
    def test_emerging_trends(self):
        """Test emerging trend detection."""
        # Create multiple posts with similar problems
        for i in range(5):
            post = {
                "id": f"post_{i}",
                "title": f"Post {i}",
                "url": f"http://example.com/{i}",
                "source": "test"
            }
            self.db.save_post(post)
            
            analysis = {
                "solution": "Auto-sync tool for accounting",
                "reasoning": "Manual data entry is tedious",
                "score": 8,
                "is_pain_point": True
            }
            self.db.save_analysis(f"post_{i}", analysis)
            self.analyzer.track_problem(f"post_{i}", analysis)
        
        # Get emerging trends
        trends = self.analyzer.get_emerging_trends(days=30, min_recent=3)
        
        self.assertGreater(len(trends), 0)
        self.assertGreaterEqual(trends[0]['occurrence_count'], 3)
    
    def test_no_trends_with_low_threshold(self):
        """Test that no trends are returned with high threshold."""
        post = {
            "id": "post_1",
            "title": "Post 1",
            "url": "http://example.com/1",
            "source": "test"
        }
        self.db.save_post(post)
        
        analysis = {
            "solution": "Test solution",
            "reasoning": "Test reasoning",
            "score": 8,
            "is_pain_point": True
        }
        self.db.save_analysis("post_1", analysis)
        self.analyzer.track_problem("post_1", analysis)
        
        # Require at least 10 occurrences
        trends = self.analyzer.get_emerging_trends(days=30, min_recent=10)
        
        self.assertEqual(len(trends), 0)


if __name__ == '__main__':
    unittest.main()
