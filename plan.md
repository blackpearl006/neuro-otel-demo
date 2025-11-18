# Comprehensive OpenTelemetry Observability Learning Project Plan
## For Neuroimaging Preprocessing with Apptainer Integration

---

## 🎯 Project Goals

**Primary Objective**: Create a complete observability stack learning environment with a dummy neuroimaging preprocessing pipeline, containerized using Apptainer for nipoppy compatibility.

**Learning Outcomes**:
- Understand OpenTelemetry instrumentation patterns
- Learn how traces, metrics, and logs correlate
- Master Apptainer container definitions for scientific workflows
- Practice multi-container orchestration without Docker
- Prepare for real nipoppy pipeline integration

---

## 📐 Architecture Overview

### Component Stack

```
┌─────────────────────────────────────────────┐
│         User Interface (Grafana)            │
│         Port: 3000                          │
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
        │  (Python with OTel)   │
        └───────────────────────┘
```

### Container Strategy

**Five Apptainer containers**:
1. `otel-collector.sif` - Central telemetry hub
2. `prometheus.sif` - Metrics storage
3. `loki.sif` - Log aggregation
4. `tempo.sif` - Trace storage
5. `grafana.sif` - Visualization dashboard

**One application container**:
6. `neuro-preprocess.sif` - Your instrumented preprocessing pipeline

---

## 📋 PHASE 1: Project Structure & Planning

### Directory Structure

```
neuro-otel-demo/
├── README.md
├── docs/
│   ├── 01-setup.md
│   ├── 02-running.md
│   ├── 03-observing.md
│   └── 04-nipoppy-integration.md
│
├── app/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Main orchestration
│   │   ├── stages/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py         # Stage 1: Load scan
│   │   │   ├── processor.py      # Stage 2: Process
│   │   │   └── writer.py         # Stage 3: Save
│   │   └── telemetry/
│   │       ├── __init__.py
│   │       ├── tracer_setup.py   # Tracing configuration
│   │       ├── metrics_setup.py  # Metrics configuration
│   │       └── logger_setup.py   # Logging configuration
│   ├── cli.py                     # Entry point
│   └── tests/
│
├── containers/
│   ├── app.def                    # Application container
│   ├── otel-collector.def
│   ├── prometheus.def
│   ├── loki.def
│   ├── tempo.def
│   ├── grafana.def
│   └── build_all.sh
│
├── configs/
│   ├── otel-collector-config.yaml
│   ├── prometheus.yml
│   ├── loki-config.yaml
│   ├── tempo-config.yaml
│   └── grafana/
│       ├── datasources.yaml
│       └── dashboards/
│           └── preprocessing-dashboard.json
│
├── scripts/
│   ├── start_stack.sh             # Launch all containers
│   ├── stop_stack.sh              # Clean shutdown
│   ├── run_demo.sh                # Execute demo scenarios
│   └── test_telemetry.sh          # Verify data flow
│
└── data/
    ├── input/                     # Dummy input files
    ├── output/                    # Processed output
    └── telemetry/                 # Persistent storage volumes
        ├── prometheus/
        ├── loki/
        ├── tempo/
        └── grafana/
```

### Key Decisions

**Language**: Python 3.10+ (matches nipoppy ecosystem)

**OpenTelemetry SDK**: Official Python SDK with OTLP exporters

**Container Runtime**: Apptainer/Singularity (for HPC compatibility)

**Data Persistence**: Bind mounts to local directories (avoid overlay complexity initially)

**Network Strategy**: Use localhost with different ports (simpler than Apptainer networking)

**Configuration Management**: YAML files mounted into containers at runtime

---

## 📋 PHASE 2: Apptainer Container Definitions

### 2.1 Base Strategy

**Decision Point**: Build from Docker images or from scratch?
- **Recommendation**: Bootstrap from Docker Hub images for standard components
- **Reason**: Official images are well-maintained, saves time, focuses learning on observability

### 2.2 Container Definition Details

#### A. OpenTelemetry Collector Container (`otel-collector.def`)

**Base Image**: `otel/opentelemetry-collector-contrib:latest`

**Purpose**: 
- Receive telemetry via OTLP (traces, metrics, logs)
- Process and batch data
- Export to Prometheus, Loki, Tempo

