import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from database import Database

class TrendAnalyzer:
    """Analyzes problem trends over time to identify emerging vs. declining patterns."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def _normalize_problem(self, solution: str, reasoning: str) -> str:
        """
        Normalize a problem description for similarity matching.
        Combines solution and reasoning to create a problem signature.
        """
        # Combine and lowercase
        text = f"{solution} {reasoning}".lower()
        
        # Remove common words that don't affect problem identity
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in text.split() if w not in stop_words and len(w) > 2]
        
        # Sort words for consistent hashing
        normalized = ' '.join(sorted(words[:20]))  # Limit to first 20 significant words
        return normalized
    
    def _hash_problem(self, normalized: str) -> str:
        """Create a hash for a normalized problem description."""
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def track_problem(self, post_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Track a problem in the trends table.
        Groups similar problems together and tracks frequency.
        """
        if not analysis.get('is_pain_point'):
            return False
        
        solution = analysis.get('solution', '')
        reasoning = analysis.get('reasoning', '')
        
        if not solution:
            return False
        
        # Normalize and hash
        normalized = self._normalize_problem(solution, reasoning)
        problem_hash = self._hash_problem(normalized)
        
        cursor = self.db.conn.cursor()
        
        # Check if this problem already exists
        cursor.execute("""
            SELECT * FROM problem_trends WHERE problem_hash = ?
        """, (problem_hash,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing trend
            sources = set(eval(existing['sources']))  # Convert JSON string to set
            sample_ids = eval(existing['sample_post_ids'])
            
            # Get post source
            cursor.execute("SELECT source FROM posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            if post:
                sources.add(post['source'])
            
            # Add to samples (keep max 10)
            if post_id not in sample_ids:
                sample_ids.append(post_id)
                sample_ids = sample_ids[-10:]  # Keep last 10
            
            cursor.execute("""
                UPDATE problem_trends SET
                    last_seen = CURRENT_TIMESTAMP,
                    occurrence_count = occurrence_count + 1,
                    avg_score = (avg_score * occurrence_count + ?) / (occurrence_count + 1),
                    sources = ?,
                    sample_post_ids = ?
                WHERE problem_hash = ?
            """, (
                analysis.get('score', 0),
                str(list(sources)),
                str(sample_ids),
                problem_hash
            ))
        else:
            # Create new trend
            cursor.execute("SELECT source FROM posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            source = post['source'] if post else 'unknown'
            
            cursor.execute("""
                INSERT INTO problem_trends (
                    problem_hash, problem_summary, first_seen, last_seen,
                    occurrence_count, avg_score, sources, sample_post_ids
                ) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, ?, ?, ?)
            """, (
                problem_hash,
                solution[:200],  # Store first 200 chars as summary
                analysis.get('score', 0),
                str([source]),
                str([post_id])
            ))
        
        self.db.conn.commit()
        return True
    
    def get_emerging_trends(self, days: int = 30, min_recent: int = 3) -> List[Dict[str, Any]]:
        """
        Identify emerging trends (problems appearing frequently in recent period).
        
        Args:
            days: Look back period
            min_recent: Minimum occurrences in recent period to be considered emerging
        """
        cursor = self.db.conn.cursor()
        
        # Find problems with recent activity
        cursor.execute("""
            SELECT 
                pt.*,
                COUNT(CASE WHEN datetime(ar.analyzed_at) >= datetime('now', '-' || ? || ' days') 
                      THEN 1 END) as recent_count,
                COUNT(ar.id) as total_count
            FROM problem_trends pt
            JOIN analysis_results ar ON ar.post_id IN (
                SELECT value FROM json_each(pt.sample_post_ids)
            )
            GROUP BY pt.id
            HAVING recent_count >= ?
            ORDER BY recent_count DESC, pt.avg_score DESC
            LIMIT 20
        """, (days, min_recent))
        
        results = []
        for row in cursor.fetchall():
            trend = dict(row)
            trend['trend_velocity'] = self._calculate_velocity(trend, days)
            trend['status'] = 'emerging' if trend['trend_velocity'] > 0.5 else 'steady'
            results.append(trend)
        
        return results
    
    def get_declining_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Identify declining trends (problems that were common but are now rare).
        """
        cursor = self.db.conn.cursor()
        
        # Find problems with past activity but little recent activity
        cursor.execute("""
            SELECT 
                pt.*,
                COUNT(CASE WHEN datetime(ar.analyzed_at) >= datetime('now', '-' || ? || ' days') 
                      THEN 1 END) as recent_count,
                COUNT(CASE WHEN datetime(ar.analyzed_at) < datetime('now', '-' || ? || ' days') 
                      THEN 1 END) as past_count
            FROM problem_trends pt
            JOIN analysis_results ar ON ar.post_id IN (
                SELECT value FROM json_each(pt.sample_post_ids)
            )
            WHERE pt.occurrence_count >= 3
            GROUP BY pt.id
            HAVING past_count > recent_count * 2  -- Past activity significantly higher
            ORDER BY past_count DESC
            LIMIT 20
        """, (days, days))
        
        results = []
        for row in cursor.fetchall():
            trend = dict(row)
            trend['status'] = 'declining'
            results.append(trend)
        
        return results
    
    def _calculate_velocity(self, trend: Dict[str, Any], days: int) -> float:
        """
        Calculate trend velocity (rate of growth).
        Returns value between 0 (no growth) and 1 (rapid growth).
        """
        # Simple heuristic: recent_count / total_count
        # Higher ratio = more recent activity = emerging
        recent = trend.get('recent_count', 0)
        total = trend.get('total_count', 1)
        
        velocity = recent / total if total > 0 else 0
        return min(velocity, 1.0)
    
    def get_frequency_stats(self, problem_hash: str, days: int = 90) -> Dict[str, Any]:
        """
        Get detailed frequency statistics for a specific problem.
        Returns daily/weekly/monthly breakdown.
        """
        cursor = self.db.conn.cursor()
        
        # Get all mentions of this problem
        cursor.execute("""
            SELECT ar.analyzed_at
            FROM problem_trends pt
            JOIN analysis_results ar ON ar.post_id IN (
                SELECT value FROM json_each(pt.sample_post_ids)
            )
            WHERE pt.problem_hash = ?
            AND datetime(ar.analyzed_at) >= datetime('now', '-' || ? || ' days')
            ORDER BY ar.analyzed_at
        """, (problem_hash, days))
        
        dates = [row['analyzed_at'] for row in cursor.fetchall()]
        
        if not dates:
            return {'daily': {}, 'weekly': {}, 'monthly': {}}
        
        # Group by day, week, month
        daily = defaultdict(int)
        weekly = defaultdict(int)
        monthly = defaultdict(int)
        
        for date_str in dates:
            dt = datetime.fromisoformat(date_str)
            daily[dt.date().isoformat()] += 1
            weekly[dt.isocalendar()[:2]] += 1  # (year, week)
            monthly[(dt.year, dt.month)] += 1
        
        return {
            'daily': dict(daily),
            'weekly': {f"{y}-W{w:02d}": count for (y, w), count in weekly.items()},
            'monthly': {f"{y}-{m:02d}": count for (y, m), count in monthly.items()}
        }
