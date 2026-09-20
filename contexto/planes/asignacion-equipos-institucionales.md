# Plan: Asignación de equipos institucionales

**Estado:** Completado  
**Fecha:** 2026-09-20  
**Documento rector:** [`../14-asignacion-equipos-institucionales.md`](../14-asignacion-equipos-institucionales.md)

## Objetivo

Solo una dependencia (Facultad, Programa o Área) puede crear y asignar equipos institucionales; el autoregistro queda limitado a `personal`; el kiosco muestra una capa visual institucional sin cambiar `Movimiento.resultado`.

## Checklist

- [x] Modelo `ResponsableDependencia` + campos de unidad en `Equipo` + migración legacy
- [x] Services de alcance / pertenencia / autorización
- [x] Bloqueo de autoasignación institucional (UI + servidor)
- [x] Panel: asignar, listado, reasignar, dar de baja
- [x] CRUD responsables de dependencia
- [x] Badge en Mis equipos + capa visual en kiosco
- [x] Permisos `equipos.asignar_institucional` / `equipos.gestionar_responsables` + rol `responsable_dependencia`
- [x] Actualizar `contexto-completo-sistema.md`

## Fuera de alcance

- Tarjeta/filtro opcional de alertas institucionales en dashboard/reportes (§5.3 del doc 14).
