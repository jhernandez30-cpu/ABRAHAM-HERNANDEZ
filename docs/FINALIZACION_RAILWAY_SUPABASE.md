# Finalizacion Railway + Supabase para JAH AI

Estado verificado el 2026-05-20.

## Railway

- Proyecto: `ABRAHAM-HERNANDEZ`
- Project ID: `3d58d4be-4f59-4016-8a6c-604035ba324e`
- Servicio: `jah-ai-bridge`
- Service ID: `9f8ed5dc-bdae-4433-bf68-598d2ecf0129`
- Entorno: `production`
- API publica: `https://jah-ai-bridge-production.up.railway.app`
- Frontend permitido: `https://jhernandez30-cpu.github.io`
- Frontend principal: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`
- Region actual del servicio: `asia-southeast1-eqsg3a`

La region se movio fuera de `sfo` porque el plan gratis bloqueo deploys en hora pico. Si despues quieres volver a Estados Unidos, usa:

```bash
railway service scale -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge southeast-asia=0 us-east=1
```

## Variables ya preparadas en Railway

Estas variables no secretas quedaron configuradas:

```env
APP_ENV=production
AUTH_PROVIDER=supabase
API_BASE_URL=https://jah-ai-bridge-production.up.railway.app
FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
AUTH_FRONTEND_URL=https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
SUPABASE_GOOGLE_ENABLED=true
SUPABASE_APPLE_ENABLED=true
OWNER_EMAIL=josuea.hernandezg@gmail.com
ADMIN_EMAILS=josuea.hernandezg@gmail.com
```

## Variables pendientes

Estas credenciales no existen en Railway todavia y deben cargarse con valores reales de Supabase:

```bash
printf "%s" "$SUPABASE_URL" | railway variable set SUPABASE_URL --stdin -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge
printf "%s" "$SUPABASE_ANON_KEY" | railway variable set SUPABASE_ANON_KEY --stdin -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge
printf "%s" "$DATABASE_URL" | railway variable set DATABASE_URL --stdin -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge
```

`SUPABASE_SERVICE_ROLE_KEY` es opcional. Solo cargalo si quieres que el backend pueda actualizar metadatos del usuario dentro de Supabase Auth:

```bash
printf "%s" "$SUPABASE_SERVICE_ROLE_KEY" | railway variable set SUPABASE_SERVICE_ROLE_KEY --stdin -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge
```

Despues de cargar secretos, redeploy:

```bash
railway deployment redeploy -p 3d58d4be-4f59-4016-8a6c-604035ba324e -e production -s jah-ai-bridge --from-source --yes
```

## Supabase Dashboard

1. En Supabase, copia `Project URL` a `SUPABASE_URL`.
2. Copia la `anon public key` a `SUPABASE_ANON_KEY`.
3. Copia el connection string de PostgreSQL a `DATABASE_URL`.
4. En Auth > URL Configuration:
   - Site URL: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`
   - Redirect URL permitida: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`
5. En Auth > Providers > Google:
   - Activa Google.
   - Carga Client ID y Client Secret de Google Cloud.
   - En Google Cloud agrega el callback que Supabase muestra para Google.
6. En Auth > Providers > Apple:
   - Activa Apple.
   - Carga Service ID, Team ID, Key ID y private key segun Supabase.
   - En Apple Developer agrega el callback que Supabase muestra para Apple.

## Pruebas

Backend:

```bash
curl https://jah-ai-bridge-production.up.railway.app/api/health
curl https://jah-ai-bridge-production.up.railway.app/api/auth/providers
```

Resultado esperado despues de cargar secretos:

```json
{
  "supabase": true,
  "supabase_enabled": true,
  "google": true,
  "apple": true,
  "postgres": true
}
```

Frontend:

```text
https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html
```

Probar registro con correo, login con correo, Google Login y Apple Login desde esa pagina.
