from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests
from urllib.parse import urlencode

from app.config import settings
from app.services.auth_defaults import DEFAULT_PREFERENCES


LOGGER = logging.getLogger(__name__)
SUPABASE_TIMEOUT_SECONDS = 20


class SupabaseServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


class SupabaseService:
    def configured(self) -> bool:
        return bool(settings.supabase_url and settings.supabase_anon_key)

    def enabled(self) -> bool:
        return settings.auth_provider == "supabase" and self.configured()

    def database_configured(self) -> bool:
        return bool(settings.database_url)

    def provider_enabled(self, provider: str) -> bool:
        if not self.configured():
            return False
        provider = provider.lower().strip()
        if provider == "google":
            return settings.supabase_google_enabled
        if provider == "apple":
            return settings.supabase_apple_enabled
        return False

    def build_oauth_url(self, provider: str, return_to: str) -> str:
        self._require_configured()
        provider = provider.lower().strip()
        if provider not in {"google", "apple"}:
            raise SupabaseServiceError("Proveedor OAuth no soportado.", 400)
        if not self.provider_enabled(provider):
            raise SupabaseServiceError(f"{provider} no esta habilitado en Supabase.", 503)
        params = {
            "provider": provider,
            "redirect_to": return_to,
        }
        return f"{self._auth_url('/authorize')}?{urlencode(params)}"

    def providers_payload(self) -> dict[str, Any]:
        return {
            "supabase": self.configured(),
            "supabase_enabled": self.enabled(),
            "google": self.provider_enabled("google"),
            "apple": self.provider_enabled("apple"),
            "postgres": self.database_configured(),
        }

    def sign_up(self, name: str, email: str, password: str) -> dict[str, Any]:
        self._require_configured()
        response = requests.post(
            self._auth_url("/signup"),
            headers=self._headers(),
            json={
                "email": _normalize_email(email),
                "password": password,
                "data": {
                    "name": name,
                    "full_name": name,
                    "display_name": name,
                },
            },
            timeout=SUPABASE_TIMEOUT_SECONDS,
        )
        data = self._json_response(response)
        return self._payload_from_auth_response(
            data,
            token=str(data.get("access_token") or ""),
            fallback_name=name,
            persistence_reason="SUPABASE_SIGNUP",
        )

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        self._require_configured()
        response = requests.post(
            self._auth_url("/token"),
            params={"grant_type": "password"},
            headers=self._headers(),
            json={
                "email": _normalize_email(email),
                "password": password,
            },
            timeout=SUPABASE_TIMEOUT_SECONDS,
        )
        data = self._json_response(response)
        return self._payload_from_auth_response(
            data,
            token=str(data.get("access_token") or ""),
            persistence_reason="SUPABASE_LOGIN",
        )

    def session_from_token(self, token: str | None) -> dict[str, Any]:
        self._require_configured()
        if not token:
            raise SupabaseServiceError("Token de Supabase ausente.", 401)
        response = requests.get(
            self._auth_url("/user"),
            headers=self._headers(token=token),
            timeout=SUPABASE_TIMEOUT_SECONDS,
        )
        data = self._json_response(response)
        return self._payload_from_user(data, token=token, persistence_reason="SUPABASE_SESSION")

    def logout(self, token: str | None) -> dict[str, Any]:
        if not self.configured() or not token:
            return {"ok": True}
        try:
            requests.post(
                self._auth_url("/logout"),
                headers=self._headers(token=token),
                timeout=SUPABASE_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            LOGGER.warning("Supabase logout request failed: %s", self._safe_error(exc))
        return {"ok": True}

    def update_preferences(self, token: str, user: dict[str, Any], preferences: dict[str, Any]) -> dict[str, Any]:
        public_user = dict(user or {})
        current = self.get_preferences(str(public_user.get("id") or ""))
        allowed = set(DEFAULT_PREFERENCES)
        for key, value in (preferences or {}).items():
            if key in allowed:
                current[key] = value
        persistence = self.upsert_profile(public_user, preferences=current)
        return self._session_payload(
            token,
            public_user,
            preferences=current,
            persistence=persistence,
        )

    def update_profile(self, token: str, user: dict[str, Any], name: str) -> dict[str, Any]:
        clean_name = (name or "").strip()
        public_user = dict(user or {})
        public_user["name"] = clean_name
        metadata_sync = self._update_auth_user_metadata(str(public_user.get("id") or ""), clean_name)
        persistence = self.upsert_profile(public_user, preferences=self.get_preferences(str(public_user.get("id") or "")))
        if metadata_sync.get("status") != "DISABLED":
            persistence = {**persistence, "auth_metadata": metadata_sync}
        return self._session_payload(
            token,
            public_user,
            preferences=self.get_preferences(str(public_user.get("id") or "")),
            persistence=persistence,
        )

    def get_preferences(self, user_id: str) -> dict[str, Any]:
        if not user_id or not self.database_configured():
            return dict(DEFAULT_PREFERENCES)
        try:
            from psycopg.rows import dict_row

            with self._connect() as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SELECT preferences FROM public.profiles WHERE id = %s::uuid", (user_id,))
                    row = cursor.fetchone()
            value = row.get("preferences") if row else {}
            return self._normalize_preferences(value)
        except Exception as exc:
            LOGGER.warning("Supabase preferences read failed: %s", self._safe_error(exc))
            return dict(DEFAULT_PREFERENCES)

    def upsert_profile(self, user: dict[str, Any], preferences: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.database_configured():
            return {"status": "SUPABASE_AUTH_ONLY", "database": "DISABLED"}
        user_id = str(user.get("id") or "")
        if not user_id:
            return {"status": "SKIPPED", "reason": "missing_user_id"}
        prefs = self._normalize_preferences(preferences or user.get("preferences"))
        try:
            from psycopg.rows import dict_row
            from psycopg.types.json import Json

            with self._connect() as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO public.profiles (
                            id, email, name, avatar_url, role, plan, preferences, last_login, updated_at
                        )
                        VALUES (
                            %s::uuid, %s, %s, %s, %s, %s, %s::jsonb, now(), now()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            email = EXCLUDED.email,
                            name = COALESCE(NULLIF(EXCLUDED.name, ''), public.profiles.name),
                            avatar_url = COALESCE(NULLIF(EXCLUDED.avatar_url, ''), public.profiles.avatar_url),
                            role = COALESCE(NULLIF(EXCLUDED.role, ''), public.profiles.role),
                            plan = COALESCE(NULLIF(EXCLUDED.plan, ''), public.profiles.plan),
                            preferences = COALESCE(public.profiles.preferences, '{}'::jsonb) || EXCLUDED.preferences,
                            last_login = now(),
                            updated_at = now()
                        RETURNING id, updated_at
                        """,
                        (
                            user_id,
                            _normalize_email(str(user.get("email") or "")),
                            str(user.get("name") or ""),
                            str(user.get("profile_picture") or user.get("avatar_url") or ""),
                            str(user.get("role") or "user"),
                            str(user.get("plan") or "Gratis"),
                            Json(prefs),
                        ),
                    )
                    row = cursor.fetchone()
                conn.commit()
            return {
                "status": "SUPABASE_POSTGRES_SYNCED",
                "profile_id": str(row.get("id") if row else user_id),
            }
        except Exception as exc:
            LOGGER.warning("Supabase profile sync failed: %s", self._safe_error(exc))
            return {"status": "SUPABASE_POSTGRES_ERROR", "error": self._safe_error(exc)}

    def save_chat_turn(self, record: dict[str, Any]) -> dict[str, Any]:
        if not self.database_configured():
            return {"status": "DISABLED"}
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        user_id = str(metadata.get("user_id") or "").strip()
        if not user_id:
            return {"status": "SKIPPED", "reason": "guest_or_missing_user"}
        try:
            from psycopg.types.json import Json

            with self._connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO public.conversation_history (
                            user_id, session_id, chat_id, user_message, ai_response, sources, metadata, created_at
                        )
                        VALUES (%s::uuid, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                        """,
                        (
                            user_id,
                            str(record.get("session_id") or ""),
                            str(metadata.get("chat_id") or ""),
                            str(record.get("user_message") or ""),
                            str(record.get("ai_response") or ""),
                            Json(record.get("sources") or []),
                            Json(metadata),
                            record.get("created_at") or _utc_now(),
                        ),
                    )
                conn.commit()
            return {"status": "SUPABASE_POSTGRES_SYNCED"}
        except Exception as exc:
            LOGGER.warning("Supabase conversation history sync failed: %s", self._safe_error(exc))
            return {"status": "SUPABASE_POSTGRES_ERROR", "error": self._safe_error(exc)}

    def _payload_from_auth_response(
        self,
        data: dict[str, Any],
        *,
        token: str,
        fallback_name: str = "",
        persistence_reason: str,
    ) -> dict[str, Any]:
        user = data.get("user") if isinstance(data.get("user"), dict) else {}
        public_user = self._public_user(user, fallback_name=fallback_name)
        if not token:
            return {
                "ok": True,
                "authenticated": False,
                "requires_email_confirmation": True,
                "token": "",
                "access_token": "",
                "user": public_user if public_user.get("id") else None,
                "preferences": dict(DEFAULT_PREFERENCES),
                "memory": {"status": "EMAIL_CONFIRMATION_REQUIRED"},
                "persistence": {"status": "SUPABASE_AUTH_PENDING"},
                "auth_source": "supabase",
            }
        return self._session_payload(
            token,
            public_user,
            preferences=self.get_preferences(str(public_user.get("id") or "")),
            persistence=self.upsert_profile(public_user, preferences=dict(DEFAULT_PREFERENCES))
            | {"reason": persistence_reason},
        )

    def _payload_from_user(self, user: dict[str, Any], *, token: str, persistence_reason: str) -> dict[str, Any]:
        public_user = self._public_user(user)
        preferences = self.get_preferences(str(public_user.get("id") or ""))
        persistence = self.upsert_profile(public_user, preferences=preferences)
        persistence["reason"] = persistence_reason
        return self._session_payload(token, public_user, preferences=preferences, persistence=persistence)

    def _session_payload(
        self,
        token: str,
        public_user: dict[str, Any],
        *,
        preferences: dict[str, Any],
        persistence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "authenticated": True,
            "token": token,
            "access_token": token,
            "user": public_user,
            "preferences": self._normalize_preferences(preferences),
            "memory": {
                "status": "LOADED",
                "session_id": f"user:{public_user.get('id', '')}",
            },
            "persistence": persistence or {"status": "SUPABASE_AUTH_ONLY"},
            "auth_source": "supabase",
        }

    def _public_user(self, user: dict[str, Any], fallback_name: str = "") -> dict[str, Any]:
        metadata = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
        app_metadata = user.get("app_metadata") if isinstance(user.get("app_metadata"), dict) else {}
        email = _normalize_email(str(user.get("email") or metadata.get("email") or ""))
        configured_admins = {_normalize_email(email_value) for email_value in settings.admin_emails}
        role = str(app_metadata.get("role") or metadata.get("role") or "user").strip().lower() or "user"
        is_admin = bool(email and email in configured_admins)
        public_role = "admin" if is_admin else role if role != "admin" else "user"
        name = (
            metadata.get("name")
            or metadata.get("full_name")
            or metadata.get("display_name")
            or fallback_name
            or email.split("@")[0]
            or "Usuario"
        )
        return {
            "id": str(user.get("id") or ""),
            "name": str(name or "Usuario"),
            "email": email,
            "auth_provider": "supabase",
            "role": public_role,
            "is_admin": is_admin,
            "profile_picture": str(metadata.get("avatar_url") or metadata.get("picture") or ""),
            "created_at": str(user.get("created_at") or ""),
            "updated_at": str(user.get("updated_at") or _utc_now()),
            "last_login": str(user.get("last_sign_in_at") or user.get("last_login") or ""),
            "plan": str(metadata.get("plan") or "Gratis"),
        }

    def _update_auth_user_metadata(self, user_id: str, name: str) -> dict[str, Any]:
        if not user_id or not settings.supabase_service_role_key:
            return {"status": "DISABLED"}
        try:
            response = requests.put(
                self._auth_url(f"/admin/users/{user_id}"),
                headers=self._headers(token=settings.supabase_service_role_key, use_service_role=True),
                json={"user_metadata": {"name": name, "full_name": name, "display_name": name}},
                timeout=SUPABASE_TIMEOUT_SECONDS,
            )
            self._json_response(response)
            return {"status": "SUPABASE_AUTH_METADATA_SYNCED"}
        except Exception as exc:
            LOGGER.warning("Supabase auth metadata update failed: %s", self._safe_error(exc))
            return {"status": "SUPABASE_AUTH_METADATA_ERROR", "error": self._safe_error(exc)}

    def _connect(self) -> Any:
        import psycopg

        return psycopg.connect(
            settings.database_url,
            connect_timeout=settings.postgres_connect_timeout_seconds,
        )

    def _auth_url(self, path: str) -> str:
        return f"{settings.supabase_url.rstrip('/')}/auth/v1{path}"

    def _headers(self, *, token: str = "", use_service_role: bool = False) -> dict[str, str]:
        api_key = settings.supabase_service_role_key if use_service_role else settings.supabase_anon_key
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _json_response(self, response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok:
            raise SupabaseServiceError(self._error_message(data, response.status_code), response.status_code)
        return data if isinstance(data, dict) else {}

    def _error_message(self, data: dict[str, Any], status_code: int) -> str:
        candidates = [
            data.get("msg"),
            data.get("message"),
            data.get("error_description"),
            data.get("error"),
        ]
        raw = " ".join(str(item) for item in candidates if item).strip()
        lowered = raw.lower()
        if "already" in lowered or "registered" in lowered:
            return "Ya existe una cuenta con ese correo."
        if "invalid login" in lowered or "invalid credentials" in lowered:
            return "Correo o contrasena incorrectos."
        if status_code in {401, 403}:
            return raw or "Token de Supabase invalido."
        return raw or f"Supabase Auth respondio con HTTP {status_code}."

    def _require_configured(self) -> None:
        if not self.configured():
            raise SupabaseServiceError("Supabase Auth no esta configurado.", 503)

    def _normalize_preferences(self, value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        source = value if isinstance(value, dict) else {}
        return {**DEFAULT_PREFERENCES, **source}

    def _safe_error(self, exc: Exception) -> str:
        message = str(exc)
        for secret in (
            settings.database_url,
            settings.supabase_anon_key,
            settings.supabase_service_role_key,
        ):
            if secret:
                message = message.replace(secret, "***")
        return message[:500]


supabase_service = SupabaseService()
