from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM

try:
    from agency_brain import build_agency_context, retrieve_agency_agents
except Exception:
    build_agency_context = None
    retrieve_agency_agents = None


BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = os.getenv("TUTOR_IA_PERSIST_DIR", str(BASE_DIR / "brain_db"))
COLLECTION_NAME = os.getenv("TUTOR_IA_COLLECTION", "conocimiento_fast")
LLM_MODEL = os.getenv("TUTOR_IA_LLM_MODEL", "llama3.2:1b")
RECOMMENDED_OLLAMA_MODEL = os.getenv("TUTOR_IA_RECOMMENDED_MODEL", "llama3.2:1b")
EMBED_DIM = int(os.getenv("TUTOR_IA_EMBED_DIM", "384"))
RETRIEVE_CANDIDATES = int(os.getenv("TUTOR_IA_RETRIEVE_CANDIDATES", "10"))
RESPONSE_TOP_K = int(os.getenv("TUTOR_IA_RESPONSE_TOP_K", "3"))
MAX_DOC_CONTEXT_CHARS = int(os.getenv("TUTOR_IA_MAX_DOC_CONTEXT_CHARS", "900"))
PROMPT_HISTORY_TURNS = int(os.getenv("TUTOR_IA_PROMPT_HISTORY_TURNS", "4"))
AGENCY_MATCH_LIMIT = int(os.getenv("TUTOR_IA_AGENCY_MATCH_LIMIT", "2"))
AGENCY_CONTEXT_CHARS = int(os.getenv("TUTOR_IA_AGENCY_CONTEXT_CHARS", "3000"))
LOW_MEMORY_MODEL_PRIORITY = ["llama3.2:1b", "qwen2.5:1.5b", "gemma3:1b", "llama3.2:3b"]
ALLOWED_GROUP_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
DEFAULT_ALLOWED_ORIGINS = "null,http://localhost,http://127.0.0.1,https://jhernandez30-cpu.github.io"
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv("TUTOR_IA_WEB_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
}
WEB_ACCESS_GROUPS = os.getenv("TUTOR_IA_WEB_GROUPS", "admin,public")

INTERACTION_MODES = {
    "study": {
        "label": "Potencia tu estudio",
        "instructions": """
Modo Potencia tu estudio:
- Actua como tutor paciente y claro.
- Explica conceptos complejos en terminos simples sin perder precision.
- Usa ejemplos del mundo real cuando el contexto lo permita.
- Refuerza la comprension con pasos, analogias, mini-resumenes o preguntas de practica.
- Si falta informacion en las fuentes, dilo con claridad.
""",
    },
    "organize": {
        "label": "Organiza tu pensamiento",
        "instructions": """
Modo Organiza tu pensamiento:
- Ordena el material en estructuras utiles: esquema, narrativa, secciones y conclusiones.
- Incluye puntos clave y evidencia de respaldo tomada del contexto.
- Ayuda a presentar temas con confianza: anticipa dudas, objeciones y transiciones.
- Si falta evidencia para una afirmacion, avisa y sugiere que fuente haria falta.
""",
    },
    "create": {
        "label": "Elabora nuevas ideas",
        "instructions": """
Modo Elabora nuevas ideas:
- Identifica patrones, tendencias, tensiones, oportunidades y huecos en el material.
- Genera ideas nuevas conectadas con las fuentes, no ocurrencias desconectadas.
- Distingue entre evidencia de las fuentes, inferencia razonable e hipotesis.
- Propone proximos pasos accionables cuando sea util.
""",
    },
    "agency": {
        "label": "Cerebro Agency",
        "instructions": """
Modo Cerebro Agency:
- Actua como orquestador de especialistas.
- Selecciona el enfoque de los agentes relevantes de Agency segun la pregunta.
- Integra metodologia de expertos con la evidencia recuperada de las fuentes privadas.
- Distingue entre hechos de las fuentes, criterio experto e inferencias.
- Entrega pasos concretos, criterios de validacion y siguientes acciones cuando sea util.
""",
    },
}

memory_store = {}


@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(COLLECTION_NAME)


@lru_cache(maxsize=8)
def get_llm(model_name):
    return OllamaLLM(model=model_name, temperature=0.3)


def get_installed_ollama_models():
    try:
        completed = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []

    if completed.returncode != 0:
        return []

    models = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def choose_llm_model(preferred_model=None):
    models = get_installed_ollama_models()
    preferred_model = preferred_model or LLM_MODEL
    for model in LOW_MEMORY_MODEL_PRIORITY:
        if model in models:
            return model
    if preferred_model in models:
        return preferred_model
    if LLM_MODEL in models:
        return LLM_MODEL
    return models[0] if models else None


