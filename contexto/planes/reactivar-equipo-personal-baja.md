# Plan: Reactivar equipo personal dado de baja

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

Permitir al dueño **dar de alta** un equipo personal con `activo=False`, reutilizando el mismo registro/serial. Mientras esté de baja, el QR no es válido en portería. No aplica a institucionales.

## Checklist

- [x] Mis equipos lista personales de baja
- [x] `POST /panel/equipos/<id>/dar-de-alta/` (solo personal)
- [x] UI: sección «Equipos personales de baja» + botón Dar de alta
- [x] Tests baja/alta + rechazo ajeno/institucional
- [x] Docs en `contexto-completo-sistema.md`

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Vista | `apps/equipos/views.py` (`mis_equipos`) |
| Endpoint | `apps/panel/views_equipos.py` (`equipo_dar_de_alta`) |
| URL | `apps/panel/urls.py` |
| UI | `templates/equipos/mis_equipos.html` |
| Tests | `apps/equipos/tests.py` |
