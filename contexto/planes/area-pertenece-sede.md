# Área pertenece a sede (obligatorio)

**Estado:** Completado  
**Fecha:** 2026-09-22

## Objetivo

Cada `Area` / dependencia pertenece obligatoriamente a una `Sede`. Unicidad por `(sede, codigo)` para permitir el mismo código (p. ej. CGCA) en varias sedes.

## Checklist

- [x] Modelo `Area.sede` (FK RESTRICT) + `UniqueConstraint(sede, codigo)`
- [x] Migración `0007_area_sede` con backfill/clonado por sede y remap de FKs
- [x] Seed upsert por `(sede, codigo)` × sedes activas (hotfix deploy `MultipleObjectsReturned`)
- [x] Panel `area_form` / listado con sede; validación persona `area.sede == persona.sede`
- [x] Alcance `_q_area` incluye `sede_id__in`; filtros UI registro/visita/persona
- [x] Tests y docs (`contexto-completo-sistema.md`)

## Criterio de listo

- Toda área tiene sede; CRUD exige sede.
- Persona solo puede asignarse área de su sede.
- Seed en Render no falla con áreas clonadas por sede.
