from __future__ import annotations

from flask import Blueprint, Response, abort, g

from app.security import login_required
from app.services import storage

bp = Blueprint("files", __name__)


@bp.route("/api/workstation/photo/<entry_id>")
@login_required
def workstation_photo(entry_id: str):
    row = g.conn.execute(
        "SELECT departmentId, photoPath, photoMimeType FROM WorkstationPhoto WHERE id = ?", (entry_id,)
    ).fetchone()
    if row is None or not row["photoPath"]:
        abort(404)

    role = g.user["role"]
    if role == "DEPARTMENT_LEAD" and row["departmentId"] != g.user.get("departmentId"):
        abort(403)

    data = storage.read(row["photoPath"])
    return Response(data, mimetype=row["photoMimeType"] or "image/jpeg")
