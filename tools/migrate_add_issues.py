"""
One-time migration: adds the Issue table. Manager raises an issue (photo +
comment) against a department; Department Lead resolves it with their own
update. Issues have their own photo storage (photoPath/photoMimeType),
independent of WorkstationPhoto's rolling monthly log, so a resolved issue
doesn't lose its photo when the month rolls over.

Safe to re-run.

Usage: python3 tools/migrate_add_issues.py [path-to-db]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS Issue (
    id TEXT PRIMARY KEY,
    departmentId TEXT NOT NULL REFERENCES Department(id),
    photoPath TEXT NOT NULL,
    photoMimeType TEXT NOT NULL,
    comment TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    createdById TEXT NOT NULL REFERENCES User(id),
    createdAt TEXT NOT NULL,
    resolvedById TEXT REFERENCES User(id),
    resolvedAt TEXT,
    resolutionComment TEXT
);
CREATE INDEX IF NOT EXISTS Issue_department_status_idx ON Issue(departmentId, status);
"""


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Migrated {db_path} -- Issue table ready")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "instance" / "app.db"
    migrate(target)
