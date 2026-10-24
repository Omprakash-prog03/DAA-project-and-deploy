# ===================================================================
# EV Charging Station Placement & Route Planning - Production Image
# Works on ALL platforms: Fly.io, Google Cloud Run, Railway, Render, Heroku
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

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Application port (default 8085, but entrypoint uses $PORT if set by platform)
EXPOSE 8085

# Health check - use $PORT or fall back to 8085
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8085}/api/health || exit 1

# Run with entrypoint script (uses $PORT from platform)
ENTRYPOINT ["./docker-entrypoint.sh"]
