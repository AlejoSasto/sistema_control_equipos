# Plan: Inventario y vigencia de equipos institucionales (doc 15 v2)

**Estado:** Completado  
**Fecha:** 2026-09-20  
**Documento rector:** [`../15-vigencia-asignacion-equipos-institucionales.md`](../15-vigencia-asignacion-equipos-institucionales.md)

## Objetivo

Separar **alta de inventario** (sin persona) de **asignación con vigencia**; unidad propietaria en `Equipo`; cierre automático al vencer (escaneo + job diario); permiso `equipos.inventario_institucional` distinto de `equipos.asignar_institucional`.

## Checklist

- [x] Modelo: `Equipo.persona` nullable + unidad + `estado_inventario`; `AsignacionEquipo` sin unidad; `sin_asignacion_activa`
- [x] Permiso `equipos.inventario_institucional` en seed / rol responsable
- [x] Alta inventario `/panel/equipos/institucionales/nuevo/`
- [x] Asignar / devolver / renovar / reasignar
- [x] Kiosco: cierre automático vencida + motivos
- [x] Command diario `cerrar_asignaciones_vencidas`
- [x] Tests + `contexto-completo-sistema.md`
