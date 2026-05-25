from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import HistoryListResponse, HistoryResponse, HistorySaveRequest
from app.services.auth_service import AuthServiceError, auth_service
from app.services.history_service import history_service


router = APIRouter(prefix="/api", tags=["history"])


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    prefix = "bearer "
    if header.lower().startswith(prefix):
        return header[len(prefix) :].strip()
    return ""


def _optional_user_id(request: Request) -> tuple[str, bool]:
    token = _bearer_token(request)
    if not token:
        return "", False
    try:
        session = auth_service.session_from_token(token)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Sesion no autenticada.")
    user = session.get("user") if isinstance(session.get("user"), dict) else {}
    return str(user.get("id") or ""), True


@router.get("/history", response_model=HistoryListResponse)
async def list_history(request: Request) -> HistoryListResponse:
    user_id, authenticated = _optional_user_id(request)
    sessions = history_service.list_sessions(user_id=user_id)
    message = "Historial backend cargado." if sessions else (
        "No hay historial backend para este usuario." if authenticated else "Modo invitado: usa historial local del navegador."
    )
    return HistoryListResponse(authenticated=authenticated, history=sessions, count=len(sessions), message=message)


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str) -> HistoryResponse:
    return HistoryResponse(session_id=session_id, history=history_service.get_history(session_id))


@router.post("/history", response_model=HistoryResponse)
async def save_history(payload: HistorySaveRequest) -> HistoryResponse:
    history_service.save_turn(
        session_id=payload.session_id,
        user_message=payload.user_message,
        ai_response=payload.ai_response,
        sources=payload.sources,
        metadata=payload.metadata,
    )
    return HistoryResponse(session_id=payload.session_id, history=history_service.get_history(payload.session_id))
