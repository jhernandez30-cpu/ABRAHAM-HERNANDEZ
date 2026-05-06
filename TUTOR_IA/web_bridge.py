from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from email import policy
from email.parser import BytesParser
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM

BASE_DIR = Path(__file__).resolve().parent


def path_from_env(value):
    return Path(value).expanduser() if value else None


def tutor_root_candidates():
    env_root = path_from_env(os.getenv("TUTOR_IA_ROOT"))
    if env_root:
        yield env_root

    yield Path.home() / "Documents" / "tutor_ia"
    yield BASE_DIR
    yield BASE_DIR.parent


def find_tutor_root():
    for candidate in tutor_root_candidates():
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if (
            (candidate / "brain_db").exists()
            or (candidate / "Tutor_IA").exists()
            or (candidate / "agency_brain.py").exists()
        ):
            return candidate
    return BASE_DIR


TUTOR_ROOT = find_tutor_root()
if str(TUTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(TUTOR_ROOT))

try:
    from agency_brain import build_agency_context, get_agency_status, retrieve_agency_agents
except Exception:
    build_agency_context = None
    get_agency_status = None
    retrieve_agency_agents = None

try:
    from jarvis_brain import build_profile_context, build_unified_brain_context, get_jarvis_stack_summary
except Exception:
    build_profile_context = None
    build_unified_brain_context = None
    get_jarvis_stack_summary = None

try:
    from programming_skills import build_programming_skills_context
    from project_workspace import build_workspace_brain_context, retrieve_workspace_context
except Exception:
    build_programming_skills_context = None
    build_workspace_brain_context = None
    retrieve_workspace_context = None

try:
    from connected_brain import (
        build_connected_brain_context,
        build_quick_code_docs,
        retrieve_connected_workspace_docs,
    )
except Exception:
    build_connected_brain_context = None
    build_quick_code_docs = None
    retrieve_connected_workspace_docs = None

try:
    from local_model_router import AUTO_MODEL_OPTION, choose_local_model, get_model_plan
except Exception:
    AUTO_MODEL_OPTION = "Auto (Cerebro Unificado)"
    choose_local_model = None
    get_model_plan = None


