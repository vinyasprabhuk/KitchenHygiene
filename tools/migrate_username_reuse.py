"""
One-time migration: makes User.username unique only among ACTIVE users, so
a deactivated account's username can be reused -- matches create_user's
Python-level duplicate check, which already only looks at active=1 rows.
Without this, recreating a user with a previously-deactivated username
crashes with sqlite3.IntegrityError instead of the friendly "already
exists" message (or, in this case, succeeding as intended).

Safe to re-run.

Usage: python3 tools/migrate_username_reuse.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("DROP INDEX IF EXISTS User_username_idx")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS User_username_idx ON User(username) WHERE active = 1")
    conn.commit()
    conn.close()
    print(f"Migrated {db_path} -- User.username now unique only among active users")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
