# Plan: Dashboard de Administrador

**Estado:** Completado  
**Fecha:** 2026-09-19  
**Documento rector:** [`../13-dashboard-administrador.md`](../13-dashboard-administrador.md)

## Objetivo

Dashboard dinámico en `/panel/dashboard/` (lógica en `reportes`): KPIs + Chart.js, filtros HTMX, caché de agregados, permiso `reportes.ver`. Sin polling ni Redis.

## Checklist

- [x] Documentación e índices
- [x] Servicio de agregados + presets + CACHES
- [x] Vistas / URLs / menú / panel_index
- [x] Templates HTMX + Chart.js
- [x] Tests y cierre

## Entregables clave

| Área | Ubicación |
|------|-----------|
| Agregados | `apps/reportes/dashboard.py` |
| Vistas | `apps/reportes/views_dashboard.py` |
| URLs | `apps/panel/urls.py` (`/panel/dashboard/`) |
| Templates | `templates/reportes/dashboard.html`, `partials/` |
| JS | `static/js/dashboard.js` + Chart.js CDN |
| Tests | `apps/reportes/tests/test_dashboard.py` |

## Notas

- Caché LocMem: TTL 45 s periodo / 300 s estructurales.
- Polling en vivo queda fuera (mejora futura del doc 13).
- Gráficos Chart.js acotados a 240px (`.dashboard-chart-box`) para evitar crecimiento infinito con `maintainAspectRatio: false`.
