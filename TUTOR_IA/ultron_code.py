import os
import asyncio
import logging
import json
import sqlite3
import threading
import time
import hashlib
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    import openai
    from openai import AsyncOpenAI
    from openai.types.chat import ChatCompletionMessageParam
except ModuleNotFoundError:
    class _OpenAIShim:
        class APIError(Exception):
            pass

    openai = _OpenAIShim()
    AsyncOpenAI = None
    ChatCompletionMessageParam = Dict[str, Any]
try:
    import pyodbc
except ModuleNotFoundError:
    pyodbc = None
from dotenv import load_dotenv

# --- Configuration and Setup ---

# Load environment variables from a .env file
load_dotenv()

# Configure logging for informative output and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for API key and model names
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not configured. Runtime memory and tutor monitoring remain available.")

# Define the models to be used for different AI components
TUTOR_MODEL = "gpt-4o"  # General-purpose model for tutoring explanations
ASSISTANT_MODEL = "gpt-4o"  # General-purpose model for programming assistance and code generation
CODEX_ADJUSTER_MODEL = "gpt-4o" # Model specifically for code review, refinement, and adjustments
EMBEDDING_MODEL = "text-embedding-3-small" # Model for converting text into vector embeddings for RAG

# Default system prompts for each AI component to define their roles and behavior
TUTOR_SYSTEM_PROMPT = """
You are TutorIA, an empathetic and knowledgeable AI tutor. Your goal is to guide students
through complex topics, explain concepts clearly, provide examples, and help them
understand by asking probing questions. Always be supportive and encourage critical thinking.
When presented with external context, prioritize and synthesize that information to enrich your explanations.
"""

ASSISTANT_SYSTEM_PROMPT = """
You are ABRAHAM-HERNANDEZ-main, a highly skilled programming assistant. Your expertise
lies in generating, debugging, explaining, and refactoring code across various languages.
Provide clear, concise, and executable code examples. Explain your reasoning and
offer best practices. When presented with external context, use it to inform your
programming advice and code generation. Aim for idiomatic and efficient code.
"""

CODEX_ADJUSTER_SYSTEM_PROMPT = """
You are Codex Adjuster, an expert AI specialized in refining, correcting, and
optimizing code and programming-related explanations. Your task is to review provided
text, identify potential errors, improve clarity, ensure code correctness,
and apply modern best practices. Focus on syntax, logic, efficiency, and
readability. If the text contains code, make sure it's executable and idiomatic.
If given specific instructions for adjustment, follow them precisely and provide
only the adjusted content unless otherwise specified.
"""

# --- Utility Functions and Classes ---

ULTRON_BASE_DIR = Path(os.getenv("ULTRON_BASE_DIR", str(Path(__file__).resolve().parent)))
ULTRON_RUNTIME_DIR = Path(os.getenv("ULTRON_RUNTIME_DIR", str(ULTRON_BASE_DIR / "ultron_runtime")))
ULTRON_LOG_DIR = Path(os.getenv("ULTRON_LOG_DIR", str(ULTRON_BASE_DIR / "logs")))
ULTRON_MEMORY_DB = Path(os.getenv("ULTRON_MEMORY_DB", str(ULTRON_RUNTIME_DIR / "ultron_memory.sqlite3")))
TUTOR_HEALTH_URL = os.getenv("TUTOR_HEALTH_URL", "https://jah-ai-bridge-production.up.railway.app/api/health")
TUTOR_MONITOR_INTERVAL_SECONDS = float(os.getenv("TUTOR_MONITOR_INTERVAL_SECONDS", "20"))
TUTOR_HEALTH_TIMEOUT_SECONDS = float(os.getenv("TUTOR_HEALTH_TIMEOUT_SECONDS", "5"))
TUTOR_RECOVERY_MAX_ATTEMPTS = int(os.getenv("TUTOR_RECOVERY_MAX_ATTEMPTS", "4"))
TUTOR_RECOVERY_BACKOFF_SECONDS = float(os.getenv("TUTOR_RECOVERY_BACKOFF_SECONDS", "1.5"))
MAX_RECENT_MEMORY_MESSAGES = int(os.getenv("ULTRON_MAX_RECENT_MEMORY_MESSAGES", "16"))
MAX_CONTEXT_SUMMARY_CHARS = int(os.getenv("ULTRON_MAX_CONTEXT_SUMMARY_CHARS", "3200"))
DEFAULT_SESSION_ID = os.getenv("ULTRON_SESSION_ID", "default")
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.72"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_RELEVANT_CHUNKS = int(os.getenv("RAG_MIN_RELEVANT_CHUNKS", "1"))
RAG_MAX_CONTEXT_CHUNKS = int(os.getenv("RAG_MAX_CONTEXT_CHUNKS", "5"))
TUTOR_IA_SCORE_THRESHOLD = float(os.getenv("TUTOR_IA_SCORE_THRESHOLD", "0.72"))
OBSIDIAN_SCORE_THRESHOLD = float(os.getenv("OBSIDIAN_SCORE_THRESHOLD", "0.78"))
OFFICIAL_SOURCES_SCORE_THRESHOLD = float(os.getenv("OFFICIAL_SOURCES_SCORE_THRESHOLD", "0.80"))
SQLSERVER_HOST = os.getenv("SQLSERVER_HOST", "localhost")
SQLSERVER_PORT = os.getenv("SQLSERVER_PORT", "1433")
SQLSERVER_DATABASE = os.getenv("SQLSERVER_DATABASE", "TUTORIA")
SQLSERVER_USER = os.getenv("SQLSERVER_USER", "")
SQLSERVER_PASSWORD = os.getenv("SQLSERVER_PASSWORD", "")
SQLSERVER_DRIVER = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
SQLSERVER_TRUSTED_CONNECTION = os.getenv("SQLSERVER_TRUSTED_CONNECTION", "false").strip().lower() in {"1", "true", "yes", "on"}
SQLSERVER_ENCRYPT = os.getenv("SQLSERVER_ENCRYPT", "true").strip().lower() in {"1", "true", "yes", "on"}
SQLSERVER_TRUST_SERVER_CERTIFICATE = os.getenv("SQLSERVER_TRUST_SERVER_CERTIFICATE", "true").strip().lower() in {"1", "true", "yes", "on"}
SQLSERVER_CONNECT_TIMEOUT_SECONDS = int(os.getenv("SQLSERVER_CONNECT_TIMEOUT_SECONDS", "5"))
SQLSERVER_QUERY_TIMEOUT_SECONDS = int(os.getenv("SQLSERVER_QUERY_TIMEOUT_SECONDS", "10"))
SQLSERVER_MAX_RETRIES = int(os.getenv("SQLSERVER_MAX_RETRIES", "3"))
SQLSERVER_BACKOFF_SECONDS = float(os.getenv("SQLSERVER_BACKOFF_SECONDS", "1.5"))
SQLSERVER_ENABLED = os.getenv("SQLSERVER_ENABLED", "auto").strip().lower() in {"1", "true", "yes", "on", "auto"}
SQLSERVER_HEALTH_CACHE_SECONDS = float(os.getenv("SQLSERVER_HEALTH_CACHE_SECONDS", "15"))
SQLSERVER_POOLING = os.getenv("SQLSERVER_POOLING", "false").strip().lower() in {"1", "true", "yes", "on"}
SQLSERVER_APPLICATION_NAME = os.getenv("SQLSERVER_APPLICATION_NAME", "ULTRON tutor_ia integration")

if pyodbc is not None:
    pyodbc.pooling = SQLSERVER_POOLING


class TutorStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    RECOVERING = "RECOVERING"


class DatabaseStatus(str, Enum):
    DB_CONNECTED = "DB_CONNECTED"
    DB_DISCONNECTED = "DB_DISCONNECTED"
    DB_RECONNECTING = "DB_RECONNECTING"
    DB_SCHEMA_INVALID = "DB_SCHEMA_INVALID"
    DB_AUTH_ERROR = "DB_AUTH_ERROR"


class UserIntent(str, Enum):
    GREETING = "GREETING"
    SOCIAL_RESPONSE = "SOCIAL_RESPONSE"
    CONTINUATION = "CONTINUATION"
    MEMORY_QUERY = "MEMORY_QUERY"
    GENERAL_TECHNICAL_HELP = "GENERAL_TECHNICAL_HELP"
    GENERAL_CREATIVE_TASK = "GENERAL_CREATIVE_TASK"
    CODE_GENERATION_TASK = "CODE_GENERATION_TASK"
    PROJECT_PLANNING_TASK = "PROJECT_PLANNING_TASK"
    DOCUMENT_GROUNDED_QUERY = "DOCUMENT_GROUNDED_QUERY"
    RAG_REQUIRED_QUERY = "RAG_REQUIRED_QUERY"
    DATABASE_QUERY = "DATABASE_QUERY"
    EXTERNAL_KNOWLEDGE_QUERY = "EXTERNAL_KNOWLEDGE_QUERY"


class RagMode(str, Enum):
    NONE = "RAG_NONE"
    OPTIONAL = "RAG_OPTIONAL"
    REQUIRED = "RAG_REQUIRED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_text(text: Any, max_chars: int = 500) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def session_hash(session_id: str) -> str:
    return hashlib.sha256(str(session_id or "default").encode("utf-8")).hexdigest()[:12]


def normalize_intent_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text)


def classify_user_intent(message: str) -> UserIntent:
    normalized = normalize_intent_text(message)
    compact = re.sub(r"[!?.;,\s]+$", "", normalized).strip()
    greetings = {
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hey",
        "hello",
        "hi",
        "que tal",
        "como estas",
        "como va",
    }
    social = {
        "gracias",
        "muchas gracias",
        "ok",
        "okay",
        "perfecto",
        "entendido",
        "excelente",
        "genial",
        "listo",
        "vale",
        "de acuerdo",
    }
    if not compact:
        return UserIntent.SOCIAL_RESPONSE
    if compact in greetings or (len(compact.split()) <= 4 and any(compact.startswith(item) for item in greetings)):
        return UserIntent.GREETING
    if compact in social or (len(compact.split()) <= 4 and any(compact.startswith(item) for item in social)):
        return UserIntent.SOCIAL_RESPONSE
    if re.search(r"\b(busca informacion actual|busca en internet|fuentes oficiales|documentacion oficial|latest|mas reciente|ultima version|busca en la web|consulta la web)\b", normalized):
        return UserIntent.EXTERNAL_KNOWLEDGE_QUERY
    if re.search(r"\b(recuerdame|que habiamos|que definimos|donde quedamos|historial|memoria|preferencia|carpeta usamos|progreso)\b", normalized):
        return UserIntent.MEMORY_QUERY
    if re.search(r"\b(solo con|unicamente con|estrictamente con|cita fuentes|con fuentes|evidencia documental)\b", normalized):
        return UserIntent.RAG_REQUIRED_QUERY
    if re.search(r"\b(que dice|segun|basado en|con base en|revisa|consulta|lee|usa|busca en|recupera).{0,80}(documento|documentos|archivo|archivos|pdf|notas|obsidian|vault|tutor_ia|tutoria|base de conocimiento|memoria)\b|\b(documento cargado|documentos cargados|mis notas|mis documentos|mi vault|contenido de tutor_ia|segun tutoria)\b", normalized):
        return UserIntent.DOCUMENT_GROUNDED_QUERY
    if re.search(r"\b(sql server|t-sql|tutoria|tutoria\.sql|ssms|sqlserver|base de datos|sesiones|session_id|memoria persistente|historial|procedimiento almacenado|stored procedure)\b", normalized):
        return UserIntent.DATABASE_QUERY
    if re.search(r"\b(sigue|continua|continuemos|corrige eso|arregla eso|agregalo|anadelo|lo anterior|esa parte)\b", normalized):
        return UserIntent.CONTINUATION
    if re.search(r"\b(crea|generame|genera|escribe|implementa|haz|construye|arma).{0,80}\b(codigo|html|css|js|javascript|python|api|endpoint|componente|script|funcion|clase|sitio web|pagina|landing|prompt|codex)\b", normalized):
        return UserIntent.CODE_GENERATION_TASK
    if re.search(r"\b(ideas|propone|propon|disena|disena|copy|texto|contenido|landing page|marca|estilo|secciones|hero|panaderia|negocio|sitio web)\b", normalized):
        return UserIntent.GENERAL_CREATIVE_TASK
    if re.search(r"\b(plan|arquitectura|estructura|roadmap|flujo|estrategia|organiza|secciones|mapa|proyecto|sitio web|landing)\b", normalized):
        return UserIntent.PROJECT_PLANNING_TASK
    if re.search(r"\b(codigo|programa|programacion|python|javascript|html|css|api|endpoint|bug|error|debug|funcion|clase|script|sql server|t-sql|tutoria|rag|embedding|backend|frontend|workflow|orquestacion|integracion|ultron|asistente de programacion|prompt|codex|explica|como hacer|ayuda)\b", normalized):
        return UserIntent.GENERAL_TECHNICAL_HELP
    if len(normalized.split()) > 12:
        return UserIntent.GENERAL_TECHNICAL_HELP
    return UserIntent.SOCIAL_RESPONSE