def normalize_groups(groups):
    if isinstance(groups, str):
        raw_groups = groups.split(",")
    else:
        raw_groups = groups or []

    clean_groups = []
    for group in raw_groups:
        group = str(group).strip().lower()
        if group and ALLOWED_GROUP_RE.fullmatch(group) and group not in clean_groups:
            clean_groups.append(group)
    return clean_groups or ["public"]


def get_interaction_mode(mode_key):
    return INTERACTION_MODES.get(mode_key, INTERACTION_MODES["study"])


def trim_prompt_text(text, max_chars):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def embed_text(text):
    vector = [0.0] * EMBED_DIM
    tokens = TOKEN_RE.findall((text or "").lower())
    if not tokens:
        return vector

    previous = ""
    for token in tokens:
        features = [token]
        if previous:
            features.append(f"{previous}_{token}")
        previous = token

        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "little", signed=False)
            index = value % EMBED_DIM
            vector[index] += 1.0 if value & 1 else -1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [value / norm for value in vector]


def retrieve(question, user_groups=None, k=None, top_k=None, selected_sources=None):
    collection = get_collection()
    total_docs = collection.count()
    if total_docs == 0:
        return []

    k = k or RETRIEVE_CANDIDATES
    top_k = top_k or RESPONSE_TOP_K
    user_groups = normalize_groups(user_groups or ["public"])
    if selected_sources is not None:
        selected_sources = set(selected_sources)
        if not selected_sources:
            return []

    n_results = min(max(k, top_k * 8), total_docs)
    where_filter = None
    if "admin" not in user_groups:
        if len(user_groups) == 1:
            where_filter = {"access_group": user_groups[0]}
        else:
            where_filter = {"$or": [{"access_group": group} for group in user_groups]}

    try:
        result = collection.query(query_embeddings=[embed_text(question)], n_results=n_results, where=where_filter)
    except Exception:
        result = collection.query(query_embeddings=[embed_text(question)], n_results=n_results)

    docs = []
    if result.get("documents"):
        for index, doc_text in enumerate(result["documents"][0]):
            metadata = result["metadatas"][0][index]
            doc_group = metadata.get("access_group", "public")
            source = metadata.get("source", "")
            source_allowed = selected_sources is None or source in selected_sources
            if source_allowed and (doc_group in user_groups or "admin" in user_groups):
                docs.append({"text": doc_text, "metadata": metadata})

    return docs[:top_k]


def add_memory_turn(memory, question, answer, max_turns=12):
    memory.append({"role": "human", "content": question})
    memory.append({"role": "ai", "content": answer})
    max_messages = max_turns * 2
    if len(memory) > max_messages:
        del memory[:-max_messages]


def generate_answer(question, docs, memory=None, interaction_mode="study", model_name=None, agency_context=""):
    mode = get_interaction_mode(interaction_mode)
    model_name = choose_llm_model(model_name)
    if not model_name:
        response = (
            "No hay modelos de Ollama instalados todavia. "
            f"Descarga uno con: `ollama pull {RECOMMENDED_OLLAMA_MODEL}`. "
            "Despues vuelve a intentarlo."
        )
        if memory is not None:
            add_memory_turn(memory, question, response)
        return response

    if not docs and not agency_context:
        response = "No encontre informacion relevante en la base de conocimiento para responder esa pregunta."
        if memory is not None:
            add_memory_turn(memory, question, response)
        return response

    context = ""
    for doc in docs or []:
        metadata = doc["metadata"]
        source_type = metadata.get("type", "fuente")
        title = metadata.get("title", metadata.get("source", "fuente"))
        context += f"[{source_type} {title}]\n{trim_prompt_text(doc['text'], MAX_DOC_CONTEXT_CHARS)}\n\n"

    if not context:
        context = "No se recuperaron fuentes privadas relevantes para esta pregunta.\n"

    agency_section = ""
    if agency_context:
        agency_section = f"""
Base Agency:
{agency_context}

Reglas para usar Agency:
- Usa Agency como metodologia interna y como apoyo experto.
- Prioriza las fuentes privadas cuando existan.
- Si solo Agency respalda una recomendacion, dilo como criterio experto o inferencia.
- No inventes que un especialista ejecuto acciones reales; solo usa su enfoque.
"""

    history_text = ""
    if memory:
        recent_memory = memory[-(PROMPT_HISTORY_TURNS * 2):]
        for message in recent_memory:
            if message.get("role") == "human":
                history_text += f"Estudiante: {trim_prompt_text(message.get('content', ''), 500)}\n"
            elif message.get("role") == "ai":
                history_text += f"Tutor: {trim_prompt_text(message.get('content', ''), 900)}\n"
        if history_text:
            history_text = "Historial de la conversacion:\n" + history_text + "\n"

    prompt = f"""
Eres el cerebro de una aplicacion y pagina web tipo NotebookLM, conectado a una base de conocimiento privada.
Tu modo actual es: {mode["label"]}.

Reglas generales:
- Usa principalmente la informacion proporcionada en el contexto.
- Si una respuesta no esta respaldada por el contexto, dilo con claridad.
- Puedes hacer inferencias utiles, pero marcalas como inferencias cuando no esten explicitas en las fuentes.
- Responde en espanol, con estructura clara y util para el usuario final.
- Cita o menciona fuentes cuando ayude a confiar en la respuesta.

{mode["instructions"]}

{agency_section}

{history_text}
Contexto:
{context}

Pregunta del estudiante: {question}
Respuesta del tutor:
"""
    try:
        response = get_llm(model_name).invoke(prompt)
    except Exception as exc:
        detail = str(exc)
        if "requires more system memory" in detail or "more system memory" in detail:
            response = (
                f"El modelo `{model_name}` es demasiado grande para la memoria disponible ahora. "
                f"Usa un modelo mas ligero: `ollama pull {RECOMMENDED_OLLAMA_MODEL}`."
            )
        else:
            response = (
                f"No pude usar el modelo `{model_name}` en Ollama. "
                f"Verifica que este instalado con `ollama list` o descargalo con "
                f"`ollama pull {model_name}`. Detalle: {exc}"
            )

    if memory is not None:
        add_memory_turn(memory, question, response)
    return response


