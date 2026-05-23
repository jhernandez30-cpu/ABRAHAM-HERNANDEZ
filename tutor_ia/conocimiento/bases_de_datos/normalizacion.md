---
title: Normalizacion
area: bases_de_datos
tipo: guia
estado: base
tags: [normalizacion, diseno, datos]
---

# Normalizacion

La normalizacion reduce duplicidad y mejora la consistencia de los datos.

## Primera forma normal

Cada campo debe tener un valor atomico, no listas mezcladas en una sola columna.

## Segunda forma normal

Cada atributo debe depender de toda la clave primaria, especialmente en tablas con clave compuesta.

## Tercera forma normal

Los atributos no clave no deben depender de otros atributos no clave.

## Criterio practico

Normaliza para evitar errores y duplicidad. Desnormaliza solo cuando haya una razon clara de rendimiento o reporte.
