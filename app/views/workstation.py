from __future__ import annotations

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.security import login_required
from app.services import workstation
from app.services.department_scope import effective_scope, list_departments, resolve_department

bp = Blueprint("workstation", __name__)


@bp.route("/workstation")
@login_required
def index():
    conn = g.conn
    can_log = g.user["role"] == "DEPARTMENT_LEAD"
    dept_param = request.args.get("departmentId")

    try:
        department = resolve_department(conn, g.user, dept_param)
    except ValueError as e:
        return render_template("workstation/no_department.html", error=str(e), is_admin=g.user["role"] == "ADMIN")

    scope = effective_scope(conn, g.user)
    departments = list_departments(conn) if scope is None else scope
    show_switcher = scope is None or len(departments) > 1
    entries = workstation.get_for_department(conn, department["departmentId"])

    return render_template(
        "workstation/index.html", department=department, can_log=can_log,
        departments=departments, show_switcher=show_switcher, entries=entries,
    )


@bp.route("/workstation/capture", methods=["POST"])
@login_required
def capture():
    if g.user["role"] != "DEPARTMENT_LEAD":
        abort(403, description="Only Department Leads can capture photos")

    conn = g.conn
    photo = request.files.get("photo")
    requested_department_id = request.form.get("departmentId")

    try:
        department = resolve_department(conn, g.user, requested_department_id)
        photo_bytes = photo.read() if photo and photo.filename else b""
        fn = photo.filename if photo else ""
        mime = photo.mimetype if photo else None
        workstation.create_photo(conn, g.user, department["departmentId"], photo_bytes, fn, mime)
        flash("Photo captured.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("workstation.index", departmentId=requested_department_id))