**Bind Mounts Needed**:
- Config: `/path/to/configs/otel-collector-config.yaml:/etc/otelcol/config.yaml`

**Ports Exposed**:
- 4317: OTLP gRPC receiver
- 4318: OTLP HTTP receiver
- 8888: Metrics endpoint (for collector self-monitoring)

**Key Configuration Sections**:
- Receivers: otlp (gRPC + HTTP)
- Processors: batch, memory_limiter
- Exporters: prometheus, loki, otlp (to Tempo)
- Service: pipelines for traces, metrics, logs

**Definition Structure**:
```
Bootstrap: docker
From: otel/opentelemetry-collector-contrib:latest

%files
    # Copy default config if needed

%environment
    export OTEL_CONFIG=/etc/otelcol/config.yaml

%runscript
    exec /otelcol --config=${OTEL_CONFIG}

%labels
    Author your-name
    Version 1.0
    Purpose OpenTelemetry Collector for telemetry aggregation
```

#### B. Prometheus Container (`prometheus.def`)

**Base Image**: `prom/prometheus:latest`

**Purpose**: 
- Scrape metrics from OTel Collector
- Store time-series data
- Provide PromQL query interface

**Bind Mounts Needed**:
- Config: `/path/to/configs/prometheus.yml:/etc/prometheus/prometheus.yml`
- Data: `/path/to/data/telemetry/prometheus:/prometheus`

**Ports Exposed**:
- 9090: Web UI and API

**Key Configuration**:
- Scrape interval: 15s
- Scrape target: OTel Collector metrics endpoint
- Retention: 15d (configurable)

**Storage Considerations**:
- TSDB stored in bind mount for persistence
- Pre-create directory with proper permissions

#### C. Loki Container (`loki.def`)

**Base Image**: `grafana/loki:latest`

**Purpose**:
- Receive logs from OTel Collector
- Index by labels (not full-text)
- Provide LogQL query interface

**Bind Mounts Needed**:
- Config: `/path/to/configs/loki-config.yaml:/etc/loki/config.yaml`
- Data: `/path/to/data/telemetry/loki:/loki`

**Ports Exposed**:
- 3100: HTTP API

**Key Configuration**:
- Ingester: Chunk storage settings
- Schema config: Index period, object store
- Storage: Local filesystem (for simplicity)
- Retention: 7d

#### D. Tempo Container (`tempo.def`)

**Base Image**: `grafana/tempo:latest`

**Purpose**:
- Receive traces via OTLP from OTel Collector
- Store trace data
- Provide TraceQL query interface

**Bind Mounts Needed**:
- Config: `/path/to/configs/tempo-config.yaml:/etc/tempo/config.yaml`
- Data: `/path/to/data/telemetry/tempo:/tmp/tempo`

**Ports Exposed**:
- 3200: HTTP API
- 4317: OTLP gRPC receiver (direct from collector)

**Key Configuration**:
- Receiver: OTLP
- Storage: Local filesystem backend
- Retention: Configurable based on disk space

#### E. Grafana Container (`grafana.def`)

**Base Image**: `grafana/grafana:latest`

**Purpose**:
- Unified visualization interface
- Connect to Prometheus, Loki, Tempo
- Pre-configured dashboards

**Bind Mounts Needed**:
- Datasources: `/path/to/configs/grafana/datasources.yaml:/etc/grafana/provisioning/datasources/`
- Dashboards: `/path/to/configs/grafana/dashboards/:/etc/grafana/provisioning/dashboards/`
- Data: `/path/to/data/telemetry/grafana:/var/lib/grafana`

**Ports Exposed**:
- 3000: Web UI

**Key Configuration**:
- Datasource provisioning: Auto-configure Prometheus, Loki, Tempo
- Dashboard provisioning: Load pre-built dashboards
- Auth: Disable for local development (or use admin/admin)

#### F. Application Container (`app.def`)

**Base Image**: Start from `python:3.10-slim`

**Purpose**:
- Run the instrumented preprocessing pipeline
- Send telemetry to OTel Collector

**Build Steps**:
```
Bootstrap: docker
From: python:3.10-slim

%files
    ./app /app

%post
    cd /app
    pip install --no-cache-dir -r requirements.txt
    pip install -e .

%environment
    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
    export OTEL_SERVICE_NAME=neuro-preprocess
    export PYTHONUNBUFFERED=1

%runscript
    exec python -m neuro_preprocess "$@"

%labels
    Author your-name
    Version 1.0
```

