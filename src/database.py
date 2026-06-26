"""
Database setup and schema initialization
"""

import sqlite3
from datetime import datetime
from typing import Optional
import os

class Database:
    def __init__(self, db_path: str = "data/coding_assistant.db"):
        self.db_path = db_path
        parent_dir = os.path.dirname(db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 10000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            target_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
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
        }
        for column, definition in extra_problem_columns.items():
            if column not in problem_columns:
                cursor.execute(f"ALTER TABLE problems ADD COLUMN {column} {definition}")
        
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
        
        conn.commit()
        conn.close()
