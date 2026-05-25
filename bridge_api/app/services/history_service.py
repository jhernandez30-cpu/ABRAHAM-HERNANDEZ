from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import HistoryRecord, HistorySessionSummary
from app.services.supabase_service import supabase_service


LOGGER = logging.getLogger(__name__)
MEMORY_FACT_RE = re.compile(
    r"\b(prefiero|recuerda|ll[aá]mame|mi nombre|me gusta|quiero que|estoy trabajando|"
    r"vamos a trabajar|sin romper|mant[eé]n|no cambies|progreso|objetivo)\b",
    re.IGNORECASE,
)


class HistoryService:
    def __init__(self, path: Path, summary_path: Path) -> None:
        self.path = path
        self.summary_path = summary_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")
        if not self.summary_path.exists():
            self.summary_path.write_text("{}", encoding="utf-8")

    def get_history(self, session_id: str) -> list[HistoryRecord]:
        data = self._read()
        records = data.get(session_id, [])
        return [HistoryRecord(**record) for record in records]

    def list_sessions(self, user_id: str = "", limit: int = 40) -> list[HistorySessionSummary]:
        data = self._read()
        summaries: list[HistorySessionSummary] = []
        for session_id, raw_records in data.items():
            if not isinstance(raw_records, list) or not raw_records:
                continue
            records = [HistoryRecord(**record) for record in raw_records if isinstance(record, dict)]
            if not records:
                continue
            if user_id and not any(str(record.metadata.get("user_id") or "") == user_id for record in records):
                continue
            if not user_id and any(str(record.metadata.get("user_id") or "") for record in records):
                continue
            latest = max((record.created_at for record in records), default=None)
            title = self._compact_text(records[-1].user_message, 64) or "Historial backend"
            summaries.append(
                HistorySessionSummary(
                    session_id=session_id,
                    title=title,
                    turn_count=len(records),
                    updated_at=latest,
                    history=records[-20:],
                )
            )
        summaries.sort(key=lambda item: item.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return summaries[:limit]

    def get_summary(self, session_id: str) -> dict[str, Any]:
        summaries = self._read_json(self.summary_path)
        raw_summary = summaries.get(session_id, {})
        return raw_summary if isinstance(raw_summary, dict) else {}

    def save_turn(
        self,
        *,
        session_id: str,
        user_message: str,
        ai_response: str,
        sources: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> HistoryRecord:
        record = HistoryRecord(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            created_at=datetime.now(timezone.utc),
            sources=sources or [],
            metadata=metadata or {},
        )
        with self._lock:
            data = self._read()
            session_records = data.setdefault(session_id, [])
            session_records.append(record.model_dump(mode="json"))
            data[session_id] = session_records[-80:]
            self._write(data)
            self._write_summary(session_id, data[session_id])
        persistence = supabase_service.save_chat_turn(record.model_dump(mode="json"))
        if persistence.get("status") == "SUPABASE_POSTGRES_ERROR":
            LOGGER.warning("Postgres history persistence failed: %s", persistence.get("error", "unknown"))
        return record

    def recent_context(self, session_id: str, max_turns: int = 4) -> str:
        records = self.get_history(session_id)[-max_turns:]
        lines: list[str] = []
        for record in records:
            lines.append(f"Usuario: {record.user_message}")
            lines.append(f"JAH AI: {record.ai_response[:900]}")
        return "\n".join(lines)

    def contextual_memory(
        self,
        session_id: str,
        *,
        client_context_summary: str = "",
        user_preferences: dict[str, Any] | None = None,
        max_turns: int | None = None,
    ) -> str:
        max_turns = max_turns or settings.recent_context_turns
        sections: list[str] = []
        preferences_text = self._preferences_text(user_preferences or {})
        if preferences_text:
            sections.append("Preferencias actuales del usuario:\n" + preferences_text)

        summary = self.get_summary(session_id)
        summary_text = str(summary.get("summary") or "").strip()
        if summary_text:
            sections.append("Resumen persistente de la conversacion:\n" + summary_text)

        client_summary = self._compact_text(client_context_summary, settings.context_summary_max_chars)
        if client_summary:
            sections.append("Resumen enviado por la interfaz:\n" + client_summary)

        recent = self.recent_context(session_id, max_turns=max_turns).strip()
        if recent:
            sections.append("Ultimos turnos:\n" + recent)
        return "\n\n".join(sections)

    def memory_metadata(self, session_id: str) -> dict[str, Any]:
        summary = self.get_summary(session_id)
        return {
            "session_id": session_id,
            "summary_chars": len(str(summary.get("summary") or "")),
            "turn_count": int(summary.get("turn_count") or len(self.get_history(session_id))),
            "updated_at": summary.get("updated_at", ""),
        }

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            data = self._read_json(self.path)
            return data if isinstance(data, dict) else {}

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)

    def _write_summary(self, session_id: str, records: list[dict[str, Any]]) -> None:
        summaries = self._read_json(self.summary_path)
        previous = summaries.get(session_id, {}) if isinstance(summaries.get(session_id), dict) else {}
        summary = self._build_summary(records, previous)
        summaries[session_id] = summary
        tmp_path = self.summary_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.summary_path)

    def _build_summary(self, records: list[dict[str, Any]], previous: dict[str, Any]) -> dict[str, Any]:
        recent_records = records[-12:]
        facts = self._dedupe_keep_order(
            [str(item) for item in previous.get("memory_facts", []) if item]
            + self._extract_memory_facts(records[-30:])
        )[-10:]
        topics = self._dedupe_keep_order(self._extract_topics(records[-20:]))[-12:]
        source_names = self._dedupe_keep_order(self._extract_sources(records[-12:]))[:12]
        preferences = self._merge_preferences(records[-12:])

        progress_lines: list[str] = []
        for record in recent_records[-6:]:
            user = self._compact_text(record.get("user_message", ""), 220)
            answer = self._compact_text(record.get("ai_response", ""), 260)
            if user:
                progress_lines.append(f"- Usuario: {user}")
            if answer:
                progress_lines.append(f"  JAH AI: {answer}")

        sections: list[str] = []
        if preferences:
            sections.append("Preferencias conocidas: " + "; ".join(f"{key}={value}" for key, value in preferences.items()))
        if facts:
            sections.append("Datos a recordar:\n" + "\n".join(f"- {fact}" for fact in facts))
        if topics:
            sections.append("Temas recientes: " + ", ".join(topics))
        if progress_lines:
            sections.append("Progreso reciente:\n" + "\n".join(progress_lines))
        if source_names:
            sections.append("Fuentes usadas recientemente: " + ", ".join(source_names))

        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "turn_count": len(records),
            "memory_facts": facts,
            "topics": topics,
            "sources": source_names,
            "preferences": preferences,
            "summary": self._compact_text("\n\n".join(sections), settings.context_summary_max_chars),
        }

    def _merge_preferences(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        allowed_keys = {
            "visible_name",
            "response_style",
            "assistant_preference",
            "direct_answers",
            "chat_history_enabled",
            "use_rag",
            "use_web",
            "deep_thinking",
        }
        for record in records:
            metadata = record.get("metadata") if isinstance(record, dict) else {}
            preferences = metadata.get("user_preferences") if isinstance(metadata, dict) else {}
            if not isinstance(preferences, dict):
                continue
            for key in allowed_keys:
                value = preferences.get(key)
                if value not in (None, ""):
                    merged[key] = value
        return merged

    def _extract_memory_facts(self, records: list[dict[str, Any]]) -> list[str]:
        facts: list[str] = []
        for record in records:
            message = str(record.get("user_message") or "").strip()
            if message and MEMORY_FACT_RE.search(message):
                facts.append(self._compact_text(message, 220))
        return facts

    def _extract_topics(self, records: list[dict[str, Any]]) -> list[str]:
        topics: list[str] = []
        topic_re = re.compile(
            r"\b(RAG|Data Science|Bases de Datos|SQL Server|T-SQL|TUTORIA|SSMS|PostgreSQL|pl[_ -]?pgsql|SQL|Python|FastAPI|"
            r"ChromaDB|Ollama|JARVIS|JAH AI|TUTOR_IA|frontend|backend|API)\b",
            re.IGNORECASE,
        )
        for record in records:
            text = f"{record.get('user_message', '')} {record.get('ai_response', '')}"
            for match in topic_re.findall(text):
                topics.append(str(match).strip())
        return topics

    def _extract_sources(self, records: list[dict[str, Any]]) -> list[str]:
        source_names: list[str] = []
        for record in records:
            for source in record.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                name = source.get("source") or source.get("title") or source.get("url")
                if name:
                    source_names.append(str(name))
        return source_names

    def _preferences_text(self, preferences: dict[str, Any]) -> str:
        if not preferences:
            return ""
        interesting = {
            "visible_name": "Nombre visible",
            "response_style": "Estilo de respuesta",
            "assistant_preference": "Preferencia del asistente",
            "direct_answers": "Respuestas directas",
            "use_rag": "Usar RAG",
            "use_web": "Usar busqueda web",
            "deep_thinking": "Pensamiento profundo",
        }
        lines = []
        for key, label in interesting.items():
            value = preferences.get(key)
            if value not in (None, ""):
                lines.append(f"- {label}: {value}")
        return "\n".join(lines)

    def _compact_text(self, text: Any, max_chars: int) -> str:
        clean = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(clean) <= max_chars:
            return clean
        return clean[: max_chars - 3].rstrip() + "..."

    def _dedupe_keep_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            clean = self._compact_text(value, 240)
            key = clean.lower()
            if not clean or key in seen:
                continue
            seen.add(key)
            output.append(clean)
        return output

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError):
            return {}


history_service = HistoryService(settings.history_path, settings.context_summary_path)
