from __future__ import annotations

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for

from app.security import login_required
from app.services import issues as issues_service
from app.services import storage
from app.services.department_scope import get_user_departments

bp = Blueprint("issues", __name__)


@bp.route("/issues")
@login_required
def index():
    conn = g.conn
    role = g.user["role"]
    if role in ("ADMIN", "MANAGER"):
        rows = issues_service.get_all(conn)
        can_resolve_ids = set()
        if role == "ADMIN":
            can_resolve_ids = {r["id"] for r in rows}
    else:
        my_depts = get_user_departments(conn, g.user["id"])
        dept_ids = [d["id"] for d in my_depts]
        rows = issues_service.get_for_departments(conn, dept_ids)
        can_resolve_ids = {r["id"] for r in rows}

    return render_template("issues/index.html", issues=rows, can_resolve_ids=can_resolve_ids)


@bp.route("/issues/create", methods=["POST"])
@login_required
def create():
    if g.user["role"] != "MANAGER":
        abort(403, description="Only Managers can create issues")

    conn = g.conn
    department_id = request.form.get("departmentId")
    comment = request.form.get("comment")
    photo = request.files.get("photo")

    try:
        if not department_id:
            raise ValueError("No department selected")
        photo_bytes = photo.read() if photo and photo.filename else b""
        fn = photo.filename if photo else ""
        mime = photo.mimetype if photo else None
        issues_service.create_issue(conn, g.user, department_id, comment, photo_bytes, fn, mime)
        flash("Issue created.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("workstation.index", departmentId=department_id))


@bp.route("/issues/<issue_id>/resolve", methods=["POST"])
@login_required
def resolve(issue_id: str):
    conn = g.conn
    role = g.user["role"]

    if role == "DEPARTMENT_LEAD":
        row = conn.execute("SELECT departmentId FROM Issue WHERE id = ?", (issue_id,)).fetchone()
        my_dept_ids = {d["id"] for d in get_user_departments(conn, g.user["id"])}
        if row is None or row["departmentId"] not in my_dept_ids:
            abort(403, description="Not your department's issue")
    elif role != "ADMIN":
        abort(403, description="Only the assigned Department Lead or an Admin can resolve issues")

    try:
        issues_service.resolve_issue(conn, g.user, issue_id, request.form.get("resolutionComment"))
        flash("Issue resolved.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("issues.index"))


@bp.route("/api/issue/photo/<issue_id>")
@login_required
def issue_photo(issue_id: str):
    row = g.conn.execute(
        "SELECT departmentId, photoPath, photoMimeType FROM Issue WHERE id = ?", (issue_id,)
    ).fetchone()
    if row is None:
        abort(404)

    if g.user["role"] == "DEPARTMENT_LEAD":
        my_dept_ids = {d["id"] for d in get_user_departments(g.conn, g.user["id"])}
        if row["departmentId"] not in my_dept_ids:
            abort(403)

    data = storage.read(row["photoPath"])
    return Response(data, mimetype=row["photoMimeType"] or "image/jpeg")
