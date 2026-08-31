"""
One-time migration: renames User.phone to User.username, since login now
accepts any username text instead of requiring a 10-digit phone number.
Safe to re-run.

Usage: python3 tools/migrate_rename_phone_to_username.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(User)")}
    if "username" not in cols and "phone" in cols:
        conn.execute("ALTER TABLE User RENAME COLUMN phone TO username")
        conn.commit()
        print(f"Renamed User.phone -> User.username in {db_path}")
    else:
        print(f"Nothing to do -- {db_path} already has username (or no User table yet)")
    conn.close()


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
