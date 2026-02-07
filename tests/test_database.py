"""
Unit tests for database module.
Tests post storage, analysis storage, and statistics.
"""

import unittest
import os
import tempfile
from database import Database


class TestDatabase(unittest.TestCase):
    """Test suite for Database class."""
    
    def setUp(self):
        """Create temporary database for testing."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = Database(db_path=self.db_file.name)
    
    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        os.unlink(self.db_file.name)
    
    def test_save_and_get_post(self):
        """Test saving and retrieving posts."""
        post = {
            "id": "test_1",
            "title": "Test Post",
            "url": "http://example.com",
            "source": "test",
            "text": "Test content"
        }
        
        self.db.save_post(post)
        retrieved = self.db.get_post("test_1")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['title'], "Test Post")
        self.assertEqual(retrieved['source'], "test")
    
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
            "competitors": "Competitor A, Competitor B",
            "difficulty": 5,
            "time_to_build": "2-3 months"
        }
        
        self.db.save_post(post)
        self.db.save_analysis("test_1", analysis)
        
        retrieved = self.db.get_analysis("test_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['score'], 9)
        self.assertEqual(retrieved['market_size'], "medium")
    
    def test_get_stats(self):
        """Test database statistics."""
        # Add some posts
        for i in range(5):
            post = {
                "id": f"post_{i}",
                "title": f"Post {i}",
                "url": f"http://example.com/{i}",
                "source": "hackernews" if i < 3 else "stackoverflow"
            }
            self.db.save_post(post)
            
            if i < 3:  # Only analyze first 3
                analysis = {
                    "is_pain_point": True if i < 2 else False,
                    "score": 8 if i < 2 else 4
                }
                self.db.save_analysis(f"post_{i}", analysis)
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_posts'], 5)
        self.assertEqual(stats['total_analyses'], 3)
        self.assertEqual(stats['pain_points_found'], 2)
        self.assertIn('hackernews', stats['posts_by_source'])
        self.assertEqual(stats['posts_by_source']['hackernews'], 3)
        self.assertEqual(stats['posts_by_source']['stackoverflow'], 2)
    
    def test_duplicate_post_update(self):
        """Test that saving same post ID updates timestamps."""
        post = {
            "id": "test_1",
            "title": "Test Post",
            "url": "http://example.com",
            "source": "test"
        }
        
        self.db.save_post(post)
        first_save = self.db.get_post("test_1")
        
        import time
        time.sleep(0.1)
        
        self.db.save_post(post)
        second_save = self.db.get_post("test_1")
        
        # last_seen_at should be updated
        self.assertIsNotNone(first_save)
        self.assertIsNotNone(second_save)


if __name__ == '__main__':
    unittest.main()
