from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.reference_data import DEPARTMENT_SUGGESTIONS
from app.security import require_role
from app.services import admin as admin_service
from app.services import audit
from app.services.department_scope import get_user_departments

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@require_role("ADMIN")
def hub():
    return redirect(url_for("admin.users"))


@bp.route("/users")
@require_role("ADMIN")
def users():
    conn = g.conn
    user_rows = [dict(r) for r in conn.execute(
        "SELECT * FROM User WHERE active = 1 ORDER BY name ASC"
    ).fetchall()]
    for u in user_rows:
        u["departments"] = get_user_departments(conn, u["id"])
    deactivated_rows = [dict(r) for r in conn.execute(
        "SELECT * FROM User WHERE active = 0 ORDER BY name ASC"
    ).fetchall()]
    dept_rows = conn.execute("SELECT id, name FROM Department WHERE active = 1 ORDER BY name ASC").fetchall()
    existing_names = {d["name"] for d in dept_rows}
    dept_suggestions = [n for n in DEPARTMENT_SUGGESTIONS if n not in existing_names]
    return render_template(
        "admin/users.html", users=user_rows, deactivated_users=deactivated_rows,
        departments=[dict(r) for r in dept_rows], roles=admin_service.ROLES,
        dept_suggestions=dept_suggestions, assignable_roles=admin_service.DEPARTMENT_ASSIGNABLE_ROLES,
    )


@bp.route("/users/create", methods=["POST"])
@require_role("ADMIN")
def users_create():
    role = request.form.get("role", "DEPARTMENT_LEAD")
    try:
        admin_service.create_user(
            g.conn, g.user, request.form.get("name", ""), request.form.get("username", ""),
            request.form.get("pin", ""), role, request.form.getlist("departmentId"),
        )
        flash("User created.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/deactivate", methods=["POST"])
@require_role("ADMIN")
def users_deactivate(user_id: str):
    admin_service.deactivate_user(g.conn, g.user, user_id)
    flash("User deactivated.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/reset-pin", methods=["POST"])
@require_role("ADMIN")
def users_reset_pin(user_id: str):
    try:
        admin_service.reset_user_pin(g.conn, g.user, user_id, request.form.get("newPin", ""))
        flash("PIN reset.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/departments", methods=["POST"])
@require_role("ADMIN")
def users_update_departments(user_id: str):
    try:
        admin_service.set_user_departments(g.conn, g.user, user_id, request.form.getlist("departmentId"))
        flash("Departments updated.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/purge", methods=["POST"])
@require_role("ADMIN")
def users_purge(user_id: str):
    try:
        admin_service.purge_user(g.conn, g.user, user_id)
        flash("User permanently deleted.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/departments/create", methods=["POST"])
@require_role("ADMIN")
def departments_create():
    try:
        admin_service.create_department(g.conn, g.user, request.form.get("name", ""))
        flash("Department added.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/departments/<department_id>/delete", methods=["POST"])
@require_role("ADMIN")
def departments_delete(department_id: str):
    try:
        admin_service.delete_department(g.conn, g.user, department_id)
        flash("Department deleted.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))


@bp.route("/audit-log")
@require_role("ADMIN")
def audit_log():
    entries = audit.recent(g.conn)
    return render_template("admin/audit_log.html", entries=entries)
