#!/usr/bin/env python3
import argparse
import os
import sqlite3
from datetime import datetime, timezone


def backup_database(source_path: str, output_dir: str) -> str:
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Database not found: {source_path}")

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = os.path.join(output_dir, f"coding_assistant_{timestamp}.db")

    src = sqlite3.connect(source_path)
    dest = sqlite3.connect(backup_path)
    with dest:
        src.backup(dest)
    src.close()
    dest.close()
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create SQLite backup using SQLite backup API.")
    parser.add_argument("--db-path", default=os.getenv("DB_PATH", "data/coding_assistant.db"))
    parser.add_argument("--output-dir", default="backups")
    args = parser.parse_args()

    backup_path = backup_database(args.db_path, args.output_dir)
    print(backup_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
