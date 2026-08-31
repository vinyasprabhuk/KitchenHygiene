from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, abort, g, send_from_directory

from app.security import login_required
from app.services import storage
from app.services.department_scope import get_user_departments

bp = Blueprint("files", __name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@bp.route("/sw.js")
def service_worker():
    # Served from the root path (not /static/sw.js) so its default scope
    # covers the whole app, not just /static/ -- a service worker's scope
    # is limited to the directory it's served from unless a broader Service-
    # Worker-Allowed header is set, so root is the simplest correct choice.
    return send_from_directory(STATIC_DIR, "sw.js", mimetype="application/javascript")


@bp.route("/api/workstation/photo/<entry_id>")
@login_required
def workstation_photo(entry_id: str):
    row = g.conn.execute(
        "SELECT departmentId, photoPath, photoMimeType FROM WorkstationPhoto WHERE id = ?", (entry_id,)
    ).fetchone()
    if row is None or not row["photoPath"]:
        abort(404)

    if g.user["role"] == "DEPARTMENT_LEAD":
        my_dept_ids = {d["id"] for d in get_user_departments(g.conn, g.user["id"])}
        if row["departmentId"] not in my_dept_ids:
            abort(403)

    data = storage.read(row["photoPath"])
    return Response(data, mimetype=row["photoMimeType"] or "image/jpeg")
