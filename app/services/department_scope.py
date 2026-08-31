"""
Department-scoping. ADMIN and MANAGER always have full visibility across
every department -- MANAGER's assigned department(s), if any, only set
which one they land on by default; it's a starting point, not a
restriction, and they can switch to any department via the dropdown.
DEPARTMENT_LEAD is the only role actually restricted -- always scoped to
exactly the department(s) they're assigned (required, at least one).
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
    """None means unrestricted (every active department is visible,
    switchable); a list means restricted to exactly those departments.
    Only DEPARTMENT_LEAD is ever restricted."""
    if user["role"] == "DEPARTMENT_LEAD":
        return get_user_departments(conn, user["id"])
    return None


def resolve_department(conn: sqlite3.Connection, user: dict,
                        requested_department_id: str | None = None) -> dict:
    role = user["role"]

    if role == "DEPARTMENT_LEAD":
        scope = get_user_departments(conn, user["id"])
        if not scope:
            raise ValueError("Your account has no department assigned -- contact an admin")
        allowed_ids = {d["id"] for d in scope}
        target_id = requested_department_id if requested_department_id in allowed_ids else scope[0]["id"]
        row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (target_id,)).fetchone()
        return {"departmentId": row["id"], "departmentName": row["name"]}

    # ADMIN / MANAGER: unrestricted. An explicit request wins; otherwise a
    # Manager's assigned department (if any) is the preferred default, and
    # everyone else falls back to the first active department overall.
    if requested_department_id:
        row = conn.execute("SELECT id, name FROM Department WHERE id = ?", (requested_department_id,)).fetchone()
        if row is None:
            raise ValueError(f"Department not found: {requested_department_id}")
        return {"departmentId": row["id"], "departmentName": row["name"]}

    if role == "MANAGER":
        preferred = get_user_departments(conn, user["id"])
        if preferred:
            return {"departmentId": preferred[0]["id"], "departmentName": preferred[0]["name"]}

    row = conn.execute("SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC LIMIT 1").fetchone()
    if row is None:
        raise ValueError("No active department found -- create one in Admin first")
    return {"departmentId": row["id"], "departmentName": row["name"]}
