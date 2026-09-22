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
| Webhook | `/webhooks/resend/` (`notifications.views_webhooks`) |
| UI reset password | `templates/accounts/password_reset_*.html` |
| Vistas reset | `accounts.views.password_reset_*` |

## 4. Variables de entorno

| Variable | Uso |
|----------|-----|
| `RESEND_API_KEY` | API key `re_...` |
| `RESEND_FROM_EMAIL` | Remitente (dominio verificado en prod) |
| `RESEND_FROM_NAME` | Nombre visible (ej. Control de Equipos UCundinamarca) |
| `RESEND_MOCK_MODE` | `True` local/tests; `False` producción |
| `RESEND_WEBHOOK_SECRET` | `whsec_...` Svix (al crear el endpoint en Resend) |
| `PUBLIC_BASE_URL` | Base de links en correos (sin `/` final), ej. `https://sistema-control-web.onrender.com` |
| `EMAIL_TOKEN_SECRET` | Hash HMAC de tokens reset; **vacío** → usa `SECRET_KEY` |
| `REDIS_URL` / `CELERY_BROKER_URL` | Broker Celery |

Plantilla local: [`.env.example`](../.env.example). Operación Render: [`operaciones/despliegue-render.md`](operaciones/despliegue-render.md).

## 5. Correos MVP

| Tipo | Disparador | Bloquea login |
|------|------------|---------------|
| `welcome` | Tras autorregistro exitoso | No |
| `password_reset` | Olvidé mi contraseña (§6) | N/A |
| `account_unlocked` | Admin desbloquea Axes | No |

**Fase 2 (no MVP):** confirmación de correo bloqueante (`email_confirmation`).

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
| Identificador aceptado | Username, correo o documento |
| Anti-enumeración | Mensaje de éxito genérico siempre |
| Vigencia token | ~2 horas; un solo uso |
| Rate limit | Solicitud 5/m; confirmación 10/m |
| Hash | HMAC-SHA256 con `EMAIL_TOKEN_SECRET` o `SECRET_KEY` |
| Plantillas UI | `password_reset_request.html`, `password_reset_confirm.html` |
| Plantillas email | `emails/password_reset.html` + `.txt` |

**Distinciones:**

- Bloqueo Axes ≠ olvidé contraseña (el desbloqueo no cambia la clave; puede enviar `account_unlocked`).
- Reset admin en panel ≠ self-service por correo.

## 7. Webhook Resend

1. Desplegar código con ruta `/webhooks/resend/`.
2. En Resend → Webhooks → Add endpoint:
   - URL: `https://<host-publico>/webhooks/resend/`
   - Eventos: `email.delivered`, `email.bounced`, `email.complained`
3. Copiar signing secret → `RESEND_WEBHOOK_SECRET` en Render (web).
4. Con `RESEND_MOCK_MODE=False`, firma inválida → HTTP 401.

La vista es `csrf_exempt`, valida Svix, persiste `ResendWebhookEvent` (idempotente por `svix_id`) y encola `process_resend_webhook_event`.

## 8. Modelos

- `EmailLog` — ciclo queued → sent → delivered | bounced | complained | failed
- `ResendWebhookEvent` — idempotencia por `svix_id`
- `EmailToken` — reset (y purpose listo para confirmación futura)

Migración: `notifications.0001_initial`.

## 9. Docker / Render

- Compose: servicios `redis` + `worker` (además de `db` + `web`).
- Render: Key Value (Redis) + worker Docker + env Resend.
- Plan free del web **no** basta para Redis/worker estables → usar **starter** (o superior) en producción.
- `entrypoint.sh`: si el CMD es `celery …`, arranca worker (sin migrate/gunicorn).

## 10. Checklist producción

- [ ] Dominio verificado en Resend (SPF/DKIM) **o** remitente de prueba documentado
- [ ] `RESEND_MOCK_MODE=False`
- [ ] Secrets: API key + webhook secret
- [ ] Worker con cola `emails`
- [ ] Redis `noeviction`
- [ ] Webhook HTTPS + firma válida
- [ ] `PUBLIC_BASE_URL` correcto (enlaces de reset)
- [ ] Throttle en forgot-password (ya en código)
- [ ] Prueba: registro → welcome; olvidé contraseña → enlace usable

## 11. Relación

Síntesis operativa: [`contexto-completo-sistema.md`](contexto-completo-sistema.md) (§9.2b, §9.8).  
Manual de usuario (prompt): [`brief-manual-usuario-claude.md`](brief-manual-usuario-claude.md).  
Deploy: [`operaciones/despliegue-render.md`](operaciones/despliegue-render.md).
