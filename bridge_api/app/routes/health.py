from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.services.auth_service import AuthServiceError, auth_service
from app.services.brain_service import brain_service


router = APIRouter(tags=["health"])


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    prefix = "bearer "
    if header.lower().startswith(prefix):
        return header[len(prefix) :].strip()
    return ""


def _require_admin(request: Request) -> dict:
    try:
        session = auth_service.session_from_token(_bearer_token(request))
    except AuthServiceError as exc:
        raise HTTPException(status_code=401, detail="Sesion no autenticada.") from exc
    if not session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Sesion no autenticada.")
    user = session.get("user") or {}
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Estado tecnico disponible solo para administrador.")
    return session


def _tutor_status_from_brain(brain: dict) -> tuple[bool, str]:
    brain_fragments = int(brain.get("fragments", 0) or 0)
    tutor_connected = bool(brain.get("root_exists")) and bool(brain.get("chroma_connected")) and brain_fragments > 0
    tutor_status = "CONNECTED" if tutor_connected else "DEGRADED" if brain.get("root_exists") else "DISCONNECTED"
    return tutor_connected, tutor_status


def _public_path_status(exists: bool) -> str:
    return "available" if exists else "missing"


def health_payload() -> dict:
    last_healthcheck = datetime.now(timezone.utc).isoformat()
    tutor_connected = False
    tutor_status = "DISCONNECTED"
    fragments = 0
    root_exists = False
    knowledge_dir_exists = False
    persist_dir_exists = False
    try:
        brain = brain_service.health()
        fragments = int(brain.get("fragments", 0) or 0)
        tutor_connected, tutor_status = _tutor_status_from_brain(brain)
        root_exists = bool(brain.get("root_exists"))
        knowledge_dir_exists = bool(brain.get("knowledge_dir_exists"))
        persist_dir_exists = bool(brain.get("persist_dir_exists"))
    except Exception:
        tutor_status = "BACKEND_UNAVAILABLE"
    service_status = "ok" if tutor_connected else "degraded"

    return {
        "ok": True,
        "success": True,
        "status": service_status,
        "service": "tutor_ia",
        "bridge_status": "ok",
        "environment": settings.app_env,
        "auth_provider": settings.auth_provider,
        "supabase_auth_configured": bool(settings.supabase_url and settings.supabase_anon_key),
        "postgres_configured": bool(settings.database_url),
        "tutor_ia_status": tutor_status,
        "tutor_ia_connected": tutor_connected,
        "tutor_status": tutor_status,
        "fragments": fragments,
        "tutor_ia_root": _public_path_status(root_exists),
        "tutor_ia_root_available": root_exists,
        "knowledge_dir_available": knowledge_dir_exists,
        "rag_persist_dir_available": persist_dir_exists,
        "message": "JAH AI Bridge API funcionando correctamente",
        "mode": "local-fastapi-bridge",
        "timestamp": last_healthcheck,
        "last_healthcheck": last_healthcheck,
    }


def admin_system_status_payload() -> dict:
    brain = brain_service.health()
    brain_fragments = int(brain.get("fragments", 0) or 0)
    tutor_connected, tutor_status = _tutor_status_from_brain(brain)
    last_healthcheck = datetime.now(timezone.utc).isoformat()
    sqlserver_health = auth_service.sqlserver.health()
    sqlserver_status = str(sqlserver_health.get("status") or "DISABLED")
    return {
        "ok": True,
        "success": True,
        "status": "SYSTEM_READY" if tutor_connected else "DEGRADED",
        "system_status": "SYSTEM_READY" if tutor_connected else "TUTOR_IA_DISCONNECTED",
        "tutor_ia_status": tutor_status,
        "sqlserver_status": sqlserver_status,
        "memory_status": "LOADED",
        "rag_status": "READY" if brain_fragments > 0 else "RAG_DEGRADED",
        "bridge_status": "ok",
        "message": "JAH AI Bridge API funcionando correctamente",
        "mode": "local-fastapi-bridge",
        "model": settings.model_name,
        "fragments": brain_fragments,
        "tutor_connected": tutor_connected,
        "tutor_ia_connected": tutor_connected,
        "database": sqlserver_status,
        "sqlserver": sqlserver_health,
        "memory_persistence": True,
        "timestamp": last_healthcheck,
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


@router.get("/api/admin/system-status")
async def admin_system_status(request: Request) -> dict:
    _require_admin(request)
    return admin_system_status_payload()
