# CONTINUUM - AI Memory Infrastructure
# Dockerfile for production deployment

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 continuum && \
    mkdir -p /app /data && \
    chown -R continuum:continuum /app /data

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=continuum:continuum . /app/

# Install continuum package
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER continuum

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    CONTINUUM_DATA_DIR=/data \
    CONTINUUM_HOST=0.0.0.0 \
    CONTINUUM_PORT=8000

# Entry point
CMD ["uvicorn", "continuum.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
