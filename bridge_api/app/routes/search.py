from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse
from app.services.brain_service import brain_service


router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(payload: SearchRequest) -> SearchResponse:
    results = brain_service.search(payload.query, k=payload.k)
    return SearchResponse(query=payload.query, results=results, count=len(results))
