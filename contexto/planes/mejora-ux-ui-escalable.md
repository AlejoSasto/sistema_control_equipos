# Plan: Mejora UX/UI escalable (doc 10)

| Campo | Valor |
|-------|--------|
| **Estado** | Completado |
| **Fecha** | 2026-09-19 |
| **Documento rector** | [`../10-plan-mejora-ux-ui-escalable.md`](../10-plan-mejora-ux-ui-escalable.md) |

## Entregado

- Bootstrap 5.3 (CDN) + variables `--bs-*` institucionales
- Sidebar `offcanvas-lg` nativo; alerts, modal, toast, pagination
- Breakpoints Bootstrap (`991.98` / `767.98` / `575.98`)
- Paginación server-side (50) en equipos, personas, usuarios, movimientos
- Debounce 350ms en búsqueda `q`
- Kiosco: error de red, reintento, anti doble escaneo 2s
- Partials en `templates/components/`
- Login comunidad → Mis Equipos

## Fase 2 (opcional)

- Export CSV del filtro actual
- Skeleton loaders en tablas HTMX
- Sprite SVG e índices DB formales
