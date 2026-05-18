from __future__ import annotations

import logging
import re
import time
import json
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from app.config import settings
from app.models.schemas import ChatRequest, Source
from app.rag.rag_chain import NO_DOCUMENT_ANSWER, RagResult, rag_chain
from app.services.ai_service import ai_service
from app.services.brain_service import brain_service
from app.services.web_search_service import WebSearchResult, web_search_service


LOGGER = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class RetrievalPlan:
    intent: UserIntent
    rag_mode: RagMode
    message: str
    use_memory: bool
    use_rag: bool
    use_web: bool
    use_uploaded_files: bool
    top_k: int
    threshold: float
    reason: str
    sources_allowed: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowAnswer:
    answer: str
    sources: list[Source]
    model: str
    context: str
    brain_parts: list[str]
    workflow: dict
    smart_search: dict | None = None
    used_smart_search: bool = False


class IntentClassifier:
    greeting_words = {
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
    social_words = {
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
    continuation_re = re.compile(
        r"\b(sigue|continua|continuemos|prosigue|hazlo|aplicalo|corrige eso|arregla eso|"
        r"agrega(lo)?|anadelo|sumalo|eso|lo anterior|ese cambio|esa parte)\b",
        re.I,
    )
    memory_re = re.compile(
        r"\b(recuerdame|que habiamos|que definimos|donde quedamos|sesion anterior|"
        r"historial|memoria|preferencia|carpeta usamos|arquitectura definida|progreso)\b",
        re.I,
    )
    document_grounded_re = re.compile(
        r"\b(que dice|segun|basado en|con base en|revisa|consulta|lee|usa|busca en|recupera).{0,80}"
        r"(documento|documentos|archivo|archivos|pdf|notas|obsidian|vault|tutor_ia|tutoria|base de conocimiento|memoria)\b|"
        r"\b(documento cargado|documentos cargados|mis notas|mis documentos|mi vault|contenido de tutor_ia|segun tutoria)\b",
        re.I,
    )
    rag_required_re = re.compile(r"\b(solo con|unicamente con|estrictamente con|cita fuentes|con fuentes|evidencia documental)\b", re.I)
    code_generation_re = re.compile(r"\b(crea|generame|genera|escribe|implementa|haz|construye|arma).{0,80}\b(codigo|html|css|js|javascript|python|api|endpoint|componente|script|funcion|clase|sitio web|pagina|landing|prompt|codex)\b", re.I)
    creative_re = re.compile(r"\b(ideas|propone|propon|disena|diseña|copy|texto|contenido|landing page|marca|estilo|secciones|hero|panaderia|negocio|sitio web)\b", re.I)
    planning_re = re.compile(r"\b(plan|arquitectura|estructura|roadmap|flujo|estrategia|organiza|secciones|mapa|proyecto|sitio web|landing)\b", re.I)
    database_re = re.compile(
        r"\b(sql server|t-sql|tutoria|tutoria\.sql|ssms|sqlserver|base de datos|"
        r"sesiones|session_id|memoria persistente|historial|procedimiento almacenado|stored procedure)\b",
        re.I,
    )
    external_re = re.compile(
        r"\b(busca informacion actual|busca en internet|verifica.*(reciente|actual|oficial)|"
        r"fuentes oficiales|documentacion oficial|latest|ultima version|mas reciente|busca en la web|consulta la web)\b",
        re.I,
    )
    technical_re = re.compile(
        r"\b(codigo|code|programa|programacion|python|javascript|html|css|api|endpoint|bug|error|"
        r"debug|funcion|clase|script|sql server|t-sql|tutoria|rag|embedding|chroma|"
        r"backend|frontend|base de datos|workflow|orquestacion|integracion|ultron|"
        r"asistente de programacion|deploy|github|test|refactor|prompt|codex|explica|como hacer|ayuda)\b",
        re.I,
    )

    def classify(self, message: str) -> UserIntent:
        normalized = self._normalize(message)
        if not normalized:
            return UserIntent.SOCIAL_RESPONSE
        if self._is_short_match(normalized, self.greeting_words):
            return UserIntent.GREETING
        if self._is_short_match(normalized, self.social_words):
            return UserIntent.SOCIAL_RESPONSE
        if self.external_re.search(normalized):
            return UserIntent.EXTERNAL_KNOWLEDGE_QUERY
        if self.memory_re.search(normalized):
            return UserIntent.MEMORY_QUERY
        if self.rag_required_re.search(normalized):
            return UserIntent.RAG_REQUIRED_QUERY
        if self.document_grounded_re.search(normalized):
            return UserIntent.DOCUMENT_GROUNDED_QUERY
        if self.database_re.search(normalized):
            return UserIntent.DATABASE_QUERY
        if self.continuation_re.search(normalized):
            return UserIntent.CONTINUATION
        if self.code_generation_re.search(normalized):
            return UserIntent.CODE_GENERATION_TASK
        if self.creative_re.search(normalized):
            return UserIntent.GENERAL_CREATIVE_TASK
        if self.planning_re.search(normalized):
            return UserIntent.PROJECT_PLANNING_TASK
        if self.technical_re.search(normalized) or len(normalized.split()) > 12:
            return UserIntent.GENERAL_TECHNICAL_HELP
        return UserIntent.SOCIAL_RESPONSE

    def _is_short_match(self, normalized: str, candidates: set[str]) -> bool:
        compact = re.sub(r"[!?.;,\s]+$", "", normalized).strip()
        if compact in candidates:
            return True
        return len(compact.split()) <= 4 and any(compact.startswith(candidate) for candidate in candidates)

    def _normalize(self, value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        text = "".join(char for char in text if not unicodedata.combining(char))
        text = re.sub(r"\s+", " ", text)
        return text


intent_classifier = IntentClassifier()


def classify_user_intent(message: str) -> UserIntent:
    return intent_classifier.classify(message)


def should_use_memory_only(message: str, conversation_state: str = "") -> bool:
    intent = classify_user_intent(message)
    if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE, UserIntent.MEMORY_QUERY}:
        return True
    return intent == UserIntent.CONTINUATION and bool(conversation_state.strip())


def should_use_external_sources(message: str) -> bool:
    return classify_user_intent(message) == UserIntent.EXTERNAL_KNOWLEDGE_QUERY


def should_use_rag(message: str, conversation_state: str = "") -> bool:
    return rag_mode_for_intent(classify_user_intent(message), conversation_state) != RagMode.NONE


def rag_mode_for_intent(intent: UserIntent, conversation_state: str = "") -> RagMode:
    if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE}:
        return RagMode.NONE
    if intent in {UserIntent.MEMORY_QUERY, UserIntent.DOCUMENT_GROUNDED_QUERY, UserIntent.RAG_REQUIRED_QUERY}:
        return RagMode.REQUIRED
    if intent == UserIntent.CONTINUATION and conversation_state.strip():
        return RagMode.NONE
    return RagMode.OPTIONAL


def route_response_strategy(intent: UserIntent, retrieval_result: list[Source], conversation_state: str = "") -> str:
    rag_mode = rag_mode_for_intent(intent, conversation_state)
    if rag_mode == RagMode.NONE:
        return "DIRECT_RESPONSE"
    if retrieval_result:
        return "DOCUMENT_GROUNDED_RESPONSE"
    if rag_mode == RagMode.REQUIRED:
        return "DOCUMENT_INSUFFICIENT"
    return "GENERAL_ASSISTANT_RESPONSE"


class QueryPlanner:
    follow_up_re = re.compile(r"\b(eso|esto|este|esta|anterior|lo mismo|continuemos|sigue|expl[ií]calo)\b", re.I)

    def plan(self, payload: ChatRequest, history_context: str) -> list[str]:
        message = payload.message.strip()
        queries = [message]

        focus = self._history_focus(history_context)
        if focus and self.follow_up_re.search(message):
            queries.append(f"{message}\nContexto de seguimiento: {focus}")

        domain_terms = self._domain_terms(message)
        if domain_terms:
            queries.append(f"{message}\nTerminos tecnicos relacionados: {', '.join(domain_terms)}")

        return self._dedupe(queries)[: max(1, settings.rag_max_queries)]

    def _history_focus(self, history_context: str) -> str:
        lines = []
        for line in str(history_context or "").splitlines():
            clean = line.strip()
            if clean.startswith("Usuario:") or clean.startswith("- Usuario:"):
                lines.append(clean.split(":", 1)[-1].strip())
        return " | ".join(lines[-3:])[:700]

    def _domain_terms(self, message: str) -> list[str]:
        normalized = message.lower()
        terms: list[str] = []
        if "pl" in normalized and "pgsql" in normalized or "postgres" in normalized:
            terms.extend(["PostgreSQL", "PL/pgSQL", "funciones", "procedimientos almacenados"])
        if "sql server" in normalized or "tutoria" in normalized or "ssms" in normalized or "t-sql" in normalized:
            terms.extend(["SQL Server", "T-SQL", "TUTORIA", "SSMS 22", "memoria persistente"])
        if "data science" in normalized or "datos" in normalized:
            terms.extend(["Data Science", "analisis de datos", "modelado", "machine learning"])
        if "base" in normalized and "dato" in normalized or "sql" in normalized:
            terms.extend(["SQL", "modelo relacional", "normalizacion", "consultas"])
        if "rag" in normalized or "cerebro" in normalized:
            terms.extend(["retrieval augmented generation", "embeddings", "ChromaDB", "memoria contextual"])
        return self._dedupe(terms)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            clean = re.sub(r"\s+", " ", value).strip()
            key = clean.lower()
            if clean and key not in seen:
                seen.add(key)
                output.append(clean)
        return output


class WorkflowService:
    def __init__(self) -> None:
        self.query_planner = QueryPlanner()

    def answer(
        self,
        payload: ChatRequest,
        *,
        history_context: str = "",
        uploaded_sources: list[Source] | None = None,
    ) -> WorkflowAnswer:
        started = time.perf_counter()
        steps: list[dict] = []
        uploaded_sources = uploaded_sources or []
        brain_parts = ["workflow_orchestrator", "chat_summarization"]
        retrieval_plan = self._plan_retrieval(payload, history_context, bool(uploaded_sources))
        brain_parts.append(f"intent_{retrieval_plan.intent.value.lower()}")

        steps.append(
            {
                "name": "intent_classification",
                "intent": retrieval_plan.intent.value,
                "rag_mode": retrieval_plan.rag_mode.value,
                "use_memory": retrieval_plan.use_memory,
                "use_rag": retrieval_plan.use_rag,
                "use_web": retrieval_plan.use_web,
                "sources_allowed": retrieval_plan.sources_allowed,
                "reason": retrieval_plan.reason,
                "duration_ms": self._elapsed_ms(started),
            }
        )

        if retrieval_plan.rag_mode == RagMode.NONE and retrieval_plan.intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE}:
            answer = self._direct_conversation_answer(payload, retrieval_plan.intent)
            workflow = {
                "pattern": "plan_act_evaluate",
                "mode": payload.response_profile or "balanced",
                "intent": retrieval_plan.intent.value,
                "rag_mode": retrieval_plan.rag_mode.value,
                "rag_used": False,
                "sources_called": [],
                "queries": [],
                "steps": steps
                + [
                    {
                        "name": "direct_response",
                        "reason": retrieval_plan.reason,
                        "duration_ms": self._elapsed_ms(started),
                    }
                ],
                "elapsed_ms": self._elapsed_ms(started),
                "rag_sources": 0,
                "web_sources": 0,
                "uploaded_sources": 0,
            }
            self._log_retrieval_event(
                {
                    "intent": retrieval_plan.intent.value,
                    "rag_used": False,
                    "sources_called": [],
                    "reason": retrieval_plan.reason,
                    "elapsed_ms": self._elapsed_ms(started),
                }
            )
            return WorkflowAnswer(
                answer=answer,
                sources=[],
                model="direct-conversation",
                context="",
                brain_parts=self._dedupe_strings(["workflow_orchestrator", f"intent_{retrieval_plan.intent.value.lower()}"]),
                workflow=workflow,
                smart_search={"enabled": False, "provider": "", "message": "Direct conversational response", "results": 0},
                used_smart_search=False,
            )

        queries = self.query_planner.plan(payload, history_context) if retrieval_plan.use_rag else [payload.message.strip()]
        steps.append(
            {
                "name": "query_planning",
                "queries": queries,
                "enabled": retrieval_plan.use_rag,
                "duration_ms": self._elapsed_ms(started),
            }
        )

        rag_started = time.perf_counter()
        rag_sources, rag_metrics = self._retrieve_rag_sources(queries, payload, retrieval_plan) if retrieval_plan.use_rag else ([], self._empty_rag_metrics(retrieval_plan))
        if retrieval_plan.use_rag:
            brain_parts.append("rag_chromadb")
        steps.append(
            {
                "name": "rag_retrieval",
                "enabled": bool(retrieval_plan.use_rag),
                "sources": len(rag_sources),
                **rag_metrics,
                "duration_ms": self._duration_ms(rag_started),
            }
        )

        web_started = time.perf_counter()
        web_result = self._search_web(payload) if retrieval_plan.use_web else WebSearchResult(False, "", [])
        if retrieval_plan.use_web:
            brain_parts.append("web_search")
        steps.append(
            {
                "name": "web_search",
                "enabled": retrieval_plan.use_web,
                "provider": web_result.provider,
                "sources": len(web_result.sources),
                "message": web_result.message,
                "duration_ms": self._duration_ms(web_started),
            }
        )

        active_uploaded_sources = uploaded_sources if retrieval_plan.use_uploaded_files else []
        sources = self._dedupe_sources(rag_sources + web_result.sources + active_uploaded_sources)
        context = self._build_context(rag_sources, web_result.sources, active_uploaded_sources)
        response_strategy = route_response_strategy(retrieval_plan.intent, sources, history_context)
        if not context.strip():
            if response_strategy == "DOCUMENT_INSUFFICIENT":
                answer = self._memory_answer(payload, history_context)
                if retrieval_plan.intent != UserIntent.MEMORY_QUERY:
                    answer = (
                        "No encontre evidencia suficiente en los documentos consultados para afirmarlo con seguridad. "
                        "Puedo volver a buscar si me indicas el archivo, nota, carpeta o tema exacto."
                    )
                model = "document-insufficient"
            else:
                answer, model = self._generate_general_answer(payload, history_context)
            if retrieval_plan.use_web and web_result.message:
                answer += f"\n\nBusqueda inteligente: {web_result.message}"
        else:
            prompt = self._build_prompt(payload, context, history_context, web_result)
            answer, model = ai_service.generate_from_prompt(
                prompt,
                fallback_context=context,
                fallback_message=payload.message,
            )
            answer = self._ensure_sources_section(answer, sources, payload.show_sources)

        steps.append(
            {
                "name": "answer_synthesis",
                "context_chars": len(context),
                "duration_ms": self._elapsed_ms(started),
            }
        )

        workflow = {
            "pattern": "plan_act_evaluate",
            "mode": payload.response_profile or "balanced",
            "intent": retrieval_plan.intent.value,
            "rag_mode": retrieval_plan.rag_mode.value,
            "response_strategy": response_strategy,
            "rag_used": bool(rag_sources),
            "sources_called": retrieval_plan.sources_allowed,
            "queries": queries,
            "steps": steps,
            "elapsed_ms": self._elapsed_ms(started),
            "rag_sources": len(rag_sources),
            "web_sources": len(web_result.sources),
            "uploaded_sources": len(active_uploaded_sources),
            "retrieval_threshold": retrieval_plan.threshold,
        }

        self._log_retrieval_event(
            {
                "intent": retrieval_plan.intent.value,
                "rag_mode": retrieval_plan.rag_mode.value,
                "response_strategy": response_strategy,
                "rag_used": bool(rag_sources),
                "sources_called": retrieval_plan.sources_allowed,
                "retrieved_chunks": rag_metrics.get("retrieved_chunks", 0),
                "accepted_chunks": rag_metrics.get("accepted_chunks", 0),
                "discarded_chunks": rag_metrics.get("discarded_chunks", 0),
                "threshold": retrieval_plan.threshold,
                "highest_score": rag_metrics.get("highest_score", 0),
                "average_score": rag_metrics.get("average_score", 0),
                "elapsed_ms": self._elapsed_ms(started),
                "reason": retrieval_plan.reason,
            }
        )

        return WorkflowAnswer(
            answer=answer,
            sources=sources,
            model=model,
            context=context,
            brain_parts=self._dedupe_strings(brain_parts),
            workflow=workflow,
            smart_search={
                "enabled": retrieval_plan.use_web,
                "provider": web_result.provider,
                "message": web_result.message,
                "results": len(web_result.sources),
            },
            used_smart_search=bool(web_result.sources),
        )

    def _plan_retrieval(self, payload: ChatRequest, history_context: str, has_uploads: bool) -> RetrievalPlan:
        intent = classify_user_intent(payload.message)
        rag_mode = rag_mode_for_intent(intent, history_context)
        target_k = min(
            payload.top_k or payload.k or settings.rag_top_k or settings.response_top_k,
            settings.rag_max_context_chunks,
        )
        threshold = settings.tutor_ia_score_threshold
        sources_allowed: list[str] = []

        if intent in {UserIntent.GREETING, UserIntent.SOCIAL_RESPONSE}:
            return RetrievalPlan(
                intent=intent,
                rag_mode=RagMode.NONE,
                message=payload.message,
                use_memory=False,
                use_rag=False,
                use_web=False,
                use_uploaded_files=False,
                top_k=0,
                threshold=threshold,
                reason="Direct conversational response",
                sources_allowed=[],
            )

        use_web = bool(self._web_enabled(payload) and should_use_external_sources(payload.message))
        use_rag = bool(payload.use_rag and rag_mode != RagMode.NONE)
        use_memory = True
        use_uploaded_files = has_uploads and intent in {
            UserIntent.GENERAL_TECHNICAL_HELP,
            UserIntent.GENERAL_CREATIVE_TASK,
            UserIntent.CODE_GENERATION_TASK,
            UserIntent.PROJECT_PLANNING_TASK,
            UserIntent.DATABASE_QUERY,
            UserIntent.DOCUMENT_GROUNDED_QUERY,
            UserIntent.RAG_REQUIRED_QUERY,
            UserIntent.EXTERNAL_KNOWLEDGE_QUERY,
        }

        if intent == UserIntent.MEMORY_QUERY:
            use_rag = bool(payload.use_rag)
            target_k = min(target_k, 2)
        elif intent in {UserIntent.DOCUMENT_GROUNDED_QUERY, UserIntent.RAG_REQUIRED_QUERY}:
            threshold = max(settings.obsidian_score_threshold, settings.tutor_ia_score_threshold, settings.rag_score_threshold)
        elif intent == UserIntent.EXTERNAL_KNOWLEDGE_QUERY:
            threshold = settings.official_sources_score_threshold
            target_k = min(target_k, 3)
        elif intent in {
            UserIntent.GENERAL_TECHNICAL_HELP,
            UserIntent.GENERAL_CREATIVE_TASK,
            UserIntent.CODE_GENERATION_TASK,
            UserIntent.PROJECT_PLANNING_TASK,
            UserIntent.DATABASE_QUERY,
        }:
            threshold = settings.tutor_ia_score_threshold

        if use_memory:
            sources_allowed.append("memory")
        if use_rag:
            sources_allowed.append("tutor_ia")
        if intent in {UserIntent.DOCUMENT_GROUNDED_QUERY, UserIntent.RAG_REQUIRED_QUERY} and use_rag:
            sources_allowed.append("obsidian_if_requested")
        if use_web:
            sources_allowed.append("official_sources")
        if use_uploaded_files:
            sources_allowed.append("uploaded_files")

        reason = {
            UserIntent.CONTINUATION: "Continuation can use compact memory first",
            UserIntent.MEMORY_QUERY: "Memory query is answered from contextual memory",
            UserIntent.GENERAL_TECHNICAL_HELP: "General technical help can use RAG as optional support",
            UserIntent.GENERAL_CREATIVE_TASK: "Creative task can use RAG as optional support",
            UserIntent.CODE_GENERATION_TASK: "Code generation can use RAG as optional support",
            UserIntent.PROJECT_PLANNING_TASK: "Project planning can use RAG as optional support",
            UserIntent.DATABASE_QUERY: "Database query can use SQL Server/TUTORIA context as optional support unless documents are required",
            UserIntent.DOCUMENT_GROUNDED_QUERY: "Document-grounded query requires reliable local evidence",
            UserIntent.RAG_REQUIRED_QUERY: "User explicitly required documentary evidence",
            UserIntent.EXTERNAL_KNOWLEDGE_QUERY: "External knowledge query allows web sources",
        }.get(intent, "Intent-based retrieval plan")

        return RetrievalPlan(
            intent=intent,
            rag_mode=rag_mode,
            message=payload.message,
            use_memory=use_memory,
            use_rag=use_rag,
            use_web=use_web,
            use_uploaded_files=use_uploaded_files,
            top_k=max(1, target_k),
            threshold=threshold,
            reason=reason,
            sources_allowed=sources_allowed,
        )

    def _direct_conversation_answer(self, payload: ChatRequest, intent: UserIntent) -> str:
        name = (payload.user_name or "Abraham").strip() or "Abraham"
        if intent == UserIntent.GREETING:
            return f"Hola, {name}. Continuamos con ULTRON o con el asistente de programacion?"
        return "Con gusto. Continuamos cuando quieras."

    def _memory_answer(self, payload: ChatRequest, history_context: str) -> str:
        compact_history = re.sub(r"\s+", " ", history_context or "").strip()
        if not compact_history:
            return "No tengo suficiente memoria contextual para responder eso todavia."
        return (
            "Esto es lo que conservo del hilo reciente: "
            f"{compact_history[:900]}"
            "\n\nDime que parte quieres retomar y sigo desde ahi."
        )

    def _generate_general_answer(self, payload: ChatRequest, history_context: str) -> tuple[str, str]:
        prompt = self._build_general_prompt(payload, history_context)
        answer, model = ai_service.generate_from_prompt(
            prompt,
            fallback_context="",
            fallback_message=payload.message,
        )
        if model == "fallback-local" and self._looks_like_context_failure(answer):
            return self._local_general_fallback(payload), "fallback-general-local"
        return answer, model

    def _build_general_prompt(self, payload: ChatRequest, history_context: str) -> str:
        return f"""Eres JAH AI, asistente de programacion de Abraham Hernandez.
Responde en espanol natural, claro y util.
Esta consulta NO depende obligatoriamente de documentos. Si no hay contexto RAG, responde con conocimiento general de programacion, diseno, arquitectura o producto.
No digas que faltan documentos salvo que el usuario haya pedido explicitamente responder segun documentos, notas, memoria o archivos.
Si conviene, cierra con una opcion breve para adaptar la respuesta al proyecto o documentos del usuario.

Memoria contextual compacta:
{history_context or "Sin historial relevante."}

Pregunta del usuario:
{payload.message}

Respuesta:
"""

    def _local_general_fallback(self, payload: ChatRequest) -> str:
        message = payload.message.lower()
        if any(term in message for term in ["panaderia", "panadería", "landing", "sitio web", "pagina web", "página web"]):
            return (
                "Claro. Para una panaderia te recomiendo una web sencilla y muy visual: inicio con foto de productos, "
                "catalogo por categorias, pedidos por WhatsApp, ubicacion con mapa, horarios, testimonios y contacto.\n\n"
                "Una buena primera estructura seria: `index.html`, `styles.css` y una seccion hero con llamada a la accion. "
                "Tambien conviene mostrar productos destacados, combos del dia y un boton fijo de WhatsApp.\n\n"
                "Puedo adaptarlo a tus documentos o a un proyecto especifico si me indicas cual."
            )
        if any(term in message for term in ["html", "css", "javascript", "codigo", "programacion", "programación"]):
            return (
                "Claro. Podemos resolverlo con una estructura simple: define el objetivo, crea el HTML semantico, "
                "aplica estilos responsivos con CSS y luego agrega interaccion con JavaScript solo si hace falta.\n\n"
                "Para empezar: usa `header`, `main`, `section` y `footer`; separa estilos en `styles.css`; y prueba en movil "
                "antes de agregar detalles visuales. Puedo darte el codigo base en el siguiente paso."
            )
        return (
            "Claro. Puedo ayudarte con eso sin depender de documentos. Te propongo empezar definiendo el objetivo, "
            "los elementos principales, el flujo de usuario y luego convertirlo en codigo o en un plan de implementacion.\n\n"
            "Puedo adaptarlo a tus documentos o a un proyecto especifico si me indicas cual."
        )

    def _looks_like_context_failure(self, answer: str) -> bool:
        normalized = re.sub(r"\s+", " ", str(answer or "").lower())
        return any(
            phrase in normalized
            for phrase in [
                "no pude contactar el modelo",
                "no encontrar contexto suficiente",
                "no encontre contexto suficiente",
                "no se encontro contexto local relevante",
                "verifica que tutor_ia",
            ]
        )

    def _retrieve_rag_sources(
        self,
        queries: list[str],
        payload: ChatRequest,
        retrieval_plan: RetrievalPlan,
    ) -> tuple[list[Source], dict]:
        target_k = retrieval_plan.top_k
        per_query_k = max(target_k, settings.rag_min_relevant_chunks, 2)
        sources: list[Source] = []
        for query in queries:
            try:
                sources.extend(brain_service.search(query, k=per_query_k))
            except Exception as exc:
                LOGGER.warning("RAG query failed query=%s: %s", query, exc)
        deduped = self._dedupe_sources(sources)
        filtered = self._filter_relevant_sources(deduped, retrieval_plan)
        ranked = sorted(filtered, key=lambda item: item.score if item.score is not None else 0, reverse=True)
        metrics = self._rag_metrics(deduped, ranked, retrieval_plan.threshold)
        return ranked[:target_k], metrics

    def _filter_relevant_sources(self, sources: list[Source], retrieval_plan: RetrievalPlan) -> list[Source]:
        relevant: list[Source] = []
        for source in sources:
            threshold = self._threshold_for_source(source, retrieval_plan)
            score = source.score
            if score is None:
                continue
            if score >= threshold:
                if not self._source_matches_intent(source, retrieval_plan):
                    continue
                relevant.append(source)
        return relevant

    def _threshold_for_source(self, source: Source, retrieval_plan: RetrievalPlan) -> float:
        source_text = " ".join(
            [
                source.source or "",
                source.title or "",
                source.type or "",
                str(source.metadata.get("source") or ""),
                str(source.metadata.get("path") or ""),
            ]
        ).lower()
        if "obsidian" in source_text or ".md" in source_text or ".canvas" in source_text:
            return max(retrieval_plan.threshold, settings.obsidian_score_threshold)
        return max(retrieval_plan.threshold, settings.tutor_ia_score_threshold, settings.rag_score_threshold)

    def _source_matches_intent(self, source: Source, retrieval_plan: RetrievalPlan) -> bool:
        query = self._normalize_for_filter(retrieval_plan.message)
        source_text = self._normalize_for_filter(
            " ".join(
                [
                    source.source or "",
                    source.title or "",
                    source.type or "",
                    str(source.metadata.get("source") or ""),
                    str(source.metadata.get("path") or ""),
                    str(source.metadata.get("category") or ""),
                    str(source.metadata.get("tags") or ""),
                ]
            )
        )
        wants_database = any(term in query for term in ["sql server", "t-sql", "tutoria", "ssms", "session", "sesion", "memoria persistente"])
        wants_marketing = any(term in query for term in ["marketing", "seo", "campana", "campaña", "ventas", "copy"])
        wants_mysql = "mysql" in query
        wants_postgres = any(term in query for term in ["postgres", "postgresql", "plpgsql", "pl/pgsql"])

        if not wants_marketing and any(term in source_text for term in ["marketing_digital", "marketing digital", "marketing"]):
            return False
        if wants_database:
            if "mysql" in source_text and not wants_mysql:
                return False
            if any(term in source_text for term in ["postgresql", "postgres", "plpgsql", "pl/pgsql"]) and not wants_postgres:
                return False
        if retrieval_plan.intent == UserIntent.DATABASE_QUERY:
            database_markers = [
                "sql",
                "sql server",
                "t-sql",
                "tutoria",
                "base",
                "dato",
                "sesion",
                "session",
                "memoria",
                "backend",
                "programacion",
                "programming",
            ]
            if any(term in source_text for term in ["marketing_digital", "marketing digital", "mysql"]) and not any(marker in source_text for marker in database_markers):
                return False
        return True

    def _normalize_for_filter(self, value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").lower())
        text = "".join(char for char in text if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", text)

    def _rag_metrics(self, retrieved: list[Source], accepted: list[Source], threshold: float) -> dict:
        scores = [source.score for source in retrieved if source.score is not None]
        accepted_scores = [source.score for source in accepted if source.score is not None]
        return {
            "retrieved_chunks": len(retrieved),
            "accepted_chunks": len(accepted),
            "discarded_chunks": max(0, len(retrieved) - len(accepted)),
            "threshold": threshold,
            "highest_score": round(max(scores), 4) if scores else 0,
            "average_score": round(sum(scores) / len(scores), 4) if scores else 0,
            "accepted_highest_score": round(max(accepted_scores), 4) if accepted_scores else 0,
        }

    def _empty_rag_metrics(self, retrieval_plan: RetrievalPlan) -> dict:
        return {
            "retrieved_chunks": 0,
            "accepted_chunks": 0,
            "discarded_chunks": 0,
            "threshold": retrieval_plan.threshold,
            "highest_score": 0,
            "average_score": 0,
            "accepted_highest_score": 0,
        }

    def _search_web(self, payload: ChatRequest) -> WebSearchResult:
        return web_search_service.search(payload.message, max_results=settings.web_search_max_results)

    def _web_enabled(self, payload: ChatRequest) -> bool:
        return bool(payload.use_web or payload.smart_search)

    def _log_retrieval_event(self, payload: dict) -> None:
        LOGGER.info("retrieval_orchestration %s", json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _build_context(
        self,
        rag_sources: list[Source],
        web_sources: list[Source],
        uploaded_sources: list[Source],
    ) -> str:
        blocks: list[str] = []
        rag_context = rag_chain.build_context(rag_sources)
        if rag_context:
            blocks.append("Contexto RAG recuperado de tutor_ia:\n" + rag_context)
        if web_sources:
            web_blocks = []
            for index, source in enumerate(web_sources, start=1):
                title = source.title or source.url or f"Resultado web {index}"
                url = f" | {source.url}" if source.url else ""
                web_blocks.append(f"[Web {index}: {title}{url}]\n{source.text}")
            blocks.append("Contexto de busqueda web en tiempo real:\n" + "\n\n".join(web_blocks))
        if uploaded_sources:
            upload_blocks = []
            for source in uploaded_sources:
                upload_blocks.append(f"[Archivo subido: {source.title or source.source}]\n{source.text}")
            blocks.append("Archivos subidos durante este turno:\n" + "\n\n".join(upload_blocks))
        return "\n\n".join(blocks)[: settings.max_context_chars]

    def _build_prompt(
        self,
        payload: ChatRequest,
        context: str,
        history_context: str,
        web_result: WebSearchResult,
    ) -> str:
        source_policy = (
            "Incluye una seccion breve 'Fuentes consultadas' solo con fuentes realmente usadas."
            if payload.show_sources
            else "Usa las fuentes como contexto interno y no agregues una lista extensa de fuentes."
        )
        web_note = ""
        if self._web_enabled(payload) and web_result.message and not web_result.sources:
            web_note = f"\nNota de busqueda web: {web_result.message}\n"
        return f"""Eres JAH AI, asistente de programacion de Abraham Hernandez.
Trabajas como un agente unico con herramientas: memoria compacta, RAG local tutor_ia, archivos subidos y busqueda web opcional.
Responde en espanol claro, tecnico y accionable. Prioriza el contexto local de tutor_ia cuando sea relevante. Para persistencia estructurada de ULTRON usa SQL Server / TUTORIA de SSMS 22; menciona PostgreSQL solo si el usuario pregunta por ese tema documental.
Si haces una inferencia fuera del contexto, marcala como inferencia. No inventes fuentes ni resultados web.

Memoria contextual compacta:
{history_context or "Sin historial relevante."}

Contexto de herramientas:
{context}
{web_note}
Pregunta del usuario:
{payload.message}

Reglas de respuesta:
- Mantén continuidad con preferencias y progreso del usuario cuando existan en la memoria.
- Si el contexto no alcanza para responder con seguridad, dilo de forma breve y pide el dato faltante.
- {source_policy}
- Evita cambiar temas visuales o proponer redisenos si el usuario pidio conservar la visualizacion.

Respuesta:
"""

    def _ensure_sources_section(self, answer: str, sources: list[Source], show_sources: bool) -> str:
        clean_answer = (answer or "").strip()
        if not show_sources or "Fuentes consultadas" in clean_answer:
            return clean_answer
        lines = ["", "Fuentes consultadas:"]
        seen: set[str] = set()
        for source in sources[:8]:
            label = source.url or source.source or source.title
            if not label or label in seen:
                continue
            seen.add(label)
            page = f" (pagina {source.page})" if source.page else ""
            lines.append(f"- {label}{page}")
        return clean_answer + "\n" + "\n".join(lines)

    def _dedupe_sources(self, sources: list[Source]) -> list[Source]:
        seen: set[str] = set()
        output: list[Source] = []
        for source in sources:
            key = "|".join(
                [
                    str(source.source or ""),
                    str(source.url or ""),
                    str(source.page or ""),
                    str(source.metadata.get("chunk_hash") or ""),
                    str(source.text[:120] or ""),
                ]
            ).lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(source)
        return output

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                output.append(value)
        return output

    def _elapsed_ms(self, started: float) -> int:
        return self._duration_ms(started)

    def _duration_ms(self, started: float) -> int:
        return int(round((time.perf_counter() - started) * 1000))


workflow_service = WorkflowService()
