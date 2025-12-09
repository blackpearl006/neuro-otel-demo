# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an OpenTelemetry observability learning environment built around a simulated neuroimaging preprocessing pipeline. The project demonstrates production-grade observability using OpenTelemetry, Grafana, Prometheus, Loki, and Tempo.

**Architecture**: The application is a Python CLI tool (`neuro-preprocess`) that processes neuroimaging files through a three-stage pipeline (load → process → write). Each stage is instrumented with OpenTelemetry to generate traces, metrics, and structured logs. Telemetry flows through the OTel Collector to Prometheus (metrics), Loki (logs), and Tempo (traces), all visualized in Grafana.

## Development Commands

### Environment Setup

```bash
# Install the Python application (development mode)
cd app/
pip install -e .

# Start observability stack (Docker)
docker-compose up -d

# Stop observability stack
docker-compose down

# Rebuild containers after config changes
cd containers && ./build_all.sh
docker-compose up -d --force-recreate
```

### Running the Application

```bash
# Process a single file
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output

# Batch process files
neuro-preprocess batch data/input -o data/output --pattern "*.nii.gz"

# Display file information
neuro-preprocess info data/input/sub-001_T1w.nii.gz

# Run demo scenarios (requires observability stack running)
./scripts/run_demo.sh normal       # Normal processing
./scripts/run_demo.sh batch        # Batch processing
./scripts/run_demo.sh sizes        # Mixed file sizes
./scripts/run_demo.sh stress       # Stress test
./scripts/run_demo.sh realtime     # Real-time monitoring demo
./scripts/run_demo.sh correlation  # Trace-to-logs correlation
./scripts/run_demo.sh performance  # Performance comparison
./scripts/run_demo.sh all          # Run all scenarios
```

### Testing

```bash
# Run all tests from app directory
cd app/
pytest

# Run specific test categories
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests only
pytest -m telemetry             # Telemetry tests only

# Run with coverage
pytest --cov=neuro_preprocess --cov-report=html --cov-report=term

# Run specific test file
pytest neuro_preprocess/tests/test_loader.py
pytest neuro_preprocess/tests/test_processor.py -v

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

### Health Checks

```bash
# Check all services
./scripts/check_health.sh

# Manual health checks
curl http://localhost:8888/metrics  # OTel Collector metrics
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3100/ready      # Loki
curl http://localhost:3200/ready      # Tempo
curl http://localhost:3000/api/health # Grafana
```

## Code Architecture

### Application Structure

The `neuro-preprocess` application follows a modular pipeline architecture:

```
app/neuro_preprocess/
├── cli.py              # Click-based CLI interface
├── pipeline.py         # Main orchestrator (PreprocessingPipeline class)
├── stages/             # Pipeline stages (each independently testable)
│   ├── loader.py       # Stage 1: DataLoader - loads neuroimaging files
│   ├── processor.py    # Stage 2: ImageProcessor - simulates processing
│   └── writer.py       # Stage 3: DataWriter - writes output files
└── telemetry/          # OpenTelemetry instrumentation
    ├── tracer_setup.py # Distributed tracing configuration
    ├── metrics_setup.py # Metrics/counters/histograms configuration
    └── logger_setup.py  # Structured logging with trace correlation
