#!/bin/sh
set -e

# Worker Celery: CMD/args empiezan por "celery" (Render dockerCommand / compose).
if [ "$1" = "celery" ]; then
  echo "Iniciando worker Celery..."
  exec "$@"
fi

if [ "${RUN_CELERY_WORKER:-}" = "1" ]; then
  echo "Iniciando worker Celery (RUN_CELERY_WORKER=1)..."
  exec celery -A config worker -l warning -Q emails,celery --concurrency="${CELERY_CONCURRENCY:-2}"
fi

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Cargando catálogos institucionales (seed_data)..."
python manage.py seed_data

echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "Iniciando Gunicorn en 0.0.0.0:${PORT}..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY:-2}" --timeout 120
