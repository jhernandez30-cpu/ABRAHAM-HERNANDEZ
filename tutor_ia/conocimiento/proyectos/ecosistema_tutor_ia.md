# Ecosistema de rendimiento de TUTOR_IA

## Carriles del sistema

1. Carga rapida
- Archivos: extraccion concurrente con `TUTOR_IA_MAX_FILE_WORKERS` (por defecto 2).
- URLs: extraccion concurrente con `TUTOR_IA_MAX_URL_WORKERS` (por defecto 4).
- Audio con Whisper: se procesa en serie para no saturar CPU/RAM.
- La lista de fuentes se cachea 30 segundos y se limpia al indexar contenido nuevo.

2. Respuesta rapida
- Recupera menos candidatos por defecto: `TUTOR_IA_RETRIEVE_CANDIDATES=10`.
- Envia menos fragmentos al LLM: `TUTOR_IA_RESPONSE_TOP_K=3`.
- Recorta cada fragmento a `TUTOR_IA_MAX_DOC_CONTEXT_CHARS=900`.
- Solo manda las ultimas `TUTOR_IA_PROMPT_HISTORY_TURNS=4` vueltas del chat.
- La interfaz usa un solo `Cerebro Unificado`; las capas internas se activan desde el mismo prompt.

3. Cerebro Agency
- Usa AGENCY-AGENTS-MAIN como capa metodologica, no como fuente documental.
- Selecciona pocos especialistas: `TUTOR_IA_AGENCY_MATCH_LIMIT=2`.
- Recorta el contexto Agency: `TUTOR_IA_AGENCY_CONTEXT_CHARS=3000`.
- Entra automaticamente dentro del `Cerebro Unificado` cuando hay especialistas disponibles.

4. Cerebro Jarvis / Programador
- Detecta `C:\Users\herna\Documents\OpenJarvis-main` y toma sus perfiles de programacion como disciplina de razonamiento.
- Detecta `C:\Users\herna\Documents\jarvis-mlx-main` y aprovecha el patron de interfaz por voz con Whisper local.
- Integra perfiles internos: orquestador, arquitecto, debugger, code reviewer y auditor seguro.
- En Windows no carga MLX directamente; solo usa la idea de STT/TTS local para no traer dependencias de macOS/Apple Silicon.
- Se puede redirigir con `TUTOR_IA_OPENJARVIS_ROOT` y `TUTOR_IA_JARVIS_MLX_ROOT`.

5. Habilidades de programacion
- `programming_skills.py` activa habilidades internas segun la pregunta: web full stack, arquitectura, bases de datos, revision de codigo, debugging, pruebas, seguridad y documentacion.
- `project_workspace.py` permite conectar una carpeta de proyecto para que el cerebro lea estructura y archivos relevantes con limites seguros.
- El panel `Proyecto de programacion` acepta una ruta de carpeta y un bloque rapido de codigo, error o requisitos.
- Las plantillas historicas viven en `conocimiento/_archivo_original/90 - Plantillas` e incluyen proyectos web, APIs, modelos de base de datos, revision de codigo y estructura de software.

6. Modelos locales
- `local_model_router.py` selecciona automaticamente el modelo local segun la tarea.
- Tareas ligeras usan un modelo rapido como `llama3.2:1b`.
- Programacion, review, debugging, arquitectura y SQL usan el mejor modelo de codigo disponible; si no hay coder instalado, usa `llama3.1:8b`.
- Recomendados para mejorar calidad:
```powershell
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:1.5b
```
- Variables opcionales: `TUTOR_IA_FAST_MODEL`, `TUTOR_IA_CODE_MODEL`, `TUTOR_IA_BALANCED_MODEL`, `TUTOR_IA_REASONING_MODEL`.

7. Conexion del cerebro programador
- `connected_brain.py` centraliza el contrato entre Streamlit y `web_bridge.py` para que ambos armen el mismo cerebro.
- El contexto conectado une Jarvis/OpenJarvis, habilidades de programacion, workspace, codigo rapido, Agency y fuentes privadas en un solo prompt.
- La deteccion de intencion normaliza tildes, por eso `programacion`, `programación`, `conectar`, `integracion` y `mejorar` activan las capacidades correctas.
- `project_workspace.py` no solo mira nombres de archivos: tambien revisa contenido de archivos de codigo para recuperar fragmentos relevantes.
- La API devuelve `brain_parts` para saber que capas fueron conectadas en cada respuesta.

## Ajustes recomendados

Equipo con poca RAM:
```powershell
$env:TUTOR_IA_MAX_FILE_WORKERS="1"
$env:TUTOR_IA_MAX_URL_WORKERS="2"
$env:TUTOR_IA_RESPONSE_TOP_K="2"
$env:TUTOR_IA_MAX_DOC_CONTEXT_CHARS="700"
```

Equipo mas fuerte:
```powershell
$env:TUTOR_IA_MAX_FILE_WORKERS="3"
$env:TUTOR_IA_MAX_URL_WORKERS="6"
$env:TUTOR_IA_RESPONSE_TOP_K="4"
$env:TUTOR_IA_MAX_DOC_CONTEXT_CHARS="1200"
```

## Proceso de uso

1. Carga fuentes por lotes pequenos o medianos.
2. Usa los modos normales para respuestas rapidas basadas en tus fuentes.
3. Pregunta desde el unico `Cerebro Unificado`; el sistema decide internamente si necesita tutor, organizador, programador, bases de datos, review, debugging, Agency u OpenJarvis.
4. Para revisar o mejorar codigo, conecta la carpeta en `Proyecto de programacion` o pega un fragmento/traceback en el bloque rapido.
5. Deja el modelo en `Auto (Cerebro Unificado)` para que TUTOR_IA elija entre rapidez y calidad.
6. Activa "Entrada por voz local" solo cuando quieras dictar preguntas.
7. Si una carga tarda, baja los workers; si el equipo responde bien, subelos.