def should_use_memory_only(message: str, conversation_state: str = "") -> bool:
    intent = classify_user_intent(message)
    if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE, UserIntent.MEMORY_QUERY}:
        return True
    return intent == UserIntent.CONTINUATION and bool(str(conversation_state or "").strip())


def should_use_external_sources(message: str) -> bool:
    return classify_user_intent(message) == UserIntent.EXTERNAL_KNOWLEDGE_QUERY


def should_use_rag(message: str, conversation_state: str = "") -> bool:
    return rag_mode_for_intent(classify_user_intent(message), conversation_state) != RagMode.NONE


def rag_mode_for_intent(intent: UserIntent, conversation_state: str = "") -> RagMode:
    if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE}:
        return RagMode.NONE
    if intent in {UserIntent.MEMORY_QUERY, UserIntent.DOCUMENT_GROUNDED_QUERY, UserIntent.RAG_REQUIRED_QUERY}:
        return RagMode.REQUIRED
    if intent == UserIntent.CONTINUATION and str(conversation_state or "").strip():
        return RagMode.NONE
    return RagMode.OPTIONAL


def route_response_strategy(intent: UserIntent, retrieval_result: List[Dict[str, Any]], conversation_state: str = "") -> str:
    rag_mode = rag_mode_for_intent(intent, conversation_state)
    if rag_mode == RagMode.NONE:
        return "DIRECT_RESPONSE"
    if retrieval_result:
        return "DOCUMENT_GROUNDED_RESPONSE"
    if rag_mode == RagMode.REQUIRED:
        return "DOCUMENT_INSUFFICIENT"
    return "GENERAL_ASSISTANT_RESPONSE"


def direct_conversation_answer(message: str, user_name: str = "Abraham") -> str:
    intent = classify_user_intent(message)
    name = user_name or "Abraham"
    if intent == UserIntent.GREETING:
        return f"Hola, {name}. Continuamos con ULTRON o con el asistente de programacion?"
    return "Con gusto. Continuamos cuando quieras."


def configure_ultron_logging() -> None:
    ULTRON_LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    runtime_log = ULTRON_LOG_DIR / "ultron_runtime.log"
    tutor_log = ULTRON_LOG_DIR / "tutor_connection.log"
    sqlserver_log = ULTRON_LOG_DIR / "sqlserver_connection.log"
    memory_log = ULTRON_LOG_DIR / "memory_persistence.log"

    existing_paths = {
        getattr(handler, "baseFilename", "")
        for handler in logging.getLogger().handlers
        if hasattr(handler, "baseFilename")
    }
    for path, target_logger in [
        (runtime_log, logger),
        (tutor_log, logging.getLogger("ultron.tutor_connection")),
        (sqlserver_log, logging.getLogger("ultron.sqlserver_connection")),
        (memory_log, logging.getLogger("ultron.memory_persistence")),
    ]:
        if str(path) in existing_paths:
            continue
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(formatter)
        target_logger.addHandler(handler)
        target_logger.setLevel(logging.INFO)


configure_ultron_logging()


@dataclass
class HealthcheckResult:
    status: TutorStatus
    ok: bool
    http_status: int = 0
    latency_ms: int = 0
    checked_at: str = ""
    error_type: str = ""
    error_message: str = ""
    payload: Optional[Dict[str, Any]] = None


@dataclass
class SqlServerHealthResult:
    status: DatabaseStatus
    ok: bool
    checked_at: str = ""
    latency_ms: int = 0
    database: str = SQLSERVER_DATABASE
    schema_valid: bool = False
    memory_table: str = ""
    message_table: str = ""
    error_type: str = ""
    error_message: str = ""


