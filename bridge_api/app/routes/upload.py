from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.models.schemas import UploadResponse
from app.services.file_service import file_service


router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    saved = await file_service.save_upload(file)
    return UploadResponse(**saved)
