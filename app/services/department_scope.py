"""
Department-scoping: DEPARTMENT_LEAD is locked to whichever department(s)
they're assigned in UserDepartment (one or more) -- never any others. ADMIN
and MANAGER can view any department, defaulting to the first active one,
with an optional ?departmentId= override.
"""
from __future__ import annotations

import sqlite3

VIEW_ALL_ROLES = ("ADMIN", "MANAGER")


def get_user_departments(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT d.id, d.name FROM UserDepartment ud JOIN Department d ON d.id = ud.departmentId "
        "WHERE ud.userId = ? AND d.active = 1 ORDER BY d.name ASC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def resolve_department(conn: sqlite3.Connection, user: dict,
                        requested_department_id: str | None = None) -> dict:
    role = user["role"]

    if role not in VIEW_ALL_ROLES:
        allowed = get_user_departments(conn, user["id"])
        if not allowed:
            raise ValueError("Your account has no department assigned -- contact an admin")
        allowed_ids = {d["id"] for d in allowed}
        if requested_department_id and requested_department_id in allowed_ids:
            target_id = requested_department_id
        else:
            target_id = allowed[0]["id"]
        row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (target_id,)).fetchone()
        return {"departmentId": row["id"], "departmentName": row["name"]}

    if requested_department_id:
        row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (requested_department_id,)).fetchone()
        if row is None:
            raise ValueError(f"Department not found: {requested_department_id}")
        return {"departmentId": row["id"], "departmentName": row["name"]}

    row = conn.execute("SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC LIMIT 1").fetchone()
    if row is None:
        raise ValueError("No active department found -- create one in Admin first")
    return {"departmentId": row["id"], "departmentName": row["name"]}


def list_departments(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC").fetchall()
    return [dict(r) for r in rows]
