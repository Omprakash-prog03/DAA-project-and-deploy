# ===================================================================
# EV Charging Station Placement & Route Planning - Production Image
# ===================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install OS dependencies (curl for healthcheck, ca-certificates for HTTPS)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 10001 -s /bin/bash appuser

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Application port
EXPOSE 8085

# Health check hits the API health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8085/api/health || exit 1

# Run with gunicorn + uvicorn workers (production-grade)
CMD ["gunicorn", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "backend.main:app", \
     "--bind", "0.0.0.0:8085", \
     "--workers", "2", \
     "--timeout", "120", \
     "--forwarded-allow-ips", "*", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
