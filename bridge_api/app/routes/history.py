from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import HistoryResponse, HistorySaveRequest
from app.services.history_service import history_service


router = APIRouter(prefix="/api", tags=["history"])


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
