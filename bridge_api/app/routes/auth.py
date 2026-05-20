from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.auth_service import AuthServiceError, auth_service
from app.services.supabase_service import SupabaseServiceError, supabase_service


LOGGER = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=256)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=256)


class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)


class PreferencesUpdateRequest(BaseModel):
    model_config = {"extra": "allow"}


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    prefix = "bearer "
    if header.lower().startswith(prefix):
        return header[len(prefix) :].strip()
    return ""


def _safe_return_to(value: str | None) -> str:
    target = (value or "").strip() or settings.auth_frontend_url
    parsed = urlparse(target)
    if parsed.scheme == "file" and settings.auth_allow_file_return:
        return target
    if parsed.scheme not in {"http", "https"}:
        return settings.auth_frontend_url
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return target

    origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    if origin in settings.allowed_origins:
        return target
    if settings.allowed_origin_regex and re.match(settings.allowed_origin_regex, origin):
        return target
    return settings.auth_frontend_url


def _redirect_with_params(return_to: str, params: dict[str, str]) -> RedirectResponse:
    parsed = urlparse(return_to)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.startswith("auth_") and key not in {"provider"}
    ]
    query.extend((key, value) for key, value in params.items() if value)
    target = urlunparse(parsed._replace(query=urlencode(query)))
    return RedirectResponse(target, status_code=302)


def _auth_error(exc: AuthServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/api/auth/providers")
async def auth_providers() -> dict[str, Any]:
    supabase_payload = supabase_service.providers_payload()
    return {
        "ok": True,
        **supabase_payload,
        "google": auth_service.google_configured(),
        "apple": auth_service.apple_configured(),
        "local": settings.auth_provider != "supabase",
        "email_password": True,
        "auth_provider": settings.auth_provider,
    }


@router.post("/api/auth/register")
async def register(payload: RegisterRequest) -> dict[str, Any]:
    try:
        return auth_service.register_local(payload.name, payload.email, payload.password)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc


@router.post("/api/auth/login")
async def login(payload: LoginRequest) -> dict[str, Any]:
    try:
        return auth_service.login_local(payload.email, payload.password)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc


@router.get("/api/auth/session")
async def session(request: Request, code: str = Query(default="")) -> dict[str, Any]:
    try:
        if code:
            return auth_service.session_from_handoff(code)
        return auth_service.session_from_token(_bearer_token(request))
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc


@router.get("/api/auth/me")
async def me(request: Request, code: str = Query(default="")) -> dict[str, Any]:
    return await session(request, code=code)


@router.post("/api/auth/logout")
async def logout(request: Request) -> dict[str, Any]:
    return auth_service.logout(_bearer_token(request))


@router.get("/api/auth/google/start")
async def google_start(return_to: str = Query(default="")) -> RedirectResponse:
    safe_return = _safe_return_to(return_to)
    if settings.auth_provider == "supabase":
        try:
            return RedirectResponse(supabase_service.build_oauth_url("google", safe_return), status_code=302)
        except SupabaseServiceError as exc:
            return _redirect_with_params(
                safe_return,
                {
                    "auth_status": "error",
                    "auth_error": str(exc),
                    "provider": "google",
                },
            )
    if not auth_service.google_configured():
        return _redirect_with_params(
            safe_return,
            {
                "auth_status": "error",
                "auth_error": "google_not_configured",
                "provider": "google",
            },
        )
    state = auth_service.create_oauth_state("google", safe_return)
    return RedirectResponse(auth_service.build_google_auth_url(state), status_code=302)


@router.get("/api/auth/google/callback")
async def google_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
) -> RedirectResponse:
    return_to = settings.auth_frontend_url
    try:
        state_data = auth_service.consume_oauth_state("google", state)
        return_to = _safe_return_to(str(state_data.get("return_to") or ""))
        if error:
            return _redirect_with_params(return_to, {"auth_status": "error", "auth_error": error, "provider": "google"})
        if not code:
            raise AuthServiceError("Google no devolvio codigo OAuth.", 400)
        session_payload = auth_service.exchange_google_code(code)
        handoff_code = auth_service.create_handoff_code(str(session_payload.get("token") or ""))
        return _redirect_with_params(
            return_to,
            {
                "auth_status": "success",
                "auth_code": handoff_code,
                "provider": "google",
            },
        )
    except AuthServiceError as exc:
        LOGGER.warning("Google auth callback failed: %s", exc)
        return _redirect_with_params(
            return_to,
            {
                "auth_status": "error",
                "auth_error": str(exc),
                "provider": "google",
            },
        )


