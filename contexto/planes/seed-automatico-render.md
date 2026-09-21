# Plan: Seed automático en Render (login)

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

Tras el primer deploy en Render solo corrían migraciones (sin admin, sin sedes, tipos MVP legacy). El seed debe ejecutarse al arrancar el contenedor.

## Checklist

- [x] `entrypoint.sh`: `seed_data` después de `migrate`
- [x] Desactivar `TipoVinculo` legado (`estudiante`, `graduado`, `administrativo`, `docente`)
- [x] No resetear contraseña de `admin` si ya existe
- [x] CSP `connect-src` incluye `cdn.jsdelivr.net` (source maps)
- [x] Instructivo Render y plan seed-mvp alineados

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Arranque | `entrypoint.sh` |
| Seed | `apps/accounts/management/commands/seed_data.py` |
| CSP | `config/middleware.py` |
| Guía | `contexto/operaciones/despliegue-render.md` |
