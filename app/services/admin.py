from __future__ import annotations

import re
import sqlite3

from app.dates import now_db
from app.db import new_id
from app.security import hash_password

ROLES = ["ADMIN", "MANAGER", "DEPARTMENT_LEAD"]
PIN_RE = re.compile(r"^\d{4,6}$")
PHONE_RE = re.compile(r"^\d{10}$")


def create_department(conn: sqlite3.Connection, name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Department name cannot be empty")
    conn.execute(
        "INSERT INTO Department (id, name, active, createdAt) VALUES (?, ?, 1, ?)",
        (new_id(), name, now_db()),
    )
    conn.commit()


def delete_department(conn: sqlite3.Connection, department_id: str) -> None:
    in_use = conn.execute(
        "SELECT COUNT(*) FROM User WHERE departmentId = ? AND active = 1", (department_id,)
    ).fetchone()[0]
    if in_use > 0:
        raise ValueError(f"Can't delete -- {in_use} active user(s) still assigned to this department")
    conn.execute("UPDATE Department SET active = 0 WHERE id = ?", (department_id,))
    conn.commit()


def create_user(conn: sqlite3.Connection, name: str, phone: str, pin: str,
                 role: str, department_id: str | None) -> None:
    name = name.strip()
    phone = phone.strip()
    if not name:
        raise ValueError("Name is required")
    if not PHONE_RE.match(phone):
        raise ValueError("Phone number must be exactly 10 digits")
    if not PIN_RE.match(pin):
        raise ValueError("PIN must be 4-6 digits")
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    if role == "DEPARTMENT_LEAD" and not department_id:
        raise ValueError("Department Lead accounts must have a department assigned")

    existing = conn.execute("SELECT id FROM User WHERE phone = ? AND active = 1", (phone,)).fetchone()
    if existing:
        raise ValueError("A user with this phone number already exists")

    conn.execute(
        "INSERT INTO User (id, name, phone, pinHash, role, departmentId, active, createdAt, updatedAt) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
        (new_id(), name, phone, hash_password(pin), role,
         department_id if role == "DEPARTMENT_LEAD" else None, now_db(), now_db()),
    )
    conn.commit()


def deactivate_user(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute("UPDATE User SET active = 0, updatedAt = ? WHERE id = ?", (now_db(), user_id))
    conn.commit()


def reset_user_pin(conn: sqlite3.Connection, user_id: str, new_pin: str) -> None:
    if not PIN_RE.match(new_pin):
        raise ValueError("PIN must be 4-6 digits")
    conn.execute(
        "UPDATE User SET pinHash = ?, updatedAt = ? WHERE id = ?",
        (hash_password(new_pin), now_db(), user_id),
    )
    conn.commit()