```

**Key Design Pattern**: Each pipeline stage is a standalone class with a single primary method (`load()`, `process()`, or `write()`). Stages return dictionaries with results and statistics. The `PreprocessingPipeline` class in `pipeline.py` orchestrates stage execution and aggregates results.

### OpenTelemetry Instrumentation

Telemetry is initialized once at CLI startup in `cli.py:initialize_telemetry()`:

1. **Tracing**: Uses context propagation to create parent-child span relationships. Root span "preprocess_file" in `pipeline.py:96` wraps the entire execution. Each stage creates child spans using `@tracer.start_as_current_span()`.

2. **Metrics**: Custom metrics are created per-pipeline using `create_pipeline_metrics()` in `pipeline.py:79`. Histograms track durations, counters track files processed/failed. Metric recording happens inline after stage completion.

3. **Logging**: Standard Python logging enhanced with trace context injection (trace_id, span_id) via `logger_setup.py`. Logs automatically correlate with traces when both trace_id fields match.

**IMPORTANT**: When adding new pipeline stages or modifying telemetry, ensure:
- New spans set appropriate attributes (file.name, file.path, status)
- Errors are recorded via `span.record_exception()` and status set to ERROR
- Metrics align with existing naming conventions (e.g., `neuro_*_duration`, `neuro_files_*`)
- Logs include context (filename, stage, operation)

### Configuration Files

- `configs/otel-collector-config.yaml` - Defines receivers (OTLP gRPC/HTTP), processors (batch), and exporters (Prometheus, Loki, Tempo). Modify to change telemetry pipeline behavior.
- `configs/prometheus.yml` - Scrape targets. Add new metrics endpoints here.
- `configs/grafana/datasources.yaml` - Pre-configured datasource connections with trace-to-logs correlation enabled.
- `docker-compose.yml` - Service orchestration. All services run on `otel-network` bridge network.

### Testing Strategy

Tests are organized by component and category (unit, integration, telemetry):

- **Unit tests** (`test_loader.py`, `test_processor.py`, `test_writer.py`): Test individual stage classes in isolation. Mock file I/O where appropriate.
- **Integration tests** (`test_integration.py`): Test full pipeline with real file creation/processing.
- **Telemetry tests**: Verify span creation, metric recording, log correlation. Use `opentelemetry.sdk.trace.TracerProvider` for inspecting exported spans.

When adding new features, follow existing test patterns: parametrize common scenarios, use fixtures for pipeline setup, test both success and failure paths.

## Environment Variables

The application respects these OpenTelemetry environment variables:

- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTel Collector endpoint (default: `http://localhost:4317`)
- `OTEL_SERVICE_NAME` - Service name for telemetry (default: `neuro-preprocess`)
- `OTEL_SDK_DISABLED` - Set to `true` to disable telemetry entirely
- `ENVIRONMENT` - Deployment environment (default: `development`)

When running in Docker, these are set in `docker-compose.yml:133-135`. For local development, set them before running commands.

## Observability Access

- **Grafana**: http://localhost:3000 (admin/admin)
  - Pre-configured datasources for Prometheus, Loki, Tempo
  - Explore mode: query traces, logs, metrics interactively
  - Dashboards: `configs/grafana/dashboards/`
- **Prometheus**: http://localhost:9090 (direct metrics queries)
- **Loki**: http://localhost:3100 (log API, rarely accessed directly)
- **Tempo**: http://localhost:3200 (trace API, rarely accessed directly)

## Common Workflows

### Adding a New Pipeline Stage

1. Create new class in `app/neuro_preprocess/stages/` following existing patterns
2. Implement primary method that returns a dict with stats and results
3. Add tracing span with descriptive name and attributes
4. Record relevant metrics (duration, counts, sizes)
5. Add structured logging at key points
6. Create unit tests in `app/neuro_preprocess/tests/test_<stage>.py`
7. Update `pipeline.py` to integrate the new stage
8. Update integration tests to cover the new stage

### Modifying Telemetry Configuration

**To add new metrics**: Edit `telemetry/metrics_setup.py:create_pipeline_metrics()`. Use descriptive names following OpenTelemetry conventions (e.g., `<namespace>_<metric>_<unit>`).

**To change export destination**: Edit `configs/otel-collector-config.yaml` exporters section. Restart collector: `docker-compose restart otel-collector`.

**To add custom span attributes**: Set attributes immediately after starting span using `span.set_attribute(key, value)`. Use semantic conventions where applicable (https://opentelemetry.io/docs/specs/semconv/).

### Creating Grafana Dashboards

1. Create dashboard in Grafana UI at http://localhost:3000
2. Export as JSON (Share → Export → Save to file)
3. Save to `configs/grafana/dashboards/<dashboard-name>.json`
4. Add dashboard provider config to `configs/grafana/dashboards/dashboards.yaml` if not present
5. Restart Grafana: `docker-compose restart grafana`

Dashboards auto-provision on container start from files in the mounted volume.

## Troubleshooting

### Application not sending telemetry

- Check `OTEL_EXPORTER_OTLP_ENDPOINT` points to correct collector address
- Verify collector is running: `docker-compose ps otel-collector`
- Check collector logs: `docker-compose logs otel-collector`
- Verify app initializes telemetry (look for "✓ OpenTelemetry enabled" message)

### Tests failing

- Ensure running from `app/` directory: `cd app && pytest`
- Check test data exists in expected locations (`data/input/`, `data/output/`)
- For telemetry tests, ensure no conflicting global tracer providers from previous runs

### Docker services won't start

- Check port conflicts: `lsof -i :3000` (Grafana), `:4317` (OTel), `:9090` (Prometheus)
- Verify Docker has sufficient resources (4GB+ memory recommended)
- Check volume permissions: `data/telemetry/` directories must be writable
- Full reset: `docker-compose down -v && docker-compose up -d`
