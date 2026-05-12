from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _path_from_env(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser()


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("JAH_AI_HOST", "127.0.0.1")
    port: int = int(os.getenv("JAH_AI_PORT", "8787"))
    log_level: str = os.getenv("JAH_AI_LOG_LEVEL", "INFO")

    tutor_ia_root: Path = _path_from_env("TUTOR_IA_ROOT", Path.home() / "Documents" / "tutor_ia")
    persist_dir: Path = _path_from_env(
        "TUTOR_IA_PERSIST_DIR",
        Path.home() / "Documents" / "tutor_ia" / "vectores" / "brain_db",
    )
    rag_persist_dir: Path = _path_from_env(
        "TUTOR_IA_RAG_PERSIST_DIR",
        Path.home() / "Documents" / "tutor_ia" / "vectores" / "jah_ai_rag",
    )
    knowledge_dir: Path = _path_from_env(
        "TUTOR_IA_KNOWLEDGE_DIR",
        Path.home() / "Documents" / "tutor_ia" / "conocimiento",
    )
    upload_dir: Path = _path_from_env(
        "JAH_AI_UPLOAD_DIR",
        Path.home() / "Documents" / "tutor_ia" / "conocimiento" / "_uploads",
    )
    history_path: Path = _path_from_env("JAH_AI_HISTORY_PATH", BASE_DIR / "app" / "storage" / "history.json")

    collection_name: str = os.getenv("TUTOR_IA_COLLECTION", "conocimiento_fast")
    rag_collection_name: str = os.getenv("JAH_AI_RAG_COLLECTION", "jah_ai_rag")
    embedding_backend: str = os.getenv("JAH_AI_EMBEDDING_BACKEND", "auto")
    embedding_model_name: str = os.getenv(
        "JAH_AI_EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2",
    )
    embed_dim: int = int(os.getenv("TUTOR_IA_EMBED_DIM", "384"))
    retrieve_candidates: int = int(os.getenv("JAH_AI_RETRIEVE_CANDIDATES", "8"))
    response_top_k: int = int(os.getenv("JAH_AI_RESPONSE_TOP_K", "4"))
    max_context_chars: int = int(os.getenv("JAH_AI_MAX_CONTEXT_CHARS", "9000"))
    chunk_size: int = int(os.getenv("JAH_AI_CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("JAH_AI_CHUNK_OVERLAP", "180"))
    index_batch_size: int = int(os.getenv("JAH_AI_INDEX_BATCH_SIZE", "64"))
    min_relevance_score: float = float(os.getenv("JAH_AI_MIN_RELEVANCE_SCORE", "0.18"))

    model_name: str = os.getenv("JAH_AI_MODEL", "llama3.2:1b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_timeout_seconds: int = int(os.getenv("JAH_AI_OLLAMA_TIMEOUT_SECONDS", "45"))
    ollama_num_ctx: int = int(os.getenv("JAH_AI_OLLAMA_NUM_CTX", "4096"))
    ollama_num_predict: int = int(os.getenv("JAH_AI_OLLAMA_NUM_PREDICT", "900"))
    ollama_temperature: float = float(os.getenv("JAH_AI_OLLAMA_TEMPERATURE", "0.2"))

    max_upload_bytes: int = int(os.getenv("JAH_AI_MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    allowed_extensions: set[str] = field(
        default_factory=lambda: {
            ".pdf",
            ".txt",
            ".docx",
            ".md",
            ".json",
            ".py",
            ".html",
            ".css",
            ".js",
            ".sql",
        }
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: _csv_env(
            "JAH_AI_ALLOWED_ORIGINS",
            "http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500,https://jhernandez30-cpu.github.io",
        )
    )
    allowed_origin_regex: str | None = os.getenv(
        "JAH_AI_ALLOWED_ORIGIN_REGEX",
        r"^https://jhernandez30-cpu\.github\.io$|^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    )


settings = Settings()
