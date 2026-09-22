# 17 — Integración Resend (correos transaccionales)

**Estado:** Implementado (MVP sync en web)  
**Fecha:** 2026-09-22  
**Ejecución:** [`planes/integracion-resend.md`](planes/integracion-resend.md)

## 1. Objetivo

Enviar correos transaccionales (bienvenida, recuperación de contraseña, aviso de desbloqueo) vía **Resend**, con registro en `EmailLog` y webhook Svix opcional (delivered / bounced / complained).

El frontend **nunca** llama a Resend; solo vistas Django.

## 2. Arquitectura vigente (MVP)

**Producción Render actual:** envío **síncrono** en el proceso web (Gunicorn). **No** requiere Redis ni worker Celery.

```
Vista (registro / reset / desbloqueo)
        │
        ▼
EmailService → EmailLog (queued) → envío inline (mismo request)
        │
        ▼
ResendAdapter → API Resend → EmailLog (sent | failed)
        │
        ▼
Webhook POST /webhooks/resend/ (opcional) → delivered | bounced | complained
```

| Modo | `EMAIL_USE_CELERY` | Requisitos |
|------|--------------------|------------|
| **MVP (vigente)** | `False` | Solo web + vars Resend |
| Fase 2 | `True` | Redis + worker Celery cola `emails` |

## 3. Apps y rutas de código

| Pieza | Ubicación |
|-------|-----------|
| Cliente Resend | `apps/integrations/resend/` |
| Dominio notificaciones | `apps/notifications/` |
| Envío sync/async | `EmailService` + `notifications.tasks.send_email_task` |
| Celery (fase 2) | `config/celery.py` |
| Webhook | `/webhooks/resend/` |
| UI reset password | `templates/accounts/password_reset_*.html` |

## 4. Variables de entorno

### Mínimas en Render (web) — canónicas MVP

```
DEBUG=False
ALLOWED_HOSTS=sistema-control-web.onrender.com
CSRF_TRUSTED_ORIGINS=https://sistema-control-web.onrender.com
PUBLIC_BASE_URL=https://sistema-control-web.onrender.com
RESEND_MOCK_MODE=False
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@dominio-verificado.com
RESEND_FROM_NAME=Control de Equipos UCundinamarca
RESEND_WEBHOOK_SECRET=whsec_...
EMAIL_USE_CELERY=False
CELERY_TASK_ALWAYS_EAGER=True
EMAIL_TOKEN_SECRET=   # opcional; vacío → SECRET_KEY
```

| Variable | Uso |
|----------|-----|
| `EMAIL_USE_CELERY` | `False` = sync en web (MVP). `True` = cola Celery (fase 2) |
| `CELERY_TASK_ALWAYS_EAGER` | Con MVP debe ser `True` (o se fuerza si `EMAIL_USE_CELERY=False`) |
| `RESEND_*` / `PUBLIC_BASE_URL` | Ver tabla anterior |
| `REDIS_URL` / `CELERY_BROKER_URL` | Solo fase 2 |

Plantilla: [`.env.example`](../.env.example). Operación: [`operaciones/despliegue-render.md`](operaciones/despliegue-render.md).

## 5. Correos MVP

| Tipo | Disparador | Bloquea login |
|------|------------|---------------|
| `welcome` | Tras autorregistro exitoso | No |
| `password_reset` | Olvidé mi contraseña (§6) | N/A |
| `account_unlocked` | Admin desbloquea Axes | No |

**Fase 2 producto (no MVP):** confirmación de correo bloqueante (`email_confirmation`).

## 6. Flujo de recuperación de contraseña

```
Login → «¿Olvidó su contraseña?»
     → GET/POST /accounts/password-reset/
     → (si usuario activo + email) EmailToken + correo password_reset
     → usuario abre /accounts/password-reset/confirmar/?token=…
     → POST nueva contraseña → login
```

| Aspecto | Valor |
|---------|--------|
| Identificador | Username, correo o documento |
| Anti-enumeración | Mensaje genérico siempre |
| Vigencia token | ~2 horas; un solo uso |
| Rate limit | Solicitud 5/m; confirmación 10/m |

## 7. Webhook Resend (opcional para el envío)

No bloquea el envío. Sirve para actualizar `EmailLog` a delivered/bounced/complained.

1. URL: `https://<host>/webhooks/resend/`
2. Eventos: `email.delivered`, `email.bounced`, `email.complained`
3. Secret → `RESEND_WEBHOOK_SECRET`

## 8. Modelos

- `EmailLog` — queued → sent | failed → (webhook) delivered | bounced | complained  
- `ResendWebhookEvent` — idempotencia `svix_id`  
- `EmailToken` — password_reset (+ purpose listo para fase 2)

## 9. Docker / Render

- **Render MVP:** servicio web + Postgres (`render.yaml`). Sin Redis/worker.
- **Local compose:** puede incluir redis/worker para probar fase 2; con `EMAIL_USE_CELERY=False` no hacen falta.
- **Fase 2:** Key Value (`noeviction`) + worker `celery -A config worker -Q emails,celery` + `EMAIL_USE_CELERY=True` + `CELERY_TASK_ALWAYS_EAGER=False`.

## 10. Checklist producción MVP

- [ ] Dominio verificado en Resend (o remitente de prueba documentado)
- [ ] `RESEND_MOCK_MODE=False`
- [ ] `EMAIL_USE_CELERY=False` y `CELERY_TASK_ALWAYS_EAGER=True`
- [ ] API key + `RESEND_FROM_EMAIL` + `PUBLIC_BASE_URL`
- [ ] Webhook opcional configurado
- [ ] Prueba: registro → welcome; olvidé contraseña → enlace usable
- [ ] `EmailLog` con `status=sent` y `resend_id`

## 11. Relación

Síntesis: [`contexto-completo-sistema.md`](contexto-completo-sistema.md) (§9.2b, §9.8).  
Brief manual: [`brief-manual-usuario-claude.md`](brief-manual-usuario-claude.md).  
Deploy: [`operaciones/despliegue-render.md`](operaciones/despliegue-render.md).
