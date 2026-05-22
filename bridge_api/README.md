# JAH AI Bridge API + Cerebro RAG

Backend FastAPI para conectar `asistente-programacion.html` con el cerebro documental de JAH AI configurado en `TUTOR_IA_ROOT`. En produccion corre en Railway; en desarrollo puede correr local.

El RAG lee documentos de `tutor_ia\conocimiento`, los divide en fragmentos, genera embeddings locales y guarda la base vectorial en ChromaDB.

## Estructura principal

```text
bridge_api/
├── main.py
├── requirements.txt
├── .env.example
├── app/
│   ├── config.py
│   ├── routes/
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── history.py
│   │   ├── index.py
│   │   ├── search.py
│   │   ├── sources.py
│   │   └── upload.py
│   ├── rag/
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   ├── embeddings.py
│   │   ├── vectorstore.py
│   │   ├── retriever.py
│   │   └── rag_chain.py
│   ├── services/
│   └── storage/
```

## Instalar dependencias

```powershell
cd C:\ruta\a\ABRAHAM-HERNANDEZ-main\bridge_api
pip install -r requirements.txt
```

Con el entorno virtual de TUTOR_IA:

```powershell
C:\ruta\a\tutor_ia\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecutar la API

```powershell
cd C:\ruta\a\ABRAHAM-HERNANDEZ-main\bridge_api
uvicorn main:app --host 127.0.0.1 --port 8787 --reload
```

Con el entorno virtual de TUTOR_IA:

```powershell
C:\ruta\a\tutor_ia\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8787 --reload
```

Servidor esperado:

```text
http://127.0.0.1:8787
```

## Agregar documentos

Guarda documentos en:

```text
C:\ruta\a\tutor_ia\conocimiento
```

Formatos soportados:

```text
.txt, .md, .pdf, .docx, .py, .html, .css, .js, .json, .sql
```

Tambien puedes subir un archivo por API. El archivo queda en `tutor_ia\conocimiento\_uploads` y luego se incorpora ejecutando `/api/index`.

```powershell
$file = "C:\ruta\documento.pdf"
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/upload -Method Post -Form @{ file = Get-Item $file }
```

## Indexar documentos

Reindexar todo desde cero:

```powershell
$body = @{ force_reindex = $true } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/index -Method Post -Body $body -ContentType "application/json"
```

Indexar solo documentos nuevos o modificados:

```powershell
$body = @{ force_reindex = $false } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/index -Method Post -Body $body -ContentType "application/json"
```

Prueba rapida con pocos archivos:

```powershell
$body = @{ force_reindex = $true; limit = 5 } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/index -Method Post -Body $body -ContentType "application/json"
```

## Listar fuentes

```powershell
Invoke-RestMethod http://127.0.0.1:8787/api/sources
```

## Probar busqueda RAG

```powershell
$body = @{ query = "programacion orientada a objetos en Python"; k = 4 } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/search -Method Post -Body $body -ContentType "application/json"
```

## Probar chat RAG

```powershell
$body = @{
  message = "Explicame que es Python usando los documentos cargados"
  session_id = "usuario_123"
  show_sources = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8787/api/chat -Method Post -Body $body -ContentType "application/json"
```

La respuesta incluye:

```json
{
  "answer": "Respuesta generada con contexto documental",
  "sources": [],
  "session_id": "usuario_123",
  "model": "llama3.2:1b",
  "brain_parts": ["fastapi_bridge", "history_json", "workflow_orchestrator", "chat_summarization", "rag_chromadb"],
  "workflow": {
    "pattern": "plan_act_evaluate",
    "intent": "TECHNICAL_QUERY",
    "rag_sources": 4,
    "web_sources": 0
  }
}
```

Si la consulta exige evidencia documental y no hay contexto suficiente, JAH AI responde claramente:

```text
No encontre suficiente informacion en los documentos cargados para responder con seguridad.
```

## Rutas disponibles

- `GET /api/health`
- `GET /api/status`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `GET /api/auth/apple/start`
- `POST /api/auth/apple/callback`
- `GET /api/auth/session`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/user/profile`
- `PUT /api/user/profile`
- `PUT /api/user/preferences`
- `POST /api/index`
- `GET /api/sources`
- `POST /api/search`
- `POST /api/chat`
- `POST /api/upload`
- `GET /api/history/{session_id}`
- `POST /api/history`

Alias de compatibilidad:

- `GET /health`
- `GET /status`
- `GET /api/status`
- `POST /ask`
- `POST /api/ask`

## Autenticacion y TUTORIA

`programming-auth.js` usa el bridge para iniciar sesion, registrar usuarios y arrancar OAuth con Google o Apple sin cambiar la visualizacion del asistente.

El frontend usa una configuracion centralizada en `js/app-config.js`, cargada antes de `programming-auth.js` y `programming-assistant.js`:

```js
window.APP_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8787" // desarrollo local
};
```

En GitHub Pages o produccion no uses `127.0.0.1` para usuarios reales. Debes desplegar el backend en una URL publica y cambiar `API_BASE_URL`, por ejemplo:

```js
window.APP_CONFIG = {
  API_BASE_URL: "https://jah-ai-bridge-production.up.railway.app"
};
```

Si `API_BASE_URL` no esta configurado en produccion, los botones de login muestran un error controlado y no redirigen a una pagina `ERR_CONNECTION_REFUSED`.

Para desarrollo local, levanta el backend antes de registrar o iniciar sesion:

```powershell
cd C:\ruta\a\ABRAHAM-HERNANDEZ-main\bridge_api
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8787
```

Verifica que responda:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/api/health
```

Si abres `asistente-programacion.html` directamente como archivo local, el backend permite el origen `null` mediante CORS para desarrollo.

Variables principales:

```text
AUTH_FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
OWNER_EMAIL=admin@tu-dominio.com
ADMIN_EMAILS=admin@tu-dominio.com
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://jah-ai-bridge-production.up.railway.app/api/auth/google/callback
APPLE_CLIENT_ID=
APPLE_CLIENT_SECRET=
APPLE_REDIRECT_URI=https://jah-ai-bridge-production.up.railway.app/api/auth/apple/callback
```

Para enlazar usuarios con SQL Server / TUTORIA, activa la conexion solo en `.env` local:

```text
SQLSERVER_ENABLED=true
SQLSERVER_HOST=localhost\SQLEXPRESS
SQLSERVER_PORT=
SQLSERVER_DATABASE=TUTORIA
SQLSERVER_TRUSTED_CONNECTION=true
SQLSERVER_ENCRYPT=true
SQLSERVER_TRUST_SERVER_CERTIFICATE=true
```

El bridge intenta sincronizar el usuario autenticado con una tabla compatible de usuarios en TUTORIA si el esquema lo permite. Si SQL Server no esta disponible o el esquema no tiene columnas compatibles, la sesion sigue funcionando en modo local JSON y el chat no se bloquea. El RAG no participa en el flujo de autenticacion.

## Estado del cerebro solo para administrador

El estado tecnico de `tutor_ia`, SQL Server, memoria y RAG no se expone a visitantes ni usuarios normales.

Endpoints:

- `GET /api/health`: salud publica minima del backend. Sirve para saber si el bridge responde.
- `GET /api/admin/system-status`: estado tecnico completo. Requiere `Authorization: Bearer <token>` de un usuario administrador.

Autorizacion:

- Define `OWNER_EMAIL` o `ADMIN_EMAILS` en `.env`.
- El correo autenticado que coincida con esas variables recibira `is_admin: true` en `/api/auth/session`.
- El frontend solo muestra el chip/panel tecnico del cerebro si `is_admin` es verdadero.
- Usuarios normales reciben `403` si intentan abrir `/api/admin/system-status`.

Pruebas rapidas:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/api/health

# Despues de iniciar sesion como admin:
Invoke-RestMethod http://127.0.0.1:8787/api/admin/system-status -Headers @{
  Authorization = "Bearer TU_TOKEN_ADMIN"
}
```

## Conectar con asistente-programacion.html

No hace falta redisenar el frontend. En produccion el asistente envia mensajes a:

```text
https://jah-ai-bridge-production.up.railway.app/api/chat
```

Ejemplo con `fetch`:

```js
const apiBaseUrl = window.APP_CONFIG?.API_BASE_URL || "https://jah-ai-bridge-production.up.railway.app";
const response = await fetch(`${apiBaseUrl}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "Explicame que es SQL",
    session_id: "usuario_123",
    show_sources: true
  })
});