**Python Dependencies**:
- opentelemetry-api
- opentelemetry-sdk
- opentelemetry-exporter-otlp-proto-grpc
- opentelemetry-instrumentation-logging
- Standard library only (time, random, logging, argparse)

---

## 📋 PHASE 3: Application Design

### 3.1 Pipeline Architecture

**Three-Stage Pipeline**:

1. **Load Stage** (`stages/loader.py`)
   - Simulate reading NIfTI/DICOM
   - Sleep 2-5 seconds (random)
   - Log: "Loading scan_{id}.nii.gz"
   - Emit metric: scan_size_mb (random 50-500)
   - Span attributes: file_path, file_size, format

2. **Process Stage** (`stages/processor.py`)
   - Simulate skull stripping, motion correction
   - Sleep 3-7 seconds (random)
   - 20% chance of random failure
   - Log: "Processing scan_{id}: motion_detected={bool}"
   - Emit metric: processing_duration_seconds
   - Span attributes: motion_detected, quality_score (random)

3. **Save Stage** (`stages/writer.py`)
   - Simulate writing output
   - Sleep 1-2 seconds (random)
   - Log: "Saved scan_{id}_processed.nii.gz"
   - Emit metric: output_size_mb
   - Span attributes: output_path, compression_ratio

### 3.2 Telemetry Instrumentation Strategy

#### Tracing Design

**Span Hierarchy**:
```
root_span: "preprocess_scan"
├── child_span: "load_scan"
├── child_span: "process_scan"
│   ├── child_span: "skull_strip"
│   └── child_span: "motion_correct"
└── child_span: "save_scan"
```

**Span Attributes** (following OpenTelemetry semantic conventions):
- `scan.id`: Unique identifier
- `scan.format`: "nifti" or "dicom"
- `scan.size_mb`: File size
- `processing.quality_score`: 0-100
- `processing.motion_detected`: boolean
- `error`: boolean (if failed)
- `error.message`: Failure reason

**Span Events** (for significant milestones):
- "validation_passed"
- "quality_check_completed"
- "error_detected"

#### Metrics Design

**Metric Types & Names**:

1. **Counters** (monotonically increasing):
   - `scans_processed_total{status="success|failed", stage="load|process|save"}`
   - `errors_total{stage="load|process|save", error_type="..."}`

2. **Histograms** (distribution of values):
   - `stage_duration_seconds{stage="load|process|save"}` (buckets: 0.1, 0.5, 1, 2, 5, 10)
   - `scan_size_mb{format="nifti|dicom"}` (buckets: 10, 50, 100, 200, 500)
   - `quality_score{stage="process"}` (buckets: 20, 40, 60, 80, 100)

3. **Gauges** (current value):
   - `active_pipelines` (currently running)
   - `queue_depth` (waiting to process)

**Metric Labels** (for filtering):
- `stage`: Which pipeline stage
- `status`: success/failed
- `format`: nifti/dicom
- `error_type`: timeout/validation/processing

#### Logging Design

**Log Levels**:
- DEBUG: Detailed parameter values, internal state
- INFO: Stage start/completion, normal operation
- WARNING: Quality issues, retries
- ERROR: Processing failures, exceptions

**Log Structure** (JSON format):
```
{
  "timestamp": "2025-11-16T10:30:45.123Z",
  "level": "INFO",
  "message": "Processing scan_042 completed",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "scan_id": "scan_042",
  "stage": "process",
  "duration_seconds": 5.23,
  "quality_score": 87
}
```

**Log-Trace Correlation**:
- Inject trace_id and span_id into every log record
- Enables jumping from trace to logs in Grafana

### 3.3 CLI Interface Design

**Basic Command**:
```bash
neuro-preprocess --input scan_001.nii.gz --output ./output/
```

**Batch Processing**:
```bash
neuro-preprocess --input-dir ./scans/ --output-dir ./output/ --parallel 3
```

**Options**:
- `--input`: Single scan file
- `--input-dir`: Directory of scans (process all)
- `--output` / `--output-dir`: Where to save
- `--parallel`: Number of concurrent pipelines
- `--fail-rate`: Probability of random failure (0.0-1.0) for testing
- `--slow-stage`: Which stage to artificially slow down
- `--otel-endpoint`: OTel Collector endpoint (default: localhost:4317)
- `--verbose`: Enable DEBUG logging

