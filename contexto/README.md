# Contexto del proyecto

Carpeta canónica de **documentación y planes** del Sistema de Control de Salida de Equipos de Cómputo (Universidad de Cundinamarca).

> Mantener este índice actualizado cada vez que se agregue, complete o cambie un plan o documento rector.

**Última actualización:** 2026-09-19 (plan 10 UX escalable implementado)

---

## Cómo usar esta carpeta

| Subcarpeta / archivos | Contenido |
|-----------------------|-----------|
| `00`–`08` + `walkthrough.md` | Documentos rectores de negocio, datos, UX e implementación |
| [`planes/`](planes/) | Planes de ejecución concretos (features, refactors) con estado |

Al implementar algo nuevo: crear o actualizar el plan en `planes/`, marcar todos como `completed`/`pending` y reflejar el cambio en la tabla de estado de abajo.

---

## Documentos rectores

| Doc | Título | Estado |
|-----|--------|--------|
| [00-arquitectura-general.md](00-arquitectura-general.md) | Arquitectura general (monolito modular Django + HTMX) | Vigente |
| [01-modelo-negocio-roles-permisos.md](01-modelo-negocio-roles-permisos.md) | Modelo de negocio, roles y permisos | Vigente |
| [02-modelo-datos-diccionario.md](02-modelo-datos-diccionario.md) | Diccionario de datos | Vigente (org. evolucionó a Facultad + Área) |
| [03-plan-implementacion-paso-a-paso.md](03-plan-implementacion-paso-a-paso.md) | Plan de implementación por fases | Completado (MVP) |
| [04-diseno-ux-ui.md](04-diseno-ux-ui.md) | Diseño UX/UI inicial | Histórico / superado por `05` y `09` |
| [05-sistema-diseno-v2.md](05-sistema-diseno-v2.md) | Sistema de diseño v2 (Inter, verde institucional) | Vigente (tokens; detalle en `09`) |
| [06-registro-externo-roles-permisos.md](06-registro-externo-roles-permisos.md) | Registro externo y TipoVinculo | Implementado (fixture 2.3 desfasado vs seed canónico) |
| [07-panel-administracion-interno.md](07-panel-administracion-interno.md) | Panel de administración interno | Implementado |
| [08-logica-completa-aplicacion.md](08-logica-completa-aplicacion.md) | Lógica completa de la aplicación | Vigente |
| [09-guia-diseno-ux-ui.md](09-guia-diseno-ux-ui.md) | Guía completa UX/UI: colores, tipografía, layout, responsive, componentes | **Vigente (referencia visual)** |
| [10-plan-mejora-ux-ui-escalable.md](10-plan-mejora-ux-ui-escalable.md) | Mejora UX a escala (Bootstrap, paginación, kiosco) | **Implementado** |
| [walkthrough.md](walkthrough.md) | Walkthrough de implementación | Completado |

---

## Planes de ejecución

| Plan | Estado | Resumen |
|------|--------|---------|
| [planes/sistema-responsive-completo.md](planes/sistema-responsive-completo.md) | **Completado** | Offcanvas + grids; desktop-first (look web intacto) |
| [planes/desktop-intacto-responsive.md](planes/desktop-intacto-responsive.md) | **Completado** | Restaura topbar/filtros/cards en escritorio |
| [planes/normalizar-qr-pistola-zebra.md](planes/normalizar-qr-pistola-zebra.md) | **Completado** | Normaliza UUID con apóstrofos de Zebra DS22 (layout US→ES) |
| [10-plan-mejora-ux-ui-escalable.md](10-plan-mejora-ux-ui-escalable.md) | **Completado** | Bootstrap 5, paginación 50, debounce, kiosco red, partials |

---

## Stack de referencia (resumen)

- Django 5.1 + templates + HTMX
- PostgreSQL
- CSS propio (`static/css/custom.css`) — design system v2
- Seed: `python manage.py seed_data`

Ver también el [README del repositorio](../README.md).
