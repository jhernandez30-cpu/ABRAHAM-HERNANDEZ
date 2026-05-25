from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.models.schemas import WorkspaceItem


class WorkspaceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list_items(self, user_id: str = "") -> list[WorkspaceItem]:
        items = [WorkspaceItem.model_validate(item) for item in self._read() if isinstance(item, dict)]
        if user_id:
            return [item for item in items if item.user_id == user_id]
        return [item for item in items if not item.user_id]

    def upsert(self, item: WorkspaceItem, user_id: str = "") -> WorkspaceItem:
        now = datetime.now(timezone.utc)
        clean = item.model_copy(update={
            "id": item.id or f"workspace-{int(now.timestamp() * 1000)}",
            "user_id": user_id or item.user_id,
            "createdAt": item.createdAt or now,
            "updatedAt": now,
        })
        with self._lock:
            items = [entry for entry in self._read() if isinstance(entry, dict)]
            replaced = False
            for index, existing in enumerate(items):
                if str(existing.get("id") or "") == clean.id:
                    items[index] = clean.model_dump(mode="json")
                    replaced = True
                    break
            if not replaced:
                items.insert(0, clean.model_dump(mode="json"))
            self._write(items[:500])
        return clean

    def _read(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _write(self, data: list[dict]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)


spaces_store = WorkspaceStore(settings.spaces_path)
projects_store = WorkspaceStore(settings.projects_path)
