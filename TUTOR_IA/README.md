# TUTOR_IA Web Bridge

Este puente permite que `asistente-programacion.html` consulte el cerebro local de TUTOR_IA desde:

`http://127.0.0.1:8787/api/chat`

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

## Variables utiles

`TUTOR_IA_PERSIST_DIR`: ruta de `brain_db`.

`TUTOR_IA_WEB_PORT`: puerto del puente. Por defecto `8787`.

`TUTOR_IA_WEB_GROUPS`: grupos permitidos para responder desde la web. Por defecto `admin,public` porque la base local actual esta indexada en `admin`.

`TUTOR_IA_WEB_ALLOWED_ORIGINS`: origenes permitidos por CORS.

## Prueba rapida

```powershell
Invoke-RestMethod http://127.0.0.1:8787/api/health
```
