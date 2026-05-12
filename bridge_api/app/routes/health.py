from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.services.brain_service import brain_service


router = APIRouter(tags=["health"])


def health_payload() -> dict:
    brain = brain_service.health()
    return {
        "ok": True,
        "success": True,
        "status": "ok",
        "message": "JAH AI Bridge API funcionando correctamente",
        "mode": "local-fastapi-bridge",
        "model": settings.model_name,
        "fragments": brain.get("fragments", 0),
        "tutor_ia_connected": bool(brain.get("root_exists")),
        "root_dir": str(settings.tutor_ia_root),
        "brain": {
            "mode": "rag-local",
            "root": str(settings.tutor_ia_root),
            "fragments": brain.get("fragments", 0),
            "local_sources": brain.get("fragments", 0),
            "obsidian_notes": brain.get("markdown_notes", 0),
            "active_model": settings.model_name,
            "chroma_connected": brain.get("chroma_connected", False),
            "collection": brain.get("collection", ""),
            "source_files": brain.get("source_files", 0),
            "embedding_backend": brain.get("embedding_backend", ""),
            "embedding_model": brain.get("embedding_model", ""),
            "embedding_dimension": brain.get("embedding_dimension", 0),
        },
        "rag": {
            "knowledge_dir": str(settings.knowledge_dir),
            "persist_dir": str(settings.rag_persist_dir),
            "collection": brain.get("collection", ""),
            "indexed_fragments": brain.get("fragments", 0),
            "source_files": brain.get("source_files", 0),
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "min_relevance_score": settings.min_relevance_score,
            "embedding_backend": brain.get("embedding_backend", ""),
            "embedding_model": brain.get("embedding_model", ""),
        },
        "obsidian": {
            "path": str(settings.knowledge_dir),
            "notes": brain.get("markdown_notes", 0),
            "available": brain.get("knowledge_dir_exists", False),
        },
        "uploads": {
            "path": str(settings.upload_dir),
            "max_upload_bytes": settings.max_upload_bytes,
            "allowed_extensions": sorted(settings.allowed_extensions),
        },
    }


@router.get("/api/health")
async def api_health() -> dict:
    return health_payload()


@router.get("/health")
async def root_health() -> dict:
    return health_payload()


@router.get("/api/status")
async def api_status() -> dict:
    return health_payload()


@router.get("/status")
async def root_status() -> dict:
    return health_payload()
