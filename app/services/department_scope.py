"""
Department-scoping. ADMIN is always unrestricted. DEPARTMENT_LEAD is always
scoped to whichever department(s) they're assigned (required, at least
one). MANAGER is scoped only if explicitly assigned department(s) --
useful for shift-based coverage (e.g. two managers each covering the same
two locations on alternating shifts) -- otherwise defaults to unrestricted,
same as before this existed.
"""
from __future__ import annotations

import sqlite3


def get_user_departments(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT d.id, d.name FROM UserDepartment ud JOIN Department d ON d.id = ud.departmentId "
        "WHERE ud.userId = ? AND d.active = 1 ORDER BY d.name ASC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_departments(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC").fetchall()
    return [dict(r) for r in rows]


def effective_scope(conn: sqlite3.Connection, user: dict) -> list[dict] | None:
    """None means unrestricted (every active department); a list means
    scoped to exactly those departments (possibly empty, for a Department
    Lead somehow left unassigned)."""
    role = user["role"]
    if role == "ADMIN":
        return None
    assigned = get_user_departments(conn, user["id"])
    if role == "MANAGER" and not assigned:
        return None
    return assigned


def resolve_department(conn: sqlite3.Connection, user: dict,
                        requested_department_id: str | None = None) -> dict:
    scope = effective_scope(conn, user)

    if scope is None:
        if requested_department_id:
            row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (requested_department_id,)).fetchone()
            if row is None:
                raise ValueError(f"Department not found: {requested_department_id}")
            return {"departmentId": row["id"], "departmentName": row["name"]}
        row = conn.execute(
            "SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No active department found -- create one in Admin first")
        return {"departmentId": row["id"], "departmentName": row["name"]}

    if not scope:
        raise ValueError("Your account has no department assigned -- contact an admin")
    allowed_ids = {d["id"] for d in scope}
    target_id = requested_department_id if requested_department_id in allowed_ids else scope[0]["id"]
    row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (target_id,)).fetchone()
    return {"departmentId": row["id"], "departmentName": row["name"]}
