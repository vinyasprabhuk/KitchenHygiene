"""
Runs every migration script in this folder, in the order they were
introduced. Each individual migration is idempotent (safe to re-run), so
this is safe to run every time you deploy -- no need to remember which
specific migration a given commit needs.

Usage: python3 tools/migrate_all.py [path-to-db]
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from tools import (
    migrate_rename_phone_to_username,
    migrate_drop_stale_phone_index,
    migrate_username_reuse,
    migrate_multi_department,
    migrate_add_photo_comment,
    migrate_add_issues,
)

MIGRATIONS = [
    migrate_rename_phone_to_username,
    migrate_drop_stale_phone_index,
    migrate_username_reuse,
    migrate_multi_department,
    migrate_add_photo_comment,
    migrate_add_issues,
]

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    for mod in MIGRATIONS:
        print(f"-- {mod.__name__} --")
        mod.migrate(target)
    print("== all migrations applied ==")
