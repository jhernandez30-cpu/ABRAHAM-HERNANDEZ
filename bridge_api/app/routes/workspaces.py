from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import WorkspaceItem, WorkspaceListResponse
from app.services.auth_service import AuthServiceError, auth_service
from app.services.workspace_service import projects_store, spaces_store


router = APIRouter(prefix="/api", tags=["workspaces"])


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


@router.get("/spaces", response_model=WorkspaceListResponse)
async def list_spaces(request: Request) -> WorkspaceListResponse:
    user_id, authenticated = _optional_user_id(request)
    items = spaces_store.list_items(user_id=user_id)
    return WorkspaceListResponse(authenticated=authenticated, items=items, count=len(items))


@router.post("/spaces", response_model=WorkspaceItem)
async def save_space(payload: WorkspaceItem, request: Request) -> WorkspaceItem:
    user_id, _ = _optional_user_id(request)
    return spaces_store.upsert(payload, user_id=user_id)


@router.get("/projects", response_model=WorkspaceListResponse)
async def list_projects(request: Request) -> WorkspaceListResponse:
    user_id, authenticated = _optional_user_id(request)
    items = projects_store.list_items(user_id=user_id)
    return WorkspaceListResponse(authenticated=authenticated, items=items, count=len(items))


@router.post("/projects", response_model=WorkspaceItem)
async def save_project(payload: WorkspaceItem, request: Request) -> WorkspaceItem:
    user_id, _ = _optional_user_id(request)
    return projects_store.upsert(payload, user_id=user_id)
