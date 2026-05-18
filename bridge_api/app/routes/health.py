from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.services.brain_service import brain_service


router = APIRouter(tags=["health"])


def health_payload() -> dict:
    brain = brain_service.health()
    brain_fragments = int(brain.get("fragments", 0) or 0)
    tutor_connected = bool(brain.get("root_exists")) and bool(brain.get("chroma_connected")) and brain_fragments > 0
    tutor_status = "CONNECTED" if tutor_connected else "DEGRADED" if brain.get("root_exists") else "DISCONNECTED"
    last_healthcheck = datetime.now(timezone.utc).isoformat()
    return {
        "ok": True,
        "success": True,
        "status": tutor_status,
        "bridge_status": "ok",
        "message": "JAH AI Bridge API funcionando correctamente",
        "mode": "local-fastapi-bridge",
        "model": settings.model_name,
        "fragments": brain_fragments,
        "tutor_connected": tutor_connected,
        "tutor_ia_connected": tutor_connected,
        "memory_persistence": True,
        "last_healthcheck": last_healthcheck,
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
            "score_threshold": settings.rag_score_threshold,
            "top_k": settings.rag_top_k,
            "min_relevant_chunks": settings.rag_min_relevant_chunks,
            "max_context_chunks": settings.rag_max_context_chunks,
            "tutor_ia_score_threshold": settings.tutor_ia_score_threshold,
            "obsidian_score_threshold": settings.obsidian_score_threshold,
            "official_sources_score_threshold": settings.official_sources_score_threshold,
            "embedding_backend": brain.get("embedding_backend", ""),
            "embedding_model": brain.get("embedding_model", ""),
        },
        "memory": {
            "history_path": str(settings.history_path),
            "context_summary_path": str(settings.context_summary_path),
            "recent_context_turns": settings.recent_context_turns,
            "summary_max_chars": settings.context_summary_max_chars,
        },
        "workflow": {
            "pattern": "plan_act_evaluate",
            "rag_max_queries": settings.rag_max_queries,
            "intent_classifier": True,
            "web_search_provider": settings.web_search_provider,
            "web_search_max_results": settings.web_search_max_results,
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