PERSIST_DIR = os.getenv("TUTOR_IA_PERSIST_DIR", str(TUTOR_ROOT / "brain_db"))
OBSIDIAN_VAULT_DIR = os.getenv("TUTOR_IA_OBSIDIAN_DIR", str(TUTOR_ROOT / "Tutor_IA"))
COLLECTION_NAME = os.getenv("TUTOR_IA_COLLECTION", "conocimiento_fast")
LLM_MODEL = os.getenv("TUTOR_IA_LLM_MODEL", "llama3.2:1b")
RECOMMENDED_OLLAMA_MODEL = os.getenv("TUTOR_IA_RECOMMENDED_MODEL", "llama3.2:1b")
EMBED_DIM = int(os.getenv("TUTOR_IA_EMBED_DIM", "384"))
RETRIEVE_CANDIDATES = int(os.getenv("TUTOR_IA_RETRIEVE_CANDIDATES", "8"))
RESPONSE_TOP_K = int(os.getenv("TUTOR_IA_RESPONSE_TOP_K", "2"))
MAX_DOC_CONTEXT_CHARS = int(os.getenv("TUTOR_IA_MAX_DOC_CONTEXT_CHARS", "700"))
PROMPT_HISTORY_TURNS = int(os.getenv("TUTOR_IA_PROMPT_HISTORY_TURNS", "3"))
AGENCY_MATCH_LIMIT = int(os.getenv("TUTOR_IA_AGENCY_MATCH_LIMIT", "2"))
AGENCY_CONTEXT_CHARS = int(os.getenv("TUTOR_IA_AGENCY_CONTEXT_CHARS", "3000"))
OBSIDIAN_TOP_K = int(os.getenv("TUTOR_IA_OBSIDIAN_TOP_K", "2"))
OBSIDIAN_MAX_NOTE_CHARS = int(os.getenv("TUTOR_IA_OBSIDIAN_MAX_NOTE_CHARS", "2200"))
OBSIDIAN_ENABLED = os.getenv("TUTOR_IA_OBSIDIAN_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
LOW_MEMORY_MODEL_PRIORITY = ["llama3.2:1b", "qwen2.5:1.5b", "gemma3:1b", "llama3.2:3b"]
ALLOWED_GROUP_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SOURCE_REQUEST_RE = re.compile(
    r"\b(fuente|fuentes|cita|citas|bibliografia|documento|documentos|de donde|origen)\b",
    re.IGNORECASE,
)
DEFAULT_ALLOWED_ORIGINS = "null,http://localhost,http://127.0.0.1,https://jhernandez30-cpu.github.io"
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv("TUTOR_IA_WEB_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
}
WEB_ACCESS_GROUPS = os.getenv("TUTOR_IA_WEB_GROUPS", "admin,public")
SMART_SEARCH_UNCONFIGURED_MESSAGE = (
    "La Búsqueda inteligente está activada, pero todavía no hay una API de búsqueda web configurada."
)
ALLOWED_UPLOAD_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".pdf",
    ".docx",
    ".txt",
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".md",
    ".sql",
    ".cs",
}
TEXT_UPLOAD_EXTENSIONS = {".txt", ".py", ".js", ".html", ".css", ".json", ".md", ".sql", ".cs"}
MAX_UPLOAD_BYTES = int(os.getenv("TUTOR_IA_MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))
MAX_UPLOAD_TEXT_CHARS = int(os.getenv("TUTOR_IA_MAX_UPLOAD_TEXT_CHARS", "6000"))

INTERACTION_MODES = {
    "unified": {
        "label": "Cerebro Unificado",
        "instructions": """
Modo Cerebro Unificado:
- Eres un solo cerebro conectado, no una lista de modos separados.
- Decide internamente si conviene ensenar, organizar, crear, programar, auditar o coordinar especialistas.
- Integra fuentes privadas, Obsidian, Agency, OpenJarvis, Ollama y el workspace de ABRAHAM-HERNANDEZ-MAIN como capas del mismo razonamiento.
- Prioriza claridad, accion concreta y validacion.
- Si falta informacion, dilo en una frase y pide el dato minimo necesario.
- No inventes ejecuciones, fuentes ni resultados que no esten en el contexto.
""",
    },
    "study": {
        "label": "Potencia tu estudio",
        "instructions": """
Modo Potencia tu estudio:
- Actua como tutor paciente y claro.
- Explica conceptos complejos en terminos simples sin perder precision.
- Usa ejemplos del mundo real cuando el contexto lo permita.
- Refuerza la comprension con pasos, analogias, mini-resumenes o preguntas de practica.
- Si falta informacion en el contexto interno, dilo con claridad.
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
- Genera ideas nuevas conectadas con el contexto, no ocurrencias desconectadas.
- Distingue entre evidencia del contexto, inferencia razonable e hipotesis.
- Propone proximos pasos accionables cuando sea util.
""",
    },
    "programming": {
        "label": "Cerebro Programador",
        "instructions": """
Modo Cerebro Programador:
- Actua como asistente senior de programacion local-first.
- Usa el perfil Jarvis/OpenJarvis como disciplina de razonamiento.
- Para debugging, sigue observar, formular hipotesis, probar y corregir.
- Para arquitectura, respeta el sistema existente, limites claros y cambios pequenos.
- Para review, prioriza correctitud, seguridad, rendimiento y mantenibilidad.
- Si no hay codigo o traceback concreto, no inventes una implementacion completa; entrega checklist y pide el fragmento necesario.
- Entrega acciones concretas, comandos o pruebas solo cuando sean utiles y verificables.
""",
    },
    "agency": {
        "label": "Cerebro Agency",
        "instructions": """
Modo Cerebro Agency:
- Actua como orquestador de especialistas.
- Selecciona el enfoque de los agentes relevantes de Agency segun la pregunta.
- Integra metodologia de expertos con la evidencia recuperada del contexto privado.
- Distingue entre hechos del contexto, criterio experto e inferencias.
- Entrega pasos concretos, criterios de validacion y siguientes acciones cuando sea util.
""",
    },
}

MODE_ALIASES = {
    "pensando": "unified",
    "thinking": "unified",
    "auto": "unified",
    "unified": "unified",
    "cerebro": "unified",
    "cerebro unificado": "unified",
    "el mas reciente - 5.5": "unified",
    "el mas reciente • 5.5": "unified",
    "el más reciente • 5.5": "unified",
    "configurar": "unified",
    "configurar...": "unified",
    "study": "unified",
    "organizar": "unified",
    "organize": "unified",
    "crear": "unified",
    "create": "unified",
    "programacion": "unified",
    "programming": "unified",
    "cerebro programador": "unified",
    "code": "unified",
    "debug": "unified",
    "agency": "unified",
    "cerebro agency": "unified",
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


def choose_llm_model(preferred_model=None, question="", docs=None, brain_context=""):
    models = get_installed_ollama_models()
    if choose_local_model:
        return choose_local_model(
            models,
            preferred_model=preferred_model,
            question=question,
            docs=docs,
            brain_context=brain_context,
            fallback_model=LLM_MODEL,
        )
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


def payload_bool(payload, key, default=False):
    if key not in payload:
        return default
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off", ""}


def normalize_mode_text(value):
    text = str(value or "").strip().lower()
    return (
        text.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("  ", " ")
    )


def normalize_interaction_mode(mode_key):
    raw_mode = str(mode_key or "unified").strip()
    if raw_mode in INTERACTION_MODES:
        return "unified" if raw_mode != "unified" else raw_mode
    normalized = normalize_mode_text(raw_mode)
    return MODE_ALIASES.get(normalized, "unified")


def get_interaction_mode(mode_key):
    return INTERACTION_MODES.get(normalize_interaction_mode(mode_key), INTERACTION_MODES["unified"])


def trim_prompt_text(text, max_chars):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def clean_answer_text(text):
    text = str(text or "").replace("**", "")
    text = re.sub(r"(?im)^\s*fuentes?\s*:\s*(?:\n\s*[-*].*)+", "", text)
    text = re.sub(r"(?im)^\s*sources?\s*:\s*(?:\n\s*[-*].*)+", "", text)
    text = re.sub(r"(?im)^\s*fuentes?\s*:\s*.*$", "", text)
    text = re.sub(r"(?im)^\s*sources?\s*:\s*.*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def source_requested(question):
    return bool(SOURCE_REQUEST_RE.search(str(question or "")))


def smart_web_search(query):
    """
    Función preparada para búsqueda inteligente en la web.
    Aquí se podrá conectar una API real de búsqueda web como Tavily, SerpAPI,
    Brave Search API, Google Custom Search o similar.
    """
    return {
        "enabled": False,
        "message": SMART_SEARCH_UNCONFIGURED_MESSAGE,
        "results": [],
    }


def file_extension(filename):
    return Path(str(filename or "")).suffix.lower()


def public_uploaded_file(file_info):
    return {
        "name": file_info.get("name", ""),
        "extension": file_info.get("extension", ""),
        "type": file_info.get("content_type", ""),
        "size": file_info.get("size", 0),
        "accepted": file_info.get("accepted", False),
    }


def normalize_uploaded_file(filename, content_type, content):
    content = content or b""
    extension = file_extension(filename)
    accepted = extension in ALLOWED_UPLOAD_EXTENSIONS and len(content) <= MAX_UPLOAD_BYTES
    text_preview = ""
    if accepted and extension in TEXT_UPLOAD_EXTENSIONS:
        text_preview = content[:MAX_UPLOAD_BYTES].decode("utf-8", errors="replace")
        text_preview = trim_prompt_text(text_preview, MAX_UPLOAD_TEXT_CHARS)

    return {
        "name": Path(str(filename or "archivo")).name,
        "extension": extension,
        "content_type": content_type or "application/octet-stream",
        "size": len(content),
        "accepted": accepted,
        "text_preview": text_preview,
    }


def build_uploaded_file_docs(uploaded_files):
    docs = []
    for file_info in uploaded_files or []:
        if not file_info.get("accepted"):
            continue

        name = file_info.get("name", "archivo")
        extension = file_info.get("extension", "")
        if file_info.get("text_preview"):
            text = f"Archivo adjunto: {name}\nContenido:\n{file_info['text_preview']}"
        else:
            text = (
                f"Archivo adjunto recibido: {name}. "
                f"Tipo: {file_info.get('content_type', 'archivo')}. "
                "El backend actual registra el archivo, pero no extrae contenido de este formato todavía."
            )

        docs.append(
            {
                "text": text,
                "metadata": {
                    "source": f"upload:{name}",
                    "type": "archivo",
                    "title": name,
                    "extension": extension,
                    "access_group": "admin",
                },
            }
        )
    return docs


def parse_multipart_form(content_type, body):
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    payload = {}
    uploaded_files = []

    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue

        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        content = part.get_payload(decode=True) or b""

        if filename:
            uploaded_files.append(
                normalize_uploaded_file(filename, part.get_content_type(), content)
            )
            continue

        payload[name] = content.decode(part.get_content_charset() or "utf-8", errors="replace")

    return payload, uploaded_files


def dot_score(left, right):
    return sum(a * b for a, b in zip(left, right))


def parse_frontmatter(raw):
    match = FRONTMATTER_RE.match(str(raw or "").lstrip("\ufeff"))
    if not match:
        return {}, raw

    metadata = {}
    current_key = ""
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            metadata[current_key] = f"{metadata.get(current_key, '')} {stripped[2:].strip()}".strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip().lower()
        metadata[current_key] = value.strip().strip('"').strip("'")
    return metadata, raw[match.end() :]


def clean_obsidian_text(text):
    text = CODE_BLOCK_RE.sub("", str(text or ""))
    text = WIKI_LINK_RE.sub(lambda match: match.group(1).split("|")[-1], text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def iter_obsidian_files():
    if not OBSIDIAN_ENABLED:
        return []

    root = Path(OBSIDIAN_VAULT_DIR).expanduser()
    if not root.exists() or not root.is_dir():
        return []

    files = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [
            name
            for name in dirs
            if name not in {".obsidian", ".git", "__pycache__"} and not name.startswith(".")
        ]
        for name in names:
            path = Path(current_root) / name
            if path.suffix.lower() in {".md", ".canvas"}:
                files.append(path)
    return sorted(files)


def read_canvas_text(raw):
    try:
        data = json.loads(raw)
    except Exception:
        return raw

    parts = []
    for node in data.get("nodes", []):
        text = node.get("text") or node.get("file") or node.get("label")
        if text:
            parts.append(str(text))
    for edge in data.get("edges", []):
        label = edge.get("label")
        if label:
            parts.append(str(label))
    return "\n".join(parts)


def build_obsidian_note(path, root):
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".canvas":
        raw = read_canvas_text(raw)
    metadata, body = parse_frontmatter(raw)
    title = metadata.get("title") or path.stem
    rel_path = path.relative_to(root).as_posix()
    summary = metadata.get("resumen", "")
    tags = metadata.get("tags", "")
    note_type = metadata.get("tipo", "obsidian")
    area = metadata.get("area", "")
    status = metadata.get("estado", "")
    cleaned_body = clean_obsidian_text(body)
    context_text = "\n".join(
        part
        for part in [
            f"Titulo: {title}",
            f"Ruta Obsidian: {rel_path}",
            f"Resumen: {summary}" if summary else "",
            f"Tags: {tags}" if tags else "",
            f"Tipo: {note_type}" if note_type else "",
            f"Area: {area}" if area else "",
            f"Estado: {status}" if status else "",
            trim_prompt_text(cleaned_body, OBSIDIAN_MAX_NOTE_CHARS),
        ]
        if part
    )
    search_text = " ".join([title, rel_path, summary, tags, note_type, area, cleaned_body])
    return {
        "text": context_text,
        "metadata": {
            "source": f"obsidian:{rel_path}",
            "type": "obsidian",
            "title": title,
            "path": rel_path,
            "access_group": "admin",
            "area": area,
            "estado": status,
        },
        "tokens": set(TOKEN_RE.findall(search_text.lower())),
        "vector": embed_text(search_text),
    }


def obsidian_signature():
    files = iter_obsidian_files()
    signature = []
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        signature.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(signature)


@lru_cache(maxsize=4)
def load_obsidian_notes(signature):
    root = Path(OBSIDIAN_VAULT_DIR).expanduser()
    notes = []
    for raw_path, _, _ in signature:
        path = Path(raw_path)
        try:
            notes.append(build_obsidian_note(path, root))
        except OSError:
            continue
    return notes


def get_obsidian_notes():
    signature = obsidian_signature()
    if not signature:
        return []
    return load_obsidian_notes(signature)


def retrieve_obsidian(question, top_k=None):
    top_k = top_k if top_k is not None else OBSIDIAN_TOP_K
    if top_k <= 0:
        return []

    notes = get_obsidian_notes()
    if not notes:
        return []

    query_text = str(question or "")
    query_vector = embed_text(query_text)
    query_tokens = set(TOKEN_RE.findall(query_text.lower()))
    scored = []
    for note in notes:
        vector_score = dot_score(query_vector, note["vector"])
        overlap = len(query_tokens & note["tokens"]) / max(len(query_tokens), 1)
        path = note["metadata"].get("path", "").lower()
        title = note["metadata"].get("title", "").lower()
        boost = 0.08 if any(token in path or token in title for token in query_tokens) else 0.0
        score = (0.78 * vector_score) + (0.22 * overlap) + boost
        scored.append((score, note))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, note in scored[: max(top_k, 0)]:
        if score <= 0:
            continue
        results.append(
            {
                "text": note["text"],
                "metadata": note["metadata"],
            }
        )
    return results


def get_obsidian_status():
    root = Path(OBSIDIAN_VAULT_DIR).expanduser()
    notes = get_obsidian_notes()
    return {
        "enabled": OBSIDIAN_ENABLED,
        "available": root.exists() and root.is_dir(),
        "path": str(root),
        "notes": len(notes),
    }


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


def generate_answer(
    question,
    docs,
    memory=None,
    interaction_mode="unified",
    model_name=None,
    agency_context="",
    brain_context="",
    show_sources=False,
    assistant_profile="",
):
    mode = get_interaction_mode(interaction_mode)
    model_name = choose_llm_model(
        model_name,
        question=question,
        docs=docs,
        brain_context=brain_context,
    )
    if not model_name:
        response = (
            "No hay modelos de Ollama instalados todavia. "
            f"Descarga uno con: `ollama pull {RECOMMENDED_OLLAMA_MODEL}`. "
            "Despues vuelve a intentarlo."
        )
        response = clean_answer_text(response)
        if memory is not None:
            add_memory_turn(memory, question, response)
        return response

    if not docs and not agency_context and not brain_context:
        response = clean_answer_text("No encontre informacion relevante en la base de conocimiento para responder esa pregunta.")
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
- Prioriza el contexto privado cuando exista.
- Si solo Agency respalda una recomendacion, dilo como criterio experto o inferencia.
- No inventes que un especialista ejecuto acciones reales; solo usa su enfoque.
"""

    brain_section = ""
    if brain_context:
        brain_section = f"""
Capa Jarvis/OpenJarvis:
{brain_context}
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

    source_rule = (
        "- Si el usuario pidio fuentes, menciona solo los titulos estrictamente necesarios al final.\n"
        if show_sources
        else "- No cites fuentes, no agregues secciones de fuentes y no digas 'segun el documento'; usa el contexto en silencio para construir una respuesta inteligente.\n"
    )
    assistant_profile_text = (
        "Perfil conectado: Asistente de Programacion de ABRAHAM-HERNANDEZ-MAIN.\n"
        "Contexto conectado: ChromaDB brain_db y vault Obsidian Tutor_IA.\n"
        if assistant_profile
        else ""
    )

    prompt = f"""
Eres el cerebro de una aplicacion y pagina web tipo NotebookLM, conectado a una base de conocimiento privada.
{assistant_profile_text}
Tu modo actual es: {mode["label"]}.

Reglas generales:
- Lee y sintetiza el contexto como material interno; no copies fragmentos largos.
- Responde como tutor tecnico inteligente: directo, claro, practico y con criterio.
- Usa principalmente la informacion proporcionada en el contexto, pero integrala con razonamiento tecnico.
- Si falta informacion para una respuesta segura, dilo en una frase y da el mejor siguiente paso.
- Puedes hacer inferencias utiles, pero marcalas como inferencias cuando no esten explicitas en el contexto.
- Responde en espanol claro.
- No uses negritas Markdown, no escribas ** y evita adornos innecesarios.
- Prioriza velocidad: respuesta breve, ejemplos minimos y solo los pasos necesarios.
{source_rule}

{mode["instructions"]}

{agency_section}
{brain_section}

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

    response = clean_answer_text(response)
    if memory is not None:
        add_memory_turn(memory, question, response)
    return response


def generate_general_answer(
    question,
    file_docs=None,
    memory=None,
    interaction_mode="unified",
    model_name=None,
):
    mode = get_interaction_mode(interaction_mode)
    model_name = choose_llm_model(model_name)
    if not model_name:
        response = (
            "No hay modelos de Ollama instalados todavia. "
            f"Descarga uno con: `ollama pull {RECOMMENDED_OLLAMA_MODEL}`. "
            "Despues vuelve a intentarlo."
        )
        response = clean_answer_text(response)
        if memory is not None:
            add_memory_turn(memory, question, response)
        return response

    file_context = ""
    for doc in file_docs or []:
        metadata = doc.get("metadata", {})
        title = metadata.get("title", "archivo")
        file_context += f"[archivo {title}]\n{trim_prompt_text(doc.get('text', ''), MAX_DOC_CONTEXT_CHARS)}\n\n"

    history_text = ""
    if memory:
        recent_memory = memory[-(PROMPT_HISTORY_TURNS * 2):]
        for message in recent_memory:
            if message.get("role") == "human":
                history_text += f"Usuario: {trim_prompt_text(message.get('content', ''), 500)}\n"
            elif message.get("role") == "ai":
                history_text += f"Asistente: {trim_prompt_text(message.get('content', ''), 900)}\n"
        if history_text:
            history_text = "Historial de la conversacion:\n" + history_text + "\n"

    prompt = f"""
Eres un asistente de programacion senior dentro de ABRAHAM-HERNANDEZ-MAIN.
El chip Cerebro tutor_ia esta desactivado, asi que no uses ni afirmes usar fuentes privadas.
Tu modo actual es: {mode["label"]}.

Reglas:
- Responde en espanol claro.
- Ayuda con HTML, CSS, JavaScript, Python, Flask, bases de datos, APIs y depuracion.
- Si faltan datos, dilo y da el siguiente paso mas util.
- No inventes fuentes privadas ni resultados web.
- Si hay archivos adjuntos, usalos como contexto de trabajo.

{history_text}
Archivos adjuntos:
{file_context or "No hay archivos adjuntos con texto extraible."}

Pregunta del usuario: {question}
Respuesta:
"""
    try:
        response = get_llm(model_name).invoke(prompt)
    except Exception as exc:
        response = (
            f"No pude usar el modelo `{model_name}` en Ollama. "
            f"Verifica que este instalado con `ollama list`. Detalle: {exc}"
        )

    response = clean_answer_text(response)
    if memory is not None:
        add_memory_turn(memory, question, response)
    return response


def answer_from_brain(payload, uploaded_files=None):
    question = str(payload.get("message") or payload.get("question") or "").strip()
    if not question:
        raise ValueError("La pregunta esta vacia.")

    session_id = str(payload.get("session_id") or "default")[:120]
    memory = memory_store.setdefault(session_id, [])
    raw_mode = payload.get("mode") or payload.get("interaction_mode") or "unified"
    interaction_mode = normalize_interaction_mode(raw_mode)
    user_groups = normalize_groups(WEB_ACCESS_GROUPS)
    selected_sources = payload.get("selected_sources")
    agency_enabled = payload_bool(payload, "agency_enabled", True)
    client_name = str(payload.get("client") or "")
    fast_profile = str(payload.get("response_profile") or "").lower() in {"fast", "fast_smart", "web_fast"}
    show_sources = payload_bool(payload, "show_sources", False) or source_requested(question)
    tutor_ia_enabled = payload_bool(payload, "tutorIA", payload_bool(payload, "tutor_ia", True))
    smart_search_enabled = payload_bool(payload, "smartSearch", payload_bool(payload, "smart_search", False))
    k = int(payload.get("k") or (6 if fast_profile else RETRIEVE_CANDIDATES))
    top_k = int(payload.get("top_k") or (2 if fast_profile else RESPONSE_TOP_K))
    include_obsidian = tutor_ia_enabled and payload_bool(payload, "include_obsidian", True)
    obsidian_top_k = int(payload.get("obsidian_top_k") or OBSIDIAN_TOP_K)
    project_path = str(payload.get("project_path") or payload.get("workspace_path") or "").strip()
    quick_code_context = str(payload.get("quick_code_context") or payload.get("code_context") or "")[:6000].strip()
    uploaded_files = uploaded_files or []
    file_docs = build_uploaded_file_docs(uploaded_files)

    brain_error = ""
    docs = []
    if tutor_ia_enabled:
        try:
            docs = retrieve(
                question,
                user_groups=user_groups,
                k=k,
                top_k=top_k,
                selected_sources=selected_sources,
            )
        except Exception as exc:
            docs = []
            brain_error = str(exc)

    obsidian_docs = retrieve_obsidian(question, top_k=obsidian_top_k) if include_obsidian else []
    if selected_sources is not None:
        selected_source_set = set(selected_sources)
        obsidian_docs = [
            doc
            for doc in obsidian_docs
            if doc.get("metadata", {}).get("source") in selected_source_set
        ]
    if tutor_ia_enabled and project_path and retrieve_connected_workspace_docs:
        workspace_docs = retrieve_connected_workspace_docs(question, project_path)
    elif tutor_ia_enabled and project_path and retrieve_workspace_context:
        workspace_docs = retrieve_workspace_context(question, project_path)
    else:
        workspace_docs = []

    if build_quick_code_docs:
        quick_code_docs = build_quick_code_docs(quick_code_context, source="payload:quick-code")
    else:
        quick_code_docs = []
        if quick_code_context:
            quick_code_docs.append(
                {
                    "text": quick_code_context,
                    "metadata": {
                        "source": "payload:quick-code",
                        "title": "Codigo o requerimiento rapido",
                        "type": "code",
                    },
                }
            )

    docs = docs + obsidian_docs + file_docs + workspace_docs + quick_code_docs

    agency_matches = []
    agency_context = ""
    if tutor_ia_enabled and agency_enabled and retrieve_agency_agents and build_agency_context:
        agency_matches = retrieve_agency_agents(question, limit=AGENCY_MATCH_LIMIT)
        agency_context = build_agency_context(agency_matches, max_chars=AGENCY_CONTEXT_CHARS)

    brain_profile = str(payload.get("jarvis_profile") or payload.get("brain_profile") or "unified")
    brain_context = ""
    brain_parts = []
    if tutor_ia_enabled and build_connected_brain_context:
        brain_bundle = build_connected_brain_context(
            question,
            interaction_mode=interaction_mode,
            brain_profile=brain_profile,
            workspace_path=project_path,
            quick_code_context=quick_code_context,
        )
        brain_context = brain_bundle["context"]
        brain_profile = brain_bundle["profile"]
        brain_parts = brain_bundle["parts"]
    elif tutor_ia_enabled and build_unified_brain_context:
        brain_context_parts = [build_unified_brain_context()]
        if build_programming_skills_context:
            brain_context_parts.append(build_programming_skills_context(f"{question}\n{quick_code_context}"))
        if project_path and build_workspace_brain_context:
            brain_context_parts.append(build_workspace_brain_context(project_path))
        brain_context = "\n\n".join(part for part in brain_context_parts if part)
        brain_profile = "unified"
        brain_parts = ["unified_brain", "programming_skills", "workspace"]
    elif tutor_ia_enabled and build_profile_context:
        brain_context = build_profile_context(brain_profile)
        brain_parts = ["jarvis_profile"]

    if tutor_ia_enabled:
        answer = generate_answer(
            question,
            docs,
            memory,
            interaction_mode=interaction_mode,
            model_name=payload.get("model"),
            agency_context=agency_context,
            brain_context=brain_context,
            show_sources=show_sources,
            assistant_profile=client_name,
        )
    else:
        answer = generate_general_answer(
            question,
            file_docs=file_docs,
            memory=memory,
            interaction_mode=interaction_mode,
            model_name=payload.get("model"),
        )

    smart_search = None
    if smart_search_enabled:
        smart_search = smart_web_search(question)
        if not smart_search.get("enabled"):
            notice = smart_search.get("message") or SMART_SEARCH_UNCONFIGURED_MESSAGE
            answer = f"{answer}\n\n{notice}" if answer else notice

    return {
        "ok": True,
        "answer": answer,
        "mode": str(raw_mode),
        "brain_mode": get_interaction_mode(interaction_mode)["label"],
        "tutorIA": tutor_ia_enabled,
        "smartSearch": smart_search_enabled,
        "usedTutorIA": tutor_ia_enabled,
        "usedSmartSearch": smart_search_enabled and bool(smart_search and smart_search.get("enabled")),
        "smart_search": smart_search,
        "show_sources": show_sources,
        "used_sources_count": len(docs),
        "model": choose_llm_model(
            payload.get("model"),
            question=question,
            docs=docs,
            brain_context=brain_context,
        ),
        "brain_error": brain_error,
        "obsidian_used_count": len(obsidian_docs),
        "workspace_used_count": len(workspace_docs),
        "quick_code_used": bool(quick_code_docs),
        "jarvis_profile": brain_profile if brain_context else "",
        "brain_parts": brain_parts,
        "sources": [
            {
                "metadata": doc.get("metadata", {}),
                "snippet": trim_prompt_text(doc.get("text", ""), 260),
            }
            for doc in docs
        ],
        "uploadedFiles": [public_uploaded_file(file_info) for file_info in uploaded_files],
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

        brain_error = ""
        try:
            fragments = get_collection().count()
        except Exception as exc:
            fragments = 0
            brain_error = str(exc)

        obsidian_status = get_obsidian_status()
        agency_status = get_agency_status() if get_agency_status else {"available": False, "count": 0}
        installed_models = get_installed_ollama_models()
        model_plan = get_model_plan(installed_models) if get_model_plan else {}
        if get_jarvis_stack_summary:
            jarvis_summary = get_jarvis_stack_summary()
            jarvis_status = {
                "openjarvis": jarvis_summary.get("openjarvis", {}),
                "jarvis_mlx": jarvis_summary.get("jarvis_mlx", {}),
                "detected_profiles": jarvis_summary.get("detected_profiles", 0),
                "tools": jarvis_summary.get("tools", []),
                "profiles": [
                    {
                        "key": profile.get("key"),
                        "label": profile.get("label"),
                        "available": profile.get("available"),
                    }
                    for profile in jarvis_summary.get("profiles", [])
                ],
            }
        else:
            jarvis_status = {"available": False}

        json_response(
            self,
            200,
            {
                "ok": True,
                "name": "TUTOR_IA",
                "profile": "abraham-programming-assistant-ready",
                "fragments": fragments,
                "model": choose_llm_model(AUTO_MODEL_OPTION, brain_context="Cerebro Unificado"),
                "models": {
                    "installed": installed_models,
                    "routing": model_plan,
                },
                "root_dir": str(TUTOR_ROOT),
                "persist_dir": PERSIST_DIR,
                "brain_error": brain_error,
                "obsidian": obsidian_status,
                "agency": agency_status,
                "jarvis": jarvis_status,
            },
        )

    def do_POST(self):
        if self.path.rstrip("/") != "/api/chat":
            json_response(self, 404, {"ok": False, "error": "Ruta no encontrada."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(min(length, (MAX_UPLOAD_BYTES * 4) + (1024 * 1024)))
            content_type = self.headers.get("Content-Type", "")
            uploaded_files = []

            if "multipart/form-data" in content_type.lower():
                payload, uploaded_files = parse_multipart_form(content_type, raw_body)
            else:
                payload = json.loads(raw_body.decode("utf-8") or "{}")

            result = answer_from_brain(payload, uploaded_files=uploaded_files)
            json_response(self, 200, result)
        except Exception as exc:
            json_response(self, 500, {"ok": False, "error": str(exc)})


def main():
    host = os.getenv("TUTOR_IA_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("TUTOR_IA_WEB_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), TutorBridgeHandler)
    print(f"TUTOR_IA web bridge listening on http://{host}:{port}")
    print(f"TUTOR_IA root: {TUTOR_ROOT}")
    print(f"Chroma brain: {PERSIST_DIR}")
    print(f"Obsidian vault: {OBSIDIAN_VAULT_DIR}")
    print("Endpoints: GET /api/health, POST /api/chat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
