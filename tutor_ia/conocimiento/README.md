# Base de conocimiento TUTOR_IA

Esta carpeta guarda el conocimiento vivo del asistente.

- Usa archivos `.md` para apuntes curados, reglas, resumenes y guias.
- Usa `conocimiento/_pdfs` para PDF generales que todavia no esten clasificados.
- Tambien puedes guardar PDF dentro de cada area, por ejemplo `programacion/` o `ciberseguridad/`, cuando pertenezcan claramente a ese tema.
- El archivo historico anterior quedo preservado en `conocimiento/_archivo_original`.

Cuando agregues PDF nuevos y quieras que el asistente los use en respuestas RAG, procesalos desde la app para que se indexen en `vectores/brain_db`.
