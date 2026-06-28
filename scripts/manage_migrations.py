#!/usr/bin/env python3
import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.migrations import apply_pending_migrations, list_migration_status, rollback_last_migration
from src.database import Database


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage versioned database migrations.")
    parser.add_argument("command", choices=["status", "upgrade", "downgrade"], help="Migration command")
    parser.add_argument(
        "--db-path",
        default=os.getenv("DB_PATH", "data/coding_assistant.db"),
        help="SQLite database file path",
    )
    args = parser.parse_args()

    if args.command in {"upgrade", "downgrade"}:
        Database(args.db_path)

    if args.command == "status":
        payload = list_migration_status(args.db_path)
    elif args.command == "upgrade":
        payload = apply_pending_migrations(args.db_path)
    else:
        payload = rollback_last_migration(args.db_path)

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
