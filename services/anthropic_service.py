from __future__ import annotations

import os
import time
from typing import Any


DEFAULT_MODEL = "claude-3-5-sonnet-latest"

try:
    from anthropic import Anthropic

    HAS_ANTHROPIC = True
except Exception:
    Anthropic = None
    HAS_ANTHROPIC = False


class AnthropicService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv("BRAIN_TIMEOUT_SECONDS", "8"))
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and HAS_ANTHROPIC)

    def generate_answer(
        self,
        message: str,
        context: str | None = None,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        if not self.api_key:
            return self._unavailable(started, "ANTHROPIC_API_KEY no configurado.")
        if not HAS_ANTHROPIC:
            return self._unavailable(started, "Paquete anthropic no instalado.")

        options = options or {}
        system_prompt = system_prompt or self._default_system_prompt(options)
        max_tokens = int(options.get("max_tokens") or (900 if options.get("deep_thinking") else 420))
        temperature = float(options.get("temperature") or 0.2)

        try:
            response = self._get_client().messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": self._build_user_content(message, context),
                    }
                ],
            )
            answer = self._extract_text(response)
            return {
                "source": "anthropic",
                "success": bool(answer),
                "answer": answer,
                "content": answer,
                "confidence": 0.9 if answer else 0.0,
                "latency_ms": self._latency(started),
                "error": None if answer else "Anthropic no devolvio texto.",
                "metadata": {"model": self.model},
            }
        except Exception as exc:
            return self._unavailable(started, f"Anthropic no disponible: {exc}")

    def synthesize_response(
        self,
        message: str,
        context: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.generate_answer(message, context=context, system_prompt=None, options=options)

    def _get_client(self):
        if self._client is None:
            self._client = Anthropic(api_key=self.api_key, timeout=self.timeout)
        return self._client

    def _default_system_prompt(self, options: dict[str, Any]) -> str:
        if options.get("deep_thinking"):
            detail = "Da una respuesta completa, con pasos claros, codigo cuando aporte valor y validacion."
        else:
            detail = "Da una respuesta breve, directa y accionable."
        return (
            "Eres un asistente senior de programacion en espanol. "
            "Usa el contexto local como material interno. "
            "Entrega una sola respuesta final profesional, sin separar por modulos. "
            "Si falta informacion, dilo en una frase y da el siguiente paso minimo. "
            f"{detail}"
        )

    @staticmethod
    def _build_user_content(message: str, context: str | None) -> str:
        return (
            f"Contexto disponible:\n{str(context or '').strip() or 'No hay contexto local disponible.'}\n\n"
            f"Pregunta del usuario:\n{message}\n\n"
            "Respuesta final:"
        )

    @staticmethod
    def _extract_text(response: Any) -> str:
        parts = []
        for block in getattr(response, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))
        return "\n".join(parts).strip()

    def _unavailable(self, started: float, error: str) -> dict[str, Any]:
        return {
            "source": "anthropic",
            "success": False,
            "answer": "",
            "content": "",
            "confidence": 0.0,
            "latency_ms": self._latency(started),
            "error": error,
            "metadata": {"model": self.model, "configured": bool(self.api_key)},
        }

    @staticmethod
    def _latency(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
