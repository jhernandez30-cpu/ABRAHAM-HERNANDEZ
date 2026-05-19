# Conexion del cerebro tutor_ia con JAH AI

## Arquitectura

| Capa | Ubicacion | Rol |
|------|-----------|-----|
| Frontend estatico | GitHub Pages / archivo local | `asistente-programacion.html` + `js/` |
| Bridge API | `bridge_api/` (repo) | FastAPI local o Railway HTTPS |
| Cerebro | `~/Documentos/tutor_ia` en desarrollo, `/app/tutor_ia` en Railway | Vectores, conocimiento, RAG |

GitHub Pages **no ejecuta Python**. Solo puede hablar con tutor_ia si el backend local esta activo en tu PC o si despliegas un backend publico.

## Configuracion central (`js/app-config.js`)

```javascript
window.APP_CONFIG = {
  RUN_MODE: "local",              // "local" | "production"
  API_BASE_URL: "http://127.0.0.1:8787",
  LOCAL_API_BASE_URL: "http://127.0.0.1:8787"
};
```

### Modo local

- `RUN_MODE=local` en archivo local o localhost.
- `API_BASE_URL=http://127.0.0.1:8787`.
- El asistente intenta healthcheck contra tu maquina.

### Modo produccion

En GitHub Pages el frontend queda en modo produccion. Debes pegar la URL HTTPS real de Railway en `js/app-config.js`.

Cuando exista un backend publico en HTTPS:

1. Despliega `bridge_api` en una URL publica HTTPS.
2. En `js/app-config.js`, reemplaza `API_BASE_URL: ''` por la URL publica de Railway.
3. Publica el frontend en GitHub Pages.

No uses una URL publica inventada hasta tener el backend desplegado.

## Iniciar tutor_ia en Ubuntu

```bash
cd ~/Documentos/tutor_ia
chmod +x install_ubuntu.sh start_ubuntu.sh
./install_ubuntu.sh    # solo la primera vez
./start_ubuntu.sh
```

Comando interno:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787 --reload
```

Alternativa desde el repo del portafolio:

```bash
cd ~/Documentos/ABRAHAM-HERNANDEZ-main/bridge_api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8787 --reload
```

Configura en `.env`:

```env
TUTOR_IA_ROOT=/home/abraham/Documentos/tutor_ia
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
  "service": "tutor_ia",
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

Regla: si activas el tutor y el backend no responde, veras **Activado · Backend local no disponible**. La preferencia **no** se desactiva sola.

El panel tecnico (`#brainStatus`, boton `#tutorIABtn`) solo es visible para usuario **administrador** autenticado.

## Abrir desde GitHub Pages

URL: `https://jhernandez30-cpu.github.io/ABRAHAM-HERNANDEZ/asistente-programacion.html`

En GitHub Pages el frontend espera una URL publica HTTPS configurada en `js/app-config.js`. Para probar contra el backend local, fuerza `RUN_MODE=local` desde la consola o usa el parametro `?api_base=http://127.0.0.1:8787`.

### Limitacion del navegador (Private Network Access)

Una pagina **HTTPS publica** que llama a `http://127.0.0.1` puede ser bloqueada por:

- **Private Network Access (PNA)** de Chrome/Edge
- **Mixed Content** (HTTPS -> HTTP)

El backend envia `Access-Control-Allow-Private-Network: true`, pero el navegador puede seguir bloqueando la peticion. En ese caso el indicador mostrara *Backend local no disponible* aunque el servidor este encendido.

**Solucion robusta:** desplegar el bridge en HTTPS publico y usar `RUN_MODE=production`.

**Alternativas de desarrollo:**

- Abrir el asistente en `http://127.0.0.1:5500` (mismo origen local).
- Anadir `?api_base=http://127.0.0.1:8787` si cambias de puerto.

## CORS

Origenes permitidos en `bridge_api`:

- `https://jhernandez30-cpu.github.io`
- `http://localhost` / `http://127.0.0.1` (cualquier puerto via regex)
