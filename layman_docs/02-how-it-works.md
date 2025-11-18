# How It Works - Complete Data Flow

This document explains how everything works together, step by step.

---

## The Big Picture

**When you run** `neuro-preprocess process scan.nii.gz`:

1. Your app processes the brain scan file
2. **While processing**, it automatically sends telemetry data
3. Telemetry goes to storage backends (Prometheus, Loki, Tempo)
4. You view the telemetry in Grafana

Let's break this down in detail!

---

## Step-by-Step: Processing A Single File

### Step 1: You Run The Command

```bash
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
```

**What happens**:
1. The CLI (`cli.py`) starts
2. **OpenTelemetry is initialized** - connects to the collector at `localhost:4317`
3. The preprocessing pipeline is created

**You see**:
```
✓ Tracing initialized: neuro-preprocess → http://localhost:4317
✓ Metrics initialized: neuro-preprocess → http://localhost:4317
✓ Logging initialized: neuro-preprocess → http://localhost:4317
```

---

### Step 2: Pipeline Starts (Root Span Created)

**Code**: `pipeline.py` → `process_file()`

**What happens**:
- A **root span** called `preprocess_file` is created
- This span gets a unique **trace ID** (like a tracking number for a package)
- The trace ID will be attached to all logs and child spans

**Think of it like**: Opening a folder for this file's processing journey

**Telemetry sent**:
- Span created with attributes:
  - `file.name`: "sub-001_T1w.nii.gz"
  - `file.path`: Full path
  - Start time recorded

**In Grafana**: This will be the top-level span in the trace waterfall

---

### Step 3: Stage 1 - Load File

**Code**: `loader.py` → `load()`

**What happens**:
1. A **child span** called `load_file` is created (inside `preprocess_file`)
2. File is read from disk
3. Simulated 3D brain image data is created
4. Metadata is extracted

**If validation is enabled**:
- Another **child span** `validate_data` is created (inside `load_file`)
- Data is checked for NaN/Inf values

**Duration**: ~0.15 seconds

**Telemetry sent**:

**Span attributes**:
- `file.size_mb`: 4.9
- `image.shape`: "(128, 128, 100)"
- `metadata.modality`: "T1-weighted MRI"

**Metrics**:
- File size: 4.9 MB
- Load duration: 0.15 seconds

**Logs**:
```
INFO - Loading file: sub-001_T1w.nii.gz
INFO - Successfully loaded sub-001_T1w.nii.gz in 0.15s
```

**In Grafana**: You'll see the `load_file` span nested under `preprocess_file`

---

### Step 4: Stage 2 - Process Image

**Code**: `processor.py` → `process()`

**What happens**:
1. A **child span** called `process_image` is created
2. Three sub-operations run (each creates a span):
   - `skull_strip` - Remove skull from brain image (~0.7s)
   - `bias_correction` - Fix intensity variations (~0.5s)
   - `normalization` - Normalize intensity values (~0.1s)

**Duration**: ~1.3 seconds total

**Telemetry sent**:

**Span attributes**:
- `image.shape`: "(128, 128, 100)"
- `modality`: "T1-weighted MRI"
- `processing.total_time`: 1.31
- `processing.steps`: 3

**Logs**:
```
INFO - Processing image with shape (128, 128, 100)
INFO - Processing completed in 1.31s
```

**In Grafana**: You'll see `process_image` with 3 child spans for each sub-step

---

### Step 5: Stage 3 - Write Output

**Code**: `writer.py` → `write()`

**What happens**:
1. A **child span** called `write_output` is created
2. Processed image is saved to disk
3. Metadata JSON file is created
4. Processing report is generated

**Duration**: ~0.5 seconds

**Telemetry sent**:

**Span attributes**:
- `output.path`: "data/output/sub-001_T1w_preprocessed"
- `output.format`: "nifti"
- `compress`: true
- `output.size_kb`: 1500

**Logs**:
```
INFO - Writing output to: sub-001_T1w_preprocessed
INFO - Successfully wrote sub-001_T1w_preprocessed
```

**In Grafana**: You'll see the `write_output` span

---

### Step 6: Pipeline Completes

**What happens**:
1. The root span `preprocess_file` is closed
2. Total duration is calculated: ~2.0 seconds
3. Final telemetry is sent

**Span status**: OK (success)

**Final span attributes**:
- `pipeline.duration`: 2.01
- `pipeline.status`: "success"

**Logs**:
```
INFO - Pipeline completed successfully for sub-001_T1w.nii.gz in 2.01s
```

**You see**:
```
✓ Complete in 2.01s
```

---

## The Complete Trace Structure

Here's what the final trace looks like (waterfall view in Grafana):

