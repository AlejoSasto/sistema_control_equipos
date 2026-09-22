# Contexto del proyecto

Carpeta canónica de **documentación, planes y operaciones** del Sistema de Control de Salida de Equipos de Cómputo (Universidad de Cundinamarca).

> Mantener este índice actualizado cada vez que se agregue, complete o cambie un plan o documento rector.

**Última actualización:** 2026-09-22 (plan 17 Resend: docs §9.2b recuperación de contraseña + brief manual 1.2)

---

## Punto de entrada

| Documento | Uso |
|-----------|-----|
| **[`contexto-completo-sistema.md`](contexto-completo-sistema.md)** | Síntesis vigente autocontenida (onboarding e IA). **Gana** si hay conflicto con docs antiguos. |
| [`brief-manual-usuario-claude.md`](brief-manual-usuario-claude.md) | Prompt maestro para generar el **manual de usuario** (Word) con Claude |

Los `00`–`17` son detalle/histórico; no sustituyen al contexto completo.

---

## Cómo usar esta carpeta

| Ubicación | Contenido |
|-----------|-----------|
| [`contexto-completo-sistema.md`](contexto-completo-sistema.md) | Contexto único vigente del sistema |
| `00`–`17` + `walkthrough.md` | Documentos rectores (arquitectura, negocio, datos, UX, seguridad, módulos, correos) |
| [`planes/`](planes/) | Planes de ejecución concretos (features / refactors) con estado |
| [`operaciones/`](operaciones/) | Procedimientos y checklists operativos (incidentes, backups) |

Al implementar algo nuevo: crear o actualizar el plan en `planes/` (kebab-case), actualizar [`planes/README.md`](planes/README.md) y la tabla de estado de abajo. Si el cambio altera el comportamiento vigente, actualizar también [`contexto-completo-sistema.md`](contexto-completo-sistema.md).

---

## Documentos rectores

| Doc | Título | Estado |
|-----|--------|--------|
| [contexto-completo-sistema.md](contexto-completo-sistema.md) | Síntesis operativa vigente (punto de entrada) | **Vigente** |
| [00-arquitectura-general.md](00-arquitectura-general.md) | Arquitectura general (monolito modular Django + HTMX) | Vigente |
| [01-modelo-negocio-roles-permisos.md](01-modelo-negocio-roles-permisos.md) | Modelo de negocio, roles y permisos | Vigente |
| [02-modelo-datos-diccionario.md](02-modelo-datos-diccionario.md) | Diccionario de datos | Vigente con salvedad: Área ahora **pertenece a Sede** (ver `contexto-completo-sistema.md` §5) |
| [03-plan-implementacion-paso-a-paso.md](03-plan-implementacion-paso-a-paso.md) | Plan de implementación por fases | Completado (MVP) |
| [04-diseno-ux-ui.md](04-diseno-ux-ui.md) | Diseño UX/UI inicial | Histórico / superado por `05` y `09` |
| [05-sistema-diseno-v2.md](05-sistema-diseno-v2.md) | Sistema de diseño v2 (Inter, verde institucional) | Vigente (tokens; detalle en `09`) |
| [06-registro-externo-roles-permisos.md](06-registro-externo-roles-permisos.md) | Registro externo y TipoVinculo | Implementado (fixture 2.3 desfasado vs seed canónico) |
| [07-panel-administracion-interno.md](07-panel-administracion-interno.md) | Panel de administración interno | Implementado |
| [08-logica-completa-aplicacion.md](08-logica-completa-aplicacion.md) | Lógica completa de la aplicación | Detalle; para estado actual preferir `contexto-completo-sistema.md` |
| [09-guia-diseno-ux-ui.md](09-guia-diseno-ux-ui.md) | Guía completa UX/UI: colores, tipografía, layout, responsive, componentes | **Vigente (referencia visual)** |
| [10-plan-mejora-ux-ui-escalable.md](10-plan-mejora-ux-ui-escalable.md) | Mejora UX a escala (Bootstrap, paginación, kiosco) | Implementado — ejecución en [`planes/mejora-ux-ui-escalable.md`](planes/mejora-ux-ui-escalable.md) |
| [11-plan-seguridad-iso27001-owasp.md](11-plan-seguridad-iso27001-owasp.md) | Plan de seguridad ISO 27001 + OWASP + Ley 1581 | Implementado (S1–S3; pentest/RNBD externos pendientes) — ejecución en [`planes/seguridad-iso27001-owasp.md`](planes/seguridad-iso27001-owasp.md) |
| [12-modulo-reportes-excel.md](12-modulo-reportes-excel.md) | Módulo de reportes Excel (filtros + gráficos nativos) | Implementado (sync; async fase 2) — ejecución en [`planes/modulo-reportes-excel.md`](planes/modulo-reportes-excel.md) |
| [13-dashboard-administrador.md](13-dashboard-administrador.md) | Dashboard admin (KPIs + Chart.js + HTMX) | **Implementado** — ejecución en [`planes/dashboard-administrador.md`](planes/dashboard-administrador.md) |
| [14-asignacion-equipos-institucionales.md](14-asignacion-equipos-institucionales.md) | Asignación de equipos institucionales por dependencia | **Implementado** — ejecución en [`planes/asignacion-equipos-institucionales.md`](planes/asignacion-equipos-institucionales.md) |
| [15-vigencia-asignacion-equipos-institucionales.md](15-vigencia-asignacion-equipos-institucionales.md) | Inventario y vigencia de equipos institucionales | **Implementado** — ejecución en [`planes/vigencia-asignacion-equipos-institucionales.md`](planes/vigencia-asignacion-equipos-institucionales.md) |
| [16-personal-externo-y-vigilante.md](16-personal-externo-y-vigilante.md) | Personal externo (VisitaExterno) y vigilante | **Implementado** — ejecución en [`planes/personal-externo-y-vigilante.md`](planes/personal-externo-y-vigilante.md) |
| [17-integracion-resend.md](17-integracion-resend.md) | Correos transaccionales Resend + Celery | **Implementado** — ejecución en [`planes/integracion-resend.md`](planes/integracion-resend.md) |
| [walkthrough.md](walkthrough.md) | Walkthrough de implementación | Completado |

