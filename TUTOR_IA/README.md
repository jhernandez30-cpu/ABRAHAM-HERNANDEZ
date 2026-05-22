# TUTOR_IA Web Bridge

Este puente es legado/local. En produccion `asistente-programacion.html` consulta el backend Railway:

`https://jah-ai-bridge-production.up.railway.app/api/chat`

Para desarrollo local tambien puede usarse:

`http://127.0.0.1:8787/api/chat`

Tambien acepta aliases compatibles con el `BrainConnector` central creado en la raiz del repo (`services/brain_connector.py`):

- `GET /health`
- `GET /status`
- `GET /api/health`
- `GET /api/status`
- `POST /ask`
- `POST /api/ask`
- `POST /api/chat`

## Importante

GitHub Pages solo sirve archivos estaticos. No ejecuta Python. Para que el asistente responda con el cerebro real en produccion, el backend debe estar corriendo en Railway o en un servidor HTTPS equivalente.

No subas `vectores/brain_db/`, `database/users.db`, `tutor_ia.db`, `.venv/` ni logs al repositorio. La carpeta `vectores/brain_db` puede contener tus fuentes privadas y `tutor_ia.db` contiene usuarios e historial del Asistente de Programacion.

## Uso local

Desde la carpeta `TUTOR_IA`:

```powershell
python -m pip install -r requirements.txt
.\start_bridge.ps1 -Python python -BrainDb "C:\ruta\a\tutor_ia\vectores\brain_db"
```

Para usar la interfaz Streamlit con login, registro, Google OAuth e historial por usuario:

```powershell
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8502
```

La app crea `tutor_ia.db` automaticamente con estas tablas: `users`, `chat_sessions` y `chat_messages`.

## SQL Server / TUTORIA

`TUTORIA.sql` debe tratarse como script T-SQL para SQL Server Management Studio 22, no como una base activa. El flujo correcto es:

1. Abrir SQL Server Management Studio 22.
2. Conectarse al motor local, por ejemplo `localhost\SQLEXPRESS`.
3. Abrir `TUTORIA.sql`.
4. Ejecutar el script para crear o actualizar la base `TUTORIA`.
5. Verificar en Object Explorer que la base y sus tablas/procedimientos existan.

`ultron_code.py` se conecta al servidor SQL Server, no a SSMS. La configuracion segura vive en `.env` y el ejemplo esta en `.env.example`:

```env
SQLSERVER_ENABLED=true
SQLSERVER_HOST=localhost\SQLEXPRESS
SQLSERVER_PORT=
SQLSERVER_DATABASE=TUTORIA
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_TRUSTED_CONNECTION=true
SQLSERVER_ENCRYPT=true
SQLSERVER_TRUST_SERVER_CERTIFICATE=true
```

La integracion inspecciona `INFORMATION_SCHEMA` antes de guardar memoria. Si encuentra tablas compatibles con `session_id` + resumen contextual, persiste `chat_summarization` en SQL Server; si no, reporta `DB_SCHEMA_INVALID` y mantiene continuidad con SQLite local hasta que el esquema real este disponible.

## Orquestacion RAG inteligente

ULTRON clasifica cada mensaje antes de recuperar contexto. Saludos como `Hola`, `Buenos dias` o respuestas sociales como `Gracias` se contestan directo, sin consultar TUTORIA, documentos, Obsidian ni busqueda externa. Las consultas tecnicas o documentales usan thresholds para evitar fragmentos debiles:

```env
RAG_SCORE_THRESHOLD=0.72
RAG_TOP_K=5
RAG_MIN_RELEVANT_CHUNKS=1
RAG_MAX_CONTEXT_CHUNKS=5
TUTOR_IA_SCORE_THRESHOLD=0.72
OBSIDIAN_SCORE_THRESHOLD=0.78
OFFICIAL_SOURCES_SCORE_THRESHOLD=0.80
```

Para tareas generales como crear una web, proponer una landing page o explicar HTML/CSS, el RAG funciona como apoyo opcional. Si no hay fragmentos suficientemente relevantes, ULTRON responde de todos modos como asistente de programacion. La respuesta bloqueante por falta de evidencia solo se usa cuando el usuario pide explicitamente documentos, notas, memoria o fuentes.

Modos de RAG:

