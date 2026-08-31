from __future__ import annotations

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session

from app.security import default_route_for_role, get_csrf_token, verify_password

bp = Blueprint("login", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if g.user is not None:
            return redirect(default_route_for_role(g.user["role"]))
        callback_url = request.args.get("callbackUrl") or None
        return render_template("login.html", error=None, callback_url=callback_url)

    phone = (request.form.get("phone") or "").strip()
    pin = request.form.get("pin") or ""
    callback_url = request.form.get("callback_url") or None
    error = None

    if not phone or not pin:
        error = "Enter your phone number and PIN."
    else:
        row = g.conn.execute(
            "SELECT id, name, phone, pinHash, role, departmentId, active FROM User WHERE phone = ?", (phone,)
        ).fetchone()
        if row is None or not row["active"] or not verify_password(pin, row["pinHash"]):
            error = "Incorrect phone number or PIN."
        else:
            session.clear()
            session["user_id"] = row["id"]
            g.user = {"id": row["id"], "name": row["name"], "phone": row["phone"],
                      "role": row["role"], "departmentId": row["departmentId"]}
            flash(f"Signed in as {row['name']}.", "success")
            dest = callback_url if callback_url and callback_url.startswith("/") else default_route_for_role(row["role"])
            return redirect(dest)

    return render_template("login.html", error=error, callback_url=callback_url)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")


@bp.route("/api/csrf-token")
def csrf_token_api():
    """Lets the capture dialog (which can stay open a minute or more while
    camera/location permissions are granted) fetch a token current as of
    submit time instead of trusting whatever was embedded at page load."""
    if g.user is None:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({"csrfToken": get_csrf_token()})
