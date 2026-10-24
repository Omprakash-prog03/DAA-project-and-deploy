#!/bin/sh
# ===================================================================
# Entrypoint script - works on ALL platforms (Fly.io, Cloud Run,
# Railway, Render, Heroku, etc.) by using $PORT if provided.
# ===================================================================
set -e

# Determine port: use $PORT from platform, fall back to 8085
PORT="${PORT:-8085}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WEB_CONCURRENCY:-2}"

echo "Starting EV Charging Station Placement & Route Planning..."
echo "  Host: ${HOST}"
echo "  Port: ${PORT}"
echo "  Workers: ${WORKERS}"

# Start with gunicorn + uvicorn workers (production-grade)
# Use python3 -m gunicorn to ensure correct interpreter
exec python3 -m gunicorn \
    -k uvicorn.workers.UvicornWorker \
    backend.main:app \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --timeout 120 \
    --forwarded-allow-ips "*" \
    --access-logfile - \
    --error-logfile -
