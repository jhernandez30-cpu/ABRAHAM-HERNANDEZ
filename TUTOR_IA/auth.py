from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode

import requests

from database import get_connection, init_db, row_to_dict, utc_now


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
DEFAULT_SCOPE = "openid email profile"
PBKDF2_ITERATIONS = 260000


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def validate_local_credentials(name: str, email: str, password: str) -> tuple[bool, str]:
    if len((name or "").strip()) < 2:
        return False, "Ingresa tu nombre."
    if "@" not in normalize_email(email):
        return False, "Ingresa un correo valido."
    if len(password or "") < 8:
        return False, "La contrasena debe tener al menos 8 caracteres."
    return True, ""


def get_user_by_email(email: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (normalize_email(email),)).fetchone()
    return row_to_dict(row)


def get_user_by_id(user_id: int) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


def get_user_by_google_id(google_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
    return row_to_dict(row)


def create_user(name: str, email: str, password: str) -> tuple[bool, str, dict | None]:
    init_db()
    valid, message = validate_local_credentials(name, email, password)
    if not valid:
        return False, message, None

    now = utc_now()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    name, email, password_hash, auth_provider,
                    created_at, updated_at, last_login
                )
                VALUES (?, ?, ?, 'local', ?, ?, ?)
                """,
                ((name or "").strip(), normalize_email(email), hash_password(password), now, now, now),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return True, "Cuenta creada correctamente.", row_to_dict(row)
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return False, "Ya existe una cuenta con ese correo.", None
        return False, f"No se pudo crear la cuenta: {exc}", None


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user.get("password_hash")):
        return False, "Correo o contrasena incorrectos.", None
    now = utc_now()
    with get_connection() as conn:
        conn.execute("UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?", (now, now, user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return True, "Sesion iniciada.", row_to_dict(row)


def upsert_google_user(profile: dict) -> tuple[bool, str, dict | None]:
    init_db()
    google_id = str(profile.get("sub") or "").strip()
    email = normalize_email(profile.get("email") or "")
    name = (profile.get("name") or email.split("@")[0] or "Usuario").strip()
    picture = profile.get("picture")
    if not google_id or not email:
        return False, "Google no devolvio un perfil valido.", None

    now = utc_now()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM users WHERE google_id = ? OR email = ?",
            (google_id, email),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?, auth_provider = 'google', google_id = ?,
                    profile_picture = ?, updated_at = ?, last_login = ?
                WHERE id = ?
                """,
                (name, email, google_id, picture, now, now, existing["id"]),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()
        else:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    name, email, password_hash, auth_provider, google_id,
                    profile_picture, created_at, updated_at, last_login
                )
                VALUES (?, ?, NULL, 'google', ?, ?, ?, ?, ?)
                """,
                (name, email, google_id, picture, now, now, now),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return True, "Sesion iniciada con Google.", row_to_dict(row)


def get_google_redirect_uri() -> str:
    default_redirect = (
        os.getenv("FRONTEND_URL", "https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ")
        if os.getenv("APP_ENV", "development").strip().lower() == "production"
        else "http://localhost:8501"
    )
    return os.getenv("GOOGLE_REDIRECT_URI", default_redirect)


def google_oauth_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def build_google_auth_url(state: str) -> str:
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "redirect_uri": get_google_redirect_uri(),
        "response_type": "code",
        "scope": os.getenv("GOOGLE_OAUTH_SCOPE", DEFAULT_SCOPE),
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code: str) -> tuple[bool, str, dict | None]:
    if not google_oauth_configured():
        return False, "Google OAuth no esta configurado en .env.", None
    token_response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": get_google_redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if token_response.status_code >= 400:
        return False, "Google no acepto el codigo OAuth.", None

    access_token = token_response.json().get("access_token")
    if not access_token:
        return False, "Google no devolvio access_token.", None

    profile_response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if profile_response.status_code >= 400:
        return False, "No se pudo leer el perfil de Google.", None

    return upsert_google_user(profile_response.json())
