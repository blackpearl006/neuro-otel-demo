# Lesson 10: Data Flow Explained

**Estimated time**: 45-55 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand the complete end-to-end data flow
✅ Know how the three databases communicate
✅ Learn the network topology of our stack
✅ Understand protocols and data formats
✅ See how everything connects together

---

## The Complete Picture

This lesson answers the key question: **"How do all the pieces talk to each other?"**

```
┌─────────────────────────────────────────────────────┐
│                 YOUR APPLICATION                    │
│             (neuro-preprocess Python app)           │
│                                                     │
│  OTel SDK generates:                                │
│  • Traces (spans)                                   │
│  • Metrics (counters, histograms)                  │
│  • Logs (structured JSON)                          │
└────────────────┬────────────────────────────────────┘
                 │
                 │ OTLP over gRPC
                 │ (port 4317)
                 │
┌────────────────▼────────────────────────────────────┐
│           OTEL COLLECTOR (Hub)                      │
│                                                     │
│  Receives → Processes → Routes:                     │
│  • Batch processing                                 │
│  • Enrichment (add labels)                          │
│  • Filtering (drop health checks)                  │
└─────┬───────────────┬───────────────┬───────────────┘
      │               │               │
      │ OTLP          │ Prometheus    │ Loki HTTP
      │ (gRPC)        │ scrape        │ push
      │               │               │
  ┌───▼────┐     ┌────▼─────┐    ┌───▼────┐
  │ Tempo  │     │Prometheus│    │  Loki  │
  │(Traces)│     │ (Metrics)│    │ (Logs) │
  └───┬────┘     └────┬─────┘    └───┬────┘
      │               │               │
      └───────────────┼───────────────┘
                      │
                 ┌────▼─────┐
                 │ Grafana  │
                 │(Viz Layer)│
                 └──────────┘
```

---

## End-to-End Data Flow

Let's trace a single request through the entire system:

### Step 1: Application Generates Telemetry

**When you run**:
```bash
neuro-preprocess process sub-001.nii.gz -o output/
```

**The app**:
1. Creates a **root span** (`process_file`)
2. Creates **child spans** (`load_file`, `process_image`, `write_output`)
3. Records **metrics** (`files_processed_total++`, `duration_seconds=2.5`)
4. Writes **logs** (`"Processing started"`, `"File loaded"`, `"Processing completed"`)

**All three** (traces, metrics, logs) share the same **trace_id** for correlation.

---

### Step 2: OTel SDK Batches and Sends

**OTel SDK**:
1. Batches spans, metrics, and logs (efficiency)
2. Encodes in **OTLP format** (Protocol Buffers)
3. Sends via **gRPC** to collector on port **4317**

**Code** (in `app/neuro_preprocess/telemetry.py`):

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Configure exporters to send to collector
trace_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
metric_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317")
```

---

### Step 3: Collector Receives Data

**Collector's OTLP Receiver**:
1. Listens on port **4317**
2. Receives gRPC requests from app
3. Deserializes OTLP Protocol Buffers
4. Passes data to processors

**Config** (`configs/otel-collector-config.yaml`):

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317  # Accept from apps
```

---

### Step 4: Collector Processes Data

**Batch Processor**:
1. Accumulates spans, metrics, logs
2. Waits for **1 second** OR **1024 items**
3. Sends batch to exporters

**Config**:

```yaml
processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
```

**Why batching?**
- Efficiency: 1 network request vs. 1000
- Reduces backend load
- Improves throughput

---

### Step 5: Collector Routes to Backends

The collector has **three pipelines**, one for each telemetry type:

#### Pipeline 1: Traces → Tempo

**Config**:

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]  # OTLP exporter

exporters:
  otlp:
    endpoint: tempo:4317
    tls:
      insecure: true
```

**What happens**:
1. Collector sends spans to **Tempo** via OTLP gRPC (port 4317)
2. Tempo stores them in **Parquet blocks** on disk
3. Tempo indexes only **trace IDs**

---

#### Pipeline 2: Metrics → Prometheus

**Config**:

```yaml
service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889  # Expose metrics for scraping
```

**What happens**:
1. Collector exposes metrics at `http://otel-collector:8889/metrics`
2. **Prometheus scrapes** this endpoint every **15 seconds**
3. Prometheus stores in **time-series database**

