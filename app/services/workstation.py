"""
Kitchen Hygiene photo log: department leads capture a photo of their
station. Rolling monthly log, not indefinite history -- each new capture
purges that department's prior-month entries.
"""
from __future__ import annotations

import sqlite3

from app.dates import now_db
from app.db import new_id
from app.services import audit, storage


def create_photo(conn: sqlite3.Connection, actor: dict, department_id: str,
                  photo_bytes: bytes, photo_filename: str, photo_mime_type: str | None,
                  comment: str | None = None) -> str:
    if not photo_bytes:
        raise ValueError("Photo is required")

    saved = storage.save(photo_bytes, photo_filename)
    entry_id = new_id()
    created_at = now_db()
    comment = comment.strip() if comment else None
    conn.execute(
        "INSERT INTO WorkstationPhoto (id, departmentId, photoPath, photoMimeType, comment, createdById, createdAt) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entry_id, department_id, saved["filePath"], photo_mime_type or "image/jpeg",
         comment, actor["id"], created_at),
    )

    current_month = created_at[:7]  # "YYYY-MM" prefix
    conn.execute(
        "DELETE FROM WorkstationPhoto WHERE departmentId = ? AND substr(createdAt, 1, 7) != ?",
        (department_id, current_month),
    )
    audit.write(conn, actor, "PHOTO_CAPTURED", "WorkstationPhoto", entry_id, {"departmentId": department_id})
    conn.commit()
    return entry_id


def current_month_key() -> str:
    return now_db()[:7]


def get_for_department(conn: sqlite3.Connection, department_id: str, date_key: str | None = None) -> list[dict]:
    """date_key is either a full day ('YYYY-MM-DD', filters to that one day)
    or left as None (whole current month, the previous default)."""
    prefix = date_key if date_key else current_month_key()
    length = len(prefix)
    rows = conn.execute(
        f"SELECT p.*, u.name AS createdByName FROM WorkstationPhoto p "
        f"JOIN User u ON u.id = p.createdById "
        f"WHERE p.departmentId = ? AND substr(p.createdAt, 1, {length}) = ? "
        f"ORDER BY p.createdAt DESC",
        (department_id, prefix),
    ).fetchall()
    return [dict(r) for r in rows]