- `RAG_NONE`: saludos y respuestas sociales.
- `RAG_OPTIONAL`: ayuda tecnica, bases de datos generales, generacion de codigo, prompts, sitios web y planificacion.
- `RAG_REQUIRED`: preguntas que exigen documentos, memoria, TUTORIA.sql, Obsidian o evidencia citada.

Si usas el entorno virtual de tu TUTOR_IA local:

```powershell
.\start_bridge.ps1 -Python "C:\ruta\a\tutor_ia\.venv\Scripts\python.exe" -BrainDb "C:\ruta\a\tutor_ia\vectores\brain_db"
```

El puente tambien autodetecta la ruta configurada en `TUTOR_IA_ROOT`: usa `vectores/brain_db`, importa los modulos desde `backend/` y lee `conocimiento/` como contexto vivo.

Tambien importa `connected_brain.py`, `programming_skills.py`, `project_workspace.py`, `jarvis_brain.py` y `local_model_router.py` desde `TUTOR_IA_ROOT\backend` cuando existen. Asi la pagina no usa un cerebro paralelo: usa el mismo contrato de contexto que TUTOR_IA.

La capa modular del repo vive en:

```text
services/brain_connector.py
services/bridge_api_client.py
services/local_brain_service.py
services/anthropic_service.py
```

Cuando este bridge corre dentro de `ABRAHAM-HERNANDEZ-main`, usa `BrainConnector` sin llamarse a si mismo por HTTP para evitar recursion. Si `ANTHROPIC_API_KEY` esta configurado, Claude puede sintetizar la respuesta final; si no, se conserva el flujo local con Ollama/RAG.

## Variables utiles

`TUTOR_IA_ROOT`: raiz de la instalacion local. Configurala con la ruta real de tu instalacion de `tutor_ia`.

`TUTOR_IA_PERSIST_DIR`: ruta de `vectores/brain_db`.

`TUTOR_IA_OBSIDIAN_DIR`: ruta de la base de conocimiento. Por ejemplo `C:\ruta\a\tutor_ia\conocimiento`.

`TUTOR_IA_OBSIDIAN_ENABLED`: activa o desactiva el contexto Obsidian. Por defecto `1`.

`TUTOR_IA_WEB_PORT`: puerto del puente. Por defecto `8787`.

`TUTOR_IA_WEB_GROUPS`: grupos permitidos para responder desde la web. Por defecto `admin,public` porque la base local actual esta indexada en `admin`.

`TUTOR_IA_WEB_ALLOWED_ORIGINS`: origenes permitidos por CORS.

`TUTOR_IA_DB_PATH`: ruta de la base SQLite del Asistente de Programacion. Por defecto `TUTOR_IA\tutor_ia.db`.

`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`: credenciales para el boton "Continuar con Google" en Streamlit.

## Perfil del Asistente de Programacion

`asistente-programacion.html` envia estas opciones al puente:

- `client: "abraham-programming-assistant"` para activar el perfil del sitio.
- `response_profile: "web_fast"` para recuperar menos fragmentos y responder mas rapido.
- `local_first: true`, `bridge_api: true`, `anthropic: true` y `fast_mode: true` para usar el contrato del cerebro unificado cuando el puente central lo soporte.
- `include_obsidian: true` para sumar notas `.md` y `.canvas` del vault.
- `project_path: "C:\ruta\a\ABRAHAM-HERNANDEZ-main"` para conectar el codigo real del sitio.
- `agency_enabled: true` y `jarvis_profile: "unified"` para activar Agency, OpenJarvis y habilidades de programacion dentro del mismo prompt.
- `show_sources: false` para usar las fuentes como contexto interno sin mostrar la lista al usuario.

El puente solo devuelve fuentes visibles si el usuario las pide explicitamente, por ejemplo con "cita las fuentes" o "de donde sale esto".

Las respuestas se limpian antes de enviarse: se eliminan `**` de negritas Markdown y cualquier linea tipo `Fuentes:`.

La respuesta de `/api/chat` incluye `brain_parts`, `workspace_used_count`, `quick_code_used`, `jarvis_profile` y `model` para verificar que las capas esten conectadas.

## Prueba rapida

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health

$body = @{ message = "estas conectado?"; tutorIA = $true; response_profile = "web_fast" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8787/api/ask -Method Post -Body $body -ContentType "application/json"
```
