import glob
import os
import sqlite3
from typing import Dict, List


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migration_dir() -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "migrations")


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _list_up_files() -> List[str]:
    migration_dir = _migration_dir()
    up_files = sorted(glob.glob(os.path.join(migration_dir, "*.up.sql")))
    return up_files


def _version_from_path(path: str) -> str:
    return os.path.basename(path).split(".", 1)[0]


def _description_from_version(version: str) -> str:
    parts = version.split("_", 1)
    return parts[1].replace("_", " ") if len(parts) > 1 else version


def list_migration_status(db_path: str) -> Dict[str, object]:
    conn = _connect(db_path)
    _ensure_migration_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    applied = {row[0] for row in cursor.fetchall()}
    available = [_version_from_path(path) for path in _list_up_files()]
    pending = [version for version in available if version not in applied]
    conn.close()
    return {"available": available, "applied": sorted(applied), "pending": pending}


def apply_pending_migrations(db_path: str) -> Dict[str, int]:
    conn = _connect(db_path)
    _ensure_migration_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in cursor.fetchall()}
    applied_count = 0

    for up_path in _list_up_files():
        version = _version_from_path(up_path)
        if version in applied_versions:
            continue

        with open(up_path, "r", encoding="utf-8") as handle:
            sql = handle.read()
        cursor.executescript(sql)
        cursor.execute(
            "INSERT INTO schema_migrations(version, description) VALUES(?, ?)",
            (version, _description_from_version(version)),
        )
        conn.commit()
        applied_count += 1

    status = list_migration_status(db_path)
    conn.close()
    return {
        "total": len(status["available"]),
        "applied": applied_count,
        "pending": len(status["pending"]),
    }


def rollback_last_migration(db_path: str) -> Dict[str, str]:
    conn = _connect(db_path)
    _ensure_migration_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at DESC, version DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"status": "noop", "message": "No applied migrations to rollback"}

    version = row[0]
    down_path = os.path.join(_migration_dir(), f"{version}.down.sql")
    if not os.path.exists(down_path):
        conn.close()
        raise RuntimeError(f"Missing rollback script for migration {version}")

    with open(down_path, "r", encoding="utf-8") as handle:
        sql = handle.read()
    cursor.executescript(sql)
    cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
    conn.commit()
    conn.close()
    return {"status": "rolled_back", "version": version}


def verify_migrations(db_path: str) -> Dict[str, object]:
    status = list_migration_status(db_path)
    missing_files = []
    for version in status["applied"]:
        up_path = os.path.join(_migration_dir(), f"{version}.up.sql")
        if not os.path.exists(up_path):
            missing_files.append(version)
    if missing_files:
        raise RuntimeError(f"Applied migrations missing files: {', '.join(missing_files)}")
    return status
