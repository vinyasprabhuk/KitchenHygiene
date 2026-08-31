"""
One-time migration: adds an optional comment column to WorkstationPhoto, so
whoever captures a photo can leave a short note with it.

Safe to re-run.

Usage: python3 tools/migrate_add_photo_comment.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(WorkstationPhoto)")}
    if "comment" not in cols:
        conn.execute("ALTER TABLE WorkstationPhoto ADD COLUMN comment TEXT")
        conn.commit()
        print(f"Added WorkstationPhoto.comment in {db_path}")
    else:
        print(f"Nothing to do -- {db_path} already has WorkstationPhoto.comment")
    conn.close()


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
