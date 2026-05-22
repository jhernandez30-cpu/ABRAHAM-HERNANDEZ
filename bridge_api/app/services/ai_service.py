from __future__ import annotations

import logging

import requests

from app.config import settings


LOGGER = logging.getLogger(__name__)


class AIService:
    def generate_answer(self, message: str, context: str, history_context: str = "") -> tuple[str, str]:
        prompt = self._build_prompt(message, context, history_context)
        return self.generate_from_prompt(prompt, fallback_context=context, fallback_message=message)

    def generate_from_prompt(
        self,
        prompt: str,
        *,
        fallback_context: str = "",
        fallback_message: str = "",
    ) -> tuple[str, str]:
        if settings.model_provider != "ollama" or not settings.ollama_base_url:
            LOGGER.info("No remote model provider configured; using deterministic fallback answer.")
            return self._fallback_answer(fallback_message, fallback_context), "fallback-no-model"

        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": settings.ollama_num_ctx,
                        "num_predict": settings.ollama_num_predict,
                        "temperature": settings.ollama_temperature,
                    },
                },
                timeout=settings.ollama_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            answer = str(data.get("response") or "").strip()
            if answer:
                return answer, settings.model_name
        except Exception as exc:
            LOGGER.warning("Ollama generation failed: %s", exc)

        return self._fallback_answer(fallback_message, fallback_context), "fallback-model-unavailable"

    def _build_prompt(self, message: str, context: str, history_context: str) -> str:
        return f"""Eres JAH AI, un asistente de programacion para Abraham Hernandez.
Responde en espanol claro, con tono profesional y practico.
Usa el contexto local cuando sea relevante. Si el contexto no alcanza, dilo y responde con buenas practicas generales.
No inventes fuentes ni archivos.

HISTORIAL RECIENTE:
{history_context or "Sin historial relevante."}

CONTEXTO LOCAL TUTOR_IA:
{context or "No se encontro contexto local relevante."}

PREGUNTA DEL USUARIO:
{message}

RESPUESTA:
"""

    def _fallback_answer(self, message: str, context: str) -> str:
        if context.strip():
            excerpt = context.strip()[:1800]
            return (
                "El backend tutor_ia esta activo, pero no hay un proveedor de modelo IA disponible. "
                "Encontre contexto relevante en los documentos.\n\n"
                f"Pregunta: {message or 'sin pregunta'}\n\n"
                "Fragmentos relevantes recuperados:\n"
                f"{excerpt}\n\n"
                "Configura OLLAMA_BASE_URL, OPENAI_API_KEY o GEMINI_API_KEY en Railway para respuestas generativas completas."
            )
        return (
            "El backend tutor_ia esta respondiendo, pero no hay un proveedor de modelo IA disponible ni contexto RAG suficiente. "
            "Verifica en Railway TUTOR_IA_ROOT, los indices de vectores y las variables del proveedor de IA."
        )


ai_service = AIService()
