# Application Container - Instrumented preprocessing pipeline
# PLACEHOLDER: Will be implemented in Phase 3-5 when application code is written

FROM python:3.10-slim

LABEL author="OpenTelemetry Learning Project"
LABEL version="1.0.0"
LABEL description="Neuroimaging preprocessing pipeline with OpenTelemetry instrumentation"

# This is a placeholder Dockerfile
# It will be completed in Phase 3 when the application code is ready

# Required environment variables (for later):
#   OTEL_EXPORTER_OTLP_ENDPOINT - Collector endpoint (default: http://otel-collector:4317)
#   OTEL_SERVICE_NAME - Service identifier (default: neuro-preprocess)

# Install system dependencies that might be needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Future: Copy application files
# COPY ./app /app

# Future: Install Python dependencies
# WORKDIR /app
# RUN pip install --no-cache-dir -r requirements.txt && \
#     pip install -e .

# Environment variables for OpenTelemetry
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_SERVICE_NAME=neuro-preprocess
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Placeholder command
CMD ["echo", "Application container placeholder - to be implemented in Phase 3"]
