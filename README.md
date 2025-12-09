# OpenTelemetry Observability Learning Project
### Neuroimaging Preprocessing with Full Stack Observability

A complete learning environment for understanding **OpenTelemetry**, **distributed tracing**, **metrics**, and **logging** using a simulated neuroimaging preprocessing pipeline.

---

## 🎯 What Is This?

This project demonstrates **production-grade observability** for a Python application using:

- **OpenTelemetry** - Industry standard for instrumentation
- **Grafana** - Unified visualization dashboard
- **Prometheus** - Metrics storage and querying
- **Loki** - Log aggregation and search
- **Tempo** - Distributed tracing backend

**The Application**: A simulated brain scan preprocessing pipeline (load → process → write) that generates rich telemetry data for learning purposes.

## Architecture

```
┌─────────────────────────────────────────────┐
│         User Interface (Grafana)            │
│         http://localhost:3000               │
└─────────────────────────────────────────────┘
                    ▲
                    │ Queries
        ┌───────────┼───────────┐
        │           │           │
    ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
    │ Tempo │   │ Loki  │   │Prometh│
    │ :3200 │   │ :3100 │   │ :9090 │
    └───▲───┘   └───▲───┘   └───▲───┘
        │           │           │
        └───────────┼───────────┘
                    │ Exports
        ┌───────────▼───────────┐
        │  OTel Collector       │
        │  :4317 (gRPC)         │
        │  :4318 (HTTP)         │
        └───────────▲───────────┘
                    │ OTLP
        ┌───────────┴───────────┐
        │  Preprocessing App    │
        │  (To be built)        │
        └───────────────────────┘
```

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

- **Docker Desktop** (macOS/Windows) or Docker + Docker Compose (Linux)
- **Python 3.10+**
- **Git**

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd neuro-otel-demo

# Install the Python application
cd app/
pip install -e .
cd ..

# Start the observability stack
docker-compose up -d

# Wait ~30 seconds for all services to be healthy
```

### 3. Run Your First Demo

```bash
# Generate sample data and process it
./scripts/run_demo.sh normal
```

### 4. View Telemetry in Grafana

Open **http://localhost:3000** (login: `admin` / `admin`)

- **Pre-built Dashboard**: http://localhost:3000/d/neuroimaging-pipeline
- **Explore Traces**: Explore → Tempo → Search for "neuro-preprocess"
- **Explore Logs**: Explore → Loki → Query: `{service_name="neuro-preprocess"}`
- **Explore Metrics**: Explore → Prometheus → Try: `neuro_files_processed_total`

## Directory Structure

```
neuro-otel-demo/
├── README.md                           # This file
├── plan.md                             # Comprehensive project plan
├── docker-compose.yml                  # Orchestration configuration
│
├── containers/                         # Docker container definitions
│   ├── Dockerfile.otel-collector
│   ├── Dockerfile.prometheus
│   ├── Dockerfile.loki
│   ├── Dockerfile.tempo
│   ├── Dockerfile.grafana
│   ├── Dockerfile.app                  # Placeholder for Phase 3
│   └── build_all.sh                    # Build script
│
├── configs/                            # Service configurations
│   ├── otel-collector-config.yaml      # Collector pipeline config
│   ├── prometheus.yml                  # Scrape configuration
│   ├── loki-config.yaml                # Log storage config
│   ├── tempo-config.yaml               # Trace storage config
│   └── grafana/
│       ├── datasources.yaml            # Auto-provisioned datasources
│       └── dashboards/                 # Dashboard definitions (Phase 7)
│
└── data/                               # Runtime data (gitignored)
    ├── input/                          # Input scan files
    ├── output/                         # Processed outputs
    └── telemetry/                      # Persistent storage
        ├── prometheus/                 # Time-series database
        ├── loki/                       # Log storage
        ├── tempo/                      # Trace storage
        └── grafana/                    # Grafana database
```

## Service Details

### OpenTelemetry Collector

**Ports**: 4317 (gRPC), 4318 (HTTP), 8888 (metrics), 8889 (Prometheus exporter)

**Purpose**: Receives telemetry from applications, processes it, and exports to backends.

**Configuration**: `configs/otel-collector-config.yaml`

### Prometheus

**Port**: 9090

**Purpose**: Stores time-series metrics data and provides PromQL query interface.

**Configuration**: `configs/prometheus.yml`

**Data**: Persisted in Docker volume `prometheus-data`

### Loki

**Port**: 3100

**Purpose**: Aggregates logs with label-based indexing (like "grep for logs").

**Configuration**: `configs/loki-config.yaml`

**Data**: Persisted in Docker volume `loki-data`

### Tempo

**Ports**: 3200 (HTTP), 4317 (OTLP gRPC)

**Purpose**: Stores distributed traces with TraceQL query support.

**Configuration**: `configs/tempo-config.yaml`

**Data**: Persisted in Docker volume `tempo-data`

### Grafana

**Port**: 3000

**Purpose**: Unified visualization dashboard for metrics, logs, and traces.

**Default Login**: admin/admin (change on first login)

**Features**:
- Pre-configured datasources for Prometheus, Loki, Tempo
- Trace-to-logs correlation enabled
- Logs-to-trace correlation enabled

## Exploring the Stack

### In Grafana (http://localhost:3000)

1. **Explore Metrics**:
   - Navigate to Explore → Select "Prometheus"
   - Try query: `up` (shows which services are running)

2. **Explore Logs**:
   - Navigate to Explore → Select "Loki"
   - Try query: `{container_name="otel-collector"}`

3. **Explore Traces**:
   - Navigate to Explore → Select "Tempo"
   - Search for traces (will be empty until app sends telemetry)

### Verify Data Flow

Check that the collector is receiving and exporting data:

```bash
# Check collector metrics
curl http://localhost:8888/metrics | grep otelcol_receiver

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Loki readiness
curl http://localhost:3100/ready

# Check Tempo readiness
curl http://localhost:3200/ready
```

## Troubleshooting

### Containers won't start

```bash
# Check logs for specific service
docker-compose logs <service-name>

# Common issues:
# - Port conflicts: Check if ports 3000, 3100, 3200, 4317, 9090 are available
# - Permission issues: Ensure data directories are writable
# - Resource limits: Ensure Docker has enough memory (4GB+ recommended)
```

### Port conflicts

If you see "port already in use" errors:

```bash
# Find what's using the port
lsof -i :3000

# Change ports in docker-compose.yml if needed
# Example: "3001:3000" to map container port 3000 to host port 3001
```

### Reset everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
cd containers && ./build_all.sh
docker-compose up -d
```

### Grafana can't connect to datasources

1. Check that all services are running: `docker-compose ps`
2. Check service names match in `configs/grafana/datasources.yaml`
3. Verify network connectivity: `docker-compose exec grafana ping prometheus`

## Converting to Apptainer (Future)

This project currently uses Docker for macOS compatibility. To convert to Apptainer for HPC/nipoppy integration:

1. **Create `.def` files** from Dockerfiles:
   - Use `Bootstrap: docker` and `From:` directives
   - Convert `LABEL` to `%labels` section
   - Convert `CMD` to `%runscript`

2. **Build SIF images**:
   ```bash
   apptainer build otel-collector.sif otel-collector.def
   ```

3. **Replace docker-compose** with launch script:
   ```bash
   apptainer instance start \
     --bind configs/otel-collector-config.yaml:/etc/otelcol/config.yaml \
     otel-collector.sif otel-collector
   ```

4. **Networking**: Apptainer shares host network by default (similar to Docker host mode)


## Resources

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
