import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_or_create_secret_key() -> str:
    """Stable across Passenger's multiple worker processes -- read from
    SECRET_KEY if set, else persisted to a local file and reused."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    key_file = BASE_DIR / "instance" / "secret_key"
    if key_file.exists():
        return key_file.read_text().strip()

    key = secrets.token_hex(32)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key)
    key_file.chmod(0o600)
    return key


class Config:
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "app.db"))
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    SECRET_KEY = _load_or_create_secret_key()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set automatically when the request came in over HTTPS (Passenger/Apache
    # terminate TLS and proxy to the app over plain HTTP).
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
