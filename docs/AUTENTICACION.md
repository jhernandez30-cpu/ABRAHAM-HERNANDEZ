# Autenticación JAH AI (asistente-programacion.html)

## Arquitectura

- **Frontend:** `js/programming-auth.js` + `js/app-config.js`
- **Backend:** `bridge_api` (FastAPI) en `http://127.0.0.1:8787`
- **No usa** Firebase ni Supabase

## Iniciar backend (obligatorio para login/registro)

```bash
cd /home/abraham/Documentos/ABRAHAM-HERNANDEZ-main/bridge_api
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8787 --reload
```

## Probar localmente

1. Abre `http://127.0.0.1:5500/asistente-programacion.html` (Live Server) con el backend activo.
2. Registro: correo nuevo + contraseña mínimo 8 caracteres.
3. Login: mismas credenciales.
4. Recarga la página: la sesión debe persistir (`localStorage`: `jahAiAuthToken`, `jahAiCurrentUser`).

## Google / Apple Login

Requieren variables en `bridge_api/.env`:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://127.0.0.1:8787/api/auth/google/callback

APPLE_CLIENT_ID=...
APPLE_CLIENT_SECRET=...
APPLE_REDIRECT_URI=http://127.0.0.1:8787/api/auth/apple/callback
```

En Google Cloud Console, autoriza el redirect URI anterior.

Si faltan credenciales, los botones aparecen deshabilitados con mensaje claro.

## GitHub Pages

- `jah-run-mode=local` → intenta `http://127.0.0.1:8787`
- El navegador puede bloquear HTTPS → localhost (Private Network Access)
- Solución de desarrollo: abrir el asistente en `http://127.0.0.1:5500` con backend activo
- Producción futura: backend HTTPS público + `jah-run-mode=production` + `jah-api-base-url`

## Admin

Define en `.env`:

```env
ADMIN_EMAILS=tu@correo.com
```

Tras iniciar sesión con ese correo, `user.is_admin` será `true` y verás el panel técnico del cerebro.
