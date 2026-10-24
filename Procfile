# Procfile - works on Heroku, Railway, Render, Cloud Run, and other PaaS
# Uses $PORT provided by the platform, falls back to 8085
web: python3 -m gunicorn -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --forwarded-allow-ips "*" --access-logfile - --error-logfile -
