# 17 — Integración Resend (correos transaccionales)

**Estado:** Implementado  
**Fecha:** 2026-09-22  
**Ejecución:** [`planes/integracion-resend.md`](planes/integracion-resend.md)

## 1. Objetivo

Enviar correos transaccionales (bienvenida, recuperación de contraseña, aviso de desbloqueo) vía **Resend**, con cola **Celery** + **Redis**, registro en `EmailLog` y webhooks Svix (delivered / bounced / complained).

El frontend **nunca** llama a Resend; solo vistas Django.

## 2. Arquitectura

```
Vista de negocio (registro, reset, desbloqueo)
        │
        ▼
EmailService → EmailLog (queued) → Celery cola "emails"
        │
        ▼
ResendAdapter → API Resend → EmailLog (sent)
        │
        ▼
Webhook POST /webhooks/resend/ → EmailLog (delivered|bounced|complained)
```

## 3. Apps y rutas de código

| Pieza | Ubicación |
|-------|-----------|
| Cliente Resend | `apps/integrations/resend/` |
| Dominio notificaciones | `apps/notifications/` |
| Celery | `config/celery.py` |
| Webhook | `/webhooks/resend/` |

## 4. Variables de entorno

| Variable | Uso |
|----------|-----|
| `RESEND_API_KEY` | API key `re_...` |
| `RESEND_FROM_EMAIL` | Remitente (dominio verificado en prod) |
| `RESEND_FROM_NAME` | Nombre visible (ej. Control de Equipos UCundinamarca) |
| `RESEND_MOCK_MODE` | `True` local/tests; `False` producción |
| `RESEND_WEBHOOK_SECRET` | `whsec_...` Svix |
| `PUBLIC_BASE_URL` | Base de links en correos |
| `EMAIL_TOKEN_SECRET` | Hash de tokens reset (default: `SECRET_KEY`) |
| `REDIS_URL` / `CELERY_BROKER_URL` | Broker Celery |

## 5. Correos MVP

| Tipo | Disparador | Bloquea login |
|------|------------|---------------|
| `welcome` | Tras autorregistro exitoso | No |
| `password_reset` | Olvidé mi contraseña | N/A |
| `account_unlocked` | Admin desbloquea Axes | No |

**Fase 2 (no MVP):** confirmación de correo bloqueante (`email_confirmation`).

## 6. Modelos

- `EmailLog` — ciclo queued → sent → delivered | bounced | complained | failed
- `ResendWebhookEvent` — idempotencia por `svix_id`
- `EmailToken` — reset (y purpose listo para confirmación futura)

## 7. Docker / Render

- Compose: servicios `redis` + `worker` (además de `db` + `web`).
- Render: Key Value (Redis) + worker Docker + env Resend.
- Plan free del web **no** basta para Redis/worker estables → usar **starter** (o superior) en producción.

## 8. Checklist producción

- [ ] Dominio verificado en Resend (SPF/DKIM)
- [ ] `RESEND_MOCK_MODE=False`
- [ ] Secrets: API key + webhook secret
- [ ] Worker con cola `emails`
- [ ] Redis `noeviction`
- [ ] Webhook HTTPS + firma válida
- [ ] `PUBLIC_BASE_URL` correcto
- [ ] Throttle en forgot-password

## 9. Relación

Síntesis operativa: [`contexto-completo-sistema.md`](contexto-completo-sistema.md).  
Deploy: [`operaciones/despliegue-render.md`](operaciones/despliegue-render.md).
