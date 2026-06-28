#!/usr/bin/env python3
import argparse
import os
import shutil
import sqlite3
import tempfile


def restore_database(backup_path: str, target_path: str) -> None:
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    src = sqlite3.connect(backup_path)
    dest = sqlite3.connect(temp_path)
    with dest:
        src.backup(dest)
    src.close()
    dest.close()
    shutil.move(temp_path, target_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore SQLite database from backup.")
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--target-db-path", default=os.getenv("DB_PATH", "data/coding_assistant.db"))
    args = parser.parse_args()

    restore_database(args.backup_path, args.target_db_path)
    print(args.target_db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
