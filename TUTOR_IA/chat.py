from __future__ import annotations

import os
from pathlib import Path

from database import get_connection, init_db, row_to_dict, utc_now


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
RECENT_HISTORY_LIMIT = int(os.getenv("TUTOR_IA_RECENT_HISTORY_LIMIT", "6"))


def ensure_user_session(user_id: int) -> dict:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            row = _create_session(conn, user_id, "Nuevo chat")
    return row_to_dict(row)


def create_chat_session(user_id: int, title: str = "Nuevo chat") -> dict:
    init_db()
    with get_connection() as conn:
        row = _create_session(conn, user_id, title)
    return row_to_dict(row)


def _create_session(conn, user_id: int, title: str):
    now = utc_now()
    cursor = conn.execute(
        """
        INSERT INTO chat_sessions (user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, title, now, now),
    )
    return conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (cursor.lastrowid,)).fetchone()


def get_chat_session(user_id: int, session_id: int) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    return row_to_dict(row)


def list_chat_sessions(user_id: int) -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.session_id = s.id) AS message_count
            FROM chat_sessions s
            WHERE s.user_id = ?
            ORDER BY s.updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_message(session_id: int, user_id: int, role: str, content: str) -> dict:
    init_db()
    now = utc_now()
    role = "assistant" if role == "ai" else role
    role = "user" if role == "human" else role
    if role not in {"user", "assistant", "system"}:
        raise ValueError("Rol de mensaje invalido.")
    with get_connection() as conn:
        _assert_session_owner(conn, session_id, user_id)
        cursor = conn.execute(
            """
            INSERT INTO chat_messages (session_id, user_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, role, content, now),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ? AND user_id = ?",
            (now, session_id, user_id),
        )
        row = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_dict(row)


def list_messages(session_id: int, user_id: int) -> list[dict]:
    init_db()
    with get_connection() as conn:
        _assert_session_owner(conn, session_id, user_id)
        rows = conn.execute(
            """
            SELECT * FROM chat_messages
            WHERE session_id = ? AND user_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (session_id, user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_memory(session_id: int, user_id: int, limit: int | None = None) -> list[dict]:
    limit = limit or RECENT_HISTORY_LIMIT
    messages = list_messages(session_id, user_id)
    recent = messages[-limit:]
    return [
        {
            "role": "human" if message["role"] == "user" else "ai",
            "content": message["content"],
        }
        for message in recent
        if message["role"] in {"user", "assistant"}
    ]


def update_session_title_from_message(session_id: int, user_id: int, content: str) -> None:
    current = get_chat_session(user_id, session_id)
    if not current or current.get("title") != "Nuevo chat":
        return
    title = " ".join((content or "").strip().split())[:56] or "Nuevo chat"
    with get_connection() as conn:
        conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (title, utc_now(), session_id, user_id),
        )


def call_assistant(message: str, session_id: int, user_id: int) -> dict:
    from web_bridge import answer_from_brain, memory_store

    memory_key = build_memory_key(user_id, session_id)
    recent_memory = get_recent_memory(session_id, user_id, limit=RECENT_HISTORY_LIMIT + 1)
    if (
        recent_memory
        and recent_memory[-1].get("role") == "human"
        and recent_memory[-1].get("content") == message
    ):
        recent_memory = recent_memory[:-1]
    memory_store[memory_key] = recent_memory
    payload = {
        "message": message,
        "session_id": memory_key,
        "client": "abraham-programming-assistant",
        "response_profile": os.getenv("TUTOR_IA_STREAMLIT_RESPONSE_PROFILE", "web_fast"),
        "local_first": True,
        "bridge_api": True,
        "anthropic": True,
        "fast_mode": True,
        "include_obsidian": True,
        "project_path": str(REPO_ROOT),
        "agency_enabled": True,
        "jarvis_profile": "unified",
        "show_sources": False,
    }
    return answer_from_brain(payload)


def build_memory_key(user_id: int, session_id: int) -> str:
    return f"streamlit-user-{user_id}-session-{session_id}"


def _assert_session_owner(conn, session_id: int, user_id: int) -> None:
    row = conn.execute(
        "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()
    if row is None:
        raise PermissionError("La conversacion no pertenece al usuario activo.")
