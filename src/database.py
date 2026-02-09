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
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
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
        
        conn.commit()
        conn.close()