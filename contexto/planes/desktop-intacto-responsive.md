# Plan: Desktop intacto + responsive profesional

| Campo | Valor |
|-------|--------|
| **Estado** | Completado |
| **Fecha** | 2026-09-19 |
| **Alcance** | CSS + templates de filtros |

---

## Objetivo

Corregir el responsive previo que había cambiado el look de escritorio (topbar, padding, filtros `auto-fit`, botones a 100%).

## Cambios aplicados

- Topbar fija 64px en desktop; wrap solo ≤767px
- `page-body` padding 24px / 32px (≥1200px); 16px solo ≤640px
- `filters-grid--6/5/4` con columnas explícitas; botones `width: auto` en desktop
- `cards-grid` desktop `minmax(340px, 1fr)`
- Documentación alineada en `sistema-responsive-completo.md`

## Verificación

- ≥1280px: topbar de una línea, filtros en fila, cards ~340px
- ~768px / ~375px: offcanvas + grids apilados
