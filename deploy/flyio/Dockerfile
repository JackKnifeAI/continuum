# CONTINUUM Production Dockerfile
# Multi-stage build for optimized Python FastAPI deployment
#
# Build: docker build -f deploy/flyio/Dockerfile -t continuum-memory .
# Run: docker run -p 8420:8420 continuum-memory

# =============================================================================
# STAGE 1: Builder - Install dependencies
# =============================================================================

FROM python:3.11-slim as builder

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
WORKDIR /build
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    psycopg2-binary>=2.9.0 \
    asyncpg>=0.29.0 \
    redis>=5.0.0 \
    hiredis>=2.2.0 \
    gunicorn>=21.2.0

# =============================================================================
# STAGE 2: Runtime - Minimal production image
# =============================================================================

FROM python:3.11-slim

# Runtime arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root for security)
RUN useradd -m -u 1000 -s /bin/bash continuum

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY continuum/ ./continuum/
COPY pyproject.toml README.md ./

# Install package in editable mode
RUN pip install --no-cache-dir -e .

# Create data directory for SQLite fallback (if needed)
RUN mkdir -p /data && chown -R continuum:continuum /data

# Switch to non-root user
USER continuum

# Expose port
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8420/v1/health || exit 1

# Environment variables with defaults
ENV CONTINUUM_ENV=production \
    CONTINUUM_PORT=8420 \
    CONTINUUM_HOST=0.0.0.0 \
    UVICORN_WORKERS=2 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# Production startup command
# Uses uvicorn with multiple workers for performance
CMD ["uvicorn", "continuum.api.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8420", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]

# Alternative: Use gunicorn with uvicorn workers (uncomment to use)
# CMD ["gunicorn", "continuum.api.server:app", \
#      "--bind", "0.0.0.0:8420", \
#      "--workers", "2", \
#      "--worker-class", "uvicorn.workers.UvicornWorker", \
#      "--access-logfile", "-", \
#      "--error-logfile", "-", \
#      "--log-level", "info"]
