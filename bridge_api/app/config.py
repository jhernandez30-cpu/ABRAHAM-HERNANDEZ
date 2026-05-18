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
    context_summary_path: Path = _path_from_env(
        "JAH_AI_CONTEXT_SUMMARY_PATH",
        BASE_DIR / "app" / "storage" / "context_summaries.json",
    )
    auth_users_path: Path = _path_from_env("JAH_AI_AUTH_USERS_PATH", BASE_DIR / "app" / "storage" / "auth_users.json")
    auth_sessions_path: Path = _path_from_env(
        "JAH_AI_AUTH_SESSIONS_PATH",
        BASE_DIR / "app" / "storage" / "auth_sessions.json",
    )
    auth_state_path: Path = _path_from_env("JAH_AI_AUTH_STATE_PATH", BASE_DIR / "app" / "storage" / "auth_state.json")

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
    rag_max_queries: int = int(os.getenv("JAH_AI_RAG_MAX_QUERIES", "3"))
    max_context_chars: int = int(os.getenv("JAH_AI_MAX_CONTEXT_CHARS", "9000"))
    chunk_size: int = int(os.getenv("JAH_AI_CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("JAH_AI_CHUNK_OVERLAP", "180"))
    index_batch_size: int = int(os.getenv("JAH_AI_INDEX_BATCH_SIZE", "64"))
    min_relevance_score: float = float(os.getenv("JAH_AI_MIN_RELEVANCE_SCORE", "0.18"))
    rag_score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", os.getenv("JAH_AI_RAG_SCORE_THRESHOLD", "0.72")))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", os.getenv("JAH_AI_RAG_TOP_K", "5")))
    rag_min_relevant_chunks: int = int(os.getenv("RAG_MIN_RELEVANT_CHUNKS", "1"))
    rag_max_context_chunks: int = int(os.getenv("RAG_MAX_CONTEXT_CHUNKS", "5"))
    tutor_ia_score_threshold: float = float(os.getenv("TUTOR_IA_SCORE_THRESHOLD", "0.72"))
    obsidian_score_threshold: float = float(os.getenv("OBSIDIAN_SCORE_THRESHOLD", "0.78"))
    official_sources_score_threshold: float = float(os.getenv("OFFICIAL_SOURCES_SCORE_THRESHOLD", "0.80"))
    recent_context_turns: int = int(os.getenv("JAH_AI_RECENT_CONTEXT_TURNS", "4"))
    context_summary_max_chars: int = int(os.getenv("JAH_AI_CONTEXT_SUMMARY_MAX_CHARS", "2800"))

    model_name: str = os.getenv("JAH_AI_MODEL", "llama3.2:1b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_timeout_seconds: int = int(os.getenv("JAH_AI_OLLAMA_TIMEOUT_SECONDS", "45"))
    ollama_num_ctx: int = int(os.getenv("JAH_AI_OLLAMA_NUM_CTX", "4096"))
    ollama_num_predict: int = int(os.getenv("JAH_AI_OLLAMA_NUM_PREDICT", "900"))
    ollama_temperature: float = float(os.getenv("JAH_AI_OLLAMA_TEMPERATURE", "0.2"))

    web_search_provider: str = os.getenv("WEB_SEARCH_PROVIDER", "tavily")
    web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
    web_search_timeout_seconds: float = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "12"))

    auth_frontend_url: str = os.getenv(
        "AUTH_FRONTEND_URL",
        "http://127.0.0.1:5500/asistente-programacion.html",
    )
    auth_session_ttl_hours: int = int(os.getenv("AUTH_SESSION_TTL_HOURS", "168"))
    auth_allow_file_return: bool = os.getenv("AUTH_ALLOW_FILE_RETURN", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8787/api/auth/google/callback",
    )
    google_oauth_scope: str = os.getenv("GOOGLE_OAUTH_SCOPE", "openid email profile")
    apple_client_id: str = os.getenv("APPLE_CLIENT_ID", "")
    apple_client_secret: str = os.getenv("APPLE_CLIENT_SECRET", "")
    apple_redirect_uri: str = os.getenv(
        "APPLE_REDIRECT_URI",
        "http://127.0.0.1:8787/api/auth/apple/callback",
    )
    apple_oauth_scope: str = os.getenv("APPLE_OAUTH_SCOPE", "name email")

    sqlserver_enabled: bool = os.getenv("SQLSERVER_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    sqlserver_host: str = os.getenv("SQLSERVER_HOST", "")
    sqlserver_port: str = os.getenv("SQLSERVER_PORT", "")
    sqlserver_database: str = os.getenv("SQLSERVER_DATABASE", "TUTORIA")
    sqlserver_driver: str = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    sqlserver_trusted_connection: bool = os.getenv("SQLSERVER_TRUSTED_CONNECTION", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    sqlserver_user: str = os.getenv("SQLSERVER_USER", "")
    sqlserver_password: str = os.getenv("SQLSERVER_PASSWORD", "")
    sqlserver_encrypt: bool = os.getenv("SQLSERVER_ENCRYPT", "true").strip().lower() in {"1", "true", "yes", "on"}
    sqlserver_trust_server_certificate: bool = os.getenv(
        "SQLSERVER_TRUST_SERVER_CERTIFICATE",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}
    sqlserver_pooling: bool = os.getenv("SQLSERVER_POOLING", "false").strip().lower() in {"1", "true", "yes", "on"}
    sqlserver_application_name: str = os.getenv("SQLSERVER_APPLICATION_NAME", "JAH AI Bridge Auth")
    sqlserver_connect_timeout_seconds: int = int(os.getenv("SQLSERVER_CONNECT_TIMEOUT_SECONDS", "5"))
    sqlserver_query_timeout_seconds: int = int(os.getenv("SQLSERVER_QUERY_TIMEOUT_SECONDS", "10"))

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