```
preprocess_file (2.01s) ████████████████████████████████████████
├─ load_file (0.15s) ████
│  └─ validate_data (0.02s) █
├─ process_image (1.31s) ██████████████████████████
│  ├─ skull_strip (0.70s) █████████████
│  ├─ bias_correction (0.50s) ██████████
│  └─ normalization (0.11s) ██
└─ write_output (0.50s) ██████████
```

**Each bar shows**:
- Width = duration
- Vertical position = when it happened
- Nesting = parent-child relationship

---

## Telemetry Data Flow

### Path 1: Traces

```
Your App creates span
       ↓
OTLP Exporter sends via gRPC
       ↓
OTel Collector (localhost:4317) receives
       ↓
Collector routes to Tempo exporter
       ↓
Tempo (localhost:3200) stores
       ↓
Grafana queries Tempo
       ↓
You see trace in Grafana UI
```

**Storage location**: `data/telemetry/tempo/`

---

### Path 2: Metrics

```
Your App records metric
       ↓
OTLP Exporter sends via gRPC
       ↓
OTel Collector (localhost:4317) receives
       ↓
Collector exposes Prometheus endpoint (:8889)
       ↓
Prometheus scrapes every 15 seconds
       ↓
Prometheus (localhost:9090) stores
       ↓
Grafana queries Prometheus
       ↓
You see metric graph in Grafana UI
```

**Storage location**: `data/telemetry/prometheus/`

**Note**: There's a **15-second delay** before metrics appear (Prometheus scrape interval)

---

### Path 3: Logs

```
Your App writes log
       ↓
OTel LoggingHandler intercepts
       ↓
Adds trace_id and span_id
       ↓
OTLP Exporter sends via gRPC
       ↓
OTel Collector (localhost:4317) receives
       ↓
Collector routes to Loki exporter
       ↓
Loki (localhost:3100) stores
       ↓
Grafana queries Loki
       ↓
You see log in Grafana UI
```

**Storage location**: `data/telemetry/loki/`

**Special feature**: Logs include trace_id, enabling **trace-to-logs correlation**!

---

## How Trace-to-Logs Correlation Works

This is one of the most powerful features!

### The Magic

1. **When a span is created**, OpenTelemetry generates a trace context:
   - Trace ID: `a1b2c3d4e5f6...` (unique for the whole operation)
   - Span ID: `1234567890ab...` (unique for this specific span)

2. **When a log is written** inside that span:
   - The logging handler automatically adds:
     - `trace_id=a1b2c3d4e5f6...`
     - `span_id=1234567890ab...`

3. **In Grafana**:
   - **Viewing a trace?** → Click "Logs for this span" → See only related logs
   - **Viewing logs?** → Click on trace_id → Jump to the full trace

### Example

**Trace view in Grafana**:
```
Span: load_file
  Duration: 0.15s
  Attributes:
    file.name: sub-001_T1w.nii.gz
    file.size_mb: 4.9
  [Button: Logs for this span] ← Click this!
```

**After clicking, you see logs**:
```
2025-11-18 21:40:14 INFO Loading file: sub-001_T1w.nii.gz
2025-11-18 21:40:14 INFO File size: 4.90 MB
2025-11-18 21:40:14 INFO Successfully loaded in 0.15s
```

**And vice versa!** Click the trace_id in a log to jump to the trace.

---

## How Services Discover Each Other

You might wonder: "How does the app know where the collector is?"

### Service Discovery via Docker Compose

**In `docker-compose.yml`**:
- All containers are on the same Docker network: `otel-network`
- Each container has a hostname matching its service name
- **Hostnames**:
  - `otel-collector`
  - `prometheus`
  - `loki`
  - `tempo`
  - `grafana`

**DNS resolution**:
- Inside the Docker network, `ping prometheus` resolves to the Prometheus container
- No need for IP addresses!

**Port mapping**:
- `3000:3000` means: Host port 3000 → Container port 3000
- You access from host: `localhost:3000`
- Containers access each other: `grafana:3000`

**Your app** (running on host, not in Docker):
- Accesses via `localhost:4317` (mapped to container port)

---

## Batch Processing Flow

When you run `neuro-preprocess batch`:

### Sequential Processing

```
For each file in directory:
  1. Create a new root span (new trace)
  2. Process the file (load → process → write)
  3. Close the span
  4. Move to next file
```

**Result**: Multiple independent traces (one per file)

**In Grafana**: You'll see multiple traces in the trace list, not one big trace

**Why?**: Each file processing is independent. If you wanted one trace for the whole batch, you'd create a parent span around the loop.

---

## Data Persistence

### What Happens When You Stop The Stack?

**Command**: `docker-compose down`

