from __future__ import annotations

import logging
import os
import time
from typing import Any

try:
    import requests

    HAS_REQUESTS = True
except Exception:
    requests = None
    HAS_REQUESTS = False


LOGGER = logging.getLogger(__name__)
DEFAULT_BASE_URL = "http://127.0.0.1:8787"
DEFAULT_TIMEOUT = int(os.getenv("BRIDGE_TIMEOUT_SECONDS", "10"))
HEALTH_TIMEOUT = int(os.getenv("BRIDGE_HEALTH_TIMEOUT_SECONDS", "3"))

HEALTH_CANDIDATES = ["/health", "/status", "/api/health", "/api/status"]
STATUS_CANDIDATES = ["/status", "/api/status", "/api/health", "/health"]
ASK_CANDIDATES = ["/ask", "/chat", "/api/ask", "/api/chat", "/api/brain/ask"]
MODEL_CANDIDATES = ["/models", "/api/models", "/api/brain/models"]
SOURCE_CANDIDATES = ["/sources", "/api/sources", "/api/unified-brain/sources"]
TOOL_CANDIDATES = ["/tools", "/api/tools", "/api/brain/tools"]


class BridgeAPIClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        self.base_url = (base_url or os.getenv("BRIDGE_API_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self._available: bool | None = None
        self._last_check = 0.0
        self._check_ttl = 20.0
        self._working_ask_path = ""

    def health_check(self, force: bool = False) -> bool:
        now = time.monotonic()
        if not force and self._available is not None and now - self._last_check < self._check_ttl:
            return self._available
        if not HAS_REQUESTS:
            self._available = False
            self._last_check = now
            return False
        for path in HEALTH_CANDIDATES:
            raw = self._get(path, timeout=HEALTH_TIMEOUT, label="health_check")
            if self._is_success(raw):
                self._available = True
                self._last_check = now
                return True
        self._available = False
        self._last_check = now
        return False

    def get_status(self) -> dict[str, Any]:
        return self._get_first(STATUS_CANDIDATES, "get_status")

    def get_models(self) -> dict[str, Any]:
        raw = self._get_first(MODEL_CANDIDATES, "get_models")
        if self._is_success(raw):
            return {"success": True, "models": raw.get("models", raw.get("data", [])), "raw": raw}
        status = self.get_status()
        models = status.get("models", {})
        if isinstance(models, dict):
            return {"success": True, "models": models.get("installed", []), "routing": models.get("routing", {}), "raw": status}
        brain = status.get("brain", {}) if isinstance(status.get("brain"), dict) else {}
        return {"success": self._is_success(status), "models": brain.get("models", []), "active_model": brain.get("active_model"), "raw": status}

    def get_sources(self) -> dict[str, Any]:
        raw = self._get_first(SOURCE_CANDIDATES, "get_sources")
        if self._is_success(raw):
            return {"success": True, "sources": raw.get("sources", raw), "raw": raw}
        return {"success": False, "sources": {}, "error": raw.get("error"), "raw": raw}

    def get_tools(self) -> dict[str, Any]:
        raw = self._get_first(TOOL_CANDIDATES, "get_tools")
        if self._is_success(raw):
            return {"success": True, "tools": raw.get("tools", raw.get("data", [])), "raw": raw}
        status = self.get_status()
        tools = []
        if isinstance(status.get("brain"), dict):
            tools = status["brain"].get("tools", []) or []
        if not tools and isinstance(status.get("jarvis"), dict):
            tools = status["jarvis"].get("tools", []) or []
        return {"success": bool(tools), "tools": tools, "raw": status}

    def ask(
        self,
        message: str,
        context: str | list | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.health_check():
            return self._unavailable_response()
        options = dict(options or {})
        payload: dict[str, Any] = {
            "message": message,
            "question": message,
            "session_id": options.pop("session_id", "abraham_web_default"),
            "response_profile": options.get("response_profile") or ("deep" if options.get("deep_thinking") else "web_fast"),
        }
        if context:
            payload["context"] = context
            payload["local_context"] = context
        payload.update(options)

        started = time.perf_counter()
        raw = self._post_first(ASK_CANDIDATES, payload, "ask")
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not self._is_success(raw):
            return {
                "source": "bridge_api",
                "success": False,
                "answer": "",
                "content": "",
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "error": raw.get("error") or raw.get("message") or "Bridge API no respondio correctamente.",
                "raw": raw,
            }

        answer = str(raw.get("answer") or raw.get("response") or raw.get("content") or "").strip()
        return {
            "source": "bridge_api",
            "success": bool(answer),
            "answer": answer,
            "content": answer,
            "confidence": 0.82 if answer else 0.0,
            "latency_ms": latency_ms,
            "error": None if answer else "Bridge API respondio sin texto.",
            "model": raw.get("model", ""),
            "mode": raw.get("mode") or raw.get("brain_mode") or "local-first",
            "sources": raw.get("sources", []),
            "raw": raw,
        }

    def _get_first(self, paths: list[str], label: str) -> dict[str, Any]:
        last = {"success": False, "error": "Sin rutas probadas."}
        for path in paths:
            raw = self._get(path, label=label)
            if self._is_success(raw):
                return raw
            last = raw
        return last

    def _post_first(self, paths: list[str], payload: dict[str, Any], label: str) -> dict[str, Any]:
        if self._working_ask_path:
            raw = self._post(self._working_ask_path, payload, label=label)
            if self._is_success(raw):
                return raw
        last = {"success": False, "error": "Sin rutas probadas."}
        for path in paths:
            raw = self._post(path, payload, label=label)
            if self._is_success(raw):
                self._working_ask_path = path
                return raw
            last = raw
        return last

    def _get(self, path: str, timeout: int | None = None, label: str = "get") -> dict[str, Any]:
        if not HAS_REQUESTS:
            return {"success": False, "error": "requests no instalado"}
        try:
            response = requests.get(f"{self.base_url}{path}", timeout=timeout or self.timeout)
            return self._decode_response(response)
        except Exception as exc:
            LOGGER.debug("BridgeAPIClient.%s fallo en %s: %s", label, path, exc)
            return {"success": False, "error": str(exc), "_path": path}

    def _post(self, path: str, payload: dict[str, Any], label: str = "post") -> dict[str, Any]:
        if not HAS_REQUESTS:
            return {"success": False, "error": "requests no instalado"}
        try:
            response = requests.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
            return self._decode_response(response)
        except Exception as exc:
            LOGGER.debug("BridgeAPIClient.%s fallo en %s: %s", label, path, exc)
            return {"success": False, "error": str(exc), "_path": path}

    @staticmethod
    def _decode_response(response: Any) -> dict[str, Any]:
        try:
            data = response.json()
            if not isinstance(data, dict):
                data = {"data": data}
        except Exception:
            data = {"content": getattr(response, "text", "")}
        data["_status_code"] = getattr(response, "status_code", 0)
        data.setdefault("success", bool(getattr(response, "ok", False) and data.get("ok") is not False))
        return data

    @staticmethod
    def _is_success(data: dict[str, Any]) -> bool:
        return bool(data.get("success") or data.get("ok") is True)

    def _unavailable_response(self) -> dict[str, Any]:
        return {
            "source": "bridge_api",
            "success": False,
            "answer": "",
            "content": "",
            "confidence": 0.0,
            "latency_ms": 0,
            "error": f"Bridge API no disponible en {self.base_url}.",
        }