@router.get("/api/auth/apple/start")
async def apple_start(return_to: str = Query(default="")) -> RedirectResponse:
    safe_return = _safe_return_to(return_to)
    if settings.auth_provider == "supabase":
        try:
            return RedirectResponse(supabase_service.build_oauth_url("apple", safe_return), status_code=302)
        except SupabaseServiceError as exc:
            return _redirect_with_params(
                safe_return,
                {
                    "auth_status": "error",
                    "auth_error": str(exc),
                    "provider": "apple",
                },
            )
    if not auth_service.apple_configured():
        return _redirect_with_params(
            safe_return,
            {
                "auth_status": "error",
                "auth_error": "apple_not_configured",
                "provider": "apple",
            },
        )
    state = auth_service.create_oauth_state("apple", safe_return)
    return RedirectResponse(auth_service.build_apple_auth_url(state), status_code=302)


async def _handle_apple_callback_values(
    *,
    code: str,
    state: str,
    error: str,
    id_token: str = "",
    user_payload: str = "",
) -> RedirectResponse:
    return_to = settings.auth_frontend_url
    try:
        state_data = auth_service.consume_oauth_state("apple", state)
        return_to = _safe_return_to(str(state_data.get("return_to") or ""))
        if error:
            return _redirect_with_params(return_to, {"auth_status": "error", "auth_error": error, "provider": "apple"})
        if not code:
            raise AuthServiceError("Apple no devolvio codigo OAuth.", 400)
        session_payload = auth_service.exchange_apple_code(code, id_token=id_token, user_payload=user_payload)
        handoff_code = auth_service.create_handoff_code(str(session_payload.get("token") or ""))
        return _redirect_with_params(
            return_to,
            {
                "auth_status": "success",
                "auth_code": handoff_code,
                "provider": "apple",
            },
        )
    except AuthServiceError as exc:
        LOGGER.warning("Apple auth callback failed: %s", exc)
        return _redirect_with_params(
            return_to,
            {
                "auth_status": "error",
                "auth_error": str(exc),
                "provider": "apple",
            },
        )


@router.post("/api/auth/apple/callback")
async def apple_callback_post(request: Request) -> RedirectResponse:
    form = await request.form()
    return await _handle_apple_callback_values(
        code=str(form.get("code") or ""),
        state=str(form.get("state") or ""),
        error=str(form.get("error") or ""),
        id_token=str(form.get("id_token") or ""),
        user_payload=str(form.get("user") or ""),
    )


@router.get("/api/auth/apple/callback")
async def apple_callback_get(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    id_token: str = Query(default=""),
    user: str = Query(default=""),
) -> RedirectResponse:
    return await _handle_apple_callback_values(
        code=code,
        state=state,
        error=error,
        id_token=id_token,
        user_payload=user,
    )


@router.get("/api/user/profile")
async def get_profile(request: Request) -> dict[str, Any]:
    payload = auth_service.session_from_token(_bearer_token(request))
    if not payload.get("authenticated"):
        raise HTTPException(status_code=401, detail="Sesion no autenticada.")
    return payload


@router.put("/api/user/profile")
async def update_profile(request: Request, payload: ProfileUpdateRequest) -> dict[str, Any]:
    try:
        return auth_service.update_profile(_bearer_token(request), payload.name)
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc


@router.put("/api/user/preferences")
async def update_preferences(request: Request, payload: PreferencesUpdateRequest) -> dict[str, Any]:
    try:
        return auth_service.update_preferences(_bearer_token(request), payload.model_dump())
    except AuthServiceError as exc:
        raise _auth_error(exc) from exc