**Data that persists** (stored in Docker volumes):
- ✅ All metrics in Prometheus
- ✅ All logs in Loki
- ✅ All traces in Tempo
- ✅ Grafana dashboards and settings

**Why?**: Configured in `docker-compose.yml` with named volumes:
```yaml
volumes:
  prometheus-data:
  loki-data:
  tempo-data:
  grafana-data:
```

### If You Want To Delete All Data

**Command**: `docker-compose down -v`

**What it does**: Removes volumes (deletes all telemetry data)

**Use when**: Starting fresh, freeing disk space

---

## Configuration Files Explained

### `otel-collector-config.yaml` - The Routing Rules

**Think of it like**: A mail sorting facility's instructions

**Structure**:
```yaml
receivers:          # Where data comes in
  otlp:
    protocols:
      grpc: 4317    # Your app sends here

processors:         # What to do with data
  batch:            # Group data for efficiency
  memory_limiter:   # Don't use too much RAM

exporters:          # Where to send data
  prometheus:       # Expose metrics endpoint
  otlphttp/loki:    # Send logs to Loki
  otlp/tempo:       # Send traces to Tempo

service:            # The actual routing
  pipelines:
    traces:         # Traces go OTLP → batch → Tempo
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo]

    metrics:        # Metrics go OTLP → batch → Prometheus
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]

    logs:           # Logs go OTLP → batch → Loki
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp/loki]
```

---

### `prometheus.yml` - What Metrics To Collect

```yaml
scrape_configs:
  - job_name: 'otel-collector'
    scrape_interval: 15s              # How often to scrape
    static_configs:
      - targets: ['otel-collector:8889']  # Where to scrape from
```

**What this means**: Every 15 seconds, Prometheus asks the collector "What metrics do you have?" and stores them.

---

### `grafana/datasources.yaml` - Where Grafana Gets Data

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090    # Where Prometheus is

  - name: Loki
    type: loki
    url: http://loki:3100          # Where Loki is

  - name: Tempo
    type: tempo
    url: http://tempo:3200         # Where Tempo is
```

**What this means**: Grafana knows where to fetch data when you query.

**Auto-provisioned**: This file tells Grafana to automatically set up these datasources on startup (no manual clicking needed!).

---

## Common Patterns & Anti-Patterns

### ✅ Good Patterns

1. **One root span per high-level operation**
   - `preprocess_file` for each file
   - Not one for the whole batch

2. **Child spans for sub-operations**
   - `load_file` inside `preprocess_file`
   - Shows hierarchical relationships

3. **Meaningful span names**
   - "load_file" not "step_1"
   - Clear what the operation is

4. **Include useful attributes**
   - File names, sizes, error messages
   - Helps debugging later

5. **Log at appropriate levels**
   - INFO for normal operations
   - ERROR for actual errors
   - Don't log at ERROR for warnings

### ❌ Anti-Patterns (What NOT To Do)

1. **Creating a span for every line of code**
   - Too much overhead
   - Clutters the trace
   - Only span "meaningful" operations

2. **Forgetting to close spans**
   - Memory leaks
   - Incomplete traces
   - Use `with` statements in Python!

3. **Not including trace context in logs**
   - Loses correlation
   - Can't jump from logs → traces
   - Our logger does this automatically

4. **Too many metrics**
   - Storage cost
   - Query slowness
   - Focus on what matters

---

## Performance Impact

**Question**: Does instrumentation make my app slower?

**Answer**: Yes, but minimally if done right.

**Our pipeline**:
- **Without instrumentation**: ~1.95 seconds per file
- **With instrumentation**: ~2.00 seconds per file
- **Overhead**: ~2.5% (acceptable!)

**Where does overhead come from?**:
1. Creating span objects (~1ms each)
2. Adding attributes (~0.1ms per attribute)
3. Sending data to collector (~5-10ms total)
4. Batching minimizes network calls

**How to minimize**:
- Use sampling (only trace 1% of requests) for high-volume apps
- Batch spans before sending
- Use asynchronous exporters (we do!)
- Don't create spans in tight loops

---

## Next Steps

Now that you understand how it works:

1. **Try it yourself**: Process a file and watch the telemetry flow
2. **Read** `03-viewing-telemetry.md` to explore Grafana
3. **Experiment**: Add your own log messages, create custom metrics
4. **Build**: Create a dashboard (see `04-creating-dashboards.md`)

---

## Summary Checklist

Can you explain:

- ✅ What happens when you run `neuro-preprocess process`?
- ✅ What's the difference between a root span and child span?
- ✅ How do logs get correlated with traces?
- ✅ Why metrics appear ~15 seconds after your app runs?
- ✅ Where telemetry data is physically stored?
- ✅ How services find each other in Docker?

If yes, you're ready to dive into Grafana!
