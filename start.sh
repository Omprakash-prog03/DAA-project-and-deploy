#!/bin/sh
# ===================================================================
# Production start script for Render / any PaaS
# Uses $PORT from environment (set by Render), falls back to 8085
# ===================================================================
set -e

cd "$(dirname "$0")"

# Use $PORT if provided by platform, otherwise default to 8085
PORT="${PORT:-8085}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WEB_CONCURRENCY:-2}"

echo "Starting EV Charging Station Placement & Route Planning..."
echo "  Host: ${HOST}"
echo "  Port: ${PORT}"
echo "  Workers: ${WORKERS}"

# Start with gunicorn + uvicorn workers
exec python3 -m gunicorn \
    -k uvicorn.workers.UvicornWorker \
    backend.main:app \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --timeout 120 \
    --forwarded-allow-ips "*" \
    --access-logfile - \
    --error-logfile -
