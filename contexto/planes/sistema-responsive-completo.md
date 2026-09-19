# Plan: Sistema responsive completo

| Campo | Valor |
|-------|--------|
| **Estado** | Completado |
| **Fecha** | 2026-09-19 |
| **Alcance** | Frontend Django (templates + CSS) |

---

## Objetivo

Hacer responsive todo el frontend: sidebar offcanvas en móvil, utilidades de grid con breakpoints y migración de grids inline rígidos.

## Enfoque

CSS propio (sin Bootstrap/Tailwind). Clases utilitarias + media queries en [`static/css/custom.css`](../../static/css/custom.css).

| Breakpoint | Comportamiento |
|---|---|
| ≤1023px | Sidebar offcanvas; botón menú en topbar |
| ≤767px | Filtros, forms y layouts 2–4 cols → 1 columna |
| ≤640px | Padding móvil; stats en 1 columna |

## Tareas

- [x] Sidebar offcanvas + hamburguesa + overlay (`templates/base.html`, `static/js/nav.js`)
- [x] Utilidades CSS: `filters-grid`, `form-grid-*`, `detail-grid-*`, `stats-grid-4`, `cards-grid`
- [x] Migrar templates (listados, forms, detalles, cards, resultado escaneo)
- [x] Sincronizar `staticfiles/css/custom.css` y `staticfiles/js/nav.js`

## Resultado

- Navegación usable en móvil sin sidebar fija de 250px
- Formularios y filtros apilados en pantallas estrechas
- Tablas con `.table-responsive` (scroll horizontal)

## Fuera de alcance (sin cambios)

- No se introdujo Bootstrap/Tailwind
- Django Admin conserva su CSS responsive propio
