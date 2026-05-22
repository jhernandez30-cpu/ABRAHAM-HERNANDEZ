# Conexion del cerebro tutor_ia con JAH AI

## Arquitectura

| Capa | Ubicacion | Rol |
|------|-----------|-----|
| Frontend estatico | GitHub Pages / archivo local | `asistente-programacion.html` + `js/` |
| Bridge API | `bridge_api/` (repo) | FastAPI en Railway HTTPS o desarrollo local |
| Cerebro | `tutor_ia/` dentro del proyecto desplegado | Vectores, conocimiento, RAG |

GitHub Pages **no ejecuta Python**. En produccion solo puede hablar con tutor_ia mediante el backend HTTPS publico en Railway.

## Configuracion central (`js/app-config.js`)

```javascript
window.APP_CONFIG = {
  RUN_MODE: "production",         // "local" | "production"
  API_BASE_URL: "https://jah-ai-bridge-production.up.railway.app",
  LOCAL_API_BASE_URL: "http://127.0.0.1:8787"
};
```

### Modo local

- `RUN_MODE=local` en archivo local o localhost.
- `API_BASE_URL=http://127.0.0.1:8787`.
- El asistente intenta healthcheck contra tu maquina.

### Modo produccion

En GitHub Pages el frontend queda en modo produccion y usa `https://jah-ai-bridge-production.up.railway.app`.

Si cambias el dominio de Railway:

1. Despliega `bridge_api` en la nueva URL publica HTTPS.
2. Actualiza `PRODUCTION_API_BASE_URL` en `js/app-config.js` y la meta `jah-api-base-url` en `asistente-programacion.html`.
3. Publica el frontend en GitHub Pages.

No pongas una URL local en el frontend publicado.

Alternativa desde el repo del portafolio:

```bash
cd ABRAHAM-HERNANDEZ-main
python3 -m venv .venv && source .venv/bin/activate
pip install -r bridge_api/requirements.txt
uvicorn main:app --app-dir bridge_api --host 127.0.0.1 --port 8787 --reload
```

Configura en `.env`:

```env
TUTOR_IA_ROOT=tutor_ia
JAH_AI_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500,https://jhernandez30-cpu.github.io
```

## Healthcheck

| Endpoint | Auth | Uso |
|----------|------|-----|
| `GET /api/health` | Publico | Estado del bridge y tutor_ia |
| `GET /api/admin/system-status` | Solo admin | Detalle tecnico ampliado |

Respuesta minima esperada:

```json
{
  "status": "ok",
  "service": "jah-ai-bridge",
  "tutor_ia": "ready",
  "tutor_ia_status": "CONNECTED"
}
```

Prueba:

```bash
curl http://127.0.0.1:8787/api/health
```

## Estados en el frontend

| Variable | Persistencia | Significado |
|----------|--------------|-------------|
| `tutorIaEnabled` | `localStorage.tutorIaEnabled` | Preferencia del usuario (activar cerebro) |
| `tutorIaConnectionStatus` | Solo en memoria | `CONNECTED`, `DISCONNECTED`, `BACKEND_UNAVAILABLE`, `CHECKING`, `RECOVERING` |

Regla: si activas el tutor y el backend no responde, veras **El backend tutor_ia no esta disponible. Revisa Railway o la URL del servicio.** La preferencia **no** se desactiva sola.

El estado tecnico publico (`#brainStatus`) consulta `/api/health`. Los controles administrativos siguen protegidos para usuario administrador autenticado.

## Abrir desde GitHub Pages

URL: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`

En GitHub Pages el frontend espera una URL publica HTTPS configurada en `js/app-config.js`. Para desarrollo local, abre el archivo en localhost o fuerza `RUN_MODE=local`.

### Limitacion del navegador (Private Network Access)

Una pagina **HTTPS publica** que llama a `http://127.0.0.1` puede ser bloqueada por:

- **Private Network Access (PNA)** de Chrome/Edge
- **Mixed Content** (HTTPS -> HTTP)

El backend envia `Access-Control-Allow-Private-Network: true` solo para desarrollo, pero el navegador puede seguir bloqueando la peticion.

**Solucion robusta:** usar el bridge HTTPS publico de Railway y `RUN_MODE=production`.

**Alternativas de desarrollo:**

- Abrir el asistente en `http://127.0.0.1:5500` (mismo origen local).
- Anadir `?api_base=http://127.0.0.1:8787` si cambias de puerto.

## CORS

Origenes permitidos en `bridge_api`:

- `https://jhernandez30-cpu.github.io`
- `http://localhost` / `http://127.0.0.1` (cualquier puerto via regex)
