# Plan: Seed automático en Render (login)

**Estado:** Completado  
**Fecha:** 2026-09-21 (actualizado 2026-09-22: seed áreas × sede)

## Objetivo

Tras el primer deploy en Render solo corrían migraciones (sin admin, sin sedes, tipos MVP legacy). El seed debe ejecutarse al arrancar el contenedor **sin borrar datos reales**.

## Checklist

- [x] `entrypoint.sh`: `seed_data` después de `migrate`
- [x] Desactivar solo `TipoVinculo` legado conocido (`estudiante`, `graduado`, `administrativo`, `docente`)
- [x] No resetear contraseña de `admin` si ya existe
- [x] No desactivar sedes/facultades/programas/áreas creadas fuera del catálogo seed
- [x] No desactivar tipos de vínculo ajenos al seed (solo legado conocido)
- [x] Limpieza demo limitada a listas fijas (`DEMO_USERNAMES` / documentos / seriales)
- [x] CSP `connect-src` incluye `cdn.jsdelivr.net` (source maps)
- [x] Instructivo Render alineado
- [x] Áreas: upsert por `(sede, codigo)` × sedes activas (post `organizacion.0007`; evita `MultipleObjectsReturned`)

## Garantías en redeploy

| Acción | ¿Borra datos reales? |
|--------|----------------------|
| Upsert permisos / roles / catálogo org | No (update_or_create) |
| Upsert áreas | No — una fila por `(sede, codigo)` del catálogo |
| Crear `admin` + alcance GLOBAL | Solo si no existe; password intacto si ya hay admin |
| Limpiar demos MVP | Solo filas con IDs/seriales de demo |
| Soft-delete masivo fuera del seed | **No** (eliminado) |

## Áreas y sedes (2026-09-22)

Tras `organizacion.0007_area_sede`, cada código de dependencia existe **por sede**. El seed itera sedes activas × `AREAS` (`seed_organizacion_data.py`). Ver plan [`area-pertenece-sede.md`](area-pertenece-sede.md).

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Arranque | `entrypoint.sh` |
| Seed | `apps/accounts/management/commands/seed_data.py` |
| CSP | `config/middleware.py` |
| Guía | `contexto/operaciones/despliegue-render.md` |
