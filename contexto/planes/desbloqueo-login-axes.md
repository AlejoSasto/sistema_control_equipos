# Plan: Desbloqueo de login (Axes) + feedback

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

Informar al usuario cuándo puede reintentar tras el bloqueo Axes, y permitir al admin desbloquear desde el panel con el permiso `usuarios.desbloquear` (incluido en seed / `admin_sistema`).

## Checklist

- [x] `AXES_LOCKOUT_TEMPLATE` + `accounts/lockout.html` (mensaje 1 hora)
- [x] Permiso `usuarios.desbloquear` en seed + migración `0010`
- [x] Panel: estado bloqueado + botón Desbloquear login
- [x] Tests + docs

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Settings | `config/settings.py` |
| Plantilla | `templates/accounts/lockout.html` |
| Seed | `apps/accounts/management/commands/seed_data.py` |
| Migración | `apps/accounts/migrations/0010_usuarios_desbloquear_permission.py` |
| Panel | `apps/panel/views.py`, `urls.py`, `usuario_detail.html` |
