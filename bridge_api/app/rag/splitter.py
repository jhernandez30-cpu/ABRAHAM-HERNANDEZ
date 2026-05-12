from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.rag.loader import LoadedDocument


@dataclass(frozen=True)
class RagChunk:
    id: str
    text: str
    metadata: dict[str, Any]


class DocumentSplitter:
    def __init__(self) -> None:
        self._splitter = self._build_splitter()

    def split_documents(self, documents: list[LoadedDocument]) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for document in documents:
            parts = self._split_text(document.text)
            for index, text in enumerate(parts):
                clean_text = text.strip()
                if len(clean_text) < 30:
                    continue
                metadata = dict(document.metadata)
                metadata["chunk_index"] = index
                metadata["chunk_chars"] = len(clean_text)
                metadata["chunk_hash"] = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:16]
                chunk_id = self._chunk_id(metadata)
                chunks.append(RagChunk(id=chunk_id, text=clean_text, metadata=metadata))
        return chunks

    def _build_splitter(self):
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            return RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    "; ",
                    ", ",
                    " ",
                    "",
                ],
            )
        except Exception:
            return None

    def _split_text(self, text: str) -> list[str]:
        if self._splitter:
            return self._splitter.split_text(text)
        return self._fallback_split(text)

    def _fallback_split(self, text: str) -> list[str]:
        chunk_size = max(settings.chunk_size, 200)
        overlap = max(0, min(settings.chunk_overlap, chunk_size // 2))
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _chunk_id(self, metadata: dict[str, Any]) -> str:
        raw = "|".join(
            [
                str(metadata.get("source_path", "")),
                str(metadata.get("page", "")),
                str(metadata.get("chunk_index", "")),
                str(metadata.get("modified_at", "")),
                str(metadata.get("size", "")),
                str(metadata.get("chunk_hash", "")),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
