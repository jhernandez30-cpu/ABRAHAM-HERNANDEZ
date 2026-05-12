from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings
from app.models.schemas import Source, SourceFile
from app.rag.embeddings import embedding_service
from app.rag.loader import DocumentLoader
from app.rag.rag_chain import RagResult, rag_chain
from app.rag.retriever import retriever
from app.rag.splitter import DocumentSplitter
from app.rag.vectorstore import vector_store


LOGGER = logging.getLogger(__name__)


class BrainService:
    def __init__(self) -> None:
        self.loader = DocumentLoader()
        self.splitter = DocumentSplitter()

    def health(self) -> dict[str, Any]:
        fragments = 0
        chroma_connected = False
        error = ""
        try:
            fragments = vector_store.count()
            chroma_connected = True
        except Exception as exc:
            error = str(exc)
            LOGGER.warning("RAG health check failed: %s", exc)

        source_count = 0
        markdown_count = 0
        if settings.knowledge_dir.exists():
            files = self.loader.list_files()
            source_count = len(files)
            markdown_count = sum(1 for item in files if item.extension == ".md")

        return {
            "root_exists": settings.tutor_ia_root.exists(),
            "root": str(settings.tutor_ia_root),
            "persist_dir": str(settings.rag_persist_dir),
            "persist_dir_exists": settings.rag_persist_dir.exists(),
            "knowledge_dir": str(settings.knowledge_dir),
            "knowledge_dir_exists": settings.knowledge_dir.exists(),
            "chroma_connected": chroma_connected,
            "collection": vector_store.collection_name,
            "fragments": fragments,
            "source_files": source_count,
            "markdown_notes": markdown_count,
            "embedding_backend": embedding_service.backend,
            "embedding_model": embedding_service.model_name,
            "embedding_dimension": embedding_service.dimension,
            "error": error,
        }

    def index_knowledge(self, *, force_reindex: bool = False, limit: int | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        settings.knowledge_dir.mkdir(parents=True, exist_ok=True)
        settings.rag_persist_dir.mkdir(parents=True, exist_ok=True)

        if force_reindex:
            LOGGER.info("Resetting RAG collection before indexing")
            vector_store.reset()

        documents_seen, documents = self.loader.load_documents(limit=limit)
        chunks = self.splitter.split_documents(documents)
        result = vector_store.index_chunks(chunks, skip_existing=not force_reindex)
        elapsed = round(time.perf_counter() - started, 3)
        LOGGER.info(
            "RAG indexing finished: files=%s docs=%s chunks=%s indexed=%s skipped=%s elapsed=%ss",
            documents_seen,
            len(documents),
            len(chunks),
            result["indexed"],
            result["skipped"],
            elapsed,
        )
        return {
            "documents_seen": documents_seen,
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "chunks_indexed": result["indexed"],
            "chunks_skipped": result["skipped"],
            "collection": vector_store.collection_name,
            "persist_dir": str(settings.rag_persist_dir),
            "embedding_backend": embedding_service.backend,
            "embedding_model": embedding_service.model_name,
            "duration_seconds": elapsed,
        }

    def list_sources(self) -> list[SourceFile]:
        files = self.loader.list_files()
        indexed_counts = vector_store.indexed_chunk_counts_by_source()
        updated: list[SourceFile] = []
        for file in files:
            data = file.model_dump()
            data["indexed_chunks"] = indexed_counts.get(file.relative_path, 0)
            updated.append(SourceFile(**data))
        return updated

    def search(self, query: str, k: int | None = None) -> list[Source]:
        return retriever.retrieve(query, k=k)

    def answer(self, question: str, *, history_context: str = "", k: int | None = None) -> RagResult:
        return rag_chain.answer(question, history_context=history_context, k=k)

    def build_context(self, query: str, k: int | None = None) -> tuple[str, list[Source]]:
        sources = self.search(query, k=k)
        return rag_chain.build_context(sources), sources

    def embed_text(self, text: str) -> list[float]:
        return embedding_service.embed_text(text)


brain_service = BrainService()
