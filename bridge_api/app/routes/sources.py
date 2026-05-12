from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import SourcesResponse
from app.services.brain_service import brain_service


router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources", response_model=SourcesResponse)
async def list_sources() -> SourcesResponse:
    files = brain_service.list_sources()
    return SourcesResponse(
        root=str(settings.knowledge_dir),
        supported_extensions=sorted(settings.allowed_extensions),
        files=files,
        count=len(files),
    )
