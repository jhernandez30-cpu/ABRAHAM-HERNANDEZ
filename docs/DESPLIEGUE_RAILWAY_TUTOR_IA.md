# Despliegue Railway - bridge_api + tutor_ia

## Que se preparo

- El backend FastAPI real esta en `bridge_api/main.py` y expone `app` con `create_app()`.
- El comando de Railway queda configurado en `railway.json`:

```bash
uvicorn main:app --app-dir bridge_api --host 0.0.0.0 --port $PORT
```

- El build desde la raiz del proyecto usa Railpack y `requirements.txt`, que referencia `bridge_api/requirements.txt`.
- `bridge_api/app/config.py` ahora soporta `APP_ENV`, `API_BASE_URL`, `PORT` y rutas derivadas de `TUTOR_IA_ROOT`.
- En produccion ya no depende de rutas locales de la maquina; por defecto usa `tutor_ia` dentro del proyecto desplegado.
- CORS permite GitHub Pages sin wildcard `*`.
- `/api/health` informa si el backend esta activo y si `tutor_ia` esta conectado o degradado sin exponer rutas internas.
- Se agrego `tutor_ia/` dentro del proyecto con una copia ligera del conocimiento en Markdown/texto. No se incluyeron `.env`, bases de datos, vectores, logs, entornos virtuales ni PDFs pesados.

## Repo que debes subir

Sube el proyecto completo desde la raiz local del repositorio:

```text
ABRAHAM-HERNANDEZ-main
```

No subas solo `bridge_api`, porque Railway necesita ver tambien:

- `railway.json`
- `requirements.txt`
- `bridge_api/`
- `tutor_ia/`

## Variables en Railway

Crea estas variables en el servicio de Railway:

```env
APP_ENV=production
API_BASE_URL=https://jah-ai-bridge-production.up.railway.app
TUTOR_IA_ROOT=tutor_ia
TUTOR_IA_PERSIST_DIR=tutor_ia/vectores/brain_db
TUTOR_IA_RAG_PERSIST_DIR=tutor_ia/vectores/jah_ai_rag
TUTOR_IA_KNOWLEDGE_DIR=tutor_ia/conocimiento
JAH_AI_UPLOAD_DIR=tutor_ia/conocimiento/_uploads
JAH_AI_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io
CORS_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io
JAH_AI_ALLOWED_ORIGIN_REGEX=^https://jhernandez30-cpu\.github\.io$
AUTH_FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ
SQLSERVER_ENABLED=false
AUTH_PROVIDER=supabase
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_GOOGLE_ENABLED=true
SUPABASE_APPLE_ENABLED=true
DATABASE_URL=postgresql://...
OWNER_EMAIL=josuea.hernandezg@gmail.com
ADMIN_EMAILS=josuea.hernandezg@gmail.com
MODEL_PROVIDER=fallback
MODEL_NAME=llama3.2:1b
```

Cuando Railway genere el dominio, puedes agregar tambien:

```env
API_BASE_URL=https://jah-ai-bridge-production.up.railway.app
```

No pongas secretos en `.env.example`. Si despues activas Google, Apple, Tavily, SQL Server u otro proveedor, crea sus variables manualmente en Railway.

## Start command

Railway ya lo lee desde `railway.json`:

```bash
uvicorn main:app --app-dir bridge_api --host 0.0.0.0 --port $PORT
```

Si lo configuras manualmente en el panel, pega exactamente ese comando.

## Generar dominio HTTPS

En Railway:

1. Abre tu servicio backend.
2. Entra a `Settings`.
3. Busca `Networking`.
4. Usa `Generate Domain`.
5. Copia la URL HTTPS generada.

Esa parte depende de tu cuenta y del panel de Railway, por eso no se automatizo.

## Probar health

Despues del deploy:

```bash
curl https://jah-ai-bridge-production.up.railway.app/api/health
```

Respuesta esperada:

```json
{
  "ok": true,
  "bridge_status": "ok",
  "tutor_ia_status": "CONNECTED o DEGRADED",
  "tutor_ia_connected": true
}
```

Si `tutor_ia_status` aparece como `DEGRADED`, `tutor_ia_connected` puede ser `false`: el backend esta vivo pero todavia no hay fragmentos RAG indexados. Puedes indexar el conocimiento con:

```bash
curl -X POST https://jah-ai-bridge-production.up.railway.app/api/index \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": false}'
```

## Actualizar el frontend

Cuando Railway genere el dominio, abre:

```text
js/app-config.js
```

La URL publica ya queda definida como `https://jah-ai-bridge-production.up.railway.app`. Si cambias el dominio de Railway, actualiza la meta `jah-api-base-url` en `asistente-programacion.html` o `PRODUCTION_API_BASE_URL` en `js/app-config.js`. Para Supabase publica, configura `js/app-config.production.js` desde la plantilla:

```js
window.APP_CONFIG = {
  API_BASE_URL: 'https://jah-ai-bridge-production.up.railway.app',
  SUPABASE_URL: 'https://TU-PROYECTO.supabase.co',
  SUPABASE_ANON_KEY: 'TU_SUPABASE_ANON_KEY_PUBLICA',
  SUPABASE_GOOGLE_ENABLED: true,
  SUPABASE_APPLE_ENABLED: true
};
```

No inventes la URL. Usa la URL HTTPS real generada por Railway y las claves reales de Supabase. No pongas `DATABASE_URL` ni `SUPABASE_SERVICE_ROLE_KEY` en frontend.

## Publicar GitHub Pages despues

1. Haz commit del cambio en `js/app-config.js`.
2. Sube el commit a GitHub.
3. En GitHub, verifica que Pages publique la rama configurada.
4. Abre:

```text
https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
```

5. Verifica desde el navegador que las llamadas apunten a `https://jah-ai-bridge-production.up.railway.app/api/health` y `https://jah-ai-bridge-production.up.railway.app/api/chat`.

## Validacion local equivalente a Railway

Desde la raiz del proyecto:

```bash
APP_ENV=production \
TUTOR_IA_ROOT="$PWD/tutor_ia" \
PORT=8787 \
uvicorn main:app --app-dir bridge_api --host 0.0.0.0 --port 8787
```

En otra terminal:

```bash
curl http://127.0.0.1:8787/api/health
```
