# Plan: Sistema responsive completo

| Campo | Valor |
|-------|--------|
| **Estado** | Completado (refinado: desktop preservado) |
| **Fecha** | 2026-09-19 |
| **Alcance** | Frontend Django (templates + CSS) |

---

## Objetivo

Hacer responsive el frontend **sin alterar la apariencia de escritorio**: sidebar offcanvas en móvil, utilidades de grid con breakpoints, columnas fijas en desktop.

## Criterio UX (desktop-first)

Los estilos por defecto = diseño institucional v2. El responsive **solo** dentro de `@media (max-width: …)`.

| Breakpoint | Comportamiento |
|---|---|
| ≥1024px | Topbar 64px, filtros con columnas originales, cards `minmax(340px)`, padding 24/32px |
| ≤1023px | Sidebar offcanvas; filtros 2 columnas; botón menú |
| ≤767px | Filtros/forms/detalles → 1 columna; topbar puede wrap; cards `280px` |
| ≤640px | Padding 16px; stats 1 columna |

## Tareas

- [x] Sidebar offcanvas + hamburguesa + overlay (`templates/base.html`, `static/js/nav.js`)
- [x] Utilidades CSS: `filters-grid--4/5/6`, `form-grid-*`, `detail-grid-*`, `stats-grid-4`, `cards-grid`
- [x] Migrar templates (listados, forms, detalles, cards, resultado escaneo)
- [x] Restaurar topbar/page-body/botones de filtro en desktop (sin `auto-fit` ni `height: auto` en base)
- [x] Sincronizar `staticfiles/css/custom.css` y `staticfiles/js/nav.js`

## Resultado

- Escritorio visualmente igual al diseño v2 original
- Navegación usable en móvil sin sidebar fija
- Formularios y filtros apilados solo en pantallas estrechas
- Tablas con `.table-responsive` (scroll horizontal)

## Fuera de alcance

- No se introdujo Bootstrap/Tailwind
- Django Admin conserva su CSS responsive propio
