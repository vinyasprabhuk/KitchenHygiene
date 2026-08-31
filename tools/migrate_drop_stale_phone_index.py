"""
One-time migration: drops the leftover User_phone_idx index.

When tools/migrate_rename_phone_to_username.py renamed User.phone to
User.username, SQLite updated that index's *definition* to reference the
new column name but did not rename the index itself -- so User_phone_idx
kept enforcing a plain (non-partial) unique constraint on username
alongside the later, correctly-partial User_username_idx (WHERE active =
1). The two together meant a deactivated user's username could never
actually be reused, despite User_username_idx allowing it: the crash
happened at User_phone_idx instead.

Only production databases that went through the phone->username rename
have this leftover index; a database created fresh via tools/init_db.py
never had a User_phone_idx to begin with, so this is a no-op there.

Safe to re-run.

Usage: python3 tools/migrate_drop_stale_phone_index.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='User_phone_idx'"
    ).fetchone()
    if existing:
        conn.execute("DROP INDEX User_phone_idx")
        conn.commit()
        print(f"Dropped leftover User_phone_idx in {db_path}")
    else:
        print(f"Nothing to do -- {db_path} has no User_phone_idx")
    conn.close()


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
