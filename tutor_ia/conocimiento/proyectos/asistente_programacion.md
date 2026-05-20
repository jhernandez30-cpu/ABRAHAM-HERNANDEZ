---
title: Asistente de Programacion
area: proyectos
tipo: proyecto
estado: activo
tags: [asistente-programacion, tutor-ia, abraham-hernandez, bridge]
---

# Asistente de Programacion

El asistente de programacion se encuentra en:

`C:\Users\herna\Documents\ABRAHAM-HERNANDEZ-main`

## Archivos clave

- Interfaz web: `asistente-programacion.html`
- Logica frontend: `js/programming-assistant.js`
- Puente local del sitio: `TUTOR_IA/web_bridge.py`
- Arranque del puente: `TUTOR_IA/start_bridge.ps1`
- App Streamlit del asistente web: `TUTOR_IA/streamlit_app.py`

## Conexion con TUTOR_IA

El asistente consulta `http://127.0.0.1:8787/api/chat` y envia `project_path` apuntando a `C:\Users\herna\Documents\ABRAHAM-HERNANDEZ-main`.

Despues de la reorganizacion, TUTOR_IA central vive en:

- Backend: `C:\Users\herna\Documents\tutor_ia\backend`
- Vectores: `C:\Users\herna\Documents\tutor_ia\vectores\brain_db`
- Conocimiento: `C:\Users\herna\Documents\tutor_ia\conocimiento`

## Objetivo

Responder dudas de programacion, analizar codigo del portafolio, trabajar con archivos cargados y mantener una experiencia conectada al cerebro local.