const data = await response.json();
console.log(data.answer);
console.log(data.sources);
```

Flujo recomendado:

1. Agrega documentos en `tutor_ia\conocimiento`.
2. Ejecuta `POST /api/index`.
3. El frontend llama `POST /api/chat`.
4. El backend busca contexto en ChromaDB.
5. El backend compacta el historial con `chat_summarization` para conservar preferencias y progreso.
6. JAH AI responde con fuentes consultadas y metadatos de workflow.

## Memoria contextual y workflow

La API mantiene dos capas de memoria:

- `app/storage/history.json`: turnos recientes por sesion/chat.
- `app/storage/context_summaries.json`: resumen compacto persistente con preferencias, progreso, temas y fuentes recientes.

El frontend envia `session_id`, `chat_id`, preferencias y un `client_context_summary` invisible para conservar continuidad sin cambiar la visualizacion de `asistente-programacion.html`.

El workflow sigue este orden:

1. `intent_classification`: detecta si el mensaje es saludo, social, continuidad, memoria, tecnico, documental o externo.
2. `chat_summarization`: combina preferencias, resumen persistente y ultimos turnos solo cuando ayuda.
3. `query_planning`: genera consultas enfocadas si la intencion justifica RAG.
4. `rag_retrieval`: recupera fragmentos de `tutor_ia/conocimiento` en ChromaDB y descarta chunks bajo threshold.
5. `web_search`: consulta fuentes externas solo ante intencion de conocimiento externo.
6. `answer_synthesis`: genera la respuesta con Ollama o fallback local.

Para saludos como `Hola` o respuestas sociales como `Gracias`, el bridge responde directo y no consulta RAG, Obsidian ni busqueda web.

El RAG tiene tres modos:

- `RAG_NONE`: saludos y respuestas sociales.
- `RAG_OPTIONAL`: ayuda tecnica general, bases de datos generales, generacion de codigo, tareas creativas y planificacion de proyectos. Si no hay chunks fuertes, el asistente responde igualmente con conocimiento general.
- `RAG_REQUIRED`: preguntas basadas explicitamente en documentos, memoria, Obsidian, tutor_ia o TUTORIA. Solo aqui se muestra una limitacion documental si no hay evidencia suficiente.

Variables utiles:

```text
JAH_AI_CONTEXT_SUMMARY_MAX_CHARS=2800
JAH_AI_RECENT_CONTEXT_TURNS=4
JAH_AI_RAG_MAX_QUERIES=3
RAG_SCORE_THRESHOLD=0.72
RAG_TOP_K=5
RAG_MIN_RELEVANT_CHUNKS=1
RAG_MAX_CONTEXT_CHUNKS=5
TUTOR_IA_SCORE_THRESHOLD=0.72
OBSIDIAN_SCORE_THRESHOLD=0.78
OFFICIAL_SOURCES_SCORE_THRESHOLD=0.80
WEB_SEARCH_PROVIDER=tavily
WEB_SEARCH_MAX_RESULTS=5
TAVILY_API_KEY=
SERPAPI_API_KEY=
BRAVE_API_KEY=
BING_SEARCH_API_KEY=
```

## Embeddings locales

Por defecto el backend intenta usar:

1. `sentence-transformers`, si esta instalado.
2. ChromaDB local ONNX `all-MiniLM-L6-v2`.
3. Un vectorizador local por hashing como respaldo.

Variables utiles en `.env`:

```text
JAH_AI_EMBEDDING_BACKEND=auto
JAH_AI_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
JAH_AI_CHUNK_SIZE=1200
JAH_AI_CHUNK_OVERLAP=180
JAH_AI_MIN_RELEVANCE_SCORE=0.18
RAG_SCORE_THRESHOLD=0.72
```
