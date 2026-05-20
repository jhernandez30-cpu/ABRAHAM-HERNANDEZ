---
title: Modelo relacional
area: bases_de_datos
tipo: guia
estado: base
tags: [modelo-relacional, tablas, relaciones]
---

# Modelo relacional

El modelo relacional organiza datos en tablas conectadas por claves.

## Elementos

- Tabla: conjunto de filas con la misma estructura.
- Fila: registro individual.
- Columna: atributo del registro.
- Clave primaria: identificador unico.
- Clave foranea: referencia a otra tabla.

## Relaciones

- Uno a uno: un registro se relaciona con uno.
- Uno a muchos: un registro se relaciona con varios.
- Muchos a muchos: requiere tabla intermedia.

## Ejemplo

Un cliente puede tener muchas ordenes. `ordenes.cliente_id` apunta a `clientes.id`.
