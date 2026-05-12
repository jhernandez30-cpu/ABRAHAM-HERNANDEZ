from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import HistoryRecord


class HistoryService:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def get_history(self, session_id: str) -> list[HistoryRecord]:
        data = self._read()
        records = data.get(session_id, [])
        return [HistoryRecord(**record) for record in records]

    def save_turn(
        self,
        *,
        session_id: str,
        user_message: str,
        ai_response: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> HistoryRecord:
        record = HistoryRecord(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            created_at=datetime.now(timezone.utc),
            sources=sources or [],
        )
        with self._lock:
            data = self._read()
            session_records = data.setdefault(session_id, [])
            session_records.append(record.model_dump(mode="json"))
            data[session_id] = session_records[-80:]
            self._write(data)
        return record

    def recent_context(self, session_id: str, max_turns: int = 4) -> str:
        records = self.get_history(session_id)[-max_turns:]
        lines: list[str] = []
        for record in records:
            lines.append(f"Usuario: {record.user_message}")
            lines.append(f"JAH AI: {record.ai_response[:900]}")
        return "\n".join(lines)

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8") or "{}")
            except (OSError, json.JSONDecodeError):
                return {}

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)


history_service = HistoryService(settings.history_path)
