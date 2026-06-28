"""
Learner Modeling Module
Tracks user mastery, identifies weakness patterns, and computes learning metrics
"""

from typing import List, Dict
from datetime import date
from src.database import Database

class LearnerModel:
    def __init__(self, db: Database):
        self.db = db
    
    def record_attempt(self, user_id: int, problem_id: str, verdict: str, 
                      time_taken: int = None, error_type: str = None) -> int:
        """Record a practice attempt"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT topic, pattern
            FROM problems
            WHERE problem_id = ?
              AND dataset_tier = 'premium'
              AND is_active = 1
        """,
            (problem_id,),
        )
        problem = cursor.fetchone()
        if not problem:
            conn.close()
            raise ValueError("Problem not found")

        cursor.execute("""
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, problem_id, verdict, time_taken, error_type))

        attempt_id = cursor.lastrowid

        is_success = verdict == "Accepted"
        has_error = error_type is not None

        self._increment_topic_metric(cursor, user_id, problem["topic"], is_success, has_error)
        pattern = problem["pattern"]
        if pattern:
            self._increment_pattern_metric(cursor, user_id, pattern, is_success, has_error)

        conn.commit()
        conn.close()
        return attempt_id

    @staticmethod
    def _compute_scores(attempts: int, successes: int, errors: int):
        mastery_score = (successes + 1) / (attempts + 2)
        error_frequency = (errors + 1) / (attempts + 2)
        return mastery_score, error_frequency

    @staticmethod
    def _derive_errors(attempts_count: int, error_frequency: float) -> int:
        derived = int(round((float(error_frequency) * (attempts_count + 2)) - 1))
        if derived < 0:
            return 0
        if attempts_count >= 0 and derived > attempts_count:
            return attempts_count
        return derived

    def _increment_topic_metric(
        self,
        cursor,
        user_id: int,
        topic: str,
        is_success: bool,
        has_error: bool,
    ) -> None:
        cursor.execute(
            """
            SELECT metric_id, attempts_count, success_count, error_frequency
            FROM learner_metrics
            WHERE user_id = ? AND topic = ? AND pattern IS NULL
            ORDER BY metric_id DESC
            LIMIT 1
        """,
            (user_id, topic),
        )
        row = cursor.fetchone()
        if row:
            previous_attempts = int(row["attempts_count"] or 0)
            previous_successes = int(row["success_count"] or 0)
            previous_errors = self._derive_errors(previous_attempts, row["error_frequency"] or 0.0)
            attempts = previous_attempts + 1
            successes = previous_successes + (1 if is_success else 0)
            errors = previous_errors + (1 if has_error else 0)
            metric_id = row["metric_id"]
        else:
            attempts = 1
            successes = 1 if is_success else 0
            errors = 1 if has_error else 0
            metric_id = None

        mastery_score, error_frequency = self._compute_scores(attempts, successes, errors)
        if metric_id:
            cursor.execute(
                """
                UPDATE learner_metrics
                SET mastery_score = ?,
                    error_frequency = ?,
                    attempts_count = ?,
                    success_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE metric_id = ?
            """,
                (mastery_score, error_frequency, attempts, successes, metric_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO learner_metrics
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, ?, NULL, ?, ?, ?, ?)
            """,
                (user_id, topic, mastery_score, error_frequency, attempts, successes),
            )

    def _increment_pattern_metric(
        self,
        cursor,
        user_id: int,
        pattern: str,
        is_success: bool,
        has_error: bool,
    ) -> None:
        cursor.execute(
            """
            SELECT metric_id, attempts_count, success_count, error_frequency
            FROM learner_metrics
            WHERE user_id = ? AND topic IS NULL AND pattern = ?
            ORDER BY metric_id DESC
            LIMIT 1
        """,
            (user_id, pattern),
        )
        row = cursor.fetchone()
        if row:
            previous_attempts = int(row["attempts_count"] or 0)
            previous_successes = int(row["success_count"] or 0)
            previous_errors = self._derive_errors(previous_attempts, row["error_frequency"] or 0.0)
            attempts = previous_attempts + 1
            successes = previous_successes + (1 if is_success else 0)
            errors = previous_errors + (1 if has_error else 0)
            metric_id = row["metric_id"]
        else:
            attempts = 1
            successes = 1 if is_success else 0
            errors = 1 if has_error else 0
            metric_id = None

        mastery_score, error_frequency = self._compute_scores(attempts, successes, errors)
        if metric_id:
            cursor.execute(
                """
                UPDATE learner_metrics
                SET mastery_score = ?,
                    error_frequency = ?,
                    attempts_count = ?,
                    success_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE metric_id = ?
            """,
                (mastery_score, error_frequency, attempts, successes, metric_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO learner_metrics
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, NULL, ?, ?, ?, ?, ?)
            """,
                (user_id, pattern, mastery_score, error_frequency, attempts, successes),
            )
    
    def update_learner_metrics(self, user_id: int):
        """Recalculate mastery scores and error frequencies for a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM learner_metrics WHERE user_id = ?", (user_id,))

        cursor.execute(
            """
            SELECT
                p.topic AS area,
                COUNT(*) AS attempts,
                SUM(CASE WHEN a.verdict = 'Accepted' THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN a.error_type IS NOT NULL THEN 1 ELSE 0 END) AS errors
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
            GROUP BY p.topic
        """,
            (user_id,),
        )
        topic_rows = cursor.fetchall()

        topic_inserts = []
        for row in topic_rows:
            attempts = int(row["attempts"] or 0)
            successes = int(row["successes"] or 0)
            errors = int(row["errors"] or 0)
            mastery_score, error_frequency = self._compute_scores(attempts, successes, errors)
            topic_inserts.append(
                (
                    user_id,
                    row["area"],
                    mastery_score,
                    error_frequency,
                    attempts,
                    successes,
                )
            )
        if topic_inserts:
            cursor.executemany(
                """
                INSERT INTO learner_metrics
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, ?, NULL, ?, ?, ?, ?)
            """,
                topic_inserts,
            )

        cursor.execute(
            """
            SELECT
                p.pattern AS area,
                COUNT(*) AS attempts,
                SUM(CASE WHEN a.verdict = 'Accepted' THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN a.error_type IS NOT NULL THEN 1 ELSE 0 END) AS errors
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
              AND p.pattern IS NOT NULL
              AND p.pattern != ''
            GROUP BY p.pattern
        """,
            (user_id,),
        )
        pattern_rows = cursor.fetchall()

        pattern_inserts = []
        for row in pattern_rows:
            attempts = int(row["attempts"] or 0)
            successes = int(row["successes"] or 0)
            errors = int(row["errors"] or 0)
            mastery_score, error_frequency = self._compute_scores(attempts, successes, errors)
            pattern_inserts.append(
                (
                    user_id,
                    row["area"],
                    mastery_score,
                    error_frequency,
                    attempts,
                    successes,
                )
            )
        if pattern_inserts:
            cursor.executemany(
                """
                INSERT INTO learner_metrics
                (user_id, topic, pattern, mastery_score, error_frequency, attempts_count, success_count)
                VALUES (?, NULL, ?, ?, ?, ?, ?)
            """,
                pattern_inserts,
            )

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
            SELECT a.error_type, COUNT(*) as count
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND a.error_type IS NOT NULL
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
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
                COUNT(DISTINCT CASE WHEN a.verdict = 'Accepted' THEN a.problem_id END) as total_solved,
                COUNT(DISTINCT a.problem_id) as unique_problems
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
        """, (user_id,))
        
        stats_row = cursor.fetchone()
        
        total_attempts = stats_row['total_attempts'] or 0
        total_solved = stats_row['total_solved'] or 0
        unique_problems = stats_row['unique_problems'] or 0
        
        success_rate = (total_solved / total_attempts * 100) if total_attempts > 0 else 0.0
        
        # Calculate current streak
        cursor.execute("""
            SELECT DISTINCT DATE(attempted_at) as attempt_date
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND a.verdict = 'Accepted'
              AND p.dataset_tier = 'premium'
              AND p.is_active = 1
            ORDER BY attempt_date DESC
            LIMIT 90
        """, (user_id,))

        recent_days = [
            date.fromisoformat(row["attempt_date"])
            for row in cursor.fetchall()
            if row["attempt_date"]
        ]
        streak = 0
        last_day = None

        for attempt_day in recent_days:
            if last_day is None:
                streak = 1
                last_day = attempt_day
                continue
            if (last_day - attempt_day).days == 1:
                streak += 1
                last_day = attempt_day
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
