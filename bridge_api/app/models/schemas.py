from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    source: str = ""
    title: str = ""
    type: str = ""
    url: str = ""
    page: int | None = None
    score: float | None = None
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceFile(BaseModel):
    name: str
    relative_path: str
    path: str
    extension: str
    size: int
    modified_at: datetime
    indexed_chunks: int = 0


class SourcesResponse(BaseModel):
    ok: bool = True
    root: str
    supported_extensions: list[str] = Field(default_factory=list)
    files: list[SourceFile] = Field(default_factory=list)
    count: int = 0


class IndexRequest(BaseModel):
    force_reindex: bool = False
    limit: int | None = Field(default=None, ge=1, le=10000)


class IndexResponse(BaseModel):
    ok: bool = True
    message: str
    documents_seen: int = 0
    documents_loaded: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    chunks_skipped: int = 0
    collection: str = ""
    persist_dir: str = ""
    embedding_backend: str = ""
    embedding_model: str = ""
    duration_seconds: float = 0.0


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str = Field(..., min_length=1, max_length=20000)
    session_id: str = Field(default="default", max_length=128)
    chat_id: str = Field(default="", max_length=160)
    user_id: str = Field(default="", max_length=160)
    user_email: str = Field(default="", max_length=320)
    user_name: str = Field(default="", max_length=160)
    project_path: str | None = None
    workspace_path: str | None = None
    show_sources: bool = False
    use_rag: bool = True
    use_web: bool = False
    smart_search: bool = Field(default=False, alias="smartSearch")
    deep_thinking: bool = False
    response_profile: str = Field(default="balanced", max_length=64)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    client_context_summary: str = Field(default="", max_length=12000)
    source: str = Field(default="typed_chat", max_length=80)
    input_source: str = Field(default="typed_chat", max_length=80)
    k: int | None = Field(default=None, ge=1, le=30)
    top_k: int | None = Field(default=None, ge=1, le=12)


class ChatResponse(BaseModel):
    ok: bool = True
    answer: str
    sources: list[Source] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    session_id: str
    model: str = ""
    brain_parts: list[str] = Field(default_factory=list)
    used_smart_search: bool = False
    usedSmartSearch: bool = False
    smart_search: dict[str, Any] | None = None
    workflow: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=12000)
    k: int | None = Field(default=None, ge=1, le=30)


class SearchResponse(BaseModel):
    ok: bool = True
    query: str
    results: list[Source] = Field(default_factory=list)
    count: int = 0


class UploadResponse(BaseModel):
    ok: bool = True
    filename: str
    saved_as: str
    path: str
    size: int
    content_type: str | None = None
    message: str = "Archivo subido correctamente. Ejecuta /api/index para incorporarlo al cerebro RAG."


class HistoryRecord(BaseModel):
    session_id: str
    user_message: str
    ai_response: str
    created_at: datetime
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HistorySaveRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    user_message: str = Field(..., min_length=1)
    ai_response: str = Field(..., min_length=1)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    ok: bool = True
    session_id: str
    history: list[HistoryRecord] = Field(default_factory=list)
