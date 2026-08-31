"""
Creates the database schema fresh and seeds one ADMIN account. Safe to
re-run (CREATE TABLE IF NOT EXISTS everywhere); the seed admin is only
inserted if no users exist yet.

Usage:
    .venv/bin/python tools/init_db.py [path-to-db]
    .venv/bin/python tools/init_db.py --admin-username admin --admin-pin 1234
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.dates import now_db
from app.db import new_id
from app.security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS Department (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    createdAt TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS Department_name_idx ON Department(name);

CREATE TABLE IF NOT EXISTS User (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT NOT NULL,
    pinHash TEXT NOT NULL,
    role TEXT NOT NULL,
    departmentId TEXT REFERENCES Department(id),
    active INTEGER NOT NULL DEFAULT 1,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS User_username_idx ON User(username) WHERE active = 1;

CREATE TABLE IF NOT EXISTS UserDepartment (
    userId TEXT NOT NULL REFERENCES User(id),
    departmentId TEXT NOT NULL REFERENCES Department(id),
    PRIMARY KEY (userId, departmentId)
);

CREATE TABLE IF NOT EXISTS WorkstationPhoto (
    id TEXT PRIMARY KEY,
    departmentId TEXT NOT NULL REFERENCES Department(id),
    photoPath TEXT NOT NULL,
    photoMimeType TEXT NOT NULL,
    comment TEXT,
    createdById TEXT NOT NULL REFERENCES User(id),
    createdAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS WorkstationPhoto_department_month_idx
    ON WorkstationPhoto(departmentId, createdAt);

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

CREATE TABLE IF NOT EXISTS AuditLog (
    id TEXT PRIMARY KEY,
    userId TEXT,
    userName TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entityId TEXT,
    details TEXT,
    createdAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS AuditLog_createdAt_idx ON AuditLog(createdAt);
"""


def init(db_path: Path, admin_username: str | None, admin_pin: str | None) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    user_count = conn.execute("SELECT COUNT(*) FROM User").fetchone()[0]
    if user_count == 0:
        username = admin_username or "admin"
        pin = admin_pin or "1234"
        ts = now_db()
        conn.execute(
            "INSERT INTO User (id, name, username, pinHash, role, departmentId, active, createdAt, updatedAt) "
            "VALUES (?, 'Admin', ?, ?, 'ADMIN', NULL, 1, ?, ?)",
            (new_id(), username, hash_password(pin), ts, ts),
        )
        conn.commit()
        print(f"Seeded admin -- username: {username}, PIN: {pin} (change this after first login)")
    else:
        print("Users already exist -- skipped seeding.")

    conn.close()
    print(f"Initialized {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", nargs="?", default=str(BASE_DIR / "instance" / "app.db"))
    parser.add_argument("--admin-username")
    parser.add_argument("--admin-pin")
    args = parser.parse_args()
    init(Path(args.db_path), args.admin_username, args.admin_pin)
