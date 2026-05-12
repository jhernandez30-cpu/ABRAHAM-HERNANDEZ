from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import Source
from app.rag.vectorstore import vector_store


LOGGER = logging.getLogger(__name__)


class Retriever:
    def retrieve(self, query: str, k: int | None = None) -> list[Source]:
        clean_query = str(query or "").strip()
        if not clean_query:
            return []
        top_k = k or settings.response_top_k
        candidates = max(top_k * 3, settings.retrieve_candidates)
        try:
            result = vector_store.query(clean_query, candidates)
        except Exception as exc:
            LOGGER.warning("RAG retrieval failed: %s", exc)
            return []
        sources = self._result_to_sources(result)
        filtered = [
            source
            for source in sources
            if source.score is None or source.score >= settings.min_relevance_score
        ]
        return filtered[:top_k]

    def _result_to_sources(self, result: dict[str, Any]) -> list[Source]:
        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]
        sources: list[Source] = []
        if not documents or not documents[0]:
            return sources
        for index, document in enumerate(documents[0]):
            metadata = metadatas[0][index] if metadatas and metadatas[0] and index < len(metadatas[0]) else {}
            distance = distances[0][index] if distances and distances[0] and index < len(distances[0]) else None
            score = self._score_from_distance(distance)
            source_name = str(metadata.get("source") or metadata.get("file_name") or "")
            file_type = str(metadata.get("file_type") or Path(source_name).suffix or "").lstrip(".")
            page_value = metadata.get("page")
            sources.append(
                Source(
                    source=source_name,
                    title=str(metadata.get("title") or Path(source_name).stem or source_name),
                    type=file_type or "document",
                    page=int(page_value) if str(page_value or "").isdigit() else None,
                    score=score,
                    text=str(document or ""),
                    metadata=dict(metadata),
                )
            )
        return sources

    def _score_from_distance(self, distance: Any) -> float | None:
        if distance is None:
            return None
        try:
            score = 1.0 - float(distance)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, score))


retriever = Retriever()
