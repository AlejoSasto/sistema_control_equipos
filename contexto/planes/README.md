# Índice de planes de ejecución

Planes concretos de implementación (features / refactors). El estado canónico también se refleja en [`../README.md`](../README.md).

Los documentos numerados `10`–`12` en la raíz de `contexto/` son la **especificación**; aquí vive el **tracker de ejecución** (checklist y entregables).

| Plan | Estado | Fecha | Documento rector |
|------|--------|-------|------------------|
| [seguridad-iso27001-owasp.md](seguridad-iso27001-owasp.md) | Completado | 2026-09-19 | [`../11-plan-seguridad-iso27001-owasp.md`](../11-plan-seguridad-iso27001-owasp.md) |
| [escaneo-qr-camara.md](escaneo-qr-camara.md) | Completado | 2026-09-19 | — |
| [sistema-responsive-completo.md](sistema-responsive-completo.md) | Completado | 2026-09-19 | — |
| [desktop-intacto-responsive.md](desktop-intacto-responsive.md) | Completado | 2026-09-19 | — |
| [normalizar-qr-pistola-zebra.md](normalizar-qr-pistola-zebra.md) | Completado | 2026-09-19 | — |
| [mejora-ux-ui-escalable.md](mejora-ux-ui-escalable.md) | Completado | 2026-09-19 | [`../10-plan-mejora-ux-ui-escalable.md`](../10-plan-mejora-ux-ui-escalable.md) |
| [seed-mvp-presentacion.md](seed-mvp-presentacion.md) | Completado | 2026-09-19 | — |
| [modulo-reportes-excel.md](modulo-reportes-excel.md) | Completado | 2026-09-19 | [`../12-modulo-reportes-excel.md`](../12-modulo-reportes-excel.md) |
| [dashboard-administrador.md](dashboard-administrador.md) | Completado | 2026-09-19 | [`../13-dashboard-administrador.md`](../13-dashboard-administrador.md) |
| [asignacion-equipos-institucionales.md](asignacion-equipos-institucionales.md) | Completado | 2026-09-20 | [`../14-asignacion-equipos-institucionales.md`](../14-asignacion-equipos-institucionales.md) |
| [vigencia-asignacion-equipos-institucionales.md](vigencia-asignacion-equipos-institucionales.md) | Completado | 2026-09-20 | [`../15-vigencia-asignacion-equipos-institucionales.md`](../15-vigencia-asignacion-equipos-institucionales.md) |
| [personal-externo-y-vigilante.md](personal-externo-y-vigilante.md) | Completado | 2026-09-20 | [`../16-personal-externo-y-vigilante.md`](../16-personal-externo-y-vigilante.md) |
| [area-post-registro-gestor.md](area-post-registro-gestor.md) | Completado | 2026-09-20 | — |
| [despliegue-render-docker.md](despliegue-render-docker.md) | Completado | 2026-09-21 | Instructivo: [`../operaciones/despliegue-render.md`](../operaciones/despliegue-render.md) |
| [seed-automatico-render.md](seed-automatico-render.md) | Completado | 2026-09-21 | Seed en entrypoint + vínculos legado |

## Convención

1. Nombre en `kebab-case.md`.
2. Cabecera con **Estado** (`Pendiente` / `En progreso` / `Completado`) y fecha.
3. Checklist de tareas con `[x]` al cerrar.
4. Si el plan detalla un módulo o dominio nuevo, el documento rector numerado vive en `contexto/` (`00`–`13`); este archivo solo trackea la ejecución.
5. Actualizar este índice y `contexto/README.md` en el mismo cambio.