---

## Planes de ejecución

Índice detallado: [`planes/README.md`](planes/README.md).

| Plan | Estado | Resumen |
|------|--------|---------|
| [planes/seguridad-iso27001-owasp.md](planes/seguridad-iso27001-owasp.md) | Completado | Controles S1–S3: settings, authz, auditoría, MFA, QR TTL |
| [planes/escaneo-qr-camara.md](planes/escaneo-qr-camara.md) | Completado | Kiosco: pistola + cámara + teclado → mismo HTMX |
| [planes/sistema-responsive-completo.md](planes/sistema-responsive-completo.md) | Completado | Offcanvas + grids; desktop-first (look web intacto) |
| [planes/desktop-intacto-responsive.md](planes/desktop-intacto-responsive.md) | Completado | Restaura topbar/filtros/cards en escritorio |
| [planes/normalizar-qr-pistola-zebra.md](planes/normalizar-qr-pistola-zebra.md) | Completado | Normaliza `'`/`ñ` de Zebra DS22 en UUID y token firmado |
| [planes/mejora-ux-ui-escalable.md](planes/mejora-ux-ui-escalable.md) | Completado | Bootstrap 5, paginación 50, debounce, kiosco red, partials |
| [planes/seed-mvp-presentacion.md](planes/seed-mvp-presentacion.md) | Completado | Seed MVP presentación (`seed_data`) |
| [planes/modulo-reportes-excel.md](planes/modulo-reportes-excel.md) | Completado | App reportes: 5 XLSX con xlsxwriter, permisos y auditoría |
| [planes/dashboard-administrador.md](planes/dashboard-administrador.md) | **Completado** | Dashboard admin: KPIs, Chart.js, HTMX, caché |
| [planes/asignacion-equipos-institucionales.md](planes/asignacion-equipos-institucionales.md) | **Completado** | Asignación institucional por Facultad/Programa/Área + badge kiosco |
| [planes/vigencia-asignacion-equipos-institucionales.md](planes/vigencia-asignacion-equipos-institucionales.md) | **Completado** | Inventario sin persona + asignación con vigencia + cierre auto |
| [planes/personal-externo-y-vigilante.md](planes/personal-externo-y-vigilante.md) | **Completado** | Personal externo + visitas + vigilante + badges kiosco |
| [planes/area-post-registro-gestor.md](planes/area-post-registro-gestor.md) | **Completado** | Gestor se registra sin área; admin la asigna en panel |
| [planes/despliegue-render-docker.md](planes/despliegue-render-docker.md) | **Completado** | Dockerfile, compose, render.yaml, gunicorn, instructivo Render |
| [planes/seed-automatico-render.md](planes/seed-automatico-render.md) | **Completado** | Seed en entrypoint; upsert seguro; áreas por (sede, codigo) |
| [planes/reactivar-equipo-personal-baja.md](planes/reactivar-equipo-personal-baja.md) | **Completado** | Alta de equipo personal tras baja (QR inválido mientras baja) |
| [planes/desbloqueo-login-axes.md](planes/desbloqueo-login-axes.md) | **Completado** | Feedback lockout + permiso `usuarios.desbloquear` en panel |
| [planes/alcance-jerarquico-usuarios.md](planes/alcance-jerarquico-usuarios.md) | **Completado** | Alcance GLOBAL/SEDE/FACULTAD/PROGRAMA/ÁREA + filtrado central |
| [planes/login-cedula-username-institucional.md](planes/login-cedula-username-institucional.md) | **Completado** | Login por cédula + username = parte local del correo institucional |
| [planes/area-pertenece-sede.md](planes/area-pertenece-sede.md) | **Completado** | Área FK a Sede; unicidad (sede, codigo); seed × sede; hotfix deploy |
| [planes/integracion-resend.md](planes/integracion-resend.md) | **Completado** | Resend + Celery/Redis; welcome, **recuperación de contraseña**, unlock, webhook |

---

## Operaciones

Índice: [`operaciones/README.md`](operaciones/README.md).

| Documento | Estado | Resumen |
|-----------|--------|---------|
| [operaciones/procedimiento-incidentes-seguridad.md](operaciones/procedimiento-incidentes-seguridad.md) | Vigente | Procedimiento mínimo de incidentes |
| [operaciones/checklist-backup-restauracion.md](operaciones/checklist-backup-restauracion.md) | Vigente | Checklist backups PostgreSQL + restauración |
| [operaciones/despliegue-render.md](operaciones/despliegue-render.md) | Vigente | Instructivo despliegue en Render (Blueprint + Docker) |

---

## Stack de referencia (resumen)

- Django 5.1 + templates + HTMX
- PostgreSQL
- Celery + Redis + Resend (correos)
- CSS propio (`static/css/custom.css`) — design system v2
- Seed: `python manage.py seed_data`

Ver también el [README del repositorio](../README.md).
