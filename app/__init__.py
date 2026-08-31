from __future__ import annotations

from flask import Flask, g, redirect, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from app.db import get_connection
from app.security import default_route_for_role, get_csrf_token, validate_csrf

PUBLIC_PATHS = ("/login", "/static", "/manifest.json")


def create_app(config_object: str = "config.Config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Passenger/Apache terminate TLS and proxy to this app over plain HTTP.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from app.views.login import bp as login_bp
    from app.views.files import bp as files_bp
    from app.views.workstation import bp as workstation_bp
    from app.views.admin import bp as admin_bp
    from app.views.issues import bp as issues_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(workstation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(issues_bp)

    @app.before_request
    def load_user_and_enforce_auth():
        g.conn = get_connection()

        user_id = session.get("user_id")
        g.user = None
        if user_id:
            row = g.conn.execute(
                "SELECT id, name, username, role, departmentId, active FROM User WHERE id = ?", (user_id,)
            ).fetchone()
            if row and row["active"]:
                g.user = {
                    "id": row["id"], "name": row["name"], "username": row["username"],
                    "role": row["role"], "departmentId": row["departmentId"],
                }
            else:
                session.clear()

        path = request.path
        if any(path == p or path.startswith(p + "/") for p in PUBLIC_PATHS):
            return None

        if g.user is None:
            return redirect(url_for("login.login", callbackUrl=path))

        if path == "/":
            return redirect(default_route_for_role(g.user["role"]))

        if path.startswith("/admin") and g.user["role"] != "ADMIN":
            return redirect(default_route_for_role(g.user["role"]))

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            validate_csrf()

        return None

    @app.teardown_request
    def close_db(exc):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    @app.context_processor
    def inject_globals():
        user = getattr(g, "user", None)
        conn = getattr(g, "conn", None)
        open_issue_count = _open_issue_count(conn, user) if (user and conn) else 0
        return {
            "current_user": user,
            "csrf_token": get_csrf_token,
            "nav_links": _nav_links(user),
            "open_issue_count": open_issue_count,
        }

    return app


def _open_issue_count(conn, user: dict) -> int:
    from app.services import issues as issues_service
    from app.services.department_scope import get_user_departments

    if user["role"] in ("ADMIN", "MANAGER"):
        return issues_service.open_count_all(conn)
    dept_ids = [d["id"] for d in get_user_departments(conn, user["id"])]
    return issues_service.open_count_for_departments(conn, dept_ids)


def _nav_links(user: dict | None) -> list[dict]:
    if user is None:
        return []
    links = [
        {"href": "/workstation", "label": "Workstation Photos"},
        {"href": "/issues", "label": "Issues"},
    ]
    if user["role"] == "ADMIN":
        links.append({"href": "/admin/users", "label": "Admin"})
    return links
