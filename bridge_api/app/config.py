from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

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
    raw_path = os.getenv(name, str(default)).strip()
    if _current_app_env() == "production" and _looks_like_local_dev_path(raw_path):
        raw_path = str(default)
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _current_app_env() -> str:
    explicit_env = os.getenv("APP_ENV", "").strip().lower()
    if explicit_env:
        return explicit_env

    railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME", "").strip().lower()
    if railway_env:
        return "production" if railway_env in {"production", "prod"} else railway_env

    railway_markers = (
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_ID",
        "RAILWAY_DEPLOYMENT_ID",
        "RAILWAY_PUBLIC_DOMAIN",
    )
    if any(os.getenv(name) for name in railway_markers):
        return "production"

    return "development"


def _production_api_base_url() -> str:
    public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip().strip("/")
    if public_domain:
        return f"https://{public_domain}".rstrip("/")
    return "https://jah-ai-bridge-production.up.railway.app"


def _looks_like_local_dev_path(value: str) -> bool:
    normalized = str(value or "").replace("\\", "/").lower()
    return (
        normalized.startswith("/home/")
        or normalized.startswith("/users/")
        or normalized.startswith("c:/users/")
        or "/documentos/" in normalized
        or "/documents/" in normalized
    )


def _is_local_url(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    hostname = (parsed.hostname or "").lower()
    return hostname in {"localhost", "127.0.0.1", "::1"}


def _safe_api_base_url() -> str:
    configured = os.getenv("API_BASE_URL", "").strip().rstrip("/")
    if APP_ENV == "production":
        return configured if configured and not _is_local_url(configured) else _production_api_base_url()
    return configured or "http://127.0.0.1:8787"


def _safe_host() -> str:
    configured = os.getenv("JAH_AI_HOST", "").strip()
    if APP_ENV == "production":
        return configured if configured and configured not in {"127.0.0.1", "localhost", "::1"} else "0.0.0.0"
    return configured or "127.0.0.1"


def _safe_frontend_url() -> str:
    configured = os.getenv("AUTH_FRONTEND_URL", os.getenv("FRONTEND_URL", "")).strip()
    if APP_ENV == "production":
        return configured if configured and not _is_local_url(configured) else _default_frontend_url()
    return configured or _default_frontend_url()


def _origin_from_value(value: str) -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
    except ValueError:
        return raw
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return raw


def _safe_allowed_origins() -> list[str]:
    origins = [_origin_from_value(item) for item in _csv_env(
        "JAH_AI_ALLOWED_ORIGINS",
        os.getenv("CORS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS),
    )]
    origins = [origin for origin in origins if origin]
    if APP_ENV != "production":
        return origins

    safe_origins = [
        origin
        for origin in origins
        if origin.startswith("https://") and not _is_local_url(origin) and origin != "*"
    ]
    github_origin = "https://jhernandez30-cpu.github.io"
    if github_origin not in safe_origins:
        safe_origins.insert(0, github_origin)
    return safe_origins


def _safe_allowed_origin_regex() -> str | None:
    configured = os.getenv("JAH_AI_ALLOWED_ORIGIN_REGEX", DEFAULT_ALLOWED_ORIGIN_REGEX)
    if APP_ENV != "production":
        return configured
    if not configured or "localhost" in configured or "127" in configured or configured.strip() in {".*", "*"}:
        return r"^https://jhernandez30-cpu\.github\.io$"
    return configured


def _default_development_tutor_root() -> Path:
    candidates = [
        Path.home() / "Documentos" / "tutor_ia",
        Path.home() / "Documents" / "tutor_ia",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _default_tutor_root() -> Path:
    if _current_app_env() == "production":
        return PROJECT_ROOT / "tutor_ia"
    return _default_development_tutor_root()


def _default_frontend_url() -> str:
    if _current_app_env() == "production":
        return "https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ"
    return "http://127.0.0.1:5500/asistente-programacion.html"


def _default_oauth_redirect(path: str) -> str:
    api_base_url = os.getenv("API_BASE_URL", "").strip().rstrip("/")
    if _current_app_env() == "production":
        return f"{api_base_url or _production_api_base_url()}{path}"
    return f"http://127.0.0.1:8787{path}"


def _default_ollama_base_url() -> str:
    if _current_app_env() == "production":
        return ""
    return "http://127.0.0.1:11434"


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


def _email_csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip().lower() for item in os.getenv(name, default).split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "")
    if not value:
        return default
    return int(value)


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


APP_ENV = _current_app_env()
DEFAULT_TUTOR_IA_ROOT = _path_from_env("TUTOR_IA_ROOT", _default_tutor_root())
DEFAULT_ALLOWED_ORIGINS = "https://jhernandez30-cpu.github.io" if APP_ENV == "production" else (
    "http://localhost,http://127.0.0.1,http://localhost:5500,"
    "http://127.0.0.1:5500,https://jhernandez30-cpu.github.io"
)
DEFAULT_ALLOWED_ORIGIN_REGEX = (
    r"^https://jhernandez30-cpu\.github\.io$"
    if APP_ENV == "production"
    else r"^https://jhernandez30-cpu\.github\.io$|^http://(localhost|127\.0\.0\.1)(:\d+)?$"
)


@dataclass(frozen=True)
class Settings:
    app_env: str = APP_ENV
    api_base_url: str = _safe_api_base_url()
    host: str = _safe_host()
    port: int = _int_env("PORT", _int_env("JAH_AI_PORT", 8787))
    log_level: str = os.getenv("JAH_AI_LOG_LEVEL", "INFO")

    tutor_ia_root: Path = DEFAULT_TUTOR_IA_ROOT
    persist_dir: Path = _path_from_env(
        "TUTOR_IA_PERSIST_DIR",
        DEFAULT_TUTOR_IA_ROOT / "vectores" / "brain_db",
    )
    rag_persist_dir: Path = _path_from_env(
        "TUTOR_IA_RAG_PERSIST_DIR",
        DEFAULT_TUTOR_IA_ROOT / "vectores" / "jah_ai_rag",
    )
    knowledge_dir: Path = _path_from_env(
        "TUTOR_IA_KNOWLEDGE_DIR",
        DEFAULT_TUTOR_IA_ROOT / "conocimiento",
    )
    upload_dir: Path = _path_from_env(
        "JAH_AI_UPLOAD_DIR",
        DEFAULT_TUTOR_IA_ROOT / "conocimiento" / "_uploads",
    )
    history_path: Path = _path_from_env("JAH_AI_HISTORY_PATH", BASE_DIR / "app" / "storage" / "history.json")
    context_summary_path: Path = _path_from_env(
        "JAH_AI_CONTEXT_SUMMARY_PATH",
        BASE_DIR / "app" / "storage" / "context_summaries.json",
    )
    spaces_path: Path = _path_from_env("JAH_AI_SPACES_PATH", BASE_DIR / "app" / "storage" / "spaces.json")
    projects_path: Path = _path_from_env("JAH_AI_PROJECTS_PATH", BASE_DIR / "app" / "storage" / "projects.json")
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

    model_provider: str = os.getenv("MODEL_PROVIDER", "ollama" if APP_ENV != "production" else "fallback").strip().lower()
    model_name: str = os.getenv("MODEL_NAME", os.getenv("JAH_AI_MODEL", "llama3.2:1b"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", _default_ollama_base_url()).rstrip("/")
    ollama_timeout_seconds: int = int(os.getenv("JAH_AI_OLLAMA_TIMEOUT_SECONDS", "45"))
    ollama_num_ctx: int = int(os.getenv("JAH_AI_OLLAMA_NUM_CTX", "4096"))
    ollama_num_predict: int = int(os.getenv("JAH_AI_OLLAMA_NUM_PREDICT", "900"))
    ollama_temperature: float = float(os.getenv("JAH_AI_OLLAMA_TEMPERATURE", "0.2"))

    web_search_provider: str = os.getenv("WEB_SEARCH_PROVIDER", "tavily")
    web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
    web_search_timeout_seconds: float = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "12"))

    auth_provider: str = os.getenv("AUTH_PROVIDER", "local").strip().lower() or "local"
    auth_frontend_url: str = _safe_frontend_url()
    auth_session_ttl_hours: int = int(os.getenv("AUTH_SESSION_TTL_HOURS", "168"))
    owner_email: str = os.getenv("OWNER_EMAIL", "").strip().lower()
    admin_emails: list[str] = field(
        default_factory=lambda: sorted(
            {
                *_email_csv_env("ADMIN_EMAILS", ""),
                *([os.getenv("OWNER_EMAIL", "").strip().lower()] if os.getenv("OWNER_EMAIL", "").strip() else []),
            }
        )
    )
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
        _default_oauth_redirect("/api/auth/google/callback"),
    )
    google_oauth_scope: str = os.getenv("GOOGLE_OAUTH_SCOPE", "openid email profile")
    apple_client_id: str = os.getenv("APPLE_CLIENT_ID", "")
    apple_client_secret: str = os.getenv("APPLE_CLIENT_SECRET", "")
    apple_redirect_uri: str = os.getenv(
        "APPLE_REDIRECT_URI",
        _default_oauth_redirect("/api/auth/apple/callback"),
    )
    apple_oauth_scope: str = os.getenv("APPLE_OAUTH_SCOPE", "name email")

    supabase_url: str = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "").strip()
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    supabase_google_enabled: bool = _bool_env("SUPABASE_GOOGLE_ENABLED", "false")
    supabase_apple_enabled: bool = _bool_env("SUPABASE_APPLE_ENABLED", "false")
    database_url: str = os.getenv("DATABASE_URL", "").strip()
    postgres_connect_timeout_seconds: int = int(os.getenv("POSTGRES_CONNECT_TIMEOUT_SECONDS", "8"))

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
    allowed_origins: list[str] = field(default_factory=_safe_allowed_origins)
    allowed_origin_regex: str | None = _safe_allowed_origin_regex()


settings = Settings()