class ContextMemoryStore:
    """
    SQLite-backed contextual memory for ULTRON.
    Stores compact summaries and recent messages so sessions survive restarts.
    """

    def __init__(self, db_path: Path = ULTRON_MEMORY_DB) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=15, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS context_memory (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    recent_messages TEXT NOT NULL DEFAULT '[]',
                    context_summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    session_status TEXT NOT NULL DEFAULT 'ACTIVE'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tutor_connection_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL,
                    last_healthcheck TEXT,
                    last_healthy_at TEXT,
                    disconnected_since TEXT,
                    last_http_status INTEGER DEFAULT 0,
                    last_latency_ms INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    last_error_type TEXT DEFAULT '',
                    last_error_message TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tutor_status_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    http_status INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    downtime_seconds REAL DEFAULT 0,
                    error_type TEXT DEFAULT '',
                    error_message TEXT DEFAULT ''
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_context_memory_user ON context_memory(user_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_tutor_events_checked_at ON tutor_status_events(checked_at)")
            connection.commit()

    def load(self, session_id: str) -> Dict[str, Any]:
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM context_memory WHERE session_id = ?",
                (clean_session_id,),
            ).fetchone()
            if not row:
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO context_memory (
                        session_id, user_id, recent_messages, context_summary,
                        created_at, updated_at, session_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (clean_session_id, "", "[]", "", now, now, "ACTIVE"),
                )
                connection.commit()
                return {
                    "session_id": clean_session_id,
                    "user_id": "",
                    "recent_messages": [],
                    "summary": "",
                    "created_at": now,
                    "updated_at": now,
                    "session_status": "ACTIVE",
                    "memory_persistence": True,
                    "backend": "sqlite",
                }

            return {
                "session_id": row["session_id"],
                "user_id": row["user_id"] or "",
                "recent_messages": self._safe_json_list(row["recent_messages"]),
                "summary": row["context_summary"] or "",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "session_status": row["session_status"],
                "memory_persistence": True,
                "backend": "sqlite",
            }

    def save(
        self,
        session_id: str,
        summary: str,
        recent_messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        current = self.load(clean_session_id)
        now = utc_now()
        messages = self._sanitize_messages(recent_messages)
        summary = compact_text(summary, MAX_CONTEXT_SUMMARY_CHARS)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO context_memory (
                    session_id, user_id, recent_messages, context_summary,
                    created_at, updated_at, session_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    recent_messages = excluded.recent_messages,
                    context_summary = excluded.context_summary,
                    updated_at = excluded.updated_at,
                    session_status = excluded.session_status
                """,
                (
                    clean_session_id,
                    user_id if user_id is not None else current.get("user_id", ""),
                    json.dumps(messages, ensure_ascii=False),
                    summary,
                    current.get("created_at") or now,
                    now,
                    session_status,
                ),
            )
            connection.commit()
        logger.info(
            "context_memory_saved session=%s messages=%s summary_chars=%s",
            session_hash(clean_session_id),
            len(messages),
            len(summary),
        )
        return self.load(clean_session_id)

    def update(
        self,
        session_id: str,
        new_turn: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        current = self.load(session_id)
        messages = list(current.get("recent_messages") or [])
        summary = str(current.get("summary") or "")
        now = utc_now()

        user_message = compact_text(new_turn.get("user_message") or new_turn.get("user") or "", 4000)
        assistant_message = compact_text(
            new_turn.get("assistant_message") or new_turn.get("assistant_response") or new_turn.get("response") or "",
            5000,
        )
        source = compact_text(new_turn.get("source") or "chat", 80)
        if user_message:
            messages.append({"role": "user", "content": user_message, "created_at": now, "source": source})
        if assistant_message:
            messages.append({"role": "assistant", "content": assistant_message, "created_at": now, "source": source})

        if len(messages) > MAX_RECENT_MEMORY_MESSAGES:
            older = messages[: -MAX_RECENT_MEMORY_MESSAGES]
            messages = messages[-MAX_RECENT_MEMORY_MESSAGES:]
            summary = self._merge_summary(summary, older)

        return self.save(
            session_id=session_id,
            summary=summary,
            recent_messages=messages,
            user_id=user_id if user_id is not None else current.get("user_id", ""),
            session_status="ACTIVE",
        )

    def clear(self, session_id: str) -> None:
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM context_memory WHERE session_id = ?", (clean_session_id,))
            connection.commit()
        logger.info("context_memory_cleared session=%s", session_hash(clean_session_id))

    def record_status(self, result: HealthcheckResult, retry_count: int = 0, downtime_seconds: float = 0) -> Dict[str, Any]:
        checked_at = result.checked_at or utc_now()
        with self._lock, self._connect() as connection:
            previous = connection.execute("SELECT * FROM tutor_connection_state WHERE id = 1").fetchone()
            previous_status = previous["status"] if previous else ""
            previous_disconnected_since = previous["disconnected_since"] if previous else None
            last_healthy_at = previous["last_healthy_at"] if previous else None
            disconnected_since = previous_disconnected_since

            if result.status == TutorStatus.CONNECTED:
                last_healthy_at = checked_at
                disconnected_since = None
            elif result.status in {TutorStatus.DISCONNECTED, TutorStatus.RECOVERING, TutorStatus.DEGRADED}:
                if previous_status == TutorStatus.CONNECTED.value or not disconnected_since:
                    disconnected_since = checked_at

            connection.execute(
                """
                INSERT INTO tutor_connection_state (
                    id, status, last_healthcheck, last_healthy_at, disconnected_since,
                    last_http_status, last_latency_ms, retry_count,
                    last_error_type, last_error_message, updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    last_healthcheck = excluded.last_healthcheck,
                    last_healthy_at = excluded.last_healthy_at,
                    disconnected_since = excluded.disconnected_since,
                    last_http_status = excluded.last_http_status,
                    last_latency_ms = excluded.last_latency_ms,
                    retry_count = excluded.retry_count,
                    last_error_type = excluded.last_error_type,
                    last_error_message = excluded.last_error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    result.status.value,
                    checked_at,
                    last_healthy_at,
                    disconnected_since,
                    result.http_status,
                    result.latency_ms,
                    retry_count,
                    result.error_type,
                    compact_text(result.error_message, 240),
                    utc_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO tutor_status_events (
                    status, checked_at, success, http_status, latency_ms,
                    retry_count, downtime_seconds, error_type, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.status.value,
                    checked_at,
                    int(result.ok),
                    result.http_status,
                    result.latency_ms,
                    retry_count,
                    downtime_seconds,
                    result.error_type,
                    compact_text(result.error_message, 240),
                ),
            )
            connection.commit()

        tutor_logger = logging.getLogger("ultron.tutor_connection")
        tutor_logger.info(
            "tutor_status status=%s ok=%s http=%s latency_ms=%s retry=%s error_type=%s",
            result.status.value,
            result.ok,
            result.http_status,
            result.latency_ms,
            retry_count,
            result.error_type,
        )
        return self.status_snapshot()

    def status_snapshot(self) -> Dict[str, Any]:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM tutor_connection_state WHERE id = 1").fetchone()
            if not row:
                return {
                    "tutor_connected": False,
                    "memory_persistence": True,
                    "status": TutorStatus.DISCONNECTED.value,
                    "last_healthcheck": "",
                    "last_healthy_at": "",
                    "disconnected_since": "",
                    "retry_count": 0,
                    "last_http_status": 0,
                    "last_latency_ms": 0,
                    "last_error_type": "",
                    "last_error_message": "",
                    "downtime_seconds": 0,
                    "health_url": TUTOR_HEALTH_URL,
                }

            disconnected_since = row["disconnected_since"] or ""
            downtime_seconds = 0
            if disconnected_since and row["status"] != TutorStatus.CONNECTED.value:
                downtime_seconds = max(0, self._seconds_since(disconnected_since))

            return {
                "tutor_connected": row["status"] == TutorStatus.CONNECTED.value,
                "memory_persistence": True,
                "status": row["status"],
                "last_healthcheck": row["last_healthcheck"] or "",
                "last_healthy_at": row["last_healthy_at"] or "",
                "disconnected_since": disconnected_since,
                "retry_count": int(row["retry_count"] or 0),
                "last_http_status": int(row["last_http_status"] or 0),
                "last_latency_ms": int(row["last_latency_ms"] or 0),
                "last_error_type": row["last_error_type"] or "",
                "last_error_message": row["last_error_message"] or "",
                "downtime_seconds": downtime_seconds,
                "health_url": TUTOR_HEALTH_URL,
            }

    def _merge_summary(self, previous_summary: str, older_messages: List[Dict[str, Any]]) -> str:
        facts: List[str] = []
        for message in older_messages:
            role = message.get("role", "user")
            content = compact_text(message.get("content", ""), 300)
            if not content:
                continue
            important = bool(re.search(r"\b(prefiero|recuerda|objetivo|decision|sin romper|mantener|progreso|tutor_ia|RAG|API|backend|frontend)\b", content, re.IGNORECASE))
            if important or role == "user":
                facts.append(f"- {role}: {content}")
        merged = "\n".join(part for part in [previous_summary.strip(), "Resumen acumulado:", "\n".join(facts)] if part)
        return compact_text(merged, MAX_CONTEXT_SUMMARY_CHARS)

    def _sanitize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clean_messages: List[Dict[str, Any]] = []
        for message in messages[-MAX_RECENT_MEMORY_MESSAGES:]:
            clean_messages.append(
                {
                    "role": compact_text(message.get("role", "user"), 32),
                    "content": compact_text(message.get("content", ""), 5000),
                    "created_at": compact_text(message.get("created_at", utc_now()), 64),
                    "source": compact_text(message.get("source", "chat"), 80),
                }
            )
        return clean_messages

    def _safe_json_list(self, raw: str) -> List[Dict[str, Any]]:
        try:
            parsed = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict)]

    def _seconds_since(self, iso_timestamp: str) -> float:
        try:
            started = datetime.fromisoformat(iso_timestamp)
        except ValueError:
            return 0
        return (datetime.now(timezone.utc) - started).total_seconds()


class SqlServerTutoriaStore:
    """
    Optional SQL Server persistence layer for the active TUTORIA database.
    It introspects the real schema first and only uses compatible objects.
    """

    SESSION_ALIASES = {"sessionid", "conversationid", "chatsessionid", "chatid", "threadid"}
    USER_ALIASES = {"userid", "user", "usuarioid", "usuario"}
    SUMMARY_ALIASES = {"contextsummary", "contextualsummary", "chatsummary", "summary", "resumencontextual", "resumen"}
    RECENT_ALIASES = {"recentmessages", "messagesjson", "historyjson", "conversationjson", "mensajesrecientes"}
    ROLE_ALIASES = {"messagerole", "role", "sender", "autor", "rol"}
    CONTENT_ALIASES = {"messagecontent", "content", "message", "text", "body", "contenido", "mensaje"}
    CREATED_ALIASES = {"createdat", "createdon", "created", "timestamp", "fecha", "fechacreacion"}
    UPDATED_ALIASES = {"updatedat", "updatedon", "lastactivityat", "modifiedat", "fechaactualizacion"}
    STATUS_ALIASES = {"sessionstatus", "status", "state", "estado"}
    GOAL_ALIASES = {"lastusergoal", "usergoal", "goal", "objetivo", "ultimoobjetivo"}
    AGENT_STATE_ALIASES = {"lastagentstate", "agentstate", "assistantstate", "estadoagente"}

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_health = SqlServerHealthResult(
            status=DatabaseStatus.DB_DISCONNECTED,
            ok=False,
            checked_at="",
            error_type="NotChecked",
            error_message="SQL Server has not been checked yet.",
        )
        self._last_check_monotonic = 0.0
        self._schema_cache: Dict[str, Any] = {}
        self._pending_memory: Dict[str, Dict[str, Any]] = {}

    def get_connection(self):
        if not SQLSERVER_ENABLED:
            raise RuntimeError("SQL Server integration is disabled.")
        if pyodbc is None:
            raise ImportError("pyodbc is required for SQL Server integration. Install it with `pip install pyodbc`.")
        connection = pyodbc.connect(self._connection_string(), timeout=SQLSERVER_CONNECT_TIMEOUT_SECONDS)
        connection.timeout = SQLSERVER_QUERY_TIMEOUT_SECONDS
        return connection

    def check_health(self, force: bool = False) -> SqlServerHealthResult:
        with self._lock:
            if not force and self._last_health.checked_at:
                elapsed = time.monotonic() - self._last_check_monotonic
                if elapsed < SQLSERVER_HEALTH_CACHE_SECONDS:
                    return self._last_health

        checked_at = utc_now()
        started = time.perf_counter()
        if not SQLSERVER_ENABLED:
            return self._record_health(
                SqlServerHealthResult(
                    status=DatabaseStatus.DB_DISCONNECTED,
                    ok=False,
                    checked_at=checked_at,
                    error_type="Disabled",
                    error_message="SQL Server integration is disabled by SQLSERVER_ENABLED.",
                )
            )
        if pyodbc is None:
            return self._record_health(
                SqlServerHealthResult(
                    status=DatabaseStatus.DB_DISCONNECTED,
                    ok=False,
                    checked_at=checked_at,
                    error_type="MissingDependency",
                    error_message="pyodbc is not installed.",
                )
            )

        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                schema = self.load_database_schema_status(connection)
                latency_ms = int(round((time.perf_counter() - started) * 1000))
                status = DatabaseStatus.DB_CONNECTED if schema.get("schema_valid") else DatabaseStatus.DB_SCHEMA_INVALID
                result = SqlServerHealthResult(
                    status=status,
                    ok=status == DatabaseStatus.DB_CONNECTED,
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                    database=SQLSERVER_DATABASE,
                    schema_valid=bool(schema.get("schema_valid")),
                    memory_table=str(schema.get("memory_table") or ""),
                    message_table=str(schema.get("message_table") or ""),
                )
                self._flush_pending_memory(connection)
                return self._record_health(result)
        except Exception as exc:
            latency_ms = int(round((time.perf_counter() - started) * 1000))
            status = self._classify_exception(exc)
            return self._record_health(
                SqlServerHealthResult(
                    status=status,
                    ok=False,
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                    database=SQLSERVER_DATABASE,
                    error_type=type(exc).__name__,
                    error_message=compact_text(str(exc), 240),
                )
            )

    def reconnect_database(self) -> Dict[str, Any]:
        self._record_health(
            SqlServerHealthResult(
                status=DatabaseStatus.DB_RECONNECTING,
                ok=False,
                checked_at=utc_now(),
                error_type="RecoveryStarted",
                error_message="Attempting SQL Server reconnection.",
            )
        )
        for attempt in range(1, SQLSERVER_MAX_RETRIES + 1):
            result = self.check_health(force=True)
            if result.ok:
                snapshot = self.status_snapshot()
                snapshot["retry_count"] = attempt
                return snapshot
            time.sleep(SQLSERVER_BACKOFF_SECONDS * (2 ** (attempt - 1)))
        return self.status_snapshot()

    def load_database_schema_status(self, connection=None) -> Dict[str, Any]:
        created_connection = connection is None
        if created_connection:
            connection = self.get_connection()
        try:
            cursor = connection.cursor()
            table_columns: Dict[str, Dict[str, Any]] = {}
            cursor.execute(
                """
                SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_CATALOG = DB_NAME()
                ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
                """
            )
            for row in cursor.fetchall():
                table_key = f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}"
                table_columns.setdefault(table_key, {"columns": {}, "types": {}})
                table_columns[table_key]["columns"][self._normalize(row.COLUMN_NAME)] = str(row.COLUMN_NAME)
                table_columns[table_key]["types"][str(row.COLUMN_NAME)] = str(row.DATA_TYPE)

            routines = self._safe_fetch_names(
                cursor,
                """
                SELECT ROUTINE_SCHEMA, ROUTINE_NAME, ROUTINE_TYPE
                FROM INFORMATION_SCHEMA.ROUTINES
                ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
                """,
                ("ROUTINE_SCHEMA", "ROUTINE_NAME", "ROUTINE_TYPE"),
            )
            views = self._safe_fetch_names(
                cursor,
                """
                SELECT TABLE_SCHEMA, TABLE_NAME, 'VIEW' AS OBJECT_TYPE
                FROM INFORMATION_SCHEMA.VIEWS
                ORDER BY TABLE_SCHEMA, TABLE_NAME
                """,
                ("TABLE_SCHEMA", "TABLE_NAME", "OBJECT_TYPE"),
            )
            triggers = self._safe_fetch_names(
                cursor,
                """
                SELECT s.name AS TRIGGER_SCHEMA, t.name AS TRIGGER_NAME, 'TRIGGER' AS OBJECT_TYPE
                FROM sys.triggers t
                JOIN sys.objects o ON t.parent_id = o.object_id
                JOIN sys.schemas s ON o.schema_id = s.schema_id
                ORDER BY s.name, t.name
                """,
                ("TRIGGER_SCHEMA", "TRIGGER_NAME", "OBJECT_TYPE"),
            )

            memory_table = self._find_table(table_columns, [self.SESSION_ALIASES, self.SUMMARY_ALIASES])
            message_table = self._find_table(table_columns, [self.SESSION_ALIASES, self.ROLE_ALIASES, self.CONTENT_ALIASES])
            session_table = self._find_table(table_columns, [self.SESSION_ALIASES])
            schema_status = {
                "schema_valid": bool(memory_table or message_table),
                "database": SQLSERVER_DATABASE,
                "tables": sorted(table_columns.keys()),
                "routines": routines,
                "views": views,
                "triggers": triggers,
                "memory_table": memory_table,
                "message_table": message_table,
                "session_table": session_table,
                "memory_columns": self._memory_column_mapping(table_columns.get(memory_table, {})) if memory_table else {},
                "message_columns": self._message_column_mapping(table_columns.get(message_table, {})) if message_table else {},
                "table_columns": table_columns,
            }
            with self._lock:
                self._schema_cache = schema_status
            return schema_status
        finally:
            if created_connection and connection is not None:
                connection.close()

    def load_memory(self, session_id: str) -> Dict[str, Any]:
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        health = self.check_health()
        if health.status != DatabaseStatus.DB_CONNECTED:
            return {
                "session_id": clean_session_id,
                "memory_persistence": False,
                "backend": "sqlserver",
                "sqlserver_status": self.status_snapshot(),
            }

        try:
            with self.get_connection() as connection:
                schema = self._schema_cache or self.load_database_schema_status(connection)
                memory = self._load_memory_with_connection(connection, schema, clean_session_id)
                memory["sqlserver_status"] = self.status_snapshot()
                return memory
        except Exception as exc:
            self._record_exception(exc)
            return {
                "session_id": clean_session_id,
                "memory_persistence": False,
                "backend": "sqlserver",
                "sqlserver_status": self.status_snapshot(),
            }

    def save_memory(
        self,
        session_id: str,
        summary: str,
        recent_messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_status: str = "ACTIVE",
        queue_on_failure: bool = True,
    ) -> bool:
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        health = self.check_health()
        if health.status != DatabaseStatus.DB_CONNECTED:
            if queue_on_failure:
                self._queue_pending_memory(clean_session_id, summary, recent_messages, user_id, session_status)
            return False

        try:
            with self.get_connection() as connection:
                schema = self._schema_cache or self.load_database_schema_status(connection)
                ok = self._save_memory_with_connection(
                    connection,
                    schema,
                    clean_session_id,
                    summary,
                    recent_messages,
                    user_id,
                    session_status,
                )
                if ok:
                    connection.commit()
                elif queue_on_failure:
                    self._queue_pending_memory(clean_session_id, summary, recent_messages, user_id, session_status)
                return ok
        except Exception as exc:
            self._record_exception(exc)
            if queue_on_failure:
                self._queue_pending_memory(clean_session_id, summary, recent_messages, user_id, session_status)
            return False

    def append_turn(
        self,
        session_id: str,
        new_turn: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> bool:
        health = self.check_health()
        if health.status != DatabaseStatus.DB_CONNECTED:
            return False
        try:
            with self.get_connection() as connection:
                schema = self._schema_cache or self.load_database_schema_status(connection)
                ok = self._append_turn_with_connection(connection, schema, str(session_id or DEFAULT_SESSION_ID), new_turn, user_id)
                if ok:
                    connection.commit()
                return ok
        except Exception as exc:
            self._record_exception(exc)
            return False

    def clear_memory(self, session_id: str) -> bool:
        health = self.check_health()
        if health.status != DatabaseStatus.DB_CONNECTED:
            return False
        clean_session_id = str(session_id or DEFAULT_SESSION_ID)
        try:
            with self.get_connection() as connection:
                schema = self._schema_cache or self.load_database_schema_status(connection)
                cursor = connection.cursor()
                deleted_any = False
                for table_name, columns_key in [
                    (schema.get("memory_table"), "memory_columns"),
                    (schema.get("message_table"), "message_columns"),
                ]:
                    columns = schema.get(columns_key) or {}
                    session_column = columns.get("session_id")
                    if not table_name or not session_column:
                        continue
                    session_value = self._coerce_session_value(schema, table_name, session_column, clean_session_id)
                    if session_value is None:
                        continue
                    cursor.execute(
                        f"DELETE FROM {self._quote_table(table_name)} WHERE {self._quote_name(session_column)} = ?",
                        (session_value,),
                    )
                    deleted_any = True
                connection.commit()
                return deleted_any
        except Exception as exc:
            self._record_exception(exc)
            return False

    def execute_tutoria_procedure(self, procedure_name: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        health = self.check_health()
        if health.status != DatabaseStatus.DB_CONNECTED:
            return {"ok": False, "status": health.status.value, "error": "SQL Server is not connected."}
        schema = self._schema_cache
        routines = schema.get("routines") or []
        target = self._find_routine(procedure_name, routines)
        if not target:
            return {"ok": False, "status": DatabaseStatus.DB_SCHEMA_INVALID.value, "error": "Stored procedure not found in TUTORIA schema."}
        params = params or []
        placeholders = ", ".join("?" for _ in params)
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(f"EXEC {self._quote_table(target)} {placeholders}".strip(), tuple(params))
                rows = self._fetch_all_dicts(cursor) if cursor.description else []
                connection.commit()
                return {"ok": True, "procedure": target, "rows": rows}
        except Exception as exc:
            self._record_exception(exc)
            return {"ok": False, "status": self.status_snapshot().get("status"), "error": type(exc).__name__}

    def status_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            health = self._last_health
            schema = self._schema_cache
            pending_count = len(self._pending_memory)
        return {
            "configured": bool(SQLSERVER_ENABLED),
            "driver_available": pyodbc is not None,
            "status": health.status.value,
            "ok": bool(health.ok),
            "database": SQLSERVER_DATABASE,
            "host": self._safe_server_label(),
            "schema_valid": bool(health.schema_valid),
            "memory_table": health.memory_table or str(schema.get("memory_table") or ""),
            "message_table": health.message_table or str(schema.get("message_table") or ""),
            "last_healthcheck": health.checked_at,
            "latency_ms": health.latency_ms,
            "error_type": health.error_type,
            "error_message": health.error_message,
            "pending_sync_count": pending_count,
        }

    def _connection_string(self) -> str:
        server = SQLSERVER_HOST.strip()
        port = SQLSERVER_PORT.strip()
        if port and "\\" not in server and "," not in server:
            server = f"{server},{port}"
        parts = [
            f"DRIVER={{{SQLSERVER_DRIVER}}}",
            f"SERVER={server}",
            f"DATABASE={SQLSERVER_DATABASE}",
            f"Encrypt={'yes' if SQLSERVER_ENCRYPT else 'no'}",
            f"TrustServerCertificate={'yes' if SQLSERVER_TRUST_SERVER_CERTIFICATE else 'no'}",
            f"APP={SQLSERVER_APPLICATION_NAME}",
            f"Connection Timeout={SQLSERVER_CONNECT_TIMEOUT_SECONDS}",
        ]
        if SQLSERVER_TRUSTED_CONNECTION:
            parts.append("Trusted_Connection=yes")
        else:
            parts.extend([f"UID={SQLSERVER_USER}", f"PWD={SQLSERVER_PASSWORD}"])
        return ";".join(parts)

    def _load_memory_with_connection(self, connection, schema: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        summary = ""
        user_id = ""
        recent_messages: List[Dict[str, Any]] = []
        created_at = utc_now()
        updated_at = created_at
        session_status = "ACTIVE"
        cursor = connection.cursor()

        memory_table = schema.get("memory_table")
        memory_columns = schema.get("memory_columns") or {}
        if memory_table and memory_columns.get("session_id") and memory_columns.get("summary"):
            session_value = self._coerce_session_value(schema, memory_table, memory_columns["session_id"], session_id)
            if session_value is not None:
                selected = [
                    column
                    for column in [
                        memory_columns.get("summary"),
                        memory_columns.get("recent_messages"),
                        memory_columns.get("user_id"),
                        memory_columns.get("created_at"),
                        memory_columns.get("updated_at"),
                        memory_columns.get("status"),
                    ]
                    if column
                ]
                order_column = memory_columns.get("updated_at") or memory_columns.get("created_at")
                query = (
                    f"SELECT TOP (1) {', '.join(self._quote_name(col) for col in selected)} "
                    f"FROM {self._quote_table(memory_table)} "
                    f"WHERE {self._quote_name(memory_columns['session_id'])} = ?"
                )
                if order_column:
                    query += f" ORDER BY {self._quote_name(order_column)} DESC"
                cursor.execute(query, (session_value,))
                row = self._fetchone_dict(cursor)
                if row:
                    summary = compact_text(row.get(memory_columns.get("summary", ""), ""), MAX_CONTEXT_SUMMARY_CHARS)
                    user_id = str(row.get(memory_columns.get("user_id", ""), "") or "")
                    created_at = str(row.get(memory_columns.get("created_at", ""), "") or created_at)
                    updated_at = str(row.get(memory_columns.get("updated_at", ""), "") or updated_at)
                    session_status = str(row.get(memory_columns.get("status", ""), "") or session_status)
                    recent_raw = row.get(memory_columns.get("recent_messages", ""), "")
                    recent_messages = self._safe_json_list(str(recent_raw or "[]"))

        if not recent_messages:
            recent_messages = self._load_recent_messages(connection, schema, session_id)

        return {
            "session_id": session_id,
            "user_id": user_id,
            "recent_messages": recent_messages[-MAX_RECENT_MEMORY_MESSAGES:],
            "summary": summary,
            "created_at": created_at,
            "updated_at": updated_at,
            "session_status": session_status,
            "memory_persistence": bool(summary or recent_messages),
            "backend": "sqlserver",
        }

    def _load_recent_messages(self, connection, schema: Dict[str, Any], session_id: str) -> List[Dict[str, Any]]:
        message_table = schema.get("message_table")
        columns = schema.get("message_columns") or {}
        if not message_table or not columns.get("session_id") or not columns.get("role") or not columns.get("content"):
            return []
        session_value = self._coerce_session_value(schema, message_table, columns["session_id"], session_id)
        if session_value is None:
            return []
        selected = [columns["role"], columns["content"]]
        if columns.get("created_at"):
            selected.append(columns["created_at"])
        query = (
            f"SELECT TOP ({MAX_RECENT_MEMORY_MESSAGES}) {', '.join(self._quote_name(col) for col in selected)} "
            f"FROM {self._quote_table(message_table)} "
            f"WHERE {self._quote_name(columns['session_id'])} = ?"
        )
        if columns.get("created_at"):
            query += f" ORDER BY {self._quote_name(columns['created_at'])} DESC"
        cursor = connection.cursor()
        cursor.execute(query, (session_value,))
        rows = self._fetch_all_dicts(cursor)
        messages = []
        for row in reversed(rows):
            messages.append(
                {
                    "role": compact_text(row.get(columns["role"], "user"), 32),
                    "content": compact_text(row.get(columns["content"], ""), 5000),
                    "created_at": str(row.get(columns.get("created_at", ""), "") or utc_now()),
                    "source": "sqlserver",
                }
            )
        return messages

    def _save_memory_with_connection(
        self,
        connection,
        schema: Dict[str, Any],
        session_id: str,
        summary: str,
        recent_messages: List[Dict[str, Any]],
        user_id: Optional[str],
        session_status: str,
    ) -> bool:
        memory_table = schema.get("memory_table")
        columns = schema.get("memory_columns") or {}
        if not memory_table or not columns.get("session_id") or not columns.get("summary"):
            return False
        session_value = self._coerce_session_value(schema, memory_table, columns["session_id"], session_id)
        if session_value is None:
            return False

        now = utc_now()
        payload: Dict[str, Any] = {
            columns["summary"]: compact_text(summary, MAX_CONTEXT_SUMMARY_CHARS),
        }
        if columns.get("recent_messages"):
            payload[columns["recent_messages"]] = json.dumps(self._sanitize_messages(recent_messages), ensure_ascii=False)
        if columns.get("user_id") and user_id:
            payload[columns["user_id"]] = user_id
        if columns.get("updated_at"):
            payload[columns["updated_at"]] = now
        if columns.get("status"):
            payload[columns["status"]] = session_status

        cursor = connection.cursor()
        cursor.execute(
            f"SELECT TOP (1) 1 FROM {self._quote_table(memory_table)} WHERE {self._quote_name(columns['session_id'])} = ?",
            (session_value,),
        )
        exists = cursor.fetchone() is not None
        if exists:
            assignments = ", ".join(f"{self._quote_name(column)} = ?" for column in payload)
            values = list(payload.values()) + [session_value]
            cursor.execute(
                f"UPDATE {self._quote_table(memory_table)} SET {assignments} WHERE {self._quote_name(columns['session_id'])} = ?",
                tuple(values),
            )
        else:
            insert_payload = {columns["session_id"]: session_value, **payload}
            if columns.get("created_at"):
                insert_payload[columns["created_at"]] = now
            cursor.execute(
                f"INSERT INTO {self._quote_table(memory_table)} "
                f"({', '.join(self._quote_name(column) for column in insert_payload)}) "
                f"VALUES ({', '.join('?' for _ in insert_payload)})",
                tuple(insert_payload.values()),
            )
        logging.getLogger("ultron.memory_persistence").info(
            "sqlserver_memory_saved session=%s messages=%s summary_chars=%s table=%s",
            session_hash(session_id),
            len(recent_messages or []),
            len(summary or ""),
            memory_table,
        )
        return True

    def _append_turn_with_connection(
        self,
        connection,
        schema: Dict[str, Any],
        session_id: str,
        new_turn: Dict[str, Any],
        user_id: Optional[str],
    ) -> bool:
        message_table = schema.get("message_table")
        columns = schema.get("message_columns") or {}
        if not message_table or not columns.get("session_id") or not columns.get("role") or not columns.get("content"):
            return False
        session_value = self._coerce_session_value(schema, message_table, columns["session_id"], session_id)
        if session_value is None:
            return False
        now = utc_now()
        rows = []
        user_message = compact_text(new_turn.get("user_message") or new_turn.get("user") or "", 4000)
        assistant_message = compact_text(
            new_turn.get("assistant_message") or new_turn.get("assistant_response") or new_turn.get("response") or "",
            5000,
        )
        if user_message:
            rows.append(("user", user_message))
        if assistant_message:
            rows.append(("assistant", assistant_message))
        if not rows:
            return False

        cursor = connection.cursor()
        for role, content in rows:
            payload = {
                columns["session_id"]: session_value,
                columns["role"]: role,
                columns["content"]: content,
            }
            if columns.get("user_id") and user_id:
                payload[columns["user_id"]] = user_id
            if columns.get("created_at"):
                payload[columns["created_at"]] = now
            cursor.execute(
                f"INSERT INTO {self._quote_table(message_table)} "
                f"({', '.join(self._quote_name(column) for column in payload)}) "
                f"VALUES ({', '.join('?' for _ in payload)})",
                tuple(payload.values()),
            )
        return True

    def _flush_pending_memory(self, connection) -> None:
        with self._lock:
            pending_items = list(self._pending_memory.items())
        if not pending_items:
            return
        schema = self._schema_cache or self.load_database_schema_status(connection)
        flushed: List[str] = []
        for session_id, payload in pending_items:
            try:
                ok = self._save_memory_with_connection(
                    connection,
                    schema,
                    session_id,
                    payload.get("summary", ""),
                    payload.get("recent_messages", []),
                    payload.get("user_id"),
                    payload.get("session_status", "ACTIVE"),
                )
                if ok:
                    flushed.append(session_id)
            except Exception as exc:
                logging.getLogger("ultron.sqlserver_connection").warning(
                    "sqlserver_pending_sync_failed session=%s error_type=%s",
                    session_hash(session_id),
                    type(exc).__name__,
                )
        if flushed:
            connection.commit()
            with self._lock:
                for session_id in flushed:
                    self._pending_memory.pop(session_id, None)
            logging.getLogger("ultron.memory_persistence").info("sqlserver_pending_sync_flushed count=%s", len(flushed))

    def _queue_pending_memory(
        self,
        session_id: str,
        summary: str,
        recent_messages: List[Dict[str, Any]],
        user_id: Optional[str],
        session_status: str,
    ) -> None:
        with self._lock:
            self._pending_memory[session_id] = {
                "summary": compact_text(summary, MAX_CONTEXT_SUMMARY_CHARS),
                "recent_messages": self._sanitize_messages(recent_messages),
                "user_id": user_id or "",
                "session_status": session_status,
                "queued_at": utc_now(),
            }
        logging.getLogger("ultron.memory_persistence").info(
            "sqlserver_memory_queued session=%s messages=%s",
            session_hash(session_id),
            len(recent_messages or []),
        )

    def _record_health(self, result: SqlServerHealthResult) -> SqlServerHealthResult:
        with self._lock:
            self._last_health = result
            self._last_check_monotonic = time.monotonic()
        logging.getLogger("ultron.sqlserver_connection").info(
            "sqlserver_status status=%s ok=%s database=%s schema_valid=%s memory_table=%s message_table=%s latency_ms=%s error_type=%s",
            result.status.value,
            result.ok,
            result.database,
            result.schema_valid,
            result.memory_table,
            result.message_table,
            result.latency_ms,
            result.error_type,
        )
        return result

    def _record_exception(self, exc: Exception) -> None:
        self._record_health(
            SqlServerHealthResult(
                status=self._classify_exception(exc),
                ok=False,
                checked_at=utc_now(),
                database=SQLSERVER_DATABASE,
                error_type=type(exc).__name__,
                error_message=compact_text(str(exc), 240),
            )
        )

    def _classify_exception(self, exc: Exception) -> DatabaseStatus:
        message = str(exc).lower()
        if any(token in message for token in ["login failed", "authentication", "permission", "access denied"]):
            return DatabaseStatus.DB_AUTH_ERROR
        return DatabaseStatus.DB_DISCONNECTED

    def _find_table(self, table_columns: Dict[str, Dict[str, Any]], required_groups: List[Set[str]]) -> str:
        for table_name, metadata in table_columns.items():
            columns = set(metadata.get("columns", {}).keys())
            if all(any(self._normalize(alias) in columns for alias in group) for group in required_groups):
                return table_name
        return ""

    def _memory_column_mapping(self, table_metadata: Dict[str, Any]) -> Dict[str, str]:
        return {
            "session_id": self._find_column(table_metadata, self.SESSION_ALIASES),
            "user_id": self._find_column(table_metadata, self.USER_ALIASES),
            "summary": self._find_column(table_metadata, self.SUMMARY_ALIASES),
            "recent_messages": self._find_column(table_metadata, self.RECENT_ALIASES),
            "created_at": self._find_column(table_metadata, self.CREATED_ALIASES),
            "updated_at": self._find_column(table_metadata, self.UPDATED_ALIASES),
            "status": self._find_column(table_metadata, self.STATUS_ALIASES),
            "last_user_goal": self._find_column(table_metadata, self.GOAL_ALIASES),
            "last_agent_state": self._find_column(table_metadata, self.AGENT_STATE_ALIASES),
        }

    def _message_column_mapping(self, table_metadata: Dict[str, Any]) -> Dict[str, str]:
        return {
            "session_id": self._find_column(table_metadata, self.SESSION_ALIASES),
            "user_id": self._find_column(table_metadata, self.USER_ALIASES),
            "role": self._find_column(table_metadata, self.ROLE_ALIASES),
            "content": self._find_column(table_metadata, self.CONTENT_ALIASES),
            "created_at": self._find_column(table_metadata, self.CREATED_ALIASES),
        }

    def _find_column(self, table_metadata: Dict[str, Any], aliases: Set[str]) -> str:
        columns = table_metadata.get("columns", {})
        for alias in aliases:
            normalized = self._normalize(alias)
            if normalized in columns:
                return columns[normalized]
        return ""

    def _safe_fetch_names(self, cursor, sql: str, fields: Tuple[str, str, str]) -> List[Dict[str, str]]:
        try:
            cursor.execute(sql)
            rows = self._fetch_all_dicts(cursor)
        except Exception:
            return []
        names = []
        for row in rows:
            names.append(
                {
                    "schema": str(row.get(fields[0], "") or ""),
                    "name": str(row.get(fields[1], "") or ""),
                    "type": str(row.get(fields[2], "") or ""),
                    "full_name": f"{row.get(fields[0], '')}.{row.get(fields[1], '')}",
                }
            )
        return names

    def _find_routine(self, procedure_name: str, routines: List[Dict[str, str]]) -> str:
        requested = self._normalize(procedure_name)
        for routine in routines:
            full_name = routine.get("full_name", "")
            bare_name = routine.get("name", "")
            if self._normalize(full_name) == requested or self._normalize(bare_name) == requested:
                return full_name
        return ""

    def _fetchone_dict(self, cursor) -> Dict[str, Any]:
        row = cursor.fetchone()
        if not row:
            return {}
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    def _fetch_all_dicts(self, cursor) -> List[Dict[str, Any]]:
        if not cursor.description:
            return []
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _sanitize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clean_messages: List[Dict[str, Any]] = []
        for message in (messages or [])[-MAX_RECENT_MEMORY_MESSAGES:]:
            clean_messages.append(
                {
                    "role": compact_text(message.get("role", "user"), 32),
                    "content": compact_text(message.get("content", ""), 5000),
                    "created_at": compact_text(message.get("created_at", utc_now()), 64),
                    "source": compact_text(message.get("source", "chat"), 80),
                }
            )
        return clean_messages

    def _safe_json_list(self, raw: str) -> List[Dict[str, Any]]:
        try:
            parsed = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict)]

    def _safe_server_label(self) -> str:
        host = SQLSERVER_HOST.strip()
        if not host:
            return ""
        return host if "\\" in host else host.split(",")[0]

    def _coerce_session_value(self, schema: Dict[str, Any], table_name: str, column_name: str, session_id: str) -> Optional[Any]:
        data_type = (
            (schema.get("table_columns") or {})
            .get(table_name, {})
            .get("types", {})
            .get(column_name, "")
            .lower()
        )
        numeric_types = {"bigint", "int", "smallint", "tinyint", "decimal", "numeric"}
        clean_session = str(session_id or DEFAULT_SESSION_ID)
        if data_type in numeric_types:
            return int(clean_session) if clean_session.isdigit() else None
        return clean_session

    def _quote_table(self, table_name: str) -> str:
        return ".".join(self._quote_name(part) for part in str(table_name).split(".") if part)

    def _quote_name(self, identifier: str) -> str:
        return "[" + str(identifier).replace("]", "]]") + "]"

    def _normalize(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


context_memory_store = ContextMemoryStore()
sqlserver_store = SqlServerTutoriaStore()


def init_sqlserver_connection() -> Dict[str, Any]:
    return check_sqlserver_health(force=True)


def check_sqlserver_health(force: bool = False) -> Dict[str, Any]:
    result = sqlserver_store.check_health(force=force)
    snapshot = sqlserver_store.status_snapshot()
    snapshot["ok"] = result.ok
    return snapshot


def reconnect_sqlserver() -> Dict[str, Any]:
    return sqlserver_store.reconnect_database()


def get_sqlserver_connection():
    return sqlserver_store.get_connection()


def validate_tutoria_schema() -> Dict[str, Any]:
    try:
        return sqlserver_store.load_database_schema_status()
    except Exception as exc:
        sqlserver_store._record_exception(exc)
        return {
            "schema_valid": False,
            "database": SQLSERVER_DATABASE,
            "error_type": type(exc).__name__,
            "error_message": compact_text(str(exc), 240),
        }


def load_database_schema_status() -> Dict[str, Any]:
    return validate_tutoria_schema()


def execute_tutoria_procedure(procedure_name: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
    return sqlserver_store.execute_tutoria_procedure(procedure_name, params=params)


def save_memory_to_sqlserver(
    session_id: str,
    summary: str,
    recent_messages: List[Dict[str, Any]],
    user_id: Optional[str] = None,
) -> bool:
    return sqlserver_store.save_memory(session_id, summary, recent_messages, user_id=user_id)


def load_memory_from_sqlserver(session_id: str = DEFAULT_SESSION_ID) -> Dict[str, Any]:
    return sqlserver_store.load_memory(session_id)


def persist_chat_summary(session_id: str, summary: str, user_id: Optional[str] = None) -> bool:
    current = context_memory_store.load(session_id)
    return save_memory_to_sqlserver(
        session_id=session_id,
        summary=summary,
        recent_messages=current.get("recent_messages", []),
        user_id=user_id if user_id is not None else current.get("user_id", ""),
    )


def restore_last_session_state(session_id: str = DEFAULT_SESSION_ID) -> Dict[str, Any]:
    return load_context_memory(session_id)


def _merge_sqlserver_memory(local_memory: Dict[str, Any], sql_memory: Dict[str, Any]) -> Dict[str, Any]:
    sql_status = sql_memory.get("sqlserver_status") or sqlserver_store.status_snapshot()
    has_sql_memory = bool(sql_memory.get("summary") or sql_memory.get("recent_messages"))
    if not has_sql_memory:
        local_memory["sqlserver_status"] = sql_status
        return local_memory

    merged = dict(local_memory)
    merged["summary"] = sql_memory.get("summary") or local_memory.get("summary", "")
    merged["recent_messages"] = sql_memory.get("recent_messages") or local_memory.get("recent_messages", [])
    merged["user_id"] = sql_memory.get("user_id") or local_memory.get("user_id", "")
    merged["created_at"] = sql_memory.get("created_at") or local_memory.get("created_at", "")
    merged["updated_at"] = sql_memory.get("updated_at") or local_memory.get("updated_at", "")
    merged["session_status"] = sql_memory.get("session_status") or local_memory.get("session_status", "ACTIVE")
    merged["backend"] = "sqlserver+sqlite-fallback"
    merged["memory_persistence"] = True
    merged["sqlserver_status"] = sql_status
    context_memory_store.save(
        session_id=merged.get("session_id", DEFAULT_SESSION_ID),
        summary=merged.get("summary", ""),
        recent_messages=merged.get("recent_messages", []),
        user_id=merged.get("user_id", ""),
        session_status=merged.get("session_status", "ACTIVE"),
    )
    return merged


def load_context_memory(session_id: str = DEFAULT_SESSION_ID) -> Dict[str, Any]:
    local_memory = context_memory_store.load(session_id)
    sql_memory = load_memory_from_sqlserver(session_id)
    return _merge_sqlserver_memory(local_memory, sql_memory)


def save_context_memory(
    session_id: str,
    summary: str,
    recent_messages: List[Dict[str, Any]],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    saved = context_memory_store.save(session_id, summary, recent_messages, user_id=user_id)
    sql_ok = save_memory_to_sqlserver(session_id, summary, recent_messages, user_id=user_id)
    saved["sqlserver_status"] = sqlserver_store.status_snapshot()
    saved["sqlserver_synced"] = sql_ok
    saved["backend"] = "sqlserver+sqlite-fallback" if sql_ok else "sqlite+pending-sqlserver"
    return saved


def update_context_memory(
    session_id: str,
    new_turn: Dict[str, Any],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    updated = context_memory_store.update(session_id, new_turn, user_id=user_id)
    sql_ok = save_memory_to_sqlserver(
        session_id=session_id,
        summary=updated.get("summary", ""),
        recent_messages=updated.get("recent_messages", []),
        user_id=user_id if user_id is not None else updated.get("user_id", ""),
    )
    sql_messages_ok = sqlserver_store.append_turn(session_id, new_turn, user_id=user_id)
    updated["sqlserver_status"] = sqlserver_store.status_snapshot()
    updated["sqlserver_synced"] = bool(sql_ok or sql_messages_ok)
    updated["backend"] = "sqlserver+sqlite-fallback" if updated["sqlserver_synced"] else "sqlite+pending-sqlserver"
    return updated


def clear_context_memory(session_id: str = DEFAULT_SESSION_ID) -> None:
    context_memory_store.clear(session_id)
    sqlserver_store.clear_memory(session_id)


def context_memory_prompt(session_id: str = DEFAULT_SESSION_ID) -> str:
    memory = load_context_memory(session_id)
    parts: List[str] = []
    if memory.get("summary"):
        parts.append("Persistent conversation summary:\n" + str(memory["summary"]))
    recent = memory.get("recent_messages") or []
    if recent:
        lines = []
        for message in recent[-8:]:
            role = message.get("role", "user")
            lines.append(f"{role}: {compact_text(message.get('content', ''), 500)}")
        parts.append("Recent relevant turns:\n" + "\n".join(lines))
    return "\n\n".join(parts)


class TutorConnectionMonitor:
    def __init__(self, health_url: str = TUTOR_HEALTH_URL) -> None:
        self.health_url = health_url
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

    def check_tutor_health(self, record: bool = True) -> HealthcheckResult:
        started = time.perf_counter()
        checked_at = utc_now()
        try:
            request = urllib.request.Request(self.health_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=TUTOR_HEALTH_TIMEOUT_SECONDS) as response:
                raw_body = response.read(1024 * 256).decode("utf-8", errors="replace")
                latency_ms = int(round((time.perf_counter() - started) * 1000))
                payload = json.loads(raw_body) if raw_body else {}
                ok = 200 <= response.status < 300 and bool(payload.get("ok", True))
                status = TutorStatus.CONNECTED if ok else TutorStatus.DEGRADED
                result = HealthcheckResult(
                    status=status,
                    ok=ok,
                    http_status=response.status,
                    latency_ms=latency_ms,
                    checked_at=checked_at,
                    payload=payload if isinstance(payload, dict) else {},
                )
        except urllib.error.HTTPError as exc:
            result = HealthcheckResult(
                status=TutorStatus.DEGRADED if 500 <= exc.code < 600 else TutorStatus.DISCONNECTED,
                ok=False,
                http_status=exc.code,
                latency_ms=int(round((time.perf_counter() - started) * 1000)),
                checked_at=checked_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            result = HealthcheckResult(
                status=TutorStatus.DISCONNECTED,
                ok=False,
                latency_ms=int(round((time.perf_counter() - started) * 1000)),
                checked_at=checked_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        except Exception as exc:
            result = HealthcheckResult(
                status=TutorStatus.DISCONNECTED,
                ok=False,
                latency_ms=int(round((time.perf_counter() - started) * 1000)),
                checked_at=checked_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        if record:
            record_tutor_status(result)
        return result

    def recover_tutor_connection(self) -> Dict[str, Any]:
        recovering = HealthcheckResult(
            status=TutorStatus.RECOVERING,
            ok=False,
            checked_at=utc_now(),
            error_type="RecoveryStarted",
            error_message="Attempting tutor_ia reconnection.",
        )
        record_tutor_status(recovering)
        for attempt in range(1, TUTOR_RECOVERY_MAX_ATTEMPTS + 1):
            result = self.check_tutor_health(record=False)
            if result.ok:
                return record_tutor_status(result, retry_count=attempt)
            record_tutor_status(result, retry_count=attempt)
            time.sleep(TUTOR_RECOVERY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
        return context_memory_store.status_snapshot()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="ultron-tutor-monitor", daemon=True)
            self._thread.start()
            logger.info("tutor_monitor_started health_url=%s", self.health_url)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            result = self.check_tutor_health(record=True)
            if not result.ok:
                self.recover_tutor_connection()
            self._stop_event.wait(TUTOR_MONITOR_INTERVAL_SECONDS)


tutor_monitor = TutorConnectionMonitor()


def check_tutor_health() -> Dict[str, Any]:
    result = tutor_monitor.check_tutor_health(record=True)
    snapshot = context_memory_store.status_snapshot()
    snapshot["ok"] = result.ok
    return snapshot


def is_tutor_connected() -> bool:
    return context_memory_store.status_snapshot().get("status") == TutorStatus.CONNECTED.value


def monitor_tutor_connection() -> None:
    tutor_monitor.start()


def stop_tutor_connection_monitor() -> None:
    tutor_monitor.stop()


def record_tutor_status(
    result: HealthcheckResult | Dict[str, Any],
    retry_count: int = 0,
    downtime_seconds: float = 0,
) -> Dict[str, Any]:
    if isinstance(result, dict):
        status_value = result.get("status") or TutorStatus.DISCONNECTED.value
        health_result = HealthcheckResult(
            status=TutorStatus(status_value),
            ok=bool(result.get("ok") or result.get("tutor_connected")),
            http_status=int(result.get("http_status") or 0),
            latency_ms=int(result.get("latency_ms") or 0),
            checked_at=str(result.get("checked_at") or utc_now()),
            error_type=str(result.get("error_type") or ""),
            error_message=str(result.get("error_message") or ""),
        )
    else:
        health_result = result
    return context_memory_store.record_status(health_result, retry_count=retry_count, downtime_seconds=downtime_seconds)


def get_ultron_status() -> Dict[str, Any]:
    return context_memory_store.status_snapshot()


def _resolve_system_status(tutor_snapshot: Dict[str, Any], sql_snapshot: Dict[str, Any]) -> str:
    if sql_snapshot.get("configured") and not sql_snapshot.get("driver_available"):
        return "SQLSERVER_DRIVER_MISSING"
    if sql_snapshot.get("configured") and sql_snapshot.get("status") == DatabaseStatus.DB_AUTH_ERROR.value:
        return "SQLSERVER_AUTH_ERROR"
    if sql_snapshot.get("configured") and sql_snapshot.get("status") == DatabaseStatus.DB_SCHEMA_INVALID.value:
        return "SCHEMA_INCOMPLETE"
    if sql_snapshot.get("configured") and sql_snapshot.get("status") in {
        DatabaseStatus.DB_DISCONNECTED.value,
        DatabaseStatus.DB_RECONNECTING.value,
    }:
        return "SQLSERVER_UNAVAILABLE"
    if tutor_snapshot.get("status") != TutorStatus.CONNECTED.value:
        return "TUTOR_IA_DISCONNECTED"
    return "SYSTEM_READY"


def bootstrap_ultron_system(session_id: str = DEFAULT_SESSION_ID) -> Dict[str, Any]:
    memory = load_context_memory(session_id)
    sql_snapshot = init_sqlserver_connection()
    tutor_snapshot = check_tutor_health()
    return {
        "system_status": _resolve_system_status(tutor_snapshot, sql_snapshot),
        "memory_status": "LOADED" if memory.get("memory_persistence") else "MEMORY_NOT_LOADED",
        "session_id": session_id,
        "memory_backend": memory.get("backend", "sqlite"),
        "sqlserver_status": sql_snapshot,
        "tutor_ia_status": tutor_snapshot,
        "last_healthcheck": utc_now(),
    }


def api_status_payload() -> Dict[str, Any]:
    snapshot = get_ultron_status()
    sql_snapshot = check_sqlserver_health(force=False)
    return {
        "system_status": _resolve_system_status(snapshot, sql_snapshot),
        "tutor_connected": snapshot["tutor_connected"],
        "memory_persistence": True,
        "memory_status": "LOADED",
        "status": snapshot["status"],
        "tutor_ia_status": snapshot["status"],
        "sqlserver_status": sql_snapshot["status"],
        "sqlserver": sql_snapshot,
        "last_healthcheck": snapshot["last_healthcheck"],
        "last_healthy_at": snapshot["last_healthy_at"],
        "retry_count": snapshot["retry_count"],
        "downtime_seconds": snapshot["downtime_seconds"],
    }


def recovery_notice(snapshot: Dict[str, Any]) -> str:
    if snapshot.get("status") == TutorStatus.CONNECTED.value:
        return ""
    return (
        "El cerebro tutor_ia esta temporalmente desconectado. "
        "ULTRON conserva tu contexto y volvera a integrarlo al restablecer la conexion."
    )


def database_recovery_notice(snapshot: Dict[str, Any]) -> str:
    if not snapshot.get("configured"):
        return ""
    if snapshot.get("status") == DatabaseStatus.DB_CONNECTED.value:
        return ""
    return (
        "La memoria persistente de ULTRON en SQL Server esta temporalmente desconectada. "
        "El sistema conserva el contexto actual e intentara sincronizarlo cuando SQL Server vuelva a estar disponible."
    )

class LLMClient:
    """
    A generic asynchronous client for interacting with OpenAI's chat completion API.
    Handles retries for transient errors and provides basic error logging.
    """
    def __init__(self, api_key: str, default_model: str = "gpt-4o", max_retries: int = 3):
        if AsyncOpenAI is None:
            raise ImportError("The openai package is required for model calls. Install it with `pip install openai`.")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in a .env file or your environment.")
        self._client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model
        self.max_retries = max_retries
        logger.info(f"LLMClient initialized with default model: {default_model}")

    async def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        temperature: float = 0.7, # Controls randomness: higher means more creative, lower means more focused
        max_tokens: Optional[int] = None, # Maximum tokens in the generated response
        timeout: int = 60 # Timeout for API call in seconds
    ) -> Optional[str]:
        """
        Sends a chat completion request to the OpenAI API and returns the generated content.
        """
        model_to_use = model if model else self.default_model
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} for model {model_to_use} with messages: {messages}")
                response = await asyncio.wait_for( # Wait with a timeout to prevent indefinite hangs
                    self._client.chat.completions.create(
                        model=model_to_use,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=timeout
                )
                # Check if the response contains valid content
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    logger.warning(f"No content received from LLM for model {model_to_use} on attempt {attempt + 1}. Response: {response}")
                    return None
            except openai.APIError as e:
                logger.error(f"OpenAI API error for model {model_to_use} (attempt {attempt + 1}/{self.max_retries}): {e}")
                # Implement exponential backoff for rate limit errors
                if "rate limit" in str(e).lower() and attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    return None
            except asyncio.TimeoutError:
                logger.error(f"LLM request timed out for model {model_to_use} on attempt {attempt + 1}/{self.max_retries}.")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    return None
            except Exception as e:
                logger.error(f"An unexpected error occurred for model {model_to_use} (attempt {attempt + 1}/{self.max_retries}): {e}")
                return None
        logger.error(f"Failed to get a response after {self.max_retries} attempts for model {model_to_use}.")
        return None

class EmbeddingModel:
    """
    Client for generating text embeddings using OpenAI's embedding API.
    Essential for converting text into numerical vectors for similarity search in RAG.
    """
    def __init__(self, api_key: str, model: str = EMBEDDING_MODEL):
        if AsyncOpenAI is None:
            raise ImportError("The openai package is required for embeddings. Install it with `pip install openai`.")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in a .env file or your environment.")
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"EmbeddingModel initialized with model: {model}")

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates an embedding vector for the given text.
        Returns None if embedding fails or input text is empty.
        """
        if not text:
            logger.warning("Attempted to get embedding for empty text.")
            return None
        # Replace newlines as they can sometimes affect embedding quality
        text = text.replace("\n", " ")
        try:
            response = await self._client.embeddings.create(input=[text], model=self.model)
            return response.data[0].embedding
        except openai.APIError as e:
            logger.error(f"OpenAI API error during embedding generation: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during embedding generation: {e}")
            return None

class KnowledgeBase:
    """
    A simple in-memory vector store for Retrieval Augmented Generation (RAG).
    In a production system, this would typically be replaced by a scalable
    vector database like FAISS, ChromaDB, Pinecone, or Weaviate.
    This implementation uses a list of tuples (embedding, original_text, metadata)
    and performs a linear scan for similarity search.
    """
    def __init__(self, embedding_model: EmbeddingModel):
        self._embedding_model = embedding_model
        # Store documents as (embedding vector, original text, associated metadata)
        self._documents: List[Tuple[List[float], str, Dict[str, Any]]] = []
        logger.info("KnowledgeBase initialized (using in-memory storage).")

    async def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Adds a single document to the knowledge base by embedding its text.
        """
        if not text:
            logger.warning("Attempted to add empty text to KnowledgeBase.")
            return

        embedding = await self._embedding_model.get_embedding(text)
        if embedding:
            self._documents.append((embedding, text, metadata if metadata else {}))
            logger.debug(f"Added document (length {len(text)}) to knowledge base.")
        else:
            logger.error(f"Failed to embed document text: {text[:50]}...")

    async def add_documents_batch(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Adds multiple documents to the knowledge base by embedding them in parallel.
        Handles cases where metadata might be missing for some documents.
        """
        # Generate embeddings for all texts concurrently
        embeddings = await asyncio.gather(*[self._embedding_model.get_embedding(text) for text in texts])
        for i, embedding in enumerate(embeddings):
            if embedding:
                # Associate embedding with its original text and metadata
                current_metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                self._documents.append((embedding, texts[i], current_metadata))
                logger.debug(f"Added document batch item {i} (length {len(texts[i])}) to knowledge base.")
            else:
                logger.error(f"Failed to embed document text in batch: {texts[i][:50]}...")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculates cosine similarity between two vectors."""
        # Handle cases where vectors might be empty or malformed
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0 # Cannot compute similarity
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        magnitude1 = sum(v1**2 for v1 in vec1)**0.5
        magnitude2 = sum(v2**2 for v2 in vec2)**0.5
        if not magnitude1 or not magnitude2:
            return 0.0 # Avoid division by zero if a vector has zero magnitude
        return dot_product / (magnitude1 * magnitude2)

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.7,
        intent: Optional[UserIntent] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant documents from the knowledge base based on a query.
        Uses cosine similarity to rank documents.
        """
        if not self._documents:
            logger.info("KnowledgeBase is empty, no documents to retrieve.")
            return []

        query_embedding = await self._embedding_model.get_embedding(query)
        if not query_embedding:
            logger.warning("Failed to get embedding for query, cannot perform retrieval.")
            return []

        similarities = []
        for doc_embedding, doc_text, doc_metadata in self._documents:
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((similarity, doc_text, doc_metadata))

        # Sort documents by similarity in descending order
        similarities.sort(key=lambda x: x[0], reverse=True)

        retrieved_docs = []
        # Filter for top_k documents above a minimum similarity threshold
        for sim, text, metadata in similarities[: max(top_k * 3, top_k)]:
            if sim >= min_similarity:
                if intent and not self._source_matches_intent(query, metadata, intent):
                    continue
                retrieved_docs.append({"text": text, "similarity": sim, "metadata": metadata})
                if len(retrieved_docs) >= top_k:
                    break
            else:
                logger.debug(f"Document below min_similarity ({min_similarity}): {sim}")
        logger.debug(f"Retrieved {len(retrieved_docs)} documents for query: '{query[:50]}...'")
        return retrieved_docs

    def _source_matches_intent(self, query: str, metadata: Dict[str, Any], intent: UserIntent) -> bool:
        query_text = normalize_intent_text(query)
        source_text = normalize_intent_text(
            " ".join(str(metadata.get(key, "")) for key in ["source", "title", "path", "category", "tags", "type"])
        )
        wants_database = any(term in query_text for term in ["sql server", "t-sql", "tutoria", "ssms", "session", "sesion", "memoria persistente"])
        wants_marketing = any(term in query_text for term in ["marketing", "seo", "campana", "ventas", "copy"])
        wants_mysql = "mysql" in query_text
        wants_postgres = any(term in query_text for term in ["postgres", "postgresql", "plpgsql", "pl/pgsql"])

        if not wants_marketing and any(term in source_text for term in ["marketing_digital", "marketing digital", "marketing"]):
            return False
        if wants_database:
            if "mysql" in source_text and not wants_mysql:
                return False
            if any(term in source_text for term in ["postgresql", "postgres", "plpgsql", "pl/pgsql"]) and not wants_postgres:
                return False
        if intent == UserIntent.DATABASE_QUERY:
            if any(term in source_text for term in ["marketing_digital", "marketing digital", "mysql"]):
                return False
        return True

# --- AI Brain Components ---

class TutorIABrain:
    """
    Implements the core logic for the TutorIA brain.
    It uses an LLM to generate educational responses, augmented by RAG context.
    """
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client
        logger.info("TutorIABrain initialized.")

    async def get_response(self, query: str, context: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generates a tutoring response based on the student's query and relevant contextual information.
        """
        # Format the retrieved context into a string to be included in the LLM prompt
        context_str = "\n".join([f"Context document (Similarity: {doc['similarity']:.2f}, Source: {doc['metadata'].get('source', 'N/A')}):\n{doc['text']}" for doc in context])

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": TUTOR_SYSTEM_PROMPT},
        ]
        if context_str:
            # Include context if available, making it clear to the LLM that this is external knowledge
            messages.append({"role": "user", "content": f"Here is some relevant context to help you formulate your response:\n{context_str}"})
        messages.append({"role": "user", "content": f"Student's query: {query}\n\nYour explanation:"})

        logger.info(f"TutorIABrain processing query: '{query[:50]}...' with {len(context)} context docs.")
        response = await self._llm_client.chat_completion(messages, model=TUTOR_MODEL, temperature=0.7)
        return response

class AbrahamHernandezAssistant:
    """
    Implements the core logic for the ABRAHAM-HERNANDEZ-main programming assistant.
    It uses an LLM to generate programming advice and code, augmented by RAG context.
    """
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client
        logger.info("AbrahamHernandezAssistant initialized.")

    async def get_response(self, query: str, context: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generates a programming assistance response (e.g., code, debugging help, explanations)
        based on the user's request and relevant contextual information.
        """
        context_str = "\n".join([f"Context document (Similarity: {doc['similarity']:.2f}, Source: {doc['metadata'].get('source', 'N/A')}):\n{doc['text']}" for doc in context])

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
        ]
        if context_str:
            messages.append({"role": "user", "content": f"Here is some relevant context for your programming advice:\n{context_str}"})
        messages.append({"role": "user", "content": f"User's programming request: {query}\n\nYour response including any code:"})

        logger.info(f"AbrahamHernandezAssistant processing query: '{query[:50]}...' with {len(context)} context docs.")
        response = await self._llm_client.chat_completion(messages, model=ASSISTANT_MODEL, temperature=0.7)
        return response

class CodexAdjuster:
    """
    Utilizes a code-focused LLM (Codex or equivalent) to perform adjustments and refinements
    on generated text, especially focusing on code correctness, style, and clarity.
    """
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client
        logger.info("CodexAdjuster initialized.")

    async def adjust(self, text_to_adjust: str, context: List[Dict[str, Any]], adjustment_instruction: Optional[str] = None) -> Optional[str]:
        """
        Adjusts the given text, primarily focusing on code correctness, style, and clarity.
        Optionally takes specific instructions for adjustment.
        """
        if not text_to_adjust:
            logger.warning("CodexAdjuster received empty text to adjust.")
            return None

        context_str = "\n".join([f"Context document (Similarity: {doc['similarity']:.2f}, Source: {doc['metadata'].get('source', 'N/A')}):\n{doc['text']}" for doc in context])

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": CODEX_ADJUSTER_SYSTEM_PROMPT},
        ]
        if context_str:
            messages.append({"role": "user", "content": f"Additional context for making adjustments:\n{context_str}"})

        # Default adjustment instruction if none is provided
        instruction = adjustment_instruction if adjustment_instruction else (
            "Review the following text for code correctness, clarity, and adherence to best practices. "
            "Suggest improvements, fix errors, and format any code snippets appropriately. "
            "Provide the revised text only, without conversational filler."
        )
        messages.append({"role": "user", "content": f"{instruction}\n\nText to adjust:\n```\n{text_to_adjust}\n```"})

        logger.info(f"CodexAdjuster processing text for adjustment (length {len(text_to_adjust)}) with instruction: '{instruction[:50]}...'")
        # Lower temperature for precise, less creative adjustments
        response = await self._llm_client.chat_completion(messages, model=CODEX_ADJUSTER_MODEL, temperature=0.2)
        return response

# --- Main Integration ---

class IntegratedAssistant:
    """
    Integrates TutorIA (for explanations), ABRAHAM-HERNANDEZ-main (for programming help),
    and Codex Adjuster (for refinement) with a RAG-based knowledge base.
    This acts as the orchestrator for the overall AI system.
    """
    def __init__(self):
        self._llm_client = LLMClient(OPENAI_API_KEY)
        self._embedding_model = EmbeddingModel(OPENAI_API_KEY)
        self._knowledge_base = KnowledgeBase(self._embedding_model)
        self._tutor_ia = TutorIABrain(self._llm_client)
        self._programming_assistant = AbrahamHernandezAssistant(self._llm_client)
        self._codex_adjuster = CodexAdjuster(self._llm_client)
        monitor_tutor_connection()
        logger.info("IntegratedAssistant initialized, ready for knowledge loading.")

    async def _load_initial_knowledge(self):
        """
        Loads initial documents into the knowledge base. This simulates ingesting
        documentation, specific learning materials, or best practices for the AI.
        These documents enhance the RAG system's ability to provide context.
        """
        docs = [
            {"text": "Python's PEP 8 is a style guide for Python code. It promotes a readable and consistent coding style, ensuring collaboration and maintainability.", "metadata": {"source": "PEP 8 Documentation"}},
            {"text": "A closure in Python is a function object that remembers values in enclosing scopes even if those scopes are no longer in memory. This allows for data hiding and functional programming patterns.", "metadata": {"source": "Python Advanced Topics"}},
            {"text": "The four main pillars of object-oriented programming (OOP) are Encapsulation (bundling data and methods), Inheritance (creating new classes from existing ones), Polymorphism (objects taking on many forms), and Abstraction (hiding complex implementation details).", "metadata": {"source": "OOP Basics Guide"}},
            {"text": "For a RAG (Retrieval Augmented Generation) system, key components include an embedding model (to convert text to vectors), a vector store (to store and search embeddings), and a retriever mechanism (to fetch relevant documents). Microsoft's AI-Agents-for-Beginners series provides excellent guidance on building AI agents with external memory, which directly relates to RAG concepts.", "metadata": {"source": "RAG Concepts / MS Learn"}},
            {"text": "Asynchronous programming in Python leverages the `async` and `await` keywords, typically used with the `asyncio` library, to enable concurrent I/O operations without blocking the main thread. This is crucial for high-performance network applications.", "metadata": {"source": "Python Asyncio Docs"}},
            {"text": """
                def calculate_factorial(n: int) -> int:
                    if n < 0:
                        raise ValueError("Factorial is not defined for negative numbers.")
                    if n == 0:
                        return 1
                    else:
                        return n * calculate_factorial(n-1)
                This is a recursive implementation of the factorial function, including type hints and error handling.
                """, "metadata": {"source": "Code Example: Factorial"}},
            {"text": """
                # Example of Python list comprehension
                squares = [x**2 for x in range(10) if x % 2 == 0]
                # Result: [0, 4, 16, 36, 64]
                List comprehensions offer a concise way to create lists.
                """, "metadata": {"source": "Python List Comprehensions"}},
        ]
        # Add all documents to the knowledge base concurrently
        await self._knowledge_base.add_documents_batch([doc["text"] for doc in docs], [doc["metadata"] for doc in docs])
        logger.info(f"Loaded {len(docs)} initial knowledge documents into the RAG system.")

    async def process_request(
        self,
        user_query: str,
        mode: str = "auto",
        adjustment_instruction: Optional[str] = None,
        session_id: str = DEFAULT_SESSION_ID,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Processes a user request by:
        1. Retrieving relevant context using RAG.
        2. Delegating the query to either TutorIA or ABRAHAM-HERNANDEZ-main based on 'mode' or query content.
        3. Passing the initial response to Codex Adjuster for refinement, especially for code.

        Args:
            user_query (str): The user's input query or request.
            mode (str): Determines which primary AI component to use:
                        "tutor" for educational explanations,
                        "assistant" for programming help,
                        "auto" to let the system decide based on keywords.
            adjustment_instruction (Optional[str]): A specific instruction for the Codex Adjuster
                                                    on how to refine the output (e.g., "make it more concise").
            session_id (str): Stable session key used to restore persistent contextual memory.
            user_id (Optional[str]): Optional user identifier for local memory grouping.

        Returns:
            str: The final, adjusted and refined response from the integrated AI system.
        """
        logger.info(
            "processing_request mode=%s session=%s query_chars=%s",
            mode,
            session_hash(session_id),
            len(user_query or ""),
        )

        intent = classify_user_intent(user_query)
        if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE}:
            answer = direct_conversation_answer(user_query)
            logger.info(
                "retrieval_orchestration intent=%s rag_used=false sources_called=[] reason=direct_conversation",
                intent.value,
            )
            return answer

        # 0. Load persistent memory and check tutor_ia health only after intent planning.
        persistent_memory = load_context_memory(session_id)
        sql_snapshot = persistent_memory.get("sqlserver_status") or check_sqlserver_health(force=False)
        tutor_snapshot = await asyncio.to_thread(check_tutor_health)
        if not tutor_snapshot.get("tutor_connected"):
            tutor_snapshot = await asyncio.to_thread(tutor_monitor.recover_tutor_connection)
        database_notice = database_recovery_notice(sql_snapshot)
        tutor_notice = recovery_notice(tutor_snapshot)

        memory_text = context_memory_prompt(session_id)
        if intent == UserIntent.MEMORY_QUERY and memory_text:
            memory_answer = (
                "Esto es lo que conservo del hilo reciente:\n\n"
                f"{compact_text(memory_text, 1200)}\n\n"
                "Dime que parte quieres retomar y sigo desde ahi."
            )
            update_context_memory(
                session_id,
                {
                    "user_message": user_query,
                    "assistant_response": memory_answer,
                    "source": "memory_only",
                },
                user_id=user_id,
            )
            logger.info(
                "retrieval_orchestration intent=%s rag_used=false sources_called=['memory'] reason=memory_query",
                intent.value,
            )
            return memory_answer

        use_rag = should_use_rag(user_query, memory_text)
        retrieved_context: List[Dict[str, Any]] = []
        if use_rag:
            top_k = max(RAG_MIN_RELEVANT_CHUNKS, min(RAG_TOP_K, RAG_MAX_CONTEXT_CHUNKS))
            threshold = (
                OFFICIAL_SOURCES_SCORE_THRESHOLD
                if intent == UserIntent.EXTERNAL_KNOWLEDGE_QUERY
                else OBSIDIAN_SCORE_THRESHOLD
                if intent in {UserIntent.DOCUMENT_GROUNDED_QUERY, UserIntent.RAG_REQUIRED_QUERY}
                else TUTOR_IA_SCORE_THRESHOLD
            )
            retrieved_context = await self._knowledge_base.retrieve(
                user_query,
                top_k=top_k,
                min_similarity=max(RAG_SCORE_THRESHOLD, threshold),
                intent=intent,
            )
            scores = [float(doc.get("similarity") or 0) for doc in retrieved_context]
            logger.info(
                "retrieval_orchestration intent=%s rag_used=%s sources_called=%s accepted_chunks=%s threshold=%s highest_score=%s",
                intent.value,
                bool(retrieved_context),
                ["tutor_ia"],
                len(retrieved_context),
                max(RAG_SCORE_THRESHOLD, threshold),
                max(scores) if scores else 0,
            )
        else:
            logger.info(
                "retrieval_orchestration intent=%s rag_used=false sources_called=['memory'] reason=memory_first",
                intent.value,
            )

        response_strategy = route_response_strategy(intent, retrieved_context, memory_text)
        if response_strategy == "DOCUMENT_INSUFFICIENT":
            insufficient_response = (
                "No encontre evidencia suficiente en los documentos consultados para afirmarlo con seguridad. "
                "Puedo volver a buscar si me indicas el archivo, nota, carpeta o tema exacto."
            )
            update_context_memory(
                session_id,
                {
                    "user_message": user_query,
                    "assistant_response": insufficient_response,
                    "source": "document_insufficient",
                },
                user_id=user_id,
            )
            return insufficient_response

        if memory_text:
            retrieved_context.insert(
                0,
                {
                    "text": memory_text,
                    "similarity": 1.0,
                    "metadata": {
                        "source": "ULTRON persistent contextual memory",
                        "session_id": session_hash(session_id),
                        "backend": persistent_memory.get("backend", "sqlite"),
                    },
                },
            )
        # Format the retrieved context for inclusion in the LLM prompt
        context_texts = [f"Source: {doc['metadata'].get('source', 'N/A')}\nContent: {doc['text']}" for doc in retrieved_context]
        full_context_for_llm = "\n\n".join(context_texts)
        if full_context_for_llm:
            logger.debug(f"Retrieved context for LLMs:\n{full_context_for_llm[:200]}...")
        else:
            logger.debug("No highly relevant context retrieved for this query.")

        primary_response: Optional[str] = None
        # 2. Determine which primary AI component (TutorIA or Programming Assistant) to use
        # This decision can be based on explicit mode or heuristic keyword matching
        if mode == "tutor" or ("explain" in user_query.lower() and "how to" not in user_query.lower() and "code" not in user_query.lower() and "implement" not in user_query.lower()):
            logger.info("Delegating to TutorIA Brain for educational explanation.")
            primary_response = await self._tutor_ia.get_response(user_query, retrieved_context)
        elif mode == "assistant" or ("code" in user_query.lower() or "implement" in user_query.lower() or "debug" in user_query.lower() or "function" in user_query.lower() or "script" in user_query.lower()):
            logger.info("Delegating to ABRAHAM-HERNANDEZ-main Programming Assistant for code/programming help.")
            primary_response = await self._programming_assistant.get_response(user_query, retrieved_context)
        else: # "auto" mode: attempt to infer intent
            # Simple keyword-based intent detection. A more robust solution might use an LLM for classification.
            if any(kw in user_query.lower() for kw in ["code", "implement", "function", "script", "debug", "error", "write a program"]):
                logger.info("Auto-mode: Inferring programming intent, delegating to ABRAHAM-HERNANDEZ-main Programming Assistant.")
                primary_response = await self._programming_assistant.get_response(user_query, retrieved_context)
            else:
                logger.info("Auto-mode: Inferring general/tutoring intent, delegating to TutorIA Brain.")
                primary_response = await self._tutor_ia.get_response(user_query, retrieved_context)

        if not primary_response:
            logger.error("Primary AI component failed to generate a response.")
            notices = "\n\n".join(notice for notice in [database_notice, tutor_notice] if notice)
            failure_response = (
                notices + "\n\n" if notices else ""
            ) + "I apologize, but I couldn't generate a primary response for your request at this time. Please try rephrasing."
            update_context_memory(
                session_id,
                {
                    "user_message": user_query,
                    "assistant_response": failure_response,
                    "source": "primary_response_failure",
                },
                user_id=user_id,
            )
            return failure_response

        logger.info(f"Primary response generated. Length: {len(primary_response)} characters. Checking for adjustment...")

        # 3. Perform necessary adjustments using the Codex Adjuster
        # Adjustment is triggered if an instruction is given, if the response contains code blocks,
        # or if the programming assistant was used (as its output is likely to need code-specific review).
        requires_adjustment = adjustment_instruction or "```" in primary_response or mode == "assistant" or ("code" in user_query.lower() and mode == "auto")

        final_response: str
        if requires_adjustment:
            logger.info("Passing primary response to Codex Adjuster for refinement.")
            adjusted_response = await self._codex_adjuster.adjust(primary_response, retrieved_context, adjustment_instruction)
            if not adjusted_response:
                logger.warning("Codex Adjuster failed to refine the response. Returning primary (unadjusted) response as a fallback.")
                final_response = primary_response # Fallback to original response
            else:
                final_response = adjusted_response
        else:
            final_response = primary_response

        if not final_response:
            # This should ideally not happen if primary_response was valid and adjustment fallback is in place
            final_response = "I apologize, but I encountered an issue generating a complete and refined response."

        notices = "\n\n".join(notice for notice in [database_notice, tutor_notice] if notice)
        if notices:
            final_response = notices + "\n\n" + final_response

        update_context_memory(
            session_id,
            {
                "user_message": user_query,
                "assistant_response": final_response,
                "source": "integrated_assistant",
            },
            user_id=user_id,
        )

        logger.info("Request processed successfully, final response generated.")
        return final_response


# --- Main execution ---
async def main():
    """
    Main function to initialize and run the integrated assistant.
    Sets up the assistant, loads initial knowledge, and enters an interactive loop.
    """
    logger.info("Starting IntegratedAssistant application...")
    assistant = IntegratedAssistant()
    # Load initial knowledge asynchronously before processing user requests
    await assistant._load_initial_knowledge()
    session_id = DEFAULT_SESSION_ID
    bootstrap = await asyncio.to_thread(bootstrap_ultron_system, session_id)
    tutor_snapshot = bootstrap.get("tutor_ia_status", {})
    sql_snapshot = bootstrap.get("sqlserver_status", {})

    print("\n--- Integrated AI Assistant (TutorIA + ABRAHAM-HERNANDEZ-main + Codex Adjuster) ---")
    print("This assistant combines tutoring, programming help, and code refinement.")
    print(f"Session restored: {session_id} | memory backend: {bootstrap.get('memory_backend', 'sqlite')}")
    print(f"system status: {bootstrap.get('system_status')} | memory: {bootstrap.get('memory_status')}")
    print(f"SQL Server: {sql_snapshot.get('status')} | schema: {sql_snapshot.get('schema_valid')} | database: {sql_snapshot.get('database')}")
    print(f"tutor_ia status: {tutor_snapshot.get('status')} | memory preserved: {tutor_snapshot.get('memory_persistence')}")
    print("Type 'exit' to quit, 'status' to inspect tutor_ia, or 'clear memory' to reset this session.")

    while True:
        user_input = input("\nYou (or type 'exit'): ")
        if user_input.lower() == 'exit':
            print("Exiting assistant. Goodbye!")
            break
        if user_input.lower() in {"status", "estado"}:
            snapshot = await asyncio.to_thread(check_tutor_health)
            print(json.dumps(api_status_payload() | {"ok": snapshot.get("ok", False)}, ensure_ascii=False, indent=2))
            continue
        if user_input.lower() in {"clear memory", "limpiar memoria", "borrar memoria"}:
            clear_context_memory(session_id)
            print("ULTRON memory cleared for this session.")
            continue
        if not user_input.strip(): # Handle empty input
            print("Please enter a valid query.")
            continue

        print("\nAssistant is processing your request...")
        try:
            # Process the user's input, automatically determining the best mode
            response = await assistant.process_request(user_input, mode="auto", session_id=session_id)
            print(f"\nAI: {response}")
        except Exception as e:
            logger.error(f"Error processing user request: {e}", exc_info=True)
            print("I apologize, an unexpected error occurred while processing your request. Please try again.")


if __name__ == "__main__":
    try:
        # Run the main asynchronous function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user (KeyboardInterrupt).")
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        print(f"Error: {e}. Please ensure your environment variables are correctly set.")
    except Exception as e:
        logger.critical(f"An unhandled critical error occurred in the main execution loop: {e}", exc_info=True)
        print("A critical error occurred. Please check the logs for more details.")
