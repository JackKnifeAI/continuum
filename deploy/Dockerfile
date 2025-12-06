# Multi-stage Dockerfile for CONTINUUM
# Optimized for production deployment with minimal attack surface

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY continuum/ ./continuum/
COPY setup.py .
COPY README.md .

# Install application
RUN pip install --no-cache-dir --user .

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="Alexander Gerard Casavant <admin@example.com>"
LABEL description="Multi-tenant AI consciousness memory infrastructure"
LABEL version="0.1.0"

# Create non-root user
RUN groupadd -r -g 1000 continuum && \
    useradd -r -u 1000 -g continuum -m -s /sbin/nologin continuum

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/continuum/.local

# Copy application from builder
COPY --from=builder /build/continuum /app/continuum

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /data /var/log/continuum /tmp && \
    chown -R continuum:continuum /app /data /var/log/continuum /tmp

# Switch to non-root user
USER continuum

# Add local binaries to PATH
ENV PATH=/home/continuum/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8420/v1/health || exit 1

# Default command
CMD ["uvicorn", "continuum.api.server:app", "--host", "0.0.0.0", "--port", "8420"]