**Demo Scenarios**:
1. `run_demo.sh normal`: 10 scans, normal execution
2. `run_demo.sh failures`: High failure rate to test error tracking
3. `run_demo.sh slow`: Bottleneck in process stage
4. `run_demo.sh concurrent`: Run 5 pipelines simultaneously

---

## 📋 PHASE 4: Configuration Files

### 4.1 OpenTelemetry Collector Configuration

**File**: `configs/otel-collector-config.yaml`

**Key Sections**:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 100
  
  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  # For Prometheus
  prometheus:
    endpoint: "0.0.0.0:8889"
  
  # For Loki
  loki:
    endpoint: http://localhost:3100/loki/api/v1/push
  
  # For Tempo
  otlp/tempo:
    endpoint: localhost:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo]
    
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

**Important Decisions**:
- Batching: Reduce network overhead
- Memory limiting: Prevent OOM in collector
- Multiple exporters: One per backend

### 4.2 Prometheus Configuration

**File**: `configs/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['localhost:8889']
  
  - job_name: 'neuro-preprocess'
    static_configs:
      - targets: ['localhost:8889']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'neuro_.*'
        action: keep
```

**Retention and Storage**:
```yaml
storage:
  tsdb:
    path: /prometheus
    retention.time: 15d
```

### 4.3 Loki Configuration

**File**: `configs/loki-config.yaml`

**Minimal configuration**:
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  retention_period: 168h  # 7 days
```

### 4.4 Tempo Configuration

**File**: `configs/tempo-config.yaml`

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

ingester:
  trace_idle_period: 10s
  max_block_duration: 5m

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces
    wal:
      path: /tmp/tempo/wal
```

### 4.5 Grafana Datasource Provisioning

**File**: `configs/grafana/datasources.yaml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
  
  - name: Loki
    type: loki
    access: proxy
    url: http://localhost:3100
    editable: false
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
  
  - name: Tempo
    type: tempo
    access: proxy
    url: http://localhost:3200
    editable: false
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        filterByTraceID: true
        filterBySpanID: false
      nodeGraph:
        enabled: true
```

**Key Feature**: Trace-to-logs correlation configured

---

## 📋 PHASE 5: Implementation Steps

### Step 1: Environment Setup
**Goal**: Prepare development environment

**Tasks**:
1. Install Apptainer/Singularity on your system
2. Verify: `apptainer --version`
3. Create project directory structure
4. Initialize git repository
5. Create Python virtual environment
6. Install Python dependencies locally for development

**Validation**: Can run `apptainer build --help`

---

### Step 2: Build Observability Containers
**Goal**: Create all five backend containers

**Tasks**:
1. Write each `.def` file following specifications above
2. Create `containers/build_all.sh`:
   - Loop through all .def files
   - Run `apptainer build <name>.sif <name>.def`
   - Handle build errors
3. Execute build script
4. Verify all `.sif` files created

**Expected Output**: 5 `.sif` files in `containers/` directory

**Validation**: `apptainer inspect <container>.sif` shows metadata

---

### Step 3: Write Configuration Files
**Goal**: Create configs for all services

**Tasks**:
1. Create `configs/` directory
2. Write `otel-collector-config.yaml` (full pipeline)
3. Write `prometheus.yml` (scrape config)
4. Write `loki-config.yaml` (local storage)
5. Write `tempo-config.yaml` (OTLP receiver)
6. Create `grafana/datasources.yaml` (all three sources)
7. Validate YAML syntax: `yamllint configs/*.yaml`

**Validation**: No YAML syntax errors

---

### Step 4: Create Data Directories
**Goal**: Prepare persistent storage locations

**Tasks**:
1. Create `data/telemetry/` subdirectories
2. Set permissions (may need ownership adjustments)
3. Create empty marker files to preserve in git
4. Document expected directory structure

**Structure**:
```
data/telemetry/
├── prometheus/
├── loki/
├── tempo/
└── grafana/
```

---

### Step 5: Develop Application (No Telemetry)
**Goal**: Create basic pipeline without instrumentation

