"""
Lightweight issue tracker: a Manager raises an issue (photo + comment)
against a department; a Department Lead of that department resolves it
with their own update. Unlike WorkstationPhoto's rolling monthly log,
issues and their photos persist indefinitely -- there's no purge, since a
resolved issue is a record worth keeping.
"""
from __future__ import annotations

import sqlite3

from app.dates import now_db
from app.db import new_id
from app.services import audit, storage


def create_issue(conn: sqlite3.Connection, actor: dict, department_id: str, comment: str,
                  photo_bytes: bytes, photo_filename: str, photo_mime_type: str | None) -> str:
    comment = (comment or "").strip()
    if not comment:
        raise ValueError("A comment is required to create an issue")
    if not photo_bytes:
        raise ValueError("Photo is required")

    saved = storage.save(photo_bytes, photo_filename)
    issue_id = new_id()
    conn.execute(
        "INSERT INTO Issue (id, departmentId, photoPath, photoMimeType, comment, status, createdById, createdAt) "
        "VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?)",
        (issue_id, department_id, saved["filePath"], photo_mime_type or "image/jpeg",
         comment, actor["id"], now_db()),
    )
    audit.write(conn, actor, "ISSUE_CREATED", "Issue", issue_id, {"departmentId": department_id})
    conn.commit()
    return issue_id


def resolve_issue(conn: sqlite3.Connection, actor: dict, issue_id: str, resolution_comment: str) -> None:
    row = conn.execute("SELECT status FROM Issue WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise ValueError("Issue not found")
    if row["status"] == "RESOLVED":
        raise ValueError("Issue is already resolved")
    conn.execute(
        "UPDATE Issue SET status = 'RESOLVED', resolvedById = ?, resolvedAt = ?, resolutionComment = ? "
        "WHERE id = ?",
        (actor["id"], now_db(), (resolution_comment or "").strip() or None, issue_id),
    )
    audit.write(conn, actor, "ISSUE_RESOLVED", "Issue", issue_id)
    conn.commit()


_SELECT = (
    "SELECT i.*, d.name AS departmentName, u1.name AS createdByName, u2.name AS resolvedByName "
    "FROM Issue i JOIN Department d ON d.id = i.departmentId "
    "JOIN User u1 ON u1.id = i.createdById "
    "LEFT JOIN User u2 ON u2.id = i.resolvedById "
)


def get_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(_SELECT + "ORDER BY (i.status = 'OPEN') DESC, i.createdAt DESC").fetchall()
    return [dict(r) for r in rows]


def get_for_departments(conn: sqlite3.Connection, department_ids: list[str]) -> list[dict]:
    if not department_ids:
        return []
    placeholders = ",".join("?" * len(department_ids))
    rows = conn.execute(
        _SELECT + f"WHERE i.departmentId IN ({placeholders}) "
        "ORDER BY (i.status = 'OPEN') DESC, i.createdAt DESC",
        department_ids,
    ).fetchall()
    return [dict(r) for r in rows]


def open_count_for_departments(conn: sqlite3.Connection, department_ids: list[str]) -> int:
    if not department_ids:
        return 0
    placeholders = ",".join("?" * len(department_ids))
    return conn.execute(
        f"SELECT COUNT(*) FROM Issue WHERE status = 'OPEN' AND departmentId IN ({placeholders})",
        department_ids,
    ).fetchone()[0]


def open_count_all(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM Issue WHERE status = 'OPEN'").fetchone()[0]
