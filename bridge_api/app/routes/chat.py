from __future__ import annotations

import json
import logging
import hashlib
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.models.schemas import ChatRequest, ChatResponse, Source
from app.services.auth_service import AuthServiceError, auth_service
from app.services.file_service import file_service
from app.services.history_service import history_service
from app.services.workflow_service import workflow_service


LOGGER = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


async def _parse_chat_request(request: Request) -> tuple[ChatRequest, list[UploadFile]]:
    content_type = request.headers.get("content-type", "").lower()
    files: list[UploadFile] = []

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        message = str(form.get("message") or form.get("question") or "").strip()
        session_id = str(form.get("session_id") or "default").strip() or "default"
        project_path = str(form.get("project_path") or form.get("workspace_path") or "").strip() or None
        k = _safe_int(form.get("k"))
        top_k = _safe_int(form.get("top_k"))
        show_sources = _as_bool(form.get("show_sources"), default=False)
        user_preferences = _json_dict(form.get("user_preferences"))
        for item in form.getlist("files"):
            if hasattr(item, "filename") and hasattr(item, "read"):
                files.append(item)
        return ChatRequest(
            message=message,
            session_id=session_id,
            chat_id=str(form.get("chat_id") or "").strip(),
            user_id=str(form.get("user_id") or "").strip(),
            user_email=str(form.get("user_email") or "").strip(),
            user_name=str(form.get("user_name") or "").strip(),
            project_path=project_path,
            workspace_path=str(form.get("workspace_path") or "").strip() or None,
            show_sources=show_sources,
            use_rag=_as_bool(form.get("use_rag") or form.get("tutorIA"), default=True),
            use_web=_as_bool(form.get("use_web") or form.get("smartSearch") or form.get("smart_search"), default=False),
            smartSearch=_as_bool(form.get("smartSearch") or form.get("smart_search"), default=False),
            deep_thinking=_as_bool(form.get("deep_thinking"), default=False),
            response_profile=str(form.get("response_profile") or "balanced").strip(),
            user_preferences=user_preferences,
            client_context_summary=str(form.get("client_context_summary") or "").strip(),
            source=str(form.get("source") or "typed_chat").strip(),
            input_source=str(form.get("input_source") or "typed_chat").strip(),
            k=k,
            top_k=top_k,
        ), files

    if "application/json" in content_type:
        data = await request.json()
        if isinstance(data, dict) and isinstance(data.get("user_preferences"), str):
            data["user_preferences"] = _json_dict(data.get("user_preferences"))
        return ChatRequest.model_validate(data), files

    raw = await request.body()
    if raw:
        try:
            return ChatRequest.model_validate(json.loads(raw.decode("utf-8"))), files
        except Exception:
            pass
    raise HTTPException(status_code=400, detail="Envia JSON o form-data con el campo `message`.")


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _memory_session_id(payload: ChatRequest) -> str:
    base = payload.user_id or payload.session_id or "default"
    if not payload.chat_id:
        return base[:128]
    digest = hashlib.sha1(f"{payload.session_id}:{payload.chat_id}".encode("utf-8")).hexdigest()[:16]
    return f"{base[:96]}:{digest}"


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    prefix = "bearer "
    if header.lower().startswith(prefix):
        return header[len(prefix) :].strip()
    return ""


def _apply_authenticated_context(request: Request, payload: ChatRequest) -> None:
    token = _bearer_token(request)
    if not token:
        payload.user_id = ""
        payload.user_email = ""
        payload.user_name = ""
        return
    try:
        session = auth_service.session_from_token(token)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Sesion no autenticada.")
    user = session.get("user") if isinstance(session.get("user"), dict) else {}
    payload.user_id = str(user.get("id") or "")
    payload.user_email = str(user.get("email") or "")
    payload.user_name = str(user.get("name") or "")
    session_preferences = session.get("preferences") if isinstance(session.get("preferences"), dict) else {}
    payload.user_preferences = {**session_preferences, **(payload.user_preferences or {})}


async def _handle_chat(request: Request) -> ChatResponse:
    payload, files = await _parse_chat_request(request)
    _apply_authenticated_context(request, payload)
    uploaded_sources: list[Source] = []
    memory_session_id = _memory_session_id(payload)

    for file in files:
        saved = await file_service.save_upload(file)
        uploaded_sources.append(
            Source(
                source=saved["filename"],
                title=saved["filename"],
                type="uploaded_file",
                text=f"Archivo guardado en {saved['path']}",
                metadata=saved,
            )
        )

    history_context = history_service.contextual_memory(
        memory_session_id,
        client_context_summary=payload.client_context_summary,
        user_preferences=payload.user_preferences,
    )
    if uploaded_sources:
        LOGGER.info("chat received %s uploaded files; they will be available after indexing", len(uploaded_sources))

    workflow_result = workflow_service.answer(
        payload,
        history_context=history_context,
        uploaded_sources=uploaded_sources,
    )
    answer = workflow_result.answer
    model = workflow_result.model
    sources = workflow_result.sources
    history_service.save_turn(
        session_id=memory_session_id,
        user_message=payload.message,
        ai_response=answer,
        sources=[source.model_dump(mode="json") for source in sources],
        metadata={
            "chat_id": payload.chat_id,
            "user_id": payload.user_id,
            "user_name": payload.user_name,
            "source": payload.source,
            "input_source": payload.input_source,
            "user_preferences": payload.user_preferences,
            "workflow": workflow_result.workflow,
        },
    )

    LOGGER.info("chat session=%s sources=%s model=%s", memory_session_id, len(sources), model)
    visible_sources = sources if payload.show_sources else sources[:4]
    return ChatResponse(
        answer=answer,
        sources=visible_sources,
        sources_used=[source.source for source in sources if source.source],
        session_id=memory_session_id,
        model=model,
        brain_parts=["fastapi_bridge", "history_json", *workflow_result.brain_parts],
        used_smart_search=workflow_result.used_smart_search,
        usedSmartSearch=workflow_result.used_smart_search,
        smart_search=workflow_result.smart_search,
        workflow=workflow_result.workflow,
        memory=history_service.memory_metadata(memory_session_id),
    )


@router.post("/api/chat", response_model=ChatResponse)
async def api_chat(request: Request) -> ChatResponse:
    return await _handle_chat(request)


@router.post("/api/ask", response_model=ChatResponse)
async def api_ask(request: Request) -> ChatResponse:
    return await _handle_chat(request)


@router.post("/ask", response_model=ChatResponse)
async def root_ask(request: Request) -> ChatResponse:
    return await _handle_chat(request)
