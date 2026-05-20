# Railway + Supabase para JAH AI

## Backend detectado

El backend real es `bridge_api/main.py`. Expone FastAPI y ya tiene rutas:

- `/api/health`
- `/api/chat`, `/api/ask`, `/ask`
- `/api/auth/providers`
- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/session`
- `/api/auth/me`
- `/api/user/profile`
- `/api/user/preferences`
- `/api/history/{session_id}`

## Railway

`railway.json` despliega desde la raiz del proyecto con Railpack:

```json
{
  "build": {
    "builder": "RAILPACK"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --app-dir bridge_api --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health"
  }
}
```

`PORT` lo define Railway. No uses un puerto fijo en produccion.

## Variables para Railway

Carga estas variables en el servicio backend:

```env
APP_ENV=production
AUTH_PROVIDER=supabase
API_BASE_URL=https://URL_PUBLICA_DE_RAILWAY
AUTH_FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
JAH_AI_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io,http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500
CORS_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io,http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500
JAH_AI_ALLOWED_ORIGIN_REGEX=^https://jhernandez30-cpu\.github\.io$|^http://(localhost|127\.0\.0\.1)(:\d+)?$
TUTOR_IA_ROOT=/app/tutor_ia
TUTOR_IA_PERSIST_DIR=/app/tutor_ia/vectores/brain_db
TUTOR_IA_RAG_PERSIST_DIR=/app/tutor_ia/vectores/jah_ai_rag
TUTOR_IA_KNOWLEDGE_DIR=/app/tutor_ia/conocimiento
JAH_AI_UPLOAD_DIR=/app/tutor_ia/conocimiento/_uploads
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_GOOGLE_ENABLED=true
SUPABASE_APPLE_ENABLED=true
DATABASE_URL=postgresql://...
POSTGRES_CONNECT_TIMEOUT_SECONDS=8
```

Opcionales:

```env
SUPABASE_SERVICE_ROLE_KEY=...
OWNER_EMAIL=tu-correo@dominio.com
ADMIN_EMAILS=tu-correo@dominio.com
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=...
OLLAMA_BASE_URL=...
JAH_AI_MODEL=llama3.2:1b
```

## Comandos Railway

Despues de autenticar el CLI:

```bash
source "$HOME/.railway/env"
railway login
railway link
railway variable set APP_ENV=production
railway variable set AUTH_PROVIDER=supabase
railway variable set API_BASE_URL=https://URL_PUBLICA_DE_RAILWAY
railway up --detach -m "Deploy JAH AI bridge with Supabase auth"
```

Para secretos, usa `--stdin`:

```bash
printf "%s" "$SUPABASE_ANON_KEY" | railway variable set SUPABASE_ANON_KEY --stdin
printf "%s" "$DATABASE_URL" | railway variable set DATABASE_URL --stdin
```

## Supabase

1. Crea un proyecto en Supabase.
2. Ejecuta `docs/supabase-schema.sql`.
3. Copia `Project URL` a `SUPABASE_URL`.
4. Copia `anon public` a `SUPABASE_ANON_KEY`.
5. Copia el connection string pooled o direct a `DATABASE_URL` solo en Railway.
6. Activa Email, Google y Apple en Authentication > Providers.
7. Agrega redirect URLs de GitHub Pages y local.

## Frontend GitHub Pages

Crea `js/app-config.production.js` desde `js/app-config.production.example.js` y define:

```js
API_BASE_URL: 'https://URL_PUBLICA_DE_RAILWAY'
SUPABASE_URL: 'https://TU-PROYECTO.supabase.co'
SUPABASE_ANON_KEY: 'TU_SUPABASE_ANON_KEY_PUBLICA'
```

Luego descomenta el script de produccion en `asistente-programacion.html` o publica ese archivo con tu configuracion real.
