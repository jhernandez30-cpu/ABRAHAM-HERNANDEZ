---
title: Buenas practicas de ciberseguridad
area: ciberseguridad
tipo: guia
estado: base
tags: [seguridad, buenas-practicas, hardening]
---

# Buenas practicas

## Para usuarios

- Usar contraseñas unicas por servicio.
- Activar MFA cuando sea posible.
- No abrir adjuntos o enlaces sospechosos.
- Mantener sistema y navegador actualizados.
- Reportar actividad extraña temprano.

## Para desarrollo

- Validar entradas del usuario.
- No guardar secretos en codigo.
- Usar variables de entorno para credenciales.
- Escapar salida en HTML para evitar XSS.
- Aplicar control de acceso en backend, no solo en frontend.

## Para servidores

- Exponer solo los puertos necesarios.
- Usar HTTPS.
- Mantener backups.
- Revisar logs de errores y accesos.
- Separar ambientes de desarrollo y produccion.
