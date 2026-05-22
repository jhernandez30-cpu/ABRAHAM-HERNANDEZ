---
title: Asistente de Programacion
area: proyectos
tipo: proyecto
estado: activo
tags: [asistente-programacion, tutor-ia, abraham-hernandez, bridge]
---

# Asistente de Programacion

El asistente de programacion se encuentra en:

`ABRAHAM-HERNANDEZ-main`

## Archivos clave

- Interfaz web: `asistente-programacion.html`
- Logica frontend: `js/programming-assistant.js`
- Backend publico del sitio: `bridge_api/main.py`
- Configuracion Railway: `railway.json`
- App Streamlit del asistente web: `TUTOR_IA/streamlit_app.py`

## Conexion con TUTOR_IA

En produccion el asistente consulta `https://jah-ai-bridge-production.up.railway.app/api/chat` desde GitHub Pages. En desarrollo local puede usar `http://127.0.0.1:8787/api/chat`.

Despues de la reorganizacion, TUTOR_IA central vive en:

- Backend: `bridge_api/`
- Vectores: `tutor_ia/vectores/brain_db`
- Conocimiento: `tutor_ia/conocimiento`

## Objetivo

Responder dudas de programacion, analizar codigo del portafolio, trabajar con archivos cargados y mantener una experiencia conectada al backend tutor_ia desplegado.
