---
title: SQL
area: bases_de_datos
tipo: guia
estado: base
tags: [sql, consultas, bases-de-datos]
---

# SQL

SQL permite crear, consultar y modificar datos en bases relacionales.

## Consultas basicas

```sql
SELECT columna1, columna2
FROM tabla
WHERE condicion
ORDER BY columna1;
```

## Operaciones comunes

- `SELECT`: consultar datos.
- `INSERT`: insertar filas.
- `UPDATE`: modificar filas.
- `DELETE`: eliminar filas.
- `JOIN`: combinar tablas relacionadas.
- `GROUP BY`: agrupar resultados.

## Buenas practicas

- Usar claves primarias.
- Crear indices para consultas frecuentes.
- Evitar `SELECT *` en produccion si no hace falta.
- Usar parametros en consultas desde codigo.
- Revisar planes de ejecucion cuando una consulta sea lenta.
