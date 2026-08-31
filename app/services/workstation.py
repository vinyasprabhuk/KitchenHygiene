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
                  photo_bytes: bytes, photo_filename: str, photo_mime_type: str | None) -> str:
    if not photo_bytes:
        raise ValueError("Photo is required")

    saved = storage.save(photo_bytes, photo_filename)
    entry_id = new_id()
    created_at = now_db()
    conn.execute(
        "INSERT INTO WorkstationPhoto (id, departmentId, photoPath, photoMimeType, createdById, createdAt) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (entry_id, department_id, saved["filePath"], photo_mime_type or "image/jpeg", actor["id"], created_at),
    )

    current_month = created_at[:7]  # "YYYY-MM" prefix
    conn.execute(
        "DELETE FROM WorkstationPhoto WHERE departmentId = ? AND substr(createdAt, 1, 7) != ?",
        (department_id, current_month),
    )
    audit.write(conn, actor, "PHOTO_CAPTURED", "WorkstationPhoto", entry_id, {"departmentId": department_id})
    conn.commit()
    return entry_id


def get_for_department(conn: sqlite3.Connection, department_id: str, month_key: str | None = None) -> list[dict]:
    month_key = month_key or now_db()[:7]
    rows = conn.execute(
        "SELECT p.*, u.name AS createdByName FROM WorkstationPhoto p "
        "JOIN User u ON u.id = p.createdById "
        "WHERE p.departmentId = ? AND substr(p.createdAt, 1, 7) = ? "
        "ORDER BY p.createdAt DESC",
        (department_id, month_key),
    ).fetchall()
    return [dict(r) for r in rows]
