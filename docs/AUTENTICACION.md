# Autenticacion JAH AI

## Arquitectura actual

- Frontend: `asistente-programacion.html`, `js/app-config.js`, `js/programming-auth.js`.
- Backend: `bridge_api` con FastAPI.
- Desarrollo local: `AUTH_PROVIDER=local` usa JSON local como respaldo.
- Produccion: `AUTH_PROVIDER=supabase` delega registro, login, Google y Apple a Supabase Auth.
- Persistencia: `DATABASE_URL` permite guardar perfil, preferencias e historial en Supabase PostgreSQL.

## Frontend

El frontend solo debe recibir valores publicos:

```js
window.APP_CONFIG = {
  API_BASE_URL: 'https://URL_PUBLICA_DE_RAILWAY',
  SUPABASE_URL: 'https://TU-PROYECTO.supabase.co',
  SUPABASE_ANON_KEY: 'TU_SUPABASE_ANON_KEY_PUBLICA',
  SUPABASE_GOOGLE_ENABLED: true,
  SUPABASE_APPLE_ENABLED: true
};
```

Usa `js/app-config.production.example.js` como plantilla y crea `js/app-config.production.js`.

No pongas `SUPABASE_SERVICE_ROLE_KEY` ni `DATABASE_URL` en archivos servidos por GitHub Pages.

## Backend Railway

Variables minimas:

```env
APP_ENV=production
AUTH_PROVIDER=supabase
API_BASE_URL=https://URL_PUBLICA_DE_RAILWAY
AUTH_FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
JAH_AI_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io,http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500
CORS_ALLOWED_ORIGINS=https://jhernandez30-cpu.github.io,http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_GOOGLE_ENABLED=true
SUPABASE_APPLE_ENABLED=true
DATABASE_URL=postgresql://...
```

`SUPABASE_SERVICE_ROLE_KEY` solo hace falta si quieres que el backend actualice metadatos del usuario dentro de Supabase Auth. Para verificar sesiones y guardar en PostgreSQL no es obligatorio si `DATABASE_URL` esta configurado.

## Supabase

1. Ejecuta `docs/supabase-schema.sql` en Supabase SQL Editor.
2. En Authentication > Providers, activa Email.
3. Activa Google y Apple cuando tengas sus credenciales.
4. En Authentication > URL Configuration, agrega:
   - Site URL: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`
   - Redirect URLs: la misma URL de GitHub Pages y tu URL local `http://127.0.0.1:5500/asistente-programacion.html`.

## Validacion local

```bash
cd /home/abraham/Documentos/ABRAHAM-HERNANDEZ-main/bridge_api
uvicorn main:app --host 127.0.0.1 --port 8787 --reload
```

Luego abre:

```text
http://127.0.0.1:5500/asistente-programacion.html
```

Con `AUTH_PROVIDER=local`, registro y login usan JSON local.
Con `AUTH_PROVIDER=supabase`, registro y login usan Supabase Auth y el backend valida el bearer token de Supabase.
