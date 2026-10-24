# ===================================================================
# EV Charging Station Placement & Route Planning - Production Dockerfile
# Optimized for Render (and any Docker-based PaaS)
# ===================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install OS dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -u 10001 -s /bin/bash appuser

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# App listens on $PORT (provided by Render), falls back to 8085
EXPOSE 8085

# Health check uses $PORT or fallback 8085
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8085}/api/health || exit 1

# Start the app (start.sh reads $PORT from environment)
CMD ["./start.sh"]