**Prometheus config** (`configs/prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'otel-collector'
    scrape_interval: 15s
    static_configs:
      - targets: ['otel-collector:8889']
```

---

#### Pipeline 3: Logs → Loki

**Config**:

```yaml
service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [loki]

exporters:
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
```

**What happens**:
1. Collector pushes logs to **Loki** via HTTP POST
2. Loki indexes by **labels** (service_name, level)
3. Loki stores log content in **chunks** on disk

---

### Step 6: Grafana Queries Backends

When you open Grafana and explore data:

**For Traces**:
```
Grafana → Tempo HTTP API (port 3200)
Query: "Find trace by ID abc123"
Tempo → Reads from disk → Returns trace
```

**For Metrics**:
```
Grafana → Prometheus HTTP API (port 9090)
Query: "rate(neuro_files_processed_total[5m])"
Prometheus → Evaluates PromQL → Returns time series
```

**For Logs**:
```
Grafana → Loki HTTP API (port 3100)
Query: "{service_name="neuro-preprocess"}"
Loki → Filters by labels → Greps content → Returns logs
```

---

## How the Three Databases "Talk"

**Key insight**: The databases **don't directly talk to each other**. They're connected via **correlation IDs** (trace_id).

### Correlation Flow

```
┌──────────────────────────────────────────────────┐
│  1. Metrics show a spike                         │
│     "Error rate increased!"                      │
│                                                  │
│     PromQL: rate(errors_total[5m])              │
└───────────────────┬──────────────────────────────┘
                    │
                    │ User clicks "Exemplars"
                    │ Gets trace_id: abc123
                    │
┌───────────────────▼──────────────────────────────┐
│  2. Traces show which requests failed            │
│     "These 5 traces have errors"                 │
│                                                  │
│     TraceQL: {status = error}                    │
│     → Trace abc123 found                         │
└───────────────────┬──────────────────────────────┘
                    │
                    │ User clicks "View Logs"
                    │ Filters by trace_id: abc123
                    │
┌───────────────────▼──────────────────────────────┐
│  3. Logs show detailed error messages            │
│     "Failed because: out of memory"              │
│                                                  │
│     LogQL: {service_name="neuro-preprocess"}     │
│            | json | trace_id="abc123"            │
└──────────────────────────────────────────────────┘
```

**The "glue"**: **trace_id** links everything together.

---

## Network Topology

Let's map out all the connections:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                   (otel-network)                        │
│                                                         │
│  ┌──────────────┐                                       │
│  │     App      │                                       │
│  │ :N/A (batch) │                                       │
│  └───────┬──────┘                                       │
│          │ gRPC 4317                                    │
│          ▼                                              │
│  ┌──────────────┐                                       │
│  │  Collector   │                                       │
│  │ :4317 (gRPC) │                                       │
│  │ :4318 (HTTP) │                                       │
│  │ :8889 (Prom) │                                       │
│  └──┬───┬───┬───┘                                       │
│     │   │   │                                           │
│     │   │   └────────────────────┐                      │
│     │   │                        │                      │
│     │   │ HTTP scrape (15s)      │ HTTP push           │
│     │   │                        │                      │
│     │   ▼                        ▼                      │
│  ┌──▼────────┐      ┌────────────────┐                 │
│  │ Tempo     │      │ Prometheus     │                 │
│  │ :3200 HTTP│      │ :9090 HTTP     │                 │
│  │ :4317 gRPC│      └────────────────┘                 │
│  └───────────┘              │                          │
│                              │                          │
│                        ┌─────▼──────┐                   │
│                        │   Loki     │                   │
│                        │ :3100 HTTP │                   │
│                        └─────┬──────┘                   │
│                              │                          │
│  ┌───────────────────────────▼──────────────┐           │
│  │               Grafana                    │           │
│  │               :3000 HTTP                 │           │
│  │                                          │           │
│  │  Datasources:                            │           │
│  │  • Tempo (http://tempo:3200)             │           │
│  │  • Prometheus (http://prometheus:9090)   │           │
│  │  • Loki (http://loki:3100)               │           │
│  └──────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
                              │
                              │ Expose to host
                              ▼
                     Host: localhost:3000
```

---

## Protocols and Data Formats

### OTLP (OpenTelemetry Protocol)

**Used between**: App ↔ Collector, Collector ↔ Tempo

**Transport**: gRPC (binary, efficient)

**Format**: Protocol Buffers (serialized binary)

**Example payload** (conceptual):

```protobuf
ExportTraceServiceRequest {
  resource_spans: [
    {
      resource: {
        attributes: [
          {key: "service.name", value: "neuro-preprocess"}
        ]
      },
      scope_spans: [
        {
          spans: [
            {
              trace_id: "7f8a9b0c...",
              span_id: "11111111...",
              name: "process_file",
              start_time_unix_nano: 1637427600000000000,
              end_time_unix_nano: 1637427602500000000,
              attributes: [...]
            }
          ]
        }
      ]
    }
  ]
}
```

---

### Prometheus Scrape

**Used between**: Prometheus ↔ Collector

**Transport**: HTTP GET

**Format**: Prometheus text format

**Example payload**:

```
# HELP neuro_files_processed_total Total files processed
# TYPE neuro_files_processed_total counter
neuro_files_processed_total{status="success"} 95
neuro_files_processed_total{status="failed"} 5

# HELP neuro_process_duration_seconds Processing duration
# TYPE neuro_process_duration_seconds histogram
neuro_process_duration_seconds_bucket{le="1.0"} 10
neuro_process_duration_seconds_bucket{le="2.0"} 25
neuro_process_duration_seconds_bucket{le="5.0"} 40
neuro_process_duration_seconds_bucket{le="+Inf"} 42
neuro_process_duration_seconds_sum 105.6
neuro_process_duration_seconds_count 42
```

**Prometheus requests** `http://otel-collector:8889/metrics` every 15 seconds.

---

### Loki Push

**Used between**: Collector ↔ Loki

**Transport**: HTTP POST

**Format**: JSON

**Example payload**:

```json
{
  "streams": [
    {
      "stream": {
        "service_name": "neuro-preprocess",
        "level": "INFO"
      },
      "values": [
        [
          "1637427600000000000",
          "{\"level\":\"INFO\",\"message\":\"Processing file\",\"trace_id\":\"7f8a9b0c...\"}"
        ],
        [
          "1637427602000000000",
          "{\"level\":\"INFO\",\"message\":\"Processing completed\",\"duration\":2.5}"
        ]
      ]
    }
  ]
}
```

**Collector posts** to `http://loki:3100/loki/api/v1/push`.

---

### Grafana Queries

**Tempo Query**:
```
GET http://tempo:3200/api/traces/7f8a9b0c1d2e3f4a
Response: JSON with full trace
```

**Prometheus Query**:
```
GET http://prometheus:9090/api/v1/query?query=rate(neuro_files_processed_total[5m])
Response: JSON with time series
```

**Loki Query**:
```
GET http://loki:3100/loki/api/v1/query_range?query={service_name="neuro-preprocess"}
Response: JSON with log streams
```

---

## Data Storage on Disk

### Prometheus (`/prometheus`)

```
/prometheus/
├── chunks/              # Time-series data blocks
│   ├── 000001
│   ├── 000002
│   └── ...
├── wal/                 # Write-Ahead Log (recent data)
│   ├── 00000000
│   └── 00000001
└── snapshots/           # Backup snapshots
```

**Format**: Custom TSDB format, compressed

---

### Loki (`/loki`)

```
/loki/
├── chunks/              # Log content (compressed)
│   ├── chunk_001.gz
│   ├── chunk_002.gz
│   └── ...
└── index/               # BoltDB indexes (labels only)
    ├── index_001
    └── index_002
```

**Format**: Compressed text chunks + BoltDB index

---

### Tempo (`/tmp/tempo`)

```
/tmp/tempo/
├── blocks/              # Parquet blocks (traces)
│   ├── block-uuid-1.parquet
│   ├── block-uuid-2.parquet
│   └── ...
└── wal/                 # Write-Ahead Log
    ├── wal_001
    └── wal_002
```

**Format**: Parquet (columnar), highly compressed

---

## Correlation in Action

### Scenario: Debug a Slow Request

**Step 1**: See metrics spike

```promql
histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))
# Result: P95 = 5.2s (normally 2s)
```

**Step 2**: Find slow traces

```traceql
{duration > 5s}
# Result: 3 traces found, trace_id = abc123, def456, ghi789
```

**Step 3**: View a trace waterfall

```
Trace abc123:
├─ process_file (5.2s)
│  ├─ load_file (0.2s)
│  ├─ process_image (4.5s) ← Bottleneck!
│  │  ├─ skull_strip (4.0s) ← Very slow!
│  │  └─ ...
│  └─ write_output (0.5s)
```

**Step 4**: Check logs for that trace

```logql
{service_name="neuro-preprocess"} | json | trace_id="abc123"
```

**Result**:

```
INFO: Processing started, file_path=sub-999.nii.gz, file_size_mb=500
WARNING: Large file detected, may be slow
ERROR: Memory pressure high during skull_strip
INFO: Processing completed, duration=5.2s
```

**Diagnosis**: Large 500MB file causes slow skull_strip due to memory pressure.

**Solution**: Optimize skull_strip algorithm or increase memory.

---

## The Complete Journey: Visual Timeline

Let's trace one file processing request through time:

```
Time: 0ms
─────────────────────────────────────────────────────
App: Start processing sub-001.nii.gz
     ↓ Create root span (trace_id=abc123)
     ↓ Create metrics objects
     ↓ Write log: "Processing started"

Time: 50ms
─────────────────────────────────────────────────────
OTel SDK: Batch telemetry (waiting for more data)

Time: 200ms
─────────────────────────────────────────────────────
App: File loaded
     ↓ Close load_file span
     ↓ Increment metrics
     ↓ Write log: "File loaded"

Time: 1200ms
─────────────────────────────────────────────────────
OTel SDK: Batch full (1024 items)
          ↓ Send OTLP request to Collector (gRPC)

Time: 1250ms
─────────────────────────────────────────────────────
Collector: Receive OTLP
           ↓ Batch processor accumulates
           ↓ Wait for timeout or size

Time: 2200ms
─────────────────────────────────────────────────────
Collector: Batch timeout (1s elapsed)
           ↓ Send to exporters

Time: 2250ms
─────────────────────────────────────────────────────
Tempo: Receive traces (gRPC)
       ↓ Write to WAL
       ↓ Buffer in memory

Prometheus: Scrape metrics (HTTP GET)
            ↓ Parse text format
            ↓ Store in TSDB

Loki: Receive logs (HTTP POST)
      ↓ Index by labels
      ↓ Store in chunks

Time: 2500ms
─────────────────────────────────────────────────────
App: Processing completed
     ↓ Close root span
     ↓ Final metrics recorded
     ↓ Write log: "Completed"

Time: 3500ms
─────────────────────────────────────────────────────
OTel SDK: Send final batch

Time: 5000ms
─────────────────────────────────────────────────────
Tempo: Flush WAL to disk (Parquet block)
Prometheus: Next scrape cycle (15s interval)
Loki: Compress and persist chunks

═════════════════════════════════════════════════════
Data now available in Grafana for querying!
```

---

## Try It Yourself

### Exercise 1: Trace Data Through the Stack

1. **Enable debug logging** on the collector:

   Edit `configs/otel-collector-config.yaml`:
   ```yaml
   exporters:
     logging:
       loglevel: debug

   service:
     pipelines:
       traces:
         exporters: [otlp, logging]
   ```

2. **Restart**:
   ```bash
   docker-compose restart otel-collector
   ```

3. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **Watch logs in real-time**:
   ```bash
   docker-compose logs -f otel-collector
   ```

5. **Observe**: Traces flowing through the collector!

---

### Exercise 2: Measure End-to-End Latency

1. **Process a file** and note the time:
   ```bash
   time neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

2. **Immediately check Grafana** (http://localhost:3000)

3. **Search for the trace** in Tempo (last 5 minutes)

4. **Questions**:
   - How long did the app say it took?
   - When does the trace appear in Tempo?
   - What's the delay between processing and visibility?

---

### Exercise 3: Follow the Correlation Chain

1. **Process some files** with errors:
   ```bash
   ./scripts/run_demo.sh stress  # Generates some failures
   ```

2. **Start in Prometheus**:
   ```promql
   rate(neuro_files_failed_total[5m])
   ```
   Note the error rate.

3. **Jump to Loki**:
   ```logql
   {service_name="neuro-preprocess", level="ERROR"}
   ```
   Find an error log.

4. **Copy trace_id** from the log.

5. **Jump to Tempo**: Paste the trace_id.

6. **View the full trace** to understand what failed.

---

## Key Takeaways

1. **Data flows**: App → Collector → Backends (Tempo, Prometheus, Loki)
2. **Protocols**:
   - OTLP (gRPC): App ↔ Collector, Collector ↔ Tempo
   - HTTP scrape: Prometheus ↔ Collector
   - HTTP push: Collector ↔ Loki
3. **The three databases don't talk directly** - they're linked via **trace_id**
4. **Collector is the hub** - routes data to appropriate backends
5. **Grafana queries** all three backends independently
6. **Correlation** enables jumping between metrics → traces → logs
7. **Network**: All services run in Docker network, communicate by service name
8. **Storage**: Each backend uses optimized format (TSDB, chunks, Parquet)

---

## Quiz

1. **What protocol does the app use to send data to the collector?**
   <details>
   <summary>Click to see answer</summary>
   OTLP over gRPC on port 4317.
   </details>

2. **How does Prometheus get metrics from the collector?**
   <details>
   <summary>Click to see answer</summary>
   Prometheus scrapes (HTTP GET) the collector's /metrics endpoint on port 8889 every 15 seconds.
   </details>

3. **Do the three databases (Prometheus, Loki, Tempo) talk to each other?**
   <details>
   <summary>Click to see answer</summary>
   No, they don't communicate directly. They're correlated via trace_id - the same trace_id appears in metrics (exemplars), logs (trace_id field), and traces (trace_id).
   </details>

4. **What's the path of a trace from app to Grafana?**
   <details>
   <summary>Click to see answer</summary>
   App → OTLP (gRPC) → Collector → OTLP (gRPC) → Tempo → HTTP API → Grafana
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand the complete data flow!

**Next**: [Lesson 11: Instrumentation Patterns →](11-instrumentation-patterns.md)

In the next lesson, you'll learn:
- How to instrument your own code
- Manual vs automatic instrumentation
- Common patterns and best practices
- Real code examples

---

**Progress**: ✅ Lessons 1-10 complete (Data Flow Explained!) | ⬜ 4 lessons remaining
