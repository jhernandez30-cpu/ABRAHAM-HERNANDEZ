from __future__ import annotations

import hashlib
import logging
import math
import re
import threading
from typing import Any

from app.config import settings


LOGGER = logging.getLogger(__name__)
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class EmbeddingService:
    def __init__(self) -> None:
        self.backend = "not-loaded"
        self.model_name = settings.embedding_model_name
        self.dimension = settings.embed_dim
        self._embedder: Any = None
        self._lock = threading.RLock()

    @property
    def collection_suffix(self) -> str:
        self._ensure_loaded()
        return re.sub(r"[^a-z0-9_]+", "_", self.backend.lower()).strip("_") or "local"

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._ensure_loaded()
        if self.backend == "sentence-transformers":
            vectors = self._embedder.encode(texts, normalize_embeddings=True)
            return [self._to_float_list(vector) for vector in vectors]
        if self.backend == "chroma-default":
            vectors = self._embedder(texts)
            return [self._to_float_list(vector) for vector in vectors]
        return [self._hash_embedding(text) for text in texts]

    def _ensure_loaded(self) -> None:
        if self._embedder is not None:
            return
        with self._lock:
            if self._embedder is not None:
                return
            requested = settings.embedding_backend.strip().lower()
            errors: list[str] = []
            existing_backend = self._existing_collection_backend() if requested == "auto" else ""
            if existing_backend == "sentence-transformers":
                if self._try_sentence_transformers(errors):
                    return
            if existing_backend == "chroma-default":
                if self._try_chroma_default(errors):
                    return
            if existing_backend == "hash-local":
                self.backend = "hash-local"
                self.model_name = "hashing-vectorizer"
                self.dimension = settings.embed_dim
                self._embedder = self._hash_embedding
                LOGGER.info("Embedding backend ready from existing collection: %s", self.backend)
                return
            if requested in {"auto", "sentence-transformers", "sentence_transformers"}:
                if self._try_sentence_transformers(errors):
                    return
            if requested in {"auto", "chroma", "chromadb", "default", "onnx"}:
                if self._try_chroma_default(errors):
                    return
            self.backend = "hash-local"
            self.model_name = "hashing-vectorizer"
            self.dimension = settings.embed_dim
            self._embedder = self._hash_embedding
            if errors:
                LOGGER.warning("Using hash embeddings after failures: %s", " | ".join(errors))

    def _existing_collection_backend(self) -> str:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            client = chromadb.PersistentClient(
                path=str(settings.rag_persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            candidates = {
                f"{settings.rag_collection_name}_chroma_default": "chroma-default",
                f"{settings.rag_collection_name}_sentence_transformers": "sentence-transformers",
                f"{settings.rag_collection_name}_hash_local": "hash-local",
            }
            counts: dict[str, int] = {}
            for collection in client.list_collections():
                if collection.name in candidates:
                    counts[candidates[collection.name]] = int(collection.count())
            for backend in ("chroma-default", "sentence-transformers", "hash-local"):
                if counts.get(backend, 0) > 0:
                    LOGGER.info("Detected existing non-empty RAG collection for backend: %s", backend)
                    return backend
        except Exception as exc:
            LOGGER.debug("Could not inspect existing RAG collections: %s", exc)
        return ""

    def _try_sentence_transformers(self, errors: list[str]) -> bool:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(settings.embedding_model_name)
            self.backend = "sentence-transformers"
            self.model_name = settings.embedding_model_name
            self.dimension = int(model.get_sentence_embedding_dimension())
            self._embedder = model
            LOGGER.info("Embedding backend ready: %s (%s)", self.backend, self.model_name)
            return True
        except Exception as exc:
            errors.append(f"sentence-transformers: {exc}")
            return False

    def _try_chroma_default(self, errors: list[str]) -> bool:
        try:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            embedder = DefaultEmbeddingFunction()
            probe = embedder(["dimension probe"])
            self.backend = "chroma-default"
            self.model_name = "all-MiniLM-L6-v2"
            self.dimension = len(self._to_float_list(probe[0])) if probe else settings.embed_dim
            self._embedder = embedder
            LOGGER.info("Embedding backend ready: %s (%s)", self.backend, self.model_name)
            return True
        except Exception as exc:
            errors.append(f"chroma-default: {exc}")
            return False

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * settings.embed_dim
        tokens = TOKEN_RE.findall((text or "").lower())
        if not tokens:
            return vector
        previous = ""
        for token in tokens:
            features = [token]
            if previous:
                features.append(f"{previous}_{token}")
            previous = token
            for feature in features:
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, "little", signed=False)
                index = value % settings.embed_dim
                vector[index] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return vector
        return [value / norm for value in vector]

    def _to_float_list(self, vector: Any) -> list[float]:
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        return [float(value) for value in vector]


embedding_service = EmbeddingService()