**Tasks**:
1. Set up Python project structure
2. Implement `stages/loader.py`:
   - Function: `load_scan(scan_id)`
   - Sleep random 2-5s
   - Print "Loading {scan_id}"
   - Return dummy data dict
3. Implement `stages/processor.py`:
   - Function: `process_scan(data)`
   - Sleep random 3-7s
   - 20% chance raise exception
   - Print "Processing {scan_id}"
4. Implement `stages/writer.py`:
   - Function: `save_scan(data)`
   - Sleep random 1-2s
   - Print "Saving {scan_id}"
5. Implement `pipeline.py`:
   - Orchestrate three stages
   - Handle exceptions
   - Return success/failure
6. Implement `cli.py`:
   - Argparse for CLI
   - Call pipeline for each input
7. Test locally: `python -m neuro_preprocess --input test.nii.gz`

**Validation**: Pipeline runs, prints stages, handles failures

---

### Step 6: Add OpenTelemetry Tracing
**Goal**: Instrument with distributed tracing

**Tasks**:
1. Create `telemetry/tracer_setup.py`:
   - Initialize TracerProvider
   - Configure OTLP exporter (endpoint from env var)
   - Set service.name resource attribute
2. Modify `pipeline.py`:
   - Import tracer
   - Wrap main function with `@tracer.start_as_current_span("preprocess_scan")`
   - Add scan_id as span attribute
3. Modify each stage:
   - Wrap functions with span decorators
   - Add relevant attributes (size, quality, etc.)
   - Add span events for milestones
4. Test locally (no collector yet):
   - Should see warnings about exporter failing
   - Add `ConsoleSpanExporter` for testing

**Validation**: Traces printed to console with parent-child relationships

---

### Step 7: Add OpenTelemetry Metrics
**Goal**: Emit performance and business metrics

**Tasks**:
1. Create `telemetry/metrics_setup.py`:
   - Initialize MeterProvider
   - Configure OTLP exporter
   - Create meter instance
2. Define metrics in each stage:
   - Counter: scans_processed
   - Histogram: stage_duration
   - Histogram: scan_size
3. Modify stages to record metrics:
   - Start timer, measure duration
   - Increment counters
   - Record histogram values
4. Test with `ConsoleMetricExporter`

**Validation**: Metrics printed to console

---

### Step 8: Add OpenTelemetry Logging
**Goal**: Structured logging with trace correlation

**Tasks**:
1. Create `telemetry/logger_setup.py`:
   - Configure Python logging
   - Add OTel logging handler
   - Set log level from env var
2. Inject trace context into logs:
   - Use `opentelemetry.instrumentation.logging`
   - Ensure trace_id, span_id in log records
3. Replace all `print()` with `logger.info/debug/error()`
4. Add structured fields: `logger.info("msg", extra={'scan_id': ...})`

**Validation**: Logs include trace_id and span_id

---

### Step 9: Launch Observability Stack
**Goal**: Start all backend services

**Tasks**:
1. Write `scripts/start_stack.sh`:
   ```bash
   # Start each container with apptainer instance start
   apptainer instance start \
     --bind configs/otel-collector-config.yaml:/etc/otelcol/config.yaml \
     containers/otel-collector.sif \
     otel-collector
   
   # Similarly for prometheus, loki, tempo, grafana
   ```
2. Handle port conflicts
3. Wait for services to be ready (health checks)
4. Print access URLs

**Key Command Pattern**:
```bash
apptainer instance start \
  --bind <config-file>:<container-path> \
  --bind <data-dir>:<container-path> \
  <container.sif> \
  <instance-name>
```

**Validation**: 
- `apptainer instance list` shows 5 running instances
- `curl http://localhost:9090` (Prometheus)
- `curl http://localhost:3000` (Grafana)
- `curl http://localhost:4318/v1/traces` (OTel Collector)

---

### Step 10: Build Application Container
**Goal**: Containerize the Python app

**Tasks**:
1. Write `containers/app.def` with app files
2. Build: `apptainer build containers/app.sif containers/app.def`
3. Test run:
   ```bash
   apptainer run \
     --env OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
     containers/app.sif \
     --input test.nii.gz
   ```

**Validation**: App runs, telemetry exports to OTel Collector

---

### Step 11: Verify Data Flow
**Goal**: Confirm telemetry reaches backends

