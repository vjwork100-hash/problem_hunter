import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class Database:
    """SQLite database for storing posts and analysis results with timestamps."""
    
    def __init__(self, db_path: str = "problem_hunter.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema."""
        cursor = self.conn.cursor()
        
        # Posts table - stores raw posts from all sources
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT,
                url TEXT,
                created_utc INTEGER,
                score INTEGER DEFAULT 0,
                num_comments INTEGER DEFAULT 0,
                metadata TEXT,  -- JSON for source-specific fields
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analysis results table - stores AI analysis with timestamps
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_pain_point BOOLEAN,
                score INTEGER,
                solution TEXT,
                reasoning TEXT,
                trend_score INTEGER,
                market_size TEXT,
                competitors TEXT,
                difficulty INTEGER,
                time_to_build TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        """)
        
        # Problem trends table - aggregated view of recurring problems
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problem_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_hash TEXT UNIQUE,  -- Hash of normalized problem description
                problem_summary TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                avg_score REAL,
                sources TEXT,  -- JSON array of sources
                sample_post_ids TEXT  -- JSON array of sample post IDs
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_utc)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_post ON analysis_results(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analyzed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_hash ON problem_trends(problem_hash)")
        
        self.conn.commit()
    
    def save_post(self, post: Dict[str, Any]) -> bool:
        """Save or update a post in the database."""
        cursor = self.conn.cursor()
        
        # Extract metadata (source-specific fields)
        metadata = {k: v for k, v in post.items() 
                   if k not in ['id', 'source', 'title', 'text', 'url', 'created_utc', 'score', 'num_comments']}
        
        try:
            cursor.execute("""
                INSERT INTO posts (id, source, title, text, url, created_utc, score, num_comments, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_seen_at = CURRENT_TIMESTAMP,
                    score = excluded.score,
                    num_comments = excluded.num_comments
            """, (
                post['id'],
                post.get('source', 'unknown'),
                post['title'],
                post.get('text', ''),
                post['url'],
                post.get('created_utc', 0),
                post.get('score', 0),
                post.get('num_comments', 0),
                json.dumps(metadata)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving post {post['id']}: {e}")
            return False
    
    def save_analysis(self, post_id: str, analysis: Dict[str, Any]) -> bool:
        """Save analysis result for a post."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO analysis_results (
                    post_id, is_pain_point, score, solution, reasoning,
                    trend_score, market_size, competitors, difficulty, time_to_build
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post_id,
                analysis.get('is_pain_point', False),
                analysis.get('score', 0),
                analysis.get('solution', ''),
                analysis.get('reasoning', ''),
                analysis.get('trend_score', 0),
                analysis.get('market_size', 'unknown'),
                analysis.get('competitors', ''),
                analysis.get('difficulty', 0),
                analysis.get('time_to_build', 'N/A')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving analysis for {post_id}: {e}")
            return False
    
    def get_recent_posts(self, days: int = 30, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get posts from the last N days."""
        cursor = self.conn.cursor()
        
        query = """
            SELECT * FROM posts 
            WHERE datetime(first_seen_at) >= datetime('now', '-' || ? || ' days')
        """
        params = [days]
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        query += " ORDER BY first_seen_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_trending_problems(self, days: int = 7, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """Get problems that are trending (appearing frequently in recent period)."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                pt.*,
                COUNT(ar.id) as recent_mentions
            FROM problem_trends pt
            LEFT JOIN analysis_results ar ON pt.problem_hash IN (
                SELECT problem_hash FROM problem_trends 
                WHERE datetime(ar.analyzed_at) >= datetime('now', '-' || ? || ' days')
            )
            WHERE pt.occurrence_count >= ?
            GROUP BY pt.id
            ORDER BY recent_mentions DESC, pt.avg_score DESC
            LIMIT 50
        """, (days, min_occurrences))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_analysis_history(self, post_id: str) -> List[Dict[str, Any]]:
        """Get all analysis results for a post (useful for tracking score changes)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM analysis_results 
            WHERE post_id = ? 
            ORDER BY analyzed_at DESC
        """, (post_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total posts
        cursor.execute("SELECT COUNT(*) as count FROM posts")
        stats['total_posts'] = cursor.fetchone()['count']
        
        # Posts by source
        cursor.execute("SELECT source, COUNT(*) as count FROM posts GROUP BY source")
        stats['posts_by_source'] = {row['source']: row['count'] for row in cursor.fetchall()}
        
        # Total analyses
        cursor.execute("SELECT COUNT(*) as count FROM analysis_results")
        stats['total_analyses'] = cursor.fetchone()['count']
        
        # Pain points found
        cursor.execute("SELECT COUNT(*) as count FROM analysis_results WHERE is_pain_point = 1")
        stats['pain_points_found'] = cursor.fetchone()['count']
        
        # Average score
        cursor.execute("SELECT AVG(score) as avg_score FROM analysis_results WHERE is_pain_point = 1")
        stats['avg_pain_score'] = round(cursor.fetchone()['avg_score'] or 0, 2)
        
        return stats
    
    def close(self):
        """Close database connection."""
        self.conn.close()
