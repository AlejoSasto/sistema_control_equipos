# Plan: Despliegue Render (Docker + Gunicorn)

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

Dejar el monolito listo para desplegar en Render (Blueprint + Docker) con instructivo UI para quien no ha usado la plataforma. Repo: `AlejoSasto/sistema_control_equipos`.

## Checklist

- [x] `gunicorn` en `requirements.txt`
- [x] `entrypoint.sh` (migrate + collectstatic + gunicorn)
- [x] `.dockerignore`
- [x] `Dockerfile` (Python 3.11-slim)
- [x] `docker-compose.yml` (web + postgres:16)
- [x] `settings.py`: `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS`, WhiteNoise
- [x] `.env.example` ampliado
- [x] `render.yaml` (Postgres + web Docker)
- [x] Instructivo `contexto/operaciones/despliegue-render.md`
- [x] Índices README / contexto / planes / contexto-completo

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Imagen | `Dockerfile`, `entrypoint.sh` |
| Local | `docker-compose.prod.yml` |
| Prod / web (canónico) | `docker-compose.yml` + `.env.prod.example` |
| Blueprint Render | `render.yaml` |
| Settings | `config/settings.py` |
| Instructivo | `contexto/operaciones/despliegue-render.md` |
