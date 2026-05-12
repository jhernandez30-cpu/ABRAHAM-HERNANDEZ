# JAH AI Bridge API + Cerebro RAG

Backend local FastAPI para conectar `asistente-programacion.html` con el cerebro documental de JAH AI en `C:\Users\herna\Documents\tutor_ia`.

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
cd C:\Users\herna\Documents\ABRAHAM-HERNANDEZ-main\bridge_api
pip install -r requirements.txt
```

Con el entorno virtual de TUTOR_IA:

```powershell
C:\Users\herna\Documents\tutor_ia\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecutar la API

```powershell
cd C:\Users\herna\Documents\ABRAHAM-HERNANDEZ-main\bridge_api
uvicorn main:app --host 127.0.0.1 --port 8787 --reload
```

Con el entorno virtual de TUTOR_IA:

```powershell
C:\Users\herna\Documents\tutor_ia\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8787 --reload
```

Servidor esperado:

```text
http://127.0.0.1:8787
```

## Agregar documentos

Guarda documentos en:

```text
C:\Users\herna\Documents\tutor_ia\conocimiento
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
  "model": "llama3.2:1b"
}
```

Si no hay contexto suficiente, JAH AI responde claramente:

```text
No encontre suficiente informacion en los documentos cargados para responder con seguridad.
```

## Rutas disponibles

- `GET /api/health`
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

## Conectar con asistente-programacion.html

No hace falta redisenar el frontend. Cuando el backend este activo, el asistente puede enviar mensajes a:

```text
http://127.0.0.1:8787/api/chat
```

Ejemplo con `fetch`:

```js
const response = await fetch("http://127.0.0.1:8787/api/chat", {
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
5. JAH AI responde con fuentes consultadas.

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
```
