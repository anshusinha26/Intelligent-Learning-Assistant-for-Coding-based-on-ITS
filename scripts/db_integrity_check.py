#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3


def run_integrity_check(db_path: str) -> dict:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA quick_check")
    quick = [row[0] for row in cursor.fetchall()]

    cursor.execute("PRAGMA foreign_key_check")
    fk_issues = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "quick_check_ok": quick == ["ok"],
        "quick_check_result": quick,
        "foreign_key_issues": fk_issues,
        "foreign_key_ok": len(fk_issues) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SQLite integrity checks.")
    parser.add_argument("--db-path", default=os.getenv("DB_PATH", "data/coding_assistant.db"))
    args = parser.parse_args()

    payload = run_integrity_check(args.db_path)
    print(json.dumps(payload, indent=2))
    return 0 if payload["quick_check_ok"] and payload["foreign_key_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
