"""
Revision Scheduler Module
Implements spaced repetition for problem review
Based on forgetting curve principles
"""

from typing import List, Dict
from datetime import date, timedelta
from src.database import Database

class RevisionScheduler:
    def __init__(self, db: Database):
        self.db = db
        # Spaced repetition intervals (in days)
        self.intervals = [1, 3, 7, 14, 30, 60]
    
    def schedule_revisions(self, user_id: int):
        """
        Schedule revision tasks for solved problems
        Uses spaced repetition intervals
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM revision_schedule
            WHERE user_id = ?
              AND problem_id IN (
                    SELECT problem_id
                    FROM problems
                    WHERE dataset_tier != 'premium' OR is_active != 1
              )
        """,
            (user_id,),
        )

        first_interval = self.intervals[0]
        cursor.execute(
            f"""
            INSERT OR IGNORE INTO revision_schedule
            (user_id, problem_id, next_review_date, interval_days)
            SELECT
                ?,
                solved.problem_id,
                DATE(solved.last_attempt, ?),
                ?
            FROM (
                SELECT a.problem_id, MAX(a.attempted_at) AS last_attempt
                FROM attempts a
                JOIN problems p ON p.problem_id = a.problem_id
                WHERE a.user_id = ?
                  AND a.verdict = 'Accepted'
                  AND p.dataset_tier = 'premium'
                  AND p.is_active = 1
                GROUP BY a.problem_id
            ) AS solved
            LEFT JOIN revision_schedule rs
              ON rs.user_id = ?
             AND rs.problem_id = solved.problem_id
             AND rs.status = 'pending'
            WHERE rs.schedule_id IS NULL
        """,
            (user_id, f"+{first_interval} day", first_interval, user_id, user_id),
        )

        conn.commit()
        conn.close()
    
    def _get_next_interval(self, current_interval: int) -> int:
        """Get next spaced repetition interval"""
        try:
            current_index = self.intervals.index(current_interval)
            if current_index < len(self.intervals) - 1:
                return self.intervals[current_index + 1]
        except ValueError:
            pass
        
        # If not in list or at end, double the interval
        return min(current_interval * 2, 90)
    
    def get_due_revisions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get problems due for revision today or earlier"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        today = date.today()
        
        cursor.execute("""
            SELECT 
                rs.schedule_id,
                rs.problem_id,
                rs.next_review_date,
                rs.interval_days,
                p.title,
                p.topic,
                p.difficulty
            FROM revision_schedule rs
            JOIN problems p ON rs.problem_id = p.problem_id
            WHERE rs.user_id = ? 
              AND rs.status = 'pending'
              AND rs.next_review_date <= ?
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
            ORDER BY rs.next_review_date ASC
            LIMIT ?
        """, (user_id, today, limit))
        
        revisions = []
        for row in cursor.fetchall():
            revisions.append({
                'schedule_id': row['schedule_id'],
                'problem_id': row['problem_id'],
                'title': row['title'],
                'topic': row['topic'],
                'difficulty': row['difficulty'],
                'next_review_date': row['next_review_date'],
                'interval_days': row['interval_days']
            })
        
        conn.close()
        return revisions
    
    def mark_revision_completed(self, schedule_id: int, user_id: int):
        """Mark a revision as completed and schedule next review"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get current schedule
        cursor.execute("""
            SELECT interval_days, problem_id
            FROM revision_schedule
            WHERE schedule_id = ? AND user_id = ? AND status = 'pending'
        """, (schedule_id, user_id))
        
        schedule = cursor.fetchone()
        
        if not schedule:
            conn.close()
            raise ValueError("Pending revision schedule not found")

        cursor.execute("""
            UPDATE revision_schedule
            SET status = 'completed'
            WHERE schedule_id = ?
        """, (schedule_id,))

        cursor.execute("""
            DELETE FROM revision_schedule
            WHERE user_id = ?
              AND problem_id = ?
              AND status = 'pending'
        """, (user_id, schedule["problem_id"]))

        next_interval = self._get_next_interval(schedule['interval_days'])
        next_review = date.today() + timedelta(days=next_interval)

        cursor.execute("""
            INSERT INTO revision_schedule
            (user_id, problem_id, next_review_date, interval_days)
            VALUES (?, ?, ?, ?)
        """, (user_id, schedule['problem_id'], next_review, next_interval))

        conn.commit()
        
        conn.close()
    
    def get_revision_stats(self, user_id: int) -> Dict:
        """Get revision statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Count due, upcoming, and completed
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN next_review_date <= ? AND status = 'pending' THEN 1 END) as due_count,
                COUNT(CASE WHEN next_review_date > ? AND status = 'pending' THEN 1 END) as upcoming_count,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count
            FROM revision_schedule rs
            JOIN problems p ON p.problem_id = rs.problem_id
            WHERE rs.user_id = ?
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
        """, (date.today(), date.today(), user_id))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'due_revisions': stats['due_count'] or 0,
            'upcoming_revisions': stats['upcoming_count'] or 0,
            'completed_revisions': stats['completed_count'] or 0
        }
