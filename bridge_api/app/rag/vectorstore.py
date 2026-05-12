from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.rag.embeddings import embedding_service
from app.rag.splitter import RagChunk


LOGGER = logging.getLogger(__name__)


class VectorStore:
    def __init__(self) -> None:
        settings.rag_persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(settings.rag_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = None

    @property
    def collection_name(self) -> str:
        return f"{settings.rag_collection_name}_{embedding_service.collection_suffix}"

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "embedding_backend": embedding_service.backend,
                    "embedding_model": embedding_service.model_name,
                    "dimension": embedding_service.dimension,
                },
            )
        return self._collection

    def count(self) -> int:
        try:
            return int(self.collection.count())
        except Exception as exc:
            LOGGER.warning("Could not count Chroma collection: %s", exc)
            return 0

    def reset(self) -> None:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None
        self.collection

    def index_chunks(self, chunks: list[RagChunk], skip_existing: bool = True) -> dict[str, int]:
        if not chunks:
            return {"indexed": 0, "skipped": 0}

        pending = chunks
        skipped = 0
        if skip_existing:
            existing_ids = self._existing_ids([chunk.id for chunk in chunks])
            changed_sources = {
                str(chunk.metadata.get("source") or "")
                for chunk in chunks
                if chunk.id not in existing_ids
            }
            changed_sources.discard("")
            if changed_sources:
                self._delete_sources(changed_sources)
                pending = [chunk for chunk in chunks if str(chunk.metadata.get("source") or "") in changed_sources]
            else:
                pending = []
            skipped = len(chunks) - len(pending)

        indexed = 0
        batch_size = max(1, settings.index_batch_size)
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            self.collection.upsert(
                ids=[chunk.id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                embeddings=embedding_service.embed_texts([chunk.text for chunk in batch]),
                metadatas=[self._sanitize_metadata(chunk.metadata) for chunk in batch],
            )
            indexed += len(batch)
            LOGGER.info("Indexed RAG chunk batch: %s/%s", indexed, len(pending))

        return {"indexed": indexed, "skipped": skipped}

    def query(self, query: str, k: int) -> dict[str, Any]:
        total = self.count()
        if total <= 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        n_results = min(max(k, 1), total)
        return self.collection.query(
            query_embeddings=[embedding_service.embed_text(query)],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def indexed_chunk_counts_by_source(self, limit: int = 100000) -> dict[str, int]:
        counts: dict[str, int] = {}
        try:
            result = self.collection.get(include=["metadatas"], limit=limit)
        except Exception as exc:
            LOGGER.warning("Could not list indexed sources: %s", exc)
            return counts
        for metadata in result.get("metadatas") or []:
            source = str(metadata.get("source") or "")
            if source:
                counts[source] = counts.get(source, 0) + 1
        return counts

    def _existing_ids(self, ids: list[str]) -> set[str]:
        existing: set[str] = set()
        batch_size = 500
        for start in range(0, len(ids), batch_size):
            batch = ids[start : start + batch_size]
            try:
                result = self.collection.get(ids=batch)
                existing.update(result.get("ids") or [])
            except Exception as exc:
                LOGGER.warning("Could not check existing Chroma ids: %s", exc)
        return existing

    def _delete_sources(self, sources: set[str]) -> None:
        for source in sources:
            try:
                self.collection.delete(where={"source": source})
            except Exception as exc:
                LOGGER.warning("Could not delete old chunks for %s: %s", source, exc)

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        clean: dict[str, str | int | float | bool] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                clean[key] = str(value)
        return clean


vector_store = VectorStore()
