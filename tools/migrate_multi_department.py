"""
One-time migration: Department Lead accounts can now be assigned to more
than one department. Adds the UserDepartment join table and backfills it
from each existing user's single User.departmentId (still left in place,
unused going forward -- not dropped, to avoid a destructive column drop on
a live database with real data).

Safe to re-run.

Usage: python3 tools/migrate_multi_department.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS UserDepartment (
    userId TEXT NOT NULL REFERENCES User(id),
    departmentId TEXT NOT NULL REFERENCES Department(id),
    PRIMARY KEY (userId, departmentId)
);
"""


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    existing = conn.execute(
        "SELECT id, departmentId FROM User WHERE departmentId IS NOT NULL AND active = 1"
    ).fetchall()
    backfilled = 0
    for user_id, department_id in existing:
        already = conn.execute(
            "SELECT 1 FROM UserDepartment WHERE userId = ? AND departmentId = ?", (user_id, department_id)
        ).fetchone()
        if not already:
            conn.execute(
                "INSERT INTO UserDepartment (userId, departmentId) VALUES (?, ?)", (user_id, department_id)
            )
            backfilled += 1
    conn.commit()
    conn.close()
    print(f"Migrated {db_path} -- UserDepartment ready, backfilled {backfilled} row(s)")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
