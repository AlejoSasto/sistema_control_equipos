# Plan: Seguridad ISO/IEC 27001 + OWASP

**Estado:** Completado  
**Fecha:** 2026-09-19  
**Documento rector:** [`../11-plan-seguridad-iso27001-owasp.md`](../11-plan-seguridad-iso27001-owasp.md)

## Objetivo

Implementar los controles técnicos y documentales del plan de seguridad (fases S1–S3) sobre el monolito Django existente.

## Checklist

### Fase S1 — Antes de producción

- [x] Settings de producción endurecidos (`DEBUG=False`, HTTPS, HSTS, cookies Secure, Argon2, CSP, `ADMIN_URL`)
- [x] Secretos solo por variables de entorno (sin fallback inseguro en prod)
- [x] IDOR en vistas QR corregido (`ver_qr_pantalla`, `render_qr_image`)
- [x] `validate_password` en registro y panel
- [x] Política de tratamiento de datos + consentimiento en registro externo

### Fase S2 — Corto plazo

- [x] Rate limiting en login y escaneo del kiosco + bloqueo Axes
- [x] App `auditoria` con tabla `auditoria_cambio` + `LOGGING` seguro
- [x] Validación reforzada de fotos (MIME, 2 MB, redimensionado)
- [x] CI: `pip-audit` + `bandit` (+ tests)

### Fase S3 — Antes de escalar

- [x] MFA obligatorio para `admin_sistema`
- [x] Token de exhibición QR con TTL firmado
- [x] Procedimiento de incidentes + checklist de backup/restauración

## Entregables clave

| Área | Ubicación |
|------|-----------|
| Settings / CSP / Axes / OTP | `config/settings.py`, `config/middleware.py` |
| Auditoría | `apps/auditoria/` |
| QR firmado + authz | `apps/equipos/models.py`, `apps/equipos/views.py` |
| MFA | `accounts/mfa/*`, `django-otp` |
| Política de datos | `templates/legal/politica_datos.html`, registro |
| CI | `.github/workflows/security.yml` |
| Incidentes / backup | `contexto/operaciones/procedimiento-incidentes-seguridad.md`, `contexto/operaciones/checklist-backup-restauracion.md` |

## Notas

- El contrato del decorador `requiere_permiso` sigue siendo redirect (302) + mensaje, no HTTP 403.
- Escaneo acepta token firmado, UUID legado y serial durante la transición.
- Pentest externo y RNBD/SIC quedan fuera del código (checklist universitario).
- En suite de tests: `AXES_ENABLED` y `RATELIMIT_ENABLE` se desactivan automáticamente.
