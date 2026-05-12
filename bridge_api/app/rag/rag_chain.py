from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.models.schemas import Source
from app.rag.retriever import retriever
from app.services.ai_service import ai_service


NO_DOCUMENT_ANSWER = (
    "No encontre suficiente informacion en los documentos cargados para responder con seguridad."
)


@dataclass(frozen=True)
class RagResult:
    answer: str
    sources: list[Source]
    model: str
    context: str


class RagChain:
    def answer(self, question: str, history_context: str = "", k: int | None = None) -> RagResult:
        sources = retriever.retrieve(question, k=k)
        context = self.build_context(sources)
        if not context.strip():
            return RagResult(
                answer=(
                    f"{NO_DOCUMENT_ANSWER}\n\n"
                    "Puedes agregar documentos a la carpeta conocimiento y ejecutar /api/index para ampliar mi base RAG."
                ),
                sources=[],
                model="rag-no-context",
                context="",
            )

        prompt = self._build_prompt(question, context, history_context)
        answer, model = ai_service.generate_from_prompt(
            prompt,
            fallback_context=context,
            fallback_message=question,
        )
        answer = self._ensure_sources_section(answer, sources)
        return RagResult(answer=answer, sources=sources, model=model, context=context)

    def build_context(self, sources: list[Source]) -> str:
        blocks: list[str] = []
        used_chars = 0
        for index, source in enumerate(sources, start=1):
            title = source.title or source.source or f"Fuente {index}"
            page = f", pagina {source.page}" if source.page else ""
            prefix = f"[Fuente {index}: {title}{page} | {source.source}]"
            block = f"{prefix}\n{source.text.strip()}"
            remaining = settings.max_context_chars - used_chars
            if remaining <= 0:
                break
            if len(block) > remaining:
                block = block[:remaining].rstrip()
            blocks.append(block)
            used_chars += len(block)
        return "\n\n".join(blocks)

    def _build_prompt(self, question: str, context: str, history_context: str) -> str:
        return f"""Eres JAH AI, un asistente de programacion conectado a una base de conocimiento documental. Responde unicamente usando el contexto proporcionado cuando sea posible. Si el contexto no contiene la respuesta, dilo claramente. No inventes datos. Explica de forma clara, tecnica y util para un estudiante o desarrollador.

Historial reciente:
{history_context or "Sin historial relevante."}

Pregunta del usuario:
{question}

Contexto recuperado:
{context}

Reglas:
- Prioriza la informacion de los documentos.
- Si la respuesta no esta sustentada por el contexto, empieza con: "{NO_DOCUMENT_ANSWER}"
- Al final agrega una seccion "Fuentes consultadas" con los archivos usados.

Respuesta:
"""

    def _ensure_sources_section(self, answer: str, sources: list[Source]) -> str:
        clean_answer = (answer or "").strip()
        if "Fuentes consultadas" in clean_answer:
            return clean_answer
        lines = ["", "Fuentes consultadas:"]
        seen: set[str] = set()
        for source in sources:
            label = source.source or source.title
            if not label or label in seen:
                continue
            seen.add(label)
            page = f" (pagina {source.page})" if source.page else ""
            lines.append(f"- {label}{page}")
        return clean_answer + "\n".join(lines)


rag_chain = RagChain()