def answer_from_brain(payload):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise ValueError("La pregunta esta vacia.")

    session_id = str(payload.get("session_id") or "default")[:120]
    memory = memory_store.setdefault(session_id, [])
    interaction_mode = payload.get("mode") or payload.get("interaction_mode") or "study"
    user_groups = normalize_groups(WEB_ACCESS_GROUPS)
    selected_sources = payload.get("selected_sources")
    agency_enabled = bool(payload.get("agency_enabled") or interaction_mode == "agency")

    docs = retrieve(
        question,
        user_groups=user_groups,
        selected_sources=selected_sources,
    )

    agency_matches = []
    agency_context = ""
    if agency_enabled and retrieve_agency_agents and build_agency_context:
        agency_matches = retrieve_agency_agents(question, limit=AGENCY_MATCH_LIMIT)
        agency_context = build_agency_context(agency_matches, max_chars=AGENCY_CONTEXT_CHARS)

    answer = generate_answer(
        question,
        docs,
        memory,
        interaction_mode=interaction_mode,
        model_name=payload.get("model"),
        agency_context=agency_context,
    )

    return {
        "ok": True,
        "answer": answer,
        "mode": get_interaction_mode(interaction_mode)["label"],
        "sources": [
            {
                "metadata": doc.get("metadata", {}),
                "snippet": trim_prompt_text(doc.get("text", ""), 260),
            }
            for doc in docs
        ],
        "agency_agents": agency_matches,
    }


def cors_origin(handler):
    origin = handler.headers.get("Origin")
    if not origin:
        return "*"
    normalized = origin.rstrip("/")
    if normalized == "null" and "null" in ALLOWED_ORIGINS:
        return origin
    parsed = urlparse(normalized)
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return origin
    if "*" in ALLOWED_ORIGINS or normalized in ALLOWED_ORIGINS:
        return origin
    return ""


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    allowed_origin = cors_origin(handler)
    if allowed_origin:
        handler.send_header("Access-Control-Allow-Origin", allowed_origin)
        handler.send_header("Vary", "Origin")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    try:
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        return


class TutorBridgeHandler(BaseHTTPRequestHandler):
    server_version = "TutorIABridge/1.0"

    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        json_response(self, 200, {"ok": True})

    def do_GET(self):
        if self.path.rstrip("/") != "/api/health":
            json_response(self, 404, {"ok": False, "error": "Ruta no encontrada."})
            return

        try:
            fragments = get_collection().count()
        except Exception as exc:
            json_response(self, 500, {"ok": False, "error": str(exc)})
            return

        json_response(
            self,
            200,
            {
                "ok": True,
                "name": "TUTOR_IA",
                "fragments": fragments,
                "model": choose_llm_model(),
                "persist_dir": PERSIST_DIR,
            },
        )

    def do_POST(self):
        if self.path.rstrip("/") != "/api/chat":
            json_response(self, 404, {"ok": False, "error": "Ruta no encontrada."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(min(length, 1024 * 1024))
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            result = answer_from_brain(payload)
            json_response(self, 200, result)
        except Exception as exc:
            json_response(self, 500, {"ok": False, "error": str(exc)})


def main():
    host = os.getenv("TUTOR_IA_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("TUTOR_IA_WEB_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), TutorBridgeHandler)
    print(f"TUTOR_IA web bridge listening on http://{host}:{port}")
    print("Endpoints: GET /api/health, POST /api/chat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
