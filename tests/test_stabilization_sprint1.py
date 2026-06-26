import os
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta

from src.auth import AuthService
from src.database import Database
from src.learner_model import LearnerModel
from src.models import AttemptCreate
from src.recommender import RecommendationEngine
from src.revision_scheduler import RevisionScheduler


def _seed_problem(conn: sqlite3.Connection, problem_id: str, title: str, topic: str, difficulty: str, pattern: str = None):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO problems (problem_id, title, topic, pattern, difficulty, tags, description, function_name, test_cases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            problem_id,
            title,
            topic,
            pattern,
            difficulty,
            "tag",
            "desc",
            "solve",
            '[{"input":[[2,7,11,15],9],"expected":[0,1]}]',
        ),
    )
    conn.commit()


class StabilizationSprint1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test.db")
        self.db = Database(self.db_path)
        self.auth = AuthService(self.db)
        self.learner = LearnerModel(self.db)
        self.recommender = RecommendationEngine(self.db)
        self.scheduler = RevisionScheduler(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_user(self):
        return self.auth.register_user(
            name="Test User",
            email=f"u_{datetime.now().timestamp()}@example.com",
            password="demo123",
            target_level="medium",
        )

    def _conn(self):
        return self.db.get_connection()

    def test_attempt_verdict_validation(self):
        AttemptCreate(problem_id="two-sum", verdict="Accepted")
        with self.assertRaises(ValueError):
            AttemptCreate(problem_id="two-sum", verdict="banana verdict")

    def test_auth_refresh_and_logout_revocation(self):
        user = self._create_user()
        access_token = user["access_token"]
        refresh_token = user["refresh_token"]
        user_id = user["user_id"]

        current = self.auth.get_current_user(access_token)
        self.assertIsNotNone(current)
        self.assertEqual(current["user_id"], user_id)

        refreshed = self.auth.refresh_access_token(refresh_token)
        self.assertIn("access_token", refreshed)
        self.assertIn("refresh_token", refreshed)

        self.auth.logout_user(access_token, user_id, refresh_token=refreshed["refresh_token"])
        self.assertIsNone(self.auth.get_current_user(access_token))

        with self.assertRaises(ValueError):
            self.auth.refresh_access_token(refresh_token)

    def test_recommendation_dedup_and_state_consistency(self):
        user = self._create_user()
        user_id = user["user_id"]

        conn = self._conn()
        _seed_problem(conn, "p1", "Problem 1", "Arrays", "Easy")
        _seed_problem(conn, "p2", "Problem 2", "Arrays", "Easy")
        _seed_problem(conn, "p3", "Problem 3", "Arrays", "Medium")
        conn.close()

        self.learner.record_attempt(user_id, "p1", "Accepted", 100, None)

        self.recommender.generate_recommendations(user_id, top_k=2, refresh_pending=True)
        self.recommender.generate_recommendations(user_id, top_k=2, refresh_pending=True)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT problem_id, status, COUNT(*) c
            FROM recommendations
            WHERE user_id = ? AND status = 'pending'
            GROUP BY problem_id, status
            HAVING COUNT(*) > 1
        """,
            (user_id,),
        )
        duplicates = cursor.fetchall()
        self.assertEqual(len(duplicates), 0)

        cursor.execute(
            """
            SELECT problem_id FROM recommendations
            WHERE user_id = ? AND status = 'pending'
            LIMIT 1
        """,
            (user_id,),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        pending_problem = row["problem_id"]
        conn.close()

        self.learner.record_attempt(user_id, pending_problem, "Accepted", 90, None)
        pending = self.recommender.get_recommendations(user_id, status="pending", limit=10)
        self.assertNotIn(pending_problem, {item["problem_id"] for item in pending})

    def test_streak_daily_stable(self):
        user = self._create_user()
        user_id = user["user_id"]

        conn = self._conn()
        _seed_problem(conn, "streak-p1", "Streak Problem", "Arrays", "Easy")
        cursor = conn.cursor()
        today = date.today()
        timestamps = [
            datetime.combine(today, datetime.min.time()).replace(hour=10).isoformat(),
            datetime.combine(today, datetime.min.time()).replace(hour=12).isoformat(),
            datetime.combine(today - timedelta(days=1), datetime.min.time()).replace(hour=9).isoformat(),
            datetime.combine(today - timedelta(days=3), datetime.min.time()).replace(hour=8).isoformat(),
        ]
        cursor.execute(
            """
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
            VALUES (?, ?, 'Accepted', 20, NULL, ?)
        """,
            (user_id, "streak-p1", timestamps[0]),
        )
        cursor.execute(
            """
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
            VALUES (?, ?, 'Accepted', 22, NULL, ?)
        """,
            (user_id, "streak-p1", timestamps[1]),
        )
        cursor.execute(
            """
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
            VALUES (?, ?, 'Accepted', 23, NULL, ?)
        """,
            (user_id, "streak-p1", timestamps[2]),
        )
        cursor.execute(
            """
            INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
            VALUES (?, ?, 'Accepted', 25, NULL, ?)
        """,
            (user_id, "streak-p1", timestamps[3]),
        )
        conn.commit()
        conn.close()

        stats = self.learner.get_user_stats(user_id)
        self.assertEqual(stats["current_streak"], 2)

    def test_revision_schedule_single_pending_and_complete(self):
        user = self._create_user()
        user_id = user["user_id"]

        conn = self._conn()
        _seed_problem(conn, "rev-p1", "Revision Problem", "Arrays", "Easy")
        conn.close()

        self.learner.record_attempt(user_id, "rev-p1", "Accepted", 55, None)
        self.scheduler.schedule_revisions(user_id)
        self.scheduler.schedule_revisions(user_id)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) c
            FROM revision_schedule
            WHERE user_id = ? AND problem_id = ? AND status = 'pending'
        """,
            (user_id, "rev-p1"),
        )
        self.assertEqual(cursor.fetchone()["c"], 1)

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        cursor.execute(
            """
            UPDATE revision_schedule
            SET next_review_date = ?
            WHERE user_id = ? AND problem_id = ? AND status = 'pending'
        """,
            (yesterday, user_id, "rev-p1"),
        )
        conn.commit()
        conn.close()

        due = self.scheduler.get_due_revisions(user_id, limit=5)
        self.assertGreaterEqual(len(due), 1)

        schedule_id = due[0]["schedule_id"]
        self.scheduler.mark_revision_completed(schedule_id, user_id)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) c
            FROM revision_schedule
            WHERE user_id = ? AND problem_id = ? AND status = 'completed'
        """,
            (user_id, "rev-p1"),
        )
        completed_count = cursor.fetchone()["c"]
        cursor.execute(
            """
            SELECT COUNT(*) c
            FROM revision_schedule
            WHERE user_id = ? AND problem_id = ? AND status = 'pending'
        """,
            (user_id, "rev-p1"),
        )
        pending_count = cursor.fetchone()["c"]
        conn.close()

        self.assertEqual(completed_count, 1)
        self.assertEqual(pending_count, 1)

    def test_recommendation_score_penalizes_recovered_topic(self):
        weak_problem = {
            "problem_id": "x1",
            "title": "Weak Area Problem",
            "topic": "Arrays",
            "pattern": "Hash Map",
            "difficulty": "Medium",
        }
        weak_areas_bad = {"Arrays": (0.3, 0.7, 6)}
        weak_areas_recovered = {"Arrays": (0.7, 0.3, 14)}

        score_bad, _ = self.recommender._score_problem(
            weak_problem,
            weak_areas_bad,
            "medium",
        )
        score_recovered, _ = self.recommender._score_problem(
            weak_problem,
            weak_areas_recovered,
            "medium",
        )

        self.assertGreater(score_bad, score_recovered)

    def test_topic_cap_reduces_after_recovery(self):
        top_k = 10
        weak_bad = {"Arrays": (0.3, 0.7, 6)}
        weak_recovered = {"Arrays": (0.6, 0.4, 10)}

        bad_cap = self.recommender._topic_recommendation_cap("Arrays", weak_bad, top_k)
        recovered_cap = self.recommender._topic_recommendation_cap(
            "Arrays",
            weak_recovered,
            top_k,
        )

        self.assertEqual(bad_cap, 10)
        self.assertLess(recovered_cap, bad_cap)


if __name__ == "__main__":
    unittest.main()
