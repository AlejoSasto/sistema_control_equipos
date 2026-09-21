#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "Iniciando Gunicorn en 0.0.0.0:${PORT}..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY:-2}" --timeout 120
