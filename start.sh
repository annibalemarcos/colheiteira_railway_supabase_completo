#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p output/history

export PORT="${PORT:-5840}"
export STORAGE_BACKEND="${STORAGE_BACKEND:-auto}"
# O container online não deve cair silenciosamente para disco efêmero.
export STORAGE_STRICT="${STORAGE_STRICT:-true}"
export PYTHONUNBUFFERED=1

exec gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --worker-class gthread \
  --threads "${GUNICORN_THREADS:-8}" \
  --timeout "${GUNICORN_TIMEOUT:-600}" \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile - \
  server.app:app
