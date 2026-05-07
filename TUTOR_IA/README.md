# TUTOR_IA Web Bridge

Este puente permite que `asistente-programacion.html` consulte el cerebro local de TUTOR_IA desde:

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

GitHub Pages solo sirve archivos estaticos. No ejecuta Python. Para que el asistente responda con el cerebro real, este puente debe estar corriendo en tu PC o en un servidor propio.

No subas `brain_db/`, `users.db`, `.venv/` ni logs al repositorio. La carpeta `brain_db` puede contener tus fuentes privadas y `users.db` contiene datos de acceso.

## Uso local

Desde la carpeta `TUTOR_IA`:

```powershell
python -m pip install -r requirements-bridge.txt
.\start_bridge.ps1 -Python python -BrainDb "C:\Users\herna\Documents\tutor_ia\brain_db"
```

Si usas el entorno virtual de tu TUTOR_IA local:

```powershell
.\start_bridge.ps1 -Python "C:\Users\herna\Documents\tutor_ia\.venv\Scripts\python.exe" -BrainDb "C:\Users\herna\Documents\tutor_ia\brain_db"
```

El puente tambien autodetecta `C:\Users\herna\Documents\tutor_ia`: usa su `brain_db`, importa `agency_brain.py` desde esa carpeta y lee el vault Obsidian `Tutor_IA` como contexto vivo.

Tambien importa `connected_brain.py`, `programming_skills.py`, `project_workspace.py`, `jarvis_brain.py` y `local_model_router.py` desde la instalacion local cuando existen. Asi la pagina no usa un cerebro paralelo: usa el mismo contrato de contexto que TUTOR_IA.

La capa modular del repo vive en:

```text
services/brain_connector.py
services/bridge_api_client.py
services/local_brain_service.py
services/anthropic_service.py
```

Cuando este bridge corre dentro de `ABRAHAM-HERNANDEZ-main`, usa `BrainConnector` sin llamarse a si mismo por HTTP para evitar recursion. Si `ANTHROPIC_API_KEY` esta configurado, Claude puede sintetizar la respuesta final; si no, se conserva el flujo local con Ollama/RAG.

## Variables utiles

`TUTOR_IA_ROOT`: raiz de la instalacion local. Por defecto intenta `C:\Users\herna\Documents\tutor_ia`.

`TUTOR_IA_PERSIST_DIR`: ruta de `brain_db`.

`TUTOR_IA_OBSIDIAN_DIR`: ruta del vault Obsidian. Por defecto `C:\Users\herna\Documents\tutor_ia\Tutor_IA`.

`TUTOR_IA_OBSIDIAN_ENABLED`: activa o desactiva el contexto Obsidian. Por defecto `1`.

`TUTOR_IA_WEB_PORT`: puerto del puente. Por defecto `8787`.

`TUTOR_IA_WEB_GROUPS`: grupos permitidos para responder desde la web. Por defecto `admin,public` porque la base local actual esta indexada en `admin`.

`TUTOR_IA_WEB_ALLOWED_ORIGINS`: origenes permitidos por CORS.

## Perfil del Asistente de Programacion

`asistente-programacion.html` envia estas opciones al puente:

- `client: "abraham-programming-assistant"` para activar el perfil del sitio.
- `response_profile: "web_fast"` para recuperar menos fragmentos y responder mas rapido.
- `local_first: true`, `bridge_api: true`, `anthropic: true` y `fast_mode: true` para usar el contrato del cerebro unificado cuando el puente central lo soporte.
- `include_obsidian: true` para sumar notas `.md` y `.canvas` del vault.
- `project_path: "C:\Users\herna\Documents\ABRAHAM-HERNANDEZ-main"` para conectar el codigo real del sitio.
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