**Tasks**:
1. Run one preprocessing job from container
2. Check Prometheus:
   - Open http://localhost:9090
   - Query: `neuro_scans_processed_total`
   - Should see data points
3. Check Loki:
   - Open Grafana → Explore → Loki
   - Query: `{job="neuro-preprocess"}`
   - Should see log lines
4. Check Tempo:
   - Open Grafana → Explore → Tempo
   - Search for recent traces
   - Should see trace tree
5. Verify trace-to-logs linking works

**Validation Checklist**:
- [ ] Metrics in Prometheus
- [ ] Logs in Loki
- [ ] Traces in Tempo
- [ ] Clicking trace opens correlated logs

---

### Step 12: Create Demo Scenarios
**Goal**: Generate interesting telemetry data

**Tasks**:
1. Write `scripts/run_demo.sh` with scenarios:
   - **Normal**: 10 scans, default settings
   - **Failures**: High error rate (50%)
   - **Slow**: Increase sleep in process stage
   - **Concurrent**: 5 parallel pipelines
2. Run each scenario
3. Observe differences in Grafana

**Commands**:
```bash
./scripts/run_demo.sh normal
./scripts/run_demo.sh failures
./scripts/run_demo.sh slow
./scripts/run_demo.sh concurrent
```

---

### Step 13: Build Grafana Dashboards
**Goal**: Create visualization for pipeline metrics

**Tasks**:
1. Create dashboard with panels:
   - **Top Row**: KPIs
     - Total scans processed (counter)
     - Success rate (calculated)
     - Average processing time
   - **Second Row**: Performance
     - Stage duration histogram (heatmap)
     - Throughput over time (graph)
   - **Third Row**: Errors
     - Error rate by stage
     - Error types (pie chart)
2. Add variables for filtering:
   - Stage selector
   - Time range
3. Export dashboard JSON to `configs/grafana/dashboards/`
4. Configure dashboard provisioning

**Key Queries**:
- Success rate: `sum(rate(neuro_scans_processed_total{status="success"}[5m])) / sum(rate(neuro_scans_processed_total[5m]))`
- P95 duration: `histogram_quantile(0.95, rate(neuro_stage_duration_seconds_bucket[5m]))`

---

### Step 14: Create Stop/Cleanup Scripts
**Goal**: Graceful shutdown and cleanup

**Tasks**:
1. Write `scripts/stop_stack.sh`:
   - Stop all Apptainer instances
   - `apptainer instance stop <instance-name>`
2. Optional: Cleanup script to remove data
3. Add signal handling for graceful shutdown

---

### Step 15: Write Documentation
**Goal**: Comprehensive usage guide

**Tasks**:
1. `docs/01-setup.md`:
   - Prerequisites
   - Building containers
   - Directory setup
2. `docs/02-running.md`:
   - Starting the stack
   - Running preprocessing
   - Demo scenarios
3. `docs/03-observing.md`:
   - Accessing Grafana
   - Example queries
   - Troubleshooting data flow
4. `docs/04-nipoppy-integration.md`:
   - How to adapt for nipoppy
   - Boutiques descriptor creation
   - Container registry considerations

**README.md** should include:
- Quick start (5 commands to get running)
- Architecture diagram
- Screenshots of Grafana dashboards
- Learning objectives checklist

---

## 📋 PHASE 6: Nipoppy Integration Planning

### 6.1 Nipoppy Context

**What nipoppy expects**:
- Boutiques descriptors for tools
- Containers (Singularity/Apptainer/Docker)
- Standardized input/output paths
- BIDS-like directory structure

### 6.2 Adapting Your Project

**Changes needed**:
1. **Boutiques Descriptor**: Create JSON descriptor for `neuro-preprocess` tool
2. **Input/Output Conventions**: 
   - Read from nipoppy's `proc/` directory
   - Write to expected output locations
   - Use nipoppy's participant/session naming
3. **Container Registry**: 
   - Push to Singularity Hub or local registry
   - Or provide .sif files directly
4. **Configuration**: 
   - Read nipoppy config for subject lists
   - Respect nipoppy's logging conventions

### 6.3 Observability in Nipoppy Pipelines

**Strategy**:
- **Option A**: Standalone observability stack per HPC node
  - Launch services in background
  - Process subjects
  - Collect telemetry
  - Shutdown and save results

