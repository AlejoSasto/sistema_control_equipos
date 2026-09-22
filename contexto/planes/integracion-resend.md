# Plan: Integración Resend (plan 17)

**Estado:** Completado  
**Fecha:** 2026-09-22  
**Documento rector:** [`../17-integracion-resend.md`](../17-integracion-resend.md)

## Objetivo

Infra Resend + Celery/Redis + webhooks; correos `welcome`, `password_reset` y `account_unlocked`; flujo UI de recuperación de contraseña; docs y deploy.

## Entregables

| Área | Resultado |
|------|-----------|
| Docs | `17-integracion-resend.md`, índices, `contexto-completo` §9.2b/§9.8, brief manual 1.1+, operaciones Render |
| Infra | `apps/integrations/resend`, `apps/notifications`, Celery, webhook Svix, deps |
| Auth UX | Bienvenida post-registro; forgot/confirm password; aviso desbloqueo Axes |
| Deploy | `docker-compose` redis/worker; `render.yaml` Key Value + worker; entrypoint Celery |
| Calidad | Tests mock / webhook / tokens reset |

## Checklist

- [x] Documento rector `17-integracion-resend.md` + índices README / planes
- [x] `apps/integrations/resend` + `apps/notifications` + Celery + webhook
- [x] Correo bienvenida tras registro (`EmailService.send_welcome`)
- [x] Flujo olvidé contraseña: `/accounts/password-reset/` + `/confirmar/` + plantillas UI/email + throttle
- [x] Correo `account_unlocked` al desbloquear Axes en panel
- [x] docker-compose redis/worker + render.yaml + `operaciones/despliegue-render.md`
- [x] `.env.example` con vars Resend / `PUBLIC_BASE_URL` / `EMAIL_TOKEN_SECRET`
- [x] Tests mock, webhook (401 + idempotencia), token válido/inválido/expirado
- [x] `contexto-completo-sistema.md` (§9.2b recuperación + §9.8 correos)
- [x] `brief-manual-usuario-claude.md` con flujo recuperación y correos (lenguaje usuario)

## Post-deploy (operativo, fuera del código)

- [ ] Env Render: `RESEND_*`, `PUBLIC_BASE_URL`, mock off
- [ ] Webhook Resend → `https://<host>/webhooks/resend/`
- [ ] Redis + worker starter si se requiere envío asíncrono real
