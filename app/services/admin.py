from __future__ import annotations

import re
import sqlite3

from app.dates import now_db
from app.db import new_id
from app.security import hash_password
from app.services import audit

ROLES = ["ADMIN", "MANAGER", "DEPARTMENT_LEAD"]
PIN_RE = re.compile(r"^\d{4,6}$")
DEPARTMENT_ASSIGNABLE_ROLES = ("DEPARTMENT_LEAD", "MANAGER")


def create_department(conn: sqlite3.Connection, actor: dict, name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Department name cannot be empty")
    dept_id = new_id()
    conn.execute(
        "INSERT INTO Department (id, name, active, createdAt) VALUES (?, ?, 1, ?)",
        (dept_id, name, now_db()),
    )
    audit.write(conn, actor, "DEPARTMENT_CREATED", "Department", dept_id, {"name": name})
    conn.commit()


def delete_department(conn: sqlite3.Connection, actor: dict, department_id: str) -> None:
    in_use = conn.execute(
        "SELECT COUNT(*) FROM UserDepartment ud JOIN User u ON u.id = ud.userId "
        "WHERE ud.departmentId = ? AND u.active = 1",
        (department_id,),
    ).fetchone()[0]
    if in_use > 0:
        raise ValueError(f"Can't delete -- {in_use} active user(s) still assigned to this department")
    conn.execute("UPDATE Department SET active = 0 WHERE id = ?", (department_id,))
    audit.write(conn, actor, "DEPARTMENT_DELETED", "Department", department_id)
    conn.commit()


def create_user(conn: sqlite3.Connection, actor: dict, name: str, username: str, pin: str,
                 role: str, department_ids: list[str]) -> None:
    name = name.strip()
    username = username.strip()
    department_ids = [d for d in (department_ids or []) if d]
    if not name or not username:
        raise ValueError("Name and username are required")
    if not PIN_RE.match(pin):
        raise ValueError("PIN must be 4-6 digits")
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    if role == "DEPARTMENT_LEAD" and not department_ids:
        raise ValueError("Department Lead accounts must have at least one department assigned")

    existing = conn.execute("SELECT id FROM User WHERE username = ? AND active = 1", (username,)).fetchone()
    if existing:
        raise ValueError("A user with this username already exists")

    user_id = new_id()
    conn.execute(
        "INSERT INTO User (id, name, username, pinHash, role, departmentId, active, createdAt, updatedAt) "
        "VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?)",
        (user_id, name, username, hash_password(pin), role, now_db(), now_db()),
    )
    if role in DEPARTMENT_ASSIGNABLE_ROLES:
        for dept_id in department_ids:
            conn.execute(
                "INSERT INTO UserDepartment (userId, departmentId) VALUES (?, ?)", (user_id, dept_id)
            )
    audit.write(conn, actor, "USER_CREATED", "User", user_id,
                {"username": username, "role": role, "departmentIds": department_ids})
    conn.commit()


def set_user_departments(conn: sqlite3.Connection, actor: dict, user_id: str, department_ids: list[str]) -> None:
    row = conn.execute("SELECT role FROM User WHERE id = ? AND active = 1", (user_id,)).fetchone()
    if row is None:
        raise ValueError("User not found")
    department_ids = [d for d in (department_ids or []) if d]
    if row["role"] == "DEPARTMENT_LEAD" and not department_ids:
        raise ValueError("Department Lead accounts must have at least one department assigned")
    if row["role"] not in DEPARTMENT_ASSIGNABLE_ROLES and department_ids:
        raise ValueError(f"{row['role']} accounts don't use department assignment")

    conn.execute("DELETE FROM UserDepartment WHERE userId = ?", (user_id,))
    for dept_id in department_ids:
        conn.execute("INSERT INTO UserDepartment (userId, departmentId) VALUES (?, ?)", (user_id, dept_id))
    audit.write(conn, actor, "USER_DEPARTMENTS_UPDATED", "User", user_id, {"departmentIds": department_ids})
    conn.commit()


def deactivate_user(conn: sqlite3.Connection, actor: dict, user_id: str) -> None:
    conn.execute("UPDATE User SET active = 0, updatedAt = ? WHERE id = ?", (now_db(), user_id))
    audit.write(conn, actor, "USER_DEACTIVATED", "User", user_id)
    conn.commit()


def purge_user(conn: sqlite3.Connection, actor: dict, user_id: str) -> None:
    """Hard-deletes a deactivated user. Gated behind already-deactivated
    (can't purge a live account by mistake) and blocked if they still have
    photos attributed to them (WorkstationPhoto.createdById has a foreign
    key on User -- deleting would either violate it or silently orphan
    hygiene records, neither of which is acceptable)."""
    row = conn.execute("SELECT username, active FROM User WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise ValueError("User not found")
    if row["active"]:
        raise ValueError("Deactivate this user before purging")

    photo_count = conn.execute(
        "SELECT COUNT(*) FROM WorkstationPhoto WHERE createdById = ?", (user_id,)
    ).fetchone()[0]
    if photo_count > 0:
        raise ValueError(
            f"Can't purge -- {photo_count} photo(s) this month are still attributed to this user"
        )

    conn.execute("DELETE FROM UserDepartment WHERE userId = ?", (user_id,))
    conn.execute("DELETE FROM User WHERE id = ?", (user_id,))
    audit.write(conn, actor, "USER_PURGED", "User", user_id, {"username": row["username"]})
    conn.commit()


def reset_user_pin(conn: sqlite3.Connection, actor: dict, user_id: str, new_pin: str) -> None:
    if not PIN_RE.match(new_pin):
        raise ValueError("PIN must be 4-6 digits")
    conn.execute(
        "UPDATE User SET pinHash = ?, updatedAt = ? WHERE id = ?",
        (hash_password(new_pin), now_db(), user_id),
    )
    audit.write(conn, actor, "USER_PIN_RESET", "User", user_id)
    conn.commit()