- **Option B**: Central observability server
  - Long-running Grafana/Prometheus/etc on head node
  - Compute nodes send telemetry over network
  - Requires network configuration

- **Recommendation**: Start with Option A for learning, move to Option B for production

### 6.4 Boutiques Descriptor Example Structure

**File**: `neuro-preprocess.json`

```json
{
  "name": "neuro-preprocess",
  "tool-version": "1.0.0",
  "description": "Neuroimaging preprocessing with OpenTelemetry",
  "command-line": "neuro-preprocess [INPUT_FILE] [OUTPUT_DIR] [OTEL_ENDPOINT]",
  "container-image": {
    "type": "singularity",
    "image": "neuro-preprocess.sif"
  },
  "inputs": [...],
  "output-files": [...]
}
```

---

## 📋 PHASE 7: Testing & Validation

### 7.1 Unit Tests
- Test each stage function independently
- Mock sleep/random for deterministic tests
- Verify span creation (use `TestSpanExporter`)
- Verify metrics recording

### 7.2 Integration Tests
- Start observability stack
- Run full pipeline
- Query backends for expected data
- Verify data correlation (trace_id in logs)

### 7.3 Load Testing
- Run 100+ scans concurrently
- Monitor collector/backend resource usage
- Verify no data loss
- Check for memory leaks

### 7.4 Failure Testing
- Kill collector mid-run (should queue/retry)
- Kill backend services (collector should buffer)
- Network delays (verify timeouts work)
- Disk full scenarios

---

## 📋 PHASE 8: Advanced Features (Optional)

### 8.1 Trace Sampling
- Implement head-based sampling in collector
- Reduce trace volume (e.g., sample 10%)
- Preserve all error traces

### 8.2 Custom Metrics
- Add business metrics (e.g., artifacts detected)
- Gauge for current memory usage
- Up/down counter for queue depth

### 8.3 Alerting
- Configure Grafana alerts
- Alert on high error rate
- Alert on slow stages
- Send to Slack/email (optional)

### 8.4 Log Enrichment
- Add hostname to logs
- Add git commit SHA
- Add user/session info

### 8.5 Trace Context Propagation
- If using multiple services, propagate context
- Use W3C Trace Context headers
- Demonstrate cross-service tracing

---

## 🎓 Learning Checkpoints

### After Phase 2-4 (Infrastructure):
- [ ] Understand Apptainer container lifecycle
- [ ] Can bind mount configurations
- [ ] Know how to start/stop instances
- [ ] Understand port management

### After Phase 5 (Application):
- [ ] Can instrument Python code with OTel
- [ ] Understand span hierarchy
- [ ] Can create custom metrics
- [ ] Know how to correlate logs with traces

### After Phase 6-7 (Integration):
- [ ] Can query Prometheus with PromQL
- [ ] Can query Loki with LogQL
- [ ] Can navigate trace flamegraphs
- [ ] Can build Grafana dashboards

### After Phase 8 (Advanced):
- [ ] Understand trace sampling strategies
- [ ] Can optimize collector performance
- [ ] Can set up alerting rules
- [ ] Ready to integrate with nipoppy

---

## 🚀 Execution Strategy

### Recommended Order for Claude Code (with extended thinking):

**Session 1**: Phases 1-2 (Structure + Containers)
- Focus on getting containers built correctly
- Test each container individually

**Session 2**: Phase 3-4 (Application + Configs)
- Build the app logic
- Write all configuration files

**Session 3**: Phase 5 (Instrumentation)
- Add OTel step by step
- Verify each telemetry type works

**Session 4**: Phase 6 (Integration & Testing)
- Launch everything together
- Debug data flow issues

**Session 5**: Phase 7 (Dashboards & Docs)
- Create visualizations
- Write comprehensive docs

**Session 6** (Optional): Phase 8 (Advanced + Nipoppy)
- Nipoppy integration
- Production hardening

---

## 📝 Key Considerations for Claude Code

1. **Checkpoint after each phase**: Commit to git, verify functionality
2. **Test incrementally**: Don't build everything before testing
3. **Use extended thinking for**:
   - Container definition decisions
   - Configuration file structure
   - Debugging telemetry data flow
4. **Document decisions**: Add comments explaining "why" not just "what"
5. **Error handling**: Plan for common failures (network, permissions)