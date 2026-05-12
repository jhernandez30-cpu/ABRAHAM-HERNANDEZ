from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings


SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


class FileService:
    def __init__(self) -> None:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> dict:
        original_name = Path(file.filename or "archivo").name
        suffix = Path(original_name).suffix.lower()
        if suffix not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Extension no permitida: {suffix or 'sin extension'}",
            )

        content = await file.read()
        size = len(content)
        if size > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo supera el limite de {settings.max_upload_bytes} bytes.",
            )

        safe_stem = SAFE_NAME_RE.sub("_", Path(original_name).stem).strip("._") or "archivo"
        digest = hashlib.sha256(content).hexdigest()[:10]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        saved_name = f"{timestamp}_{safe_stem}_{digest}{suffix}"
        target = (settings.upload_dir / saved_name).resolve()
        upload_root = settings.upload_dir.resolve()
        if upload_root not in target.parents:
            raise HTTPException(status_code=400, detail="Ruta de archivo invalida.")

        target.write_bytes(content)
        return {
            "filename": original_name,
            "saved_as": saved_name,
            "path": str(target),
            "size": size,
            "content_type": file.content_type,
        }


file_service = FileService()
