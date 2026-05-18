from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from app.config import settings
from app.services.history_service import history_service


LOGGER = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
PBKDF2_ITERATIONS = 260000

DEFAULT_PREFERENCES: dict[str, Any] = {
    "theme": "system",
    "language": "es",
    "response_style": "explicativo",
    "assistant_preference": "respuestas_completas",
    "visible_name": "",
    "use_rag": True,
    "use_web": False,
    "jarvis_voice": False,
    "direct_answers": False,
    "deep_thinking": False,
    "chat_history_enabled": True,
}


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _base64url_json(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        value = json.loads(decoded)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


class SqlServerAuthSync:
    FIELD_CANDIDATES = {
        "id": ["id", "user_id", "usuario_id", "userid", "usuarioid"],
        "name": ["name", "display_name", "nombre", "nombre_visible", "full_name"],
        "email": ["email", "correo", "correo_electronico", "mail"],
        "password_hash": ["password_hash", "passwordhash", "hash_password", "contrasena_hash"],
        "auth_provider": ["auth_provider", "provider", "proveedor", "proveedor_auth"],
        "google_id": ["google_id", "google_sub", "id_google"],
        "apple_id": ["apple_id", "apple_sub", "id_apple"],
        "profile_picture": ["profile_picture", "avatar_url", "picture", "foto_perfil"],
        "created_at": ["created_at", "created_on", "fecha_creacion", "creado_en"],
        "updated_at": ["updated_at", "updated_on", "fecha_actualizacion", "actualizado_en"],
        "last_login": ["last_login", "last_login_at", "ultima_sesion", "ultimo_login"],
    }
    USER_TABLE_NAMES = {"users", "usuarios", "app_users", "auth_users", "usuario", "usuarioauth"}

    def __init__(self) -> None:
        self._last_health: dict[str, Any] = {
            "status": "DISABLED" if not settings.sqlserver_enabled else "DB_DISCONNECTED",
            "user_table": "",
            "last_checked": "",
        }

    def health(self) -> dict[str, Any]:
        if not self._configured():
            self._last_health = {
                "status": "DISABLED",
                "user_table": "",
                "last_checked": utc_now(),
            }
            return dict(self._last_health)
        last_checked = _parse_datetime(str(self._last_health.get("last_checked") or ""))
        if last_checked and (datetime.now(timezone.utc) - last_checked).total_seconds() < 10:
            return dict(self._last_health)
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1")
                table = self._detect_user_table(conn)
            self._last_health = {
                "status": "DB_CONNECTED" if table else "DB_SCHEMA_INVALID",
                "user_table": table.get("ref", "") if table else "",
                "last_checked": utc_now(),
            }
        except Exception as exc:
            self._last_health = {
                "status": "DB_DISCONNECTED",
                "user_table": "",
                "last_checked": utc_now(),
                "error": self._safe_error(exc),
            }
        return dict(self._last_health)

    def sync_user(self, user: dict[str, Any]) -> dict[str, Any]:
        if not self._configured():
            return {"status": "DISABLED"}
        try:
            with self._connect() as conn:
                table = self._detect_user_table(conn)
                if not table:
                    return {"status": "DB_SCHEMA_INVALID"}
                remote_id = self._upsert_user(conn, table, user)
                conn.commit()
            self._last_health = {
                "status": "DB_CONNECTED",
                "user_table": table.get("ref", ""),
                "last_checked": utc_now(),
            }
            return {"status": "SQLSERVER_SYNCED", "remote_user_id": str(remote_id or "")}
        except Exception as exc:
            LOGGER.warning("SQL Server auth sync failed: %s", self._safe_error(exc))
            self._last_health = {
                "status": "DB_DISCONNECTED",
                "user_table": "",
                "last_checked": utc_now(),
                "error": self._safe_error(exc),
            }
            return {"status": "DB_DISCONNECTED", "error": self._safe_error(exc)}

    def _configured(self) -> bool:
        return bool(settings.sqlserver_enabled and settings.sqlserver_host and settings.sqlserver_database)

    def _connect(self) -> Any:
        try:
            import pyodbc  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local ODBC setup
            raise RuntimeError("pyodbc no esta instalado para conectar con SQL Server.") from exc

        pyodbc.pooling = settings.sqlserver_pooling
        server = settings.sqlserver_host
        if settings.sqlserver_port:
            server = f"{server},{settings.sqlserver_port}"
        parts = [
            f"DRIVER={{{settings.sqlserver_driver}}}",
            f"SERVER={server}",
            f"DATABASE={settings.sqlserver_database}",
            f"Encrypt={'yes' if settings.sqlserver_encrypt else 'no'}",
            f"TrustServerCertificate={'yes' if settings.sqlserver_trust_server_certificate else 'no'}",
            f"APP={settings.sqlserver_application_name}",
            f"Connection Timeout={settings.sqlserver_connect_timeout_seconds}",
        ]
        if settings.sqlserver_trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            parts.extend([f"UID={settings.sqlserver_user}", f"PWD={settings.sqlserver_password}"])
        conn = pyodbc.connect(";".join(parts), timeout=settings.sqlserver_connect_timeout_seconds)
        conn.timeout = settings.sqlserver_query_timeout_seconds
        return conn

    def _detect_user_table(self, conn: Any) -> dict[str, Any] | None:
        rows = conn.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            """
        ).fetchall()
        candidates: list[tuple[str, str, dict[str, str]]] = []
        for schema, table in rows:
            columns = self._columns(conn, str(schema), str(table))
            has_email = self._column(columns, "email")
            has_id = self._column(columns, "id")
            if not has_email or not has_id:
                continue
            table_key = str(table).replace("_", "").lower()
            if str(table).lower() in self.USER_TABLE_NAMES or table_key in self.USER_TABLE_NAMES:
                candidates.insert(0, (str(schema), str(table), columns))
            else:
                candidates.append((str(schema), str(table), columns))
        if not candidates:
            return None
        schema, table, columns = candidates[0]
        return {
            "schema": schema,
            "table": table,
            "columns": columns,
            "ref": f"{self._quote(schema)}.{self._quote(table)}",
        }

    def _columns(self, conn: Any, schema: str, table: str) -> dict[str, str]:
        rows = conn.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """,
            schema,
            table,
        ).fetchall()
        return {str(row[0]).lower(): str(row[0]) for row in rows}

    def _upsert_user(self, conn: Any, table: dict[str, Any], user: dict[str, Any]) -> Any:
        columns: dict[str, str] = table["columns"]
        table_ref = table["ref"]
        id_col = self._column(columns, "id")
        email_col = self._column(columns, "email")
        if not id_col or not email_col:
            raise RuntimeError("La tabla de usuarios no tiene columnas id/email compatibles.")

        provider = str(user.get("auth_provider") or "local")
        values_by_field = {
            "name": user.get("name") or user.get("email") or "Usuario",
            "email": normalize_email(str(user.get("email") or "")),
            "password_hash": user.get("password_hash"),
            "auth_provider": provider,
            "google_id": user.get("google_id"),
            "apple_id": user.get("apple_id"),
            "profile_picture": user.get("profile_picture"),
            "created_at": user.get("created_at") or utc_now(),
            "updated_at": utc_now(),
            "last_login": user.get("last_login") or utc_now(),
        }
        mapped = {
            actual: value
            for field, value in values_by_field.items()
            if (actual := self._column(columns, field)) and value not in (None, "")
        }

        existing_id = self._find_existing_user_id(conn, table_ref, columns, id_col, provider, user)
        if existing_id:
            assignments = [f"{self._quote(column)} = ?" for column in mapped if column != id_col]
            if assignments:
                params = [mapped[column] for column in mapped if column != id_col]
                params.append(existing_id)
                conn.execute(
                    f"UPDATE {table_ref} SET {', '.join(assignments)} WHERE {self._quote(id_col)} = ?",
                    *params,
                )
            return existing_id

        insert_columns = [column for column in mapped if column != id_col]
        if not insert_columns:
            raise RuntimeError("No hay columnas compatibles para crear usuario en SQL Server.")
        placeholders = ", ".join("?" for _ in insert_columns)
        quoted_cols = ", ".join(self._quote(column) for column in insert_columns)
        cursor = conn.execute(
            f"INSERT INTO {table_ref} ({quoted_cols}) OUTPUT INSERTED.{self._quote(id_col)} VALUES ({placeholders})",
            *[mapped[column] for column in insert_columns],
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def _find_existing_user_id(
        self,
        conn: Any,
        table_ref: str,
        columns: dict[str, str],
        id_col: str,
        provider: str,
        user: dict[str, Any],
    ) -> Any:
        clauses: list[str] = []
        params: list[Any] = []
        provider_col = self._column(columns, f"{provider}_id")
        provider_value = user.get(f"{provider}_id")
        if provider_col and provider_value:
            clauses.append(f"{self._quote(provider_col)} = ?")
            params.append(provider_value)
        email_col = self._column(columns, "email")
        email = normalize_email(str(user.get("email") or ""))
        if email_col and email:
            clauses.append(f"{self._quote(email_col)} = ?")
            params.append(email)
        if not clauses:
            return None
        row = conn.execute(
            f"SELECT TOP 1 {self._quote(id_col)} FROM {table_ref} WHERE {' OR '.join(clauses)}",
            *params,
        ).fetchone()
        return row[0] if row else None

    def _column(self, columns: dict[str, str], field: str) -> str | None:
        for candidate in self.FIELD_CANDIDATES.get(field, [field]):
            if candidate.lower() in columns:
                return columns[candidate.lower()]
        return None

    def _quote(self, identifier: str) -> str:
        return "[" + identifier.replace("]", "]]") + "]"

    def _safe_error(self, exc: Exception) -> str:
        message = str(exc)
        if settings.sqlserver_password:
            message = message.replace(settings.sqlserver_password, "***")
        if settings.sqlserver_user:
            message = message.replace(settings.sqlserver_user, "***")
        return message[:500]


class AuthService:
    def __init__(self, users_path: Path, sessions_path: Path, state_path: Path) -> None:
        self.users_path = users_path
        self.sessions_path = sessions_path
        self.state_path = state_path
        for path in (self.users_path, self.sessions_path, self.state_path):
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("{}", encoding="utf-8")
        self._lock = threading.RLock()
        self.sqlserver = SqlServerAuthSync()

    def register_local(self, name: str, email: str, password: str) -> dict[str, Any]:
        clean_name = (name or "").strip()
        clean_email = normalize_email(email)
        if len(clean_name) < 2:
            raise AuthServiceError("Escribe tu nombre.")
        if "@" not in clean_email:
            raise AuthServiceError("Escribe un correo electronico valido.")
        if len(password or "") < 8:
            raise AuthServiceError("La contrasena debe tener minimo 8 caracteres.")

        with self._lock:
            data = self._read_users()
            if self._find_user_by_email(data, clean_email):
                raise AuthServiceError("Ya existe una cuenta con ese correo.", 409)
            now = utc_now()
            user = {
                "id": str(data.get("next_id", 1)),
                "name": clean_name,
                "email": clean_email,
                "password_hash": hash_password(password),
                "auth_provider": "local",
                "google_id": "",
                "apple_id": "",
                "profile_picture": "",
                "created_at": now,
                "updated_at": now,
                "last_login": now,
                "plan": "Gratis",
                "preferences": dict(DEFAULT_PREFERENCES),
            }
            data["next_id"] = int(data.get("next_id", 1)) + 1
            data.setdefault("users", {})[user["id"]] = user
            self._write_json(self.users_path, data)

        sync = self.sqlserver.sync_user(user)
        return self._issue_session(user, sync)

    def login_local(self, email: str, password: str) -> dict[str, Any]:
        with self._lock:
            data = self._read_users()
            user = self._find_user_by_email(data, normalize_email(email))
            if not user or not verify_password(password, user.get("password_hash")):
                raise AuthServiceError("Correo o contrasena incorrectos.", 401)
            user["last_login"] = utc_now()
            user["updated_at"] = utc_now()
            data.setdefault("users", {})[str(user["id"])] = user
            self._write_json(self.users_path, data)

        sync = self.sqlserver.sync_user(user)
        return self._issue_session(user, sync)

    def upsert_oauth_user(self, provider: str, profile: dict[str, Any]) -> dict[str, Any]:
        provider = provider.lower().strip()
        if provider not in {"google", "apple"}:
            raise AuthServiceError("Proveedor OAuth no soportado.", 400)
        provider_id = str(profile.get("sub") or "").strip()
        email = normalize_email(str(profile.get("email") or ""))
        name = (profile.get("name") or profile.get("given_name") or email.split("@")[0] or "Usuario").strip()
        picture = str(profile.get("picture") or "")
        if not provider_id:
            raise AuthServiceError(f"{provider} no devolvio un identificador valido.", 400)
        if not email:
            email = f"{provider_id}@{provider}.local"

        with self._lock:
            data = self._read_users()
            user = self._find_user_by_provider(data, provider, provider_id) or self._find_user_by_email(data, email)
            now = utc_now()
            if user:
                user.update(
                    {
                        "name": name or user.get("name") or "Usuario",
                        "email": email,
                        "auth_provider": provider,
                        f"{provider}_id": provider_id,
                        "profile_picture": picture or user.get("profile_picture", ""),
                        "updated_at": now,
                        "last_login": now,
                    }
                )
            else:
                user = {
                    "id": str(data.get("next_id", 1)),
                    "name": name,
                    "email": email,
                    "password_hash": "",
                    "auth_provider": provider,
                    "google_id": provider_id if provider == "google" else "",
                    "apple_id": provider_id if provider == "apple" else "",
                    "profile_picture": picture,
                    "created_at": now,
                    "updated_at": now,
                    "last_login": now,
                    "plan": "Gratis",
                    "preferences": dict(DEFAULT_PREFERENCES),
                }
                data["next_id"] = int(data.get("next_id", 1)) + 1
            data.setdefault("users", {})[str(user["id"])] = user
            self._write_json(self.users_path, data)

        sync = self.sqlserver.sync_user(user)
        return self._issue_session(user, sync)

    def session_from_token(self, token: str | None) -> dict[str, Any]:
        if not token:
            return self._guest_session()
        with self._lock:
            sessions = self._read_sessions()
            session = sessions.get(token)
            if not session:
                return self._guest_session()
            expires_at = _parse_datetime(str(session.get("expires_at") or ""))
            if expires_at and expires_at < datetime.now(timezone.utc):
                sessions.pop(token, None)
                self._write_json(self.sessions_path, sessions)
                return self._guest_session()
            session["last_seen_at"] = utc_now()
            sessions[token] = session
            self._write_json(self.sessions_path, sessions)
            user = self._get_user_by_id(str(session.get("user_id") or ""))
        if not user:
            return self._guest_session()
        return self._session_payload(token, user, session.get("persistence", {}))

    def session_from_handoff(self, code: str) -> dict[str, Any]:
        with self._lock:
            state = self._read_state()
            handoffs = state.setdefault("handoffs", {})
            handoff = handoffs.pop(code, None)
            self._write_json(self.state_path, state)
        if not handoff:
            raise AuthServiceError("Codigo de autenticacion expirado o invalido.", 401)
        expires_at = _parse_datetime(str(handoff.get("expires_at") or ""))
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise AuthServiceError("Codigo de autenticacion expirado.", 401)
        return self.session_from_token(str(handoff.get("token") or ""))

    def logout(self, token: str | None) -> dict[str, Any]:
        if token:
            with self._lock:
                sessions = self._read_sessions()
                sessions.pop(token, None)
                self._write_json(self.sessions_path, sessions)
        return {"ok": True, "authenticated": False}

    def update_preferences(self, token: str | None, preferences: dict[str, Any]) -> dict[str, Any]:
        session = self.session_from_token(token)
        if not session.get("authenticated"):
            raise AuthServiceError("Sesion no autenticada.", 401)
        user_id = str(session["user"]["id"])
        allowed = set(DEFAULT_PREFERENCES)
        with self._lock:
            data = self._read_users()
            user = data.get("users", {}).get(user_id)
            if not user:
                raise AuthServiceError("Usuario no encontrado.", 404)
            current = self._normalize_preferences(user.get("preferences"))
            for key, value in (preferences or {}).items():
                if key in allowed:
                    current[key] = value
            user["preferences"] = self._normalize_preferences(current)
            user["updated_at"] = utc_now()
            data["users"][user_id] = user
            self._write_json(self.users_path, data)
        return self.session_from_token(token)

    def update_profile(self, token: str | None, name: str) -> dict[str, Any]:
        session = self.session_from_token(token)
        if not session.get("authenticated"):
            raise AuthServiceError("Sesion no autenticada.", 401)
        clean_name = (name or "").strip()
        if len(clean_name) < 2:
            raise AuthServiceError("Escribe un nombre valido.")
        user_id = str(session["user"]["id"])
        with self._lock:
            data = self._read_users()
            user = data.get("users", {}).get(user_id)
            if not user:
                raise AuthServiceError("Usuario no encontrado.", 404)
            user["name"] = clean_name
            user["updated_at"] = utc_now()
            data["users"][user_id] = user
            self._write_json(self.users_path, data)
        sync = self.sqlserver.sync_user(user)
        payload = self.session_from_token(token)
        payload["persistence"] = sync
        return payload

    def create_oauth_state(self, provider: str, return_to: str) -> str:
        state_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        with self._lock:
            state = self._read_state()
            states = state.setdefault("states", {})
            states[state_value] = {
                "provider": provider,
                "return_to": return_to,
                "created_at": utc_now(),
                "expires_at": expires_at.isoformat(),
            }
            self._prune_state(state)
            self._write_json(self.state_path, state)
        return state_value

    def consume_oauth_state(self, provider: str, state_value: str) -> dict[str, Any]:
        with self._lock:
            state = self._read_state()
            states = state.setdefault("states", {})
            item = states.pop(state_value, None)
            self._write_json(self.state_path, state)
        if not item or item.get("provider") != provider:
            raise AuthServiceError("Estado OAuth invalido.", 401)
        expires_at = _parse_datetime(str(item.get("expires_at") or ""))
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise AuthServiceError("Estado OAuth expirado.", 401)
        return item

    def create_handoff_code(self, token: str) -> str:
        code = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        with self._lock:
            state = self._read_state()
            state.setdefault("handoffs", {})[code] = {
                "token": token,
                "created_at": utc_now(),
                "expires_at": expires_at.isoformat(),
            }
            self._prune_state(state)
            self._write_json(self.state_path, state)
        return code

    def google_configured(self) -> bool:
        return bool(settings.google_client_id and settings.google_client_secret)

    def build_google_auth_url(self, state_value: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": settings.google_oauth_scope,
            "state": state_value,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def exchange_google_code(self, code: str) -> dict[str, Any]:
        if not self.google_configured():
            raise AuthServiceError("Google OAuth no esta configurado.", 503)
        try:
            token_response = requests.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=20,
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise AuthServiceError("Google no devolvio access_token.", 502)
            profile_response = requests.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=20,
            )
            profile_response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Google OAuth exchange failed: %s", exc)
            raise AuthServiceError("No se pudo completar el inicio con Google.", 502) from exc
        return self.upsert_oauth_user("google", profile_response.json())

    def apple_configured(self) -> bool:
        return bool(settings.apple_client_id and settings.apple_client_secret)

    def build_apple_auth_url(self, state_value: str) -> str:
        params = {
            "client_id": settings.apple_client_id,
            "redirect_uri": settings.apple_redirect_uri,
            "response_type": "code id_token",
            "scope": settings.apple_oauth_scope,
            "response_mode": "form_post",
            "state": state_value,
        }
        return f"{APPLE_AUTH_URL}?{urlencode(params)}"

    def exchange_apple_code(self, code: str, id_token: str = "", user_payload: str = "") -> dict[str, Any]:
        if not self.apple_configured():
            raise AuthServiceError("Apple OAuth no esta configurado.", 503)
        try:
            token_response = requests.post(
                APPLE_TOKEN_URL,
                data={
                    "client_id": settings.apple_client_id,
                    "client_secret": settings.apple_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.apple_redirect_uri,
                },
                timeout=20,
            )
            token_response.raise_for_status()
            token_data = token_response.json()
        except requests.RequestException as exc:
            LOGGER.warning("Apple OAuth exchange failed: %s", exc)
            raise AuthServiceError("No se pudo completar el inicio con Apple.", 502) from exc

        profile = self._apple_profile_from_token(token_data.get("id_token") or id_token, user_payload)
        return self.upsert_oauth_user("apple", profile)

    def _apple_profile_from_token(self, id_token: str, user_payload: str) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        parts = (id_token or "").split(".")
        if len(parts) >= 2:
            payload = _base64url_json(parts[1])
        profile = {
            "sub": payload.get("sub", ""),
            "email": payload.get("email", ""),
            "name": "",
        }
        try:
            user_data = json.loads(user_payload or "{}")
            name_data = user_data.get("name") if isinstance(user_data, dict) else {}
            if isinstance(name_data, dict):
                profile["name"] = " ".join(
                    part for part in [name_data.get("firstName"), name_data.get("lastName")] if part
                ).strip()
            if not profile["email"] and isinstance(user_data, dict):
                profile["email"] = user_data.get("email", "")
        except json.JSONDecodeError:
            pass
        return profile

    def _issue_session(self, user: dict[str, Any], persistence: dict[str, Any] | None = None) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.auth_session_ttl_hours)
        with self._lock:
            sessions = self._read_sessions()
            sessions[token] = {
                "user_id": str(user["id"]),
                "created_at": utc_now(),
                "last_seen_at": utc_now(),
                "expires_at": expires_at.isoformat(),
                "persistence": persistence or {"status": "LOCAL_JSON"},
            }
            self._write_json(self.sessions_path, sessions)
        return self._session_payload(token, user, persistence or {"status": "LOCAL_JSON"})

    def _session_payload(self, token: str, user: dict[str, Any], persistence: dict[str, Any] | None = None) -> dict[str, Any]:
        memory_session_id = f"user:{user['id']}"
        return {
            "ok": True,
            "authenticated": True,
            "token": token,
            "access_token": token,
            "user": self._public_user(user),
            "preferences": self._normalize_preferences(user.get("preferences")),
            "memory": {
                "status": "LOADED",
                **history_service.memory_metadata(memory_session_id),
            },
            "persistence": persistence or {"status": "LOCAL_JSON"},
            "sqlserver": self.sqlserver.health(),
        }

    def _guest_session(self) -> dict[str, Any]:
        return {
            "ok": True,
            "authenticated": False,
            "token": "",
            "access_token": "",
            "user": None,
            "preferences": dict(DEFAULT_PREFERENCES),
            "memory": {"status": "GUEST_MODE"},
            "persistence": {"status": "GUEST_MODE"},
            "sqlserver": self.sqlserver.health(),
        }

    def _public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(user.get("id") or ""),
            "name": user.get("name") or "",
            "email": user.get("email") or "",
            "auth_provider": user.get("auth_provider") or "local",
            "profile_picture": user.get("profile_picture") or "",
            "created_at": user.get("created_at") or "",
            "updated_at": user.get("updated_at") or "",
            "last_login": user.get("last_login") or "",
            "plan": user.get("plan") or "Gratis",
        }

    def _normalize_preferences(self, value: Any) -> dict[str, Any]:
        source = value if isinstance(value, dict) else {}
        return {**DEFAULT_PREFERENCES, **source}

    def _get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        data = self._read_users()
        user = data.get("users", {}).get(user_id)
        return user if isinstance(user, dict) else None

    def _find_user_by_email(self, data: dict[str, Any], email: str) -> dict[str, Any] | None:
        for user in data.get("users", {}).values():
            if normalize_email(str(user.get("email") or "")) == email:
                return user
        return None

    def _find_user_by_provider(self, data: dict[str, Any], provider: str, provider_id: str) -> dict[str, Any] | None:
        key = f"{provider}_id"
        for user in data.get("users", {}).values():
            if str(user.get(key) or "") == provider_id:
                return user
        return None

    def _read_users(self) -> dict[str, Any]:
        data = self._read_json(self.users_path)
        if "users" not in data:
            data["users"] = {}
        if "next_id" not in data:
            data["next_id"] = 1
        return data

    def _read_sessions(self) -> dict[str, Any]:
        data = self._read_json(self.sessions_path)
        return data if isinstance(data, dict) else {}

    def _read_state(self) -> dict[str, Any]:
        data = self._read_json(self.state_path)
        if "states" not in data:
            data["states"] = {}
        if "handoffs" not in data:
            data["handoffs"] = {}
        return data

    def _prune_state(self, state: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        for bucket in ("states", "handoffs"):
            items = state.setdefault(bucket, {})
            expired = []
            for key, item in items.items():
                expires_at = _parse_datetime(str(item.get("expires_at") or ""))
                if expires_at and expires_at < now:
                    expired.append(key)
            for key in expired:
                items.pop(key, None)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8") or "{}")
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)


auth_service = AuthService(settings.auth_users_path, settings.auth_sessions_path, settings.auth_state_path)
