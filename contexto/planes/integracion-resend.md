# Plan: Integración Resend (plan 17)

**Estado:** Completado (MVP sync; Celery = fase 2)  
**Fecha:** 2026-09-22  
**Documento rector:** [`../17-integracion-resend.md`](../17-integracion-resend.md)

## Objetivo

Correos `welcome`, `password_reset` y `account_unlocked` vía Resend.  
**Producción vigente:** envío **síncrono** en el web (`EMAIL_USE_CELERY=False`), sin Redis ni worker.  
Celery + Redis documentados como fase 2.

## Entregables

| Área | Resultado |
|------|-----------|
| Docs | `17`, índices, `contexto-completo` §9.2b/§9.8, operaciones Render (modo sync) |
| Infra | `integrations/resend`, `notifications`, webhook; Celery opcional |
| Auth UX | Bienvenida, forgot/confirm password, unlock |
| Deploy MVP | `render.yaml` web+DB; `EMAIL_USE_CELERY=False` |
| Calidad | Tests mock / webhook / tokens |

## Checklist

- [x] Documento rector + índices
- [x] Paquete Resend + notifications + webhook
- [x] Bienvenida, reset password, unlock + plantillas
- [x] Modo sync oficial (`EMAIL_USE_CELERY=False` + eager)
- [x] `render.yaml` MVP sin Redis/worker obligatorios
- [x] Tests + contexto-completo + operaciones
- [x] Ajuste post-deploy: documentar env Render sin Celery

## Post-deploy (operativo)

- [ ] En Render Environment: `EMAIL_USE_CELERY=False`, `CELERY_TASK_ALWAYS_EAGER=True`, Resend real
- [ ] Redeploy y probar welcome / password-reset
- [ ] (Opcional) Webhook → `/webhooks/resend/`
