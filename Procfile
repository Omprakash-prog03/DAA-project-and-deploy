# Heroku / Render / Railway / Cloud Run compatible
web: gunicorn -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --forwarded-allow-ips "*" --access-logfile - --error-logfile -
