from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import IndexRequest, IndexResponse
from app.services.brain_service import brain_service


router = APIRouter(prefix="/api", tags=["rag"])


@router.post("/index", response_model=IndexResponse)
async def index_knowledge(payload: IndexRequest | None = None) -> IndexResponse:
    request = payload or IndexRequest()
    result = brain_service.index_knowledge(
        force_reindex=request.force_reindex,
        limit=request.limit,
    )
    return IndexResponse(
        message="Base de conocimiento RAG indexada correctamente",
        **result,
    )
