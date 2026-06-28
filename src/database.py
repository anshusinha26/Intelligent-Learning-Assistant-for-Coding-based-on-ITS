"""
Database setup and schema initialization
"""

import logging
import os
import sqlite3
import time

from src.observability import record_db_query
from src.security import structured_log

logger = logging.getLogger("ila-api.db")


def _read_slow_query_threshold() -> int:
    try:
        value = int(os.getenv("DB_SLOW_QUERY_THRESHOLD_MS", "120") or "120")
    except ValueError:
        value = 120
    return max(1, value)


DB_SLOW_QUERY_THRESHOLD_MS = _read_slow_query_threshold()


class ObservedCursor(sqlite3.Cursor):
    def _observe(self, sql: str, started_at: float) -> None:
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        threshold = DB_SLOW_QUERY_THRESHOLD_MS
        record_db_query(sql, elapsed_ms, threshold)
        if elapsed_ms >= threshold:
            logger.warning(
                structured_log(
                    "db_slow_query",
                    statement=(sql or "").strip().split(None, 1)[0].lower() if sql else "unknown",
                    elapsed_ms=round(elapsed_ms, 3),
                    threshold_ms=threshold,
                )
            )

    def execute(self, sql, parameters=()):
        started_at = time.perf_counter()
        try:
            return super().execute(sql, parameters)
        finally:
            self._observe(sql, started_at)

    def executemany(self, sql, seq_of_parameters):
        started_at = time.perf_counter()
        try:
            return super().executemany(sql, seq_of_parameters)
        finally:
            self._observe(sql, started_at)

    def executescript(self, sql_script):
        started_at = time.perf_counter()
        try:
            return super().executescript(sql_script)
        finally:
            self._observe(sql_script, started_at)


class ObservedConnection(sqlite3.Connection):
    def cursor(self, *args, **kwargs):
        kwargs.setdefault("factory", ObservedCursor)
        return super().cursor(*args, **kwargs)

