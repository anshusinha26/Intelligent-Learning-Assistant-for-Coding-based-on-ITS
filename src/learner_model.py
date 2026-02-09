"""
Learner Modeling Module
Tracks user mastery, identifies weakness patterns, and computes learning metrics
"""

from typing import List, Dict
from datetime import datetime
from src.database import Database

class LearnerModel:
    def __init__(self, db: Database):
        self.db = db
    
    def record_attempt(self, user_id: int, problem_id: str, verdict: str, 
                      time_taken: int = None, error_type: str = None) -> int:
        """Record a practice attempt"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, problem_id, verdict, time_taken, error_type))
        
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update learner metrics after recording attempt
        self.update_learner_metrics(user_id)
        
        return attempt_id
    
    def update_learner_metrics(self, user_id: int):
        """Recalculate mastery scores and error frequencies for a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all attempts with problem metadata
        cursor.execute("""
            SELECT a.problem_id, a.verdict, a.error_type, 
                   p.topic, p.pattern
            FROM attempts a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.user_id = ?
        """, (user_id,))
        
        attempts = cursor.fetchall()
        
        # Calculate metrics by topic and pattern
        topic_stats = {}
        pattern_stats = {}
        
        for attempt in attempts:
            topic = attempt['topic']
            pattern = attempt['pattern']
            is_success = attempt['verdict'] == 'Accepted'
            has_error = attempt['error_type'] is not None
            
            # Track topic stats
            if topic not in topic_stats:
                topic_stats[topic] = {'attempts': 0, 'successes': 0, 'errors': 0}
            topic_stats[topic]['attempts'] += 1
            if is_success:
                topic_stats[topic]['successes'] += 1
            if has_error:
                topic_stats[topic]['errors'] += 1
            
            # Track pattern stats
            if pattern:
                if pattern not in pattern_stats:
                    pattern_stats[pattern] = {'attempts': 0, 'successes': 0, 'errors': 0}
                pattern_stats[pattern]['attempts'] += 1
                if is_success:
                    pattern_stats[pattern]['successes'] += 1
                if has_error:
                    pattern_stats[pattern]['errors'] += 1
        
        # Delete old metrics
        cursor.execute("DELETE FROM learner_metrics WHERE user_id = ?", (user_id,))
        
        # Insert updated topic metrics
        for topic, stats in topic_stats.items():
            mastery_score = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0.0
            error_frequency = stats['errors'] / stats['attempts'] if stats['attempts'] > 0 else 0.0
            
            cursor.execute("""
                INSERT INTO learner_metrics 
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, ?, NULL, ?, ?, ?, ?)
            """, (user_id, topic, mastery_score, error_frequency, stats['attempts'], stats['successes']))
        
        # Insert updated pattern metrics
        for pattern, stats in pattern_stats.items():
            mastery_score = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0.0
            error_frequency = stats['errors'] / stats['attempts'] if stats['attempts'] > 0 else 0.0
            
            cursor.execute("""
                INSERT INTO learner_metrics 
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, NULL, ?, ?, ?, ?, ?)
            """, (user_id, pattern, mastery_score, error_frequency, stats['attempts'], stats['successes']))
        
        conn.commit()
        conn.close()
    
    def get_weakness_summary(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get top weaknesses (low mastery topics/patterns)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(topic, pattern) as area,
                mastery_score,
                error_frequency,
                attempts_count,
                success_count,
                ROUND(CAST(success_count AS FLOAT) / attempts_count * 100, 2) as success_rate
            FROM learner_metrics
            WHERE user_id = ?
            ORDER BY mastery_score ASC, error_frequency DESC
            LIMIT ?
        """, (user_id, limit))
        
        weaknesses = []
        for row in cursor.fetchall():
            weaknesses.append({
                'topic': row['area'],
                'mastery_score': row['mastery_score'],
                'error_frequency': row['error_frequency'],
                'attempts_count': row['attempts_count'],
                'success_rate': row['success_rate']
            })
        
        conn.close()
        return weaknesses
    
    def get_error_patterns(self, user_id: int) -> Dict[str, int]:
        """Get recurring error types"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM attempts
            WHERE user_id = ? AND error_type IS NOT NULL
            GROUP BY error_type
            ORDER BY count DESC
        """, (user_id,))
        
        errors = {}
        for row in cursor.fetchall():
            errors[row['error_type']] = row['count']
        
        conn.close()
        return errors
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get overall user statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total attempts and successes
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN verdict = 'Accepted' THEN 1 ELSE 0 END) as total_solved,
                COUNT(DISTINCT problem_id) as unique_problems
            FROM attempts
            WHERE user_id = ?
        """, (user_id,))
        
        stats_row = cursor.fetchone()
        
        total_attempts = stats_row['total_attempts'] or 0
        total_solved = stats_row['total_solved'] or 0
        unique_problems = stats_row['unique_problems'] or 0
        
        success_rate = (total_solved / total_attempts * 100) if total_attempts > 0 else 0.0
        
        # Calculate current streak
        cursor.execute("""
            SELECT verdict, DATE(attempted_at) as attempt_date
            FROM attempts
            WHERE user_id = ?
            ORDER BY attempted_at DESC
            LIMIT 30
        """, (user_id,))
        
        recent_attempts = cursor.fetchall()
        streak = 0
        last_date = None
        
        for attempt in recent_attempts:
            if attempt['verdict'] == 'Accepted':
                current_date = attempt['attempt_date']
                if last_date is None or current_date == last_date:
                    streak += 1
                    last_date = current_date
                else:
                    break
            else:
                break
        
        conn.close()
        
        return {
            'total_problems_attempted': unique_problems,
            'total_problems_solved': total_solved,
            'total_attempts': total_attempts,
            'current_streak': streak,
            'success_rate': round(success_rate, 2)
        }