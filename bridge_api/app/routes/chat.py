from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.models.schemas import ChatRequest, ChatResponse, Source
from app.services.brain_service import brain_service
from app.services.file_service import file_service
from app.services.history_service import history_service


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
        for item in form.getlist("files"):
            if hasattr(item, "filename") and hasattr(item, "read"):
                files.append(item)
        return ChatRequest(
            message=message,
            session_id=session_id,
            project_path=project_path,
            show_sources=show_sources,
            k=k,
            top_k=top_k,
        ), files

    if "application/json" in content_type:
        data = await request.json()
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


async def _handle_chat(request: Request) -> ChatResponse:
    payload, files = await _parse_chat_request(request)
    uploaded_sources: list[Source] = []

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

    history_context = history_service.recent_context(payload.session_id)
    if uploaded_sources:
        LOGGER.info("chat received %s uploaded files; they will be available after indexing", len(uploaded_sources))

    rag_result = brain_service.answer(
        payload.message,
        history_context=history_context,
        k=payload.top_k or payload.k,
    )
    answer = rag_result.answer
    model = rag_result.model
    brain_sources = rag_result.sources
    sources = brain_sources + uploaded_sources
    history_service.save_turn(
        session_id=payload.session_id,
        user_message=payload.message,
        ai_response=answer,
        sources=[source.model_dump(mode="json") for source in sources],
    )

    LOGGER.info("chat session=%s sources=%s model=%s", payload.session_id, len(sources), model)
    visible_sources = sources if payload.show_sources else sources[:4]
    return ChatResponse(
        answer=answer,
        sources=visible_sources,
        sources_used=[source.source for source in sources if source.source],
        session_id=payload.session_id,
        model=model,
        brain_parts=["fastapi_bridge", "rag_chromadb", "history_json"],
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