class Database:
    def __init__(self, db_path: str = "data/coding_assistant.db"):
        self.db_path = db_path
        self._connect_timeout_s = 10
        self._busy_timeout_ms = 10000
        parent_dir = os.path.dirname(db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=self._connect_timeout_s,
            factory=ObservedConnection,
            cached_statements=512,
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            target_level TEXT,
            email_verified INTEGER DEFAULT 0,
            email_verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        user_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(users)")}
        extra_user_columns = {
            "email_verified": "INTEGER DEFAULT 0",
            "email_verified_at": "TIMESTAMP",
        }
        for column, definition in extra_user_columns.items():
            if column not in user_columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")

        # Problems table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            problem_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            pattern TEXT,
            difficulty TEXT NOT NULL,
            tags TEXT,
            description TEXT,
            constraints TEXT,
            examples TEXT,
            source_url TEXT,
            function_name TEXT DEFAULT 'solve',
            starter_code TEXT,
            test_cases TEXT,
            dataset_tier TEXT DEFAULT 'premium',
            is_active INTEGER DEFAULT 1,
            curriculum_version INTEGER DEFAULT 1,
            time_complexity TEXT,
            space_complexity TEXT,
            metadata_json TEXT,
            learning_objectives_json TEXT,
            common_mistakes_json TEXT,
            recommendation_graph_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        problem_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(problems)")}
        extra_problem_columns = {
            "constraints": "TEXT",
            "examples": "TEXT",
            "source_url": "TEXT",
            "function_name": "TEXT DEFAULT 'solve'",
            "starter_code": "TEXT",
            "test_cases": "TEXT",
            "dataset_tier": "TEXT DEFAULT 'premium'",
            "is_active": "INTEGER DEFAULT 1",
            "curriculum_version": "INTEGER DEFAULT 1",
            "time_complexity": "TEXT",
            "space_complexity": "TEXT",
            "metadata_json": "TEXT",
            "learning_objectives_json": "TEXT",
            "common_mistakes_json": "TEXT",
            "recommendation_graph_json": "TEXT",
        }
        for column, definition in extra_problem_columns.items():
            if column not in problem_columns:
                cursor.execute(f"ALTER TABLE problems ADD COLUMN {column} {definition}")

        cursor.execute("""
        UPDATE problems
        SET dataset_tier = COALESCE(NULLIF(dataset_tier, ''), 'premium')
        """)
        cursor.execute("""
        UPDATE problems
        SET is_active = 1
        WHERE is_active IS NULL
        """)
        cursor.execute("""
        UPDATE problems
        SET curriculum_version = 1
        WHERE curriculum_version IS NULL
        """)

        # Attempts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            verdict TEXT NOT NULL,
            time_taken INTEGER,
            error_type TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        # Learner metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS learner_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT,
            pattern TEXT,
            mastery_score REAL DEFAULT 0.0,
            error_frequency REAL DEFAULT 0.0,
            attempts_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)

        # Recommendations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            score REAL NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            revoked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replaced_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            token_id TEXT PRIMARY KEY,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            consumed INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)

        # Revision schedule table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            next_review_date DATE NOT NULL,
            interval_days INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        # Code submissions power the limited Python judge and feed attempts.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            language TEXT DEFAULT 'python',
            code TEXT NOT NULL,
            verdict TEXT NOT NULL,
            runtime_ms INTEGER,
            output TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            editor_language TEXT DEFAULT 'python',
            email_notifications INTEGER DEFAULT 1,
            ai_assistant_enabled INTEGER DEFAULT 1,
            daily_goal INTEGER DEFAULT 2,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_problem_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            statement_md TEXT NOT NULL,
            constraints_md TEXT NOT NULL,
            examples_md TEXT NOT NULL,
            editorial_md TEXT NOT NULL,
            reference_solution TEXT NOT NULL,
            starter_code TEXT NOT NULL,
            time_complexity TEXT NOT NULL,
            space_complexity TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            learning_objectives_json TEXT NOT NULL,
            common_mistakes_json TEXT NOT NULL,
            recommendation_graph_json TEXT NOT NULL,
            is_current INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_problem_hints (
            hint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            hint_order INTEGER NOT NULL,
            hint_md TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_problem_tests (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            visibility TEXT NOT NULL,
            input_json TEXT NOT NULL,
            expected_json TEXT NOT NULL,
            explanation TEXT,
            weight REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_problem_relationships (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            related_problem_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE,
            FOREIGN KEY (related_problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_problem_rag_chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            chunk_type TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding_model TEXT,
            embedding_vector TEXT,
            content_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        DELETE FROM recommendations
        WHERE rec_id NOT IN (
            SELECT MAX(rec_id)
            FROM recommendations
            GROUP BY user_id, problem_id, status
        )
        """)

        cursor.execute("""
        DELETE FROM revision_schedule
        WHERE status = 'pending'
          AND schedule_id NOT IN (
            SELECT MIN(schedule_id)
            FROM revision_schedule
            WHERE status = 'pending'
            GROUP BY user_id, problem_id
        )
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_recommendations_unique_state
        ON recommendations(user_id, problem_id, status)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recommendations_user_status
        ON recommendations(user_id, status)
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_revision_unique_pending
        ON revision_schedule(user_id, problem_id)
        WHERE status = 'pending'
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_revoked
        ON refresh_tokens(user_id, revoked)
        """)

        cursor.execute("""
        DELETE FROM bookmarks
        WHERE bookmark_id NOT IN (
            SELECT MIN(bookmark_id)
            FROM bookmarks
            GROUP BY user_id, problem_id
        )
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_bookmarks_unique_user_problem
        ON bookmarks(user_id, problem_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_user_problem
        ON notes(user_id, problem_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_otp_lookup
        ON otp_codes(email, purpose, consumed, expires_at)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_problems_dataset_active
        ON problems(dataset_tier, is_active, topic, difficulty)
        """)

        cursor.execute("DROP INDEX IF EXISTS idx_attempts_user_attempted_at")
        cursor.execute("DROP INDEX IF EXISTS idx_attempts_user_problem")
        cursor.execute("DROP INDEX IF EXISTS idx_submissions_user_submitted_at")

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_versions_unique
        ON premium_problem_versions(problem_id, version)
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_versions_current
        ON premium_problem_versions(problem_id)
        WHERE is_current = 1
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_hints_unique
        ON premium_problem_hints(problem_id, version, hint_order)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_premium_problem_tests_visibility
        ON premium_problem_tests(problem_id, version, visibility)
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_relationships_unique
        ON premium_problem_relationships(problem_id, related_problem_id, edge_type)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_premium_problem_rag_chunks_lookup
        ON premium_problem_rag_chunks(problem_id, version, chunk_type)
        """)

        conn.commit()
        conn.close()
