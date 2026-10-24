#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-8085}"
WORKERS="${WORKERS:-2}"
PYTHON="${PYTHON:-python3}"

echo "Starting EV Charging Station Placement & Route Planning..."
echo "  Python:  ${PYTHON}"
echo "  Host:    ${HOST}"
echo "  Port:    ${PORT}"
echo "  Workers: ${WORKERS}"

if "${PYTHON}" -c "import gunicorn" 2>/dev/null; then
    exec "${PYTHON}" -m gunicorn \
        -k uvicorn.workers.UvicornWorker \
        backend.main:app \
        --bind "${HOST}:${PORT}" \
        --workers "${WORKERS}" \
        --timeout 120 \
        --forwarded-allow-ips "*" \
        --access-logfile - \
        --error-logfile -
else
    exec "${PYTHON}" -m uvicorn backend.main:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --workers "${WORKERS}"
fi
