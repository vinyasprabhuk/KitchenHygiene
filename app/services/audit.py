"""Lightweight write-action log for the Admin panel."""
from __future__ import annotations

import json
import sqlite3

from app.dates import now_db
from app.db import new_id


def write(conn: sqlite3.Connection, user: dict | None, action: str, entity: str,
          entity_id: str | None = None, details: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO AuditLog (id, userId, userName, action, entity, entityId, details, createdAt) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (new_id(), user["id"] if user else None, user["name"] if user else "system",
         action, entity, entity_id, json.dumps(details) if details is not None else None, now_db()),
    )


def recent(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM AuditLog ORDER BY createdAt DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]
