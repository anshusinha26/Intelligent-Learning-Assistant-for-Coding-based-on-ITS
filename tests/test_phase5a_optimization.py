import os
import tempfile
from datetime import date, timedelta

from src.auth import AuthService
from src.database import Database
from src.learner_model import LearnerModel
from src.recommender import RecommendationEngine
from src.revision_scheduler import RevisionScheduler


def _seed_problem(conn, problem_id: str, title: str, topic: str, pattern: str, difficulty: str = "Easy"):
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


def _create_stack():
    tmp = tempfile.TemporaryDirectory()
    db_path = os.path.join(tmp.name, "phase5a.db")
    db = Database(db_path)
    auth = AuthService(db)
    learner = LearnerModel(db)
    recommender = RecommendationEngine(db)
    scheduler = RevisionScheduler(db)
    return tmp, db, auth, learner, recommender, scheduler


def test_incremental_metric_refresh_matches_attempts():
    tmp, db, auth, learner, _recommender, _scheduler = _create_stack()
    try:
        user = auth.register_user(
            name="Perf User",
            email="perf_user@example.com",
            password="demo123",
            target_level="medium",
        )
        user_id = user["user_id"]

        conn = db.get_connection()
        _seed_problem(conn, "arr-1", "A1", "Arrays", "Hash Map")
        _seed_problem(conn, "arr-2", "A2", "Arrays", "Two Pointers")
        conn.close()

        learner.record_attempt(user_id, "arr-1", "Wrong Answer", 100, "timeout")
        learner.record_attempt(user_id, "arr-1", "Accepted", 80, None)
        learner.record_attempt(user_id, "arr-2", "Accepted", 70, None)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT topic, pattern, attempts_count, success_count, mastery_score, error_frequency
            FROM learner_metrics
            WHERE user_id = ?
            ORDER BY topic IS NULL, topic, pattern
        """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        by_topic = {row["topic"]: row for row in rows if row["topic"] is not None}
        by_pattern = {row["pattern"]: row for row in rows if row["pattern"] is not None}

        arrays = by_topic["Arrays"]
        assert arrays["attempts_count"] == 3
        assert arrays["success_count"] == 2
        assert round(arrays["mastery_score"], 6) == round((2 + 1) / (3 + 2), 6)
        assert round(arrays["error_frequency"], 6) == round((1 + 1) / (3 + 2), 6)

        hashmap = by_pattern["Hash Map"]
        assert hashmap["attempts_count"] == 2
        assert hashmap["success_count"] == 1
        assert round(hashmap["mastery_score"], 6) == round((1 + 1) / (2 + 2), 6)

        two_pointers = by_pattern["Two Pointers"]
        assert two_pointers["attempts_count"] == 1
        assert two_pointers["success_count"] == 1
    finally:
        tmp.cleanup()


def test_revision_schedule_bulk_insert_stays_idempotent():
    tmp, db, auth, learner, _recommender, scheduler = _create_stack()
    try:
        user = auth.register_user(
            name="Revision User",
            email="revision_user@example.com",
            password="demo123",
            target_level="medium",
        )
        user_id = user["user_id"]

        conn = db.get_connection()
        for idx in range(1, 26):
            _seed_problem(conn, f"rev-{idx}", f"Rev {idx}", "Arrays", "Hash Map")
        conn.close()

        for idx in range(1, 26):
            learner.record_attempt(user_id, f"rev-{idx}", "Accepted", 50 + idx, None)

        scheduler.schedule_revisions(user_id)
        scheduler.schedule_revisions(user_id)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS c
            FROM revision_schedule
            WHERE user_id = ? AND status = 'pending'
        """,
            (user_id,),
        )
        pending = cursor.fetchone()["c"]

        cursor.execute(
            """
            SELECT COUNT(*) AS c
            FROM (
                SELECT problem_id
                FROM revision_schedule
                WHERE user_id = ? AND status = 'pending'
                GROUP BY problem_id
                HAVING COUNT(*) > 1
            ) dup
        """,
            (user_id,),
        )
        duplicates = cursor.fetchone()["c"]
        conn.close()

        assert pending == 25
        assert duplicates == 0

        due_date = (date.today() - timedelta(days=1)).isoformat()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE revision_schedule
            SET next_review_date = ?
            WHERE user_id = ? AND status = 'pending'
        """,
            (due_date, user_id),
        )
        conn.commit()
        conn.close()

        due = scheduler.get_due_revisions(user_id, limit=50)
        assert len(due) == 25
    finally:
        tmp.cleanup()
