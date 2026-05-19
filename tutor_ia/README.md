# tutor_ia desplegable

Esta carpeta es la version incluida en el repositorio para Railway. `bridge_api` la usa como raiz de conocimiento en produccion con:

```text
TUTOR_IA_ROOT=/app/tutor_ia
TUTOR_IA_KNOWLEDGE_DIR=/app/tutor_ia/conocimiento
TUTOR_IA_RAG_PERSIST_DIR=/app/tutor_ia/vectores/jah_ai_rag
```

No contiene entornos virtuales, `.env`, bases de datos, logs, vectores Chroma ni PDFs pesados. Esos archivos deben mantenerse fuera del repositorio o cargarse mediante procesos controlados.
