# Lesson 8: Tempo Guide

**Estimated time**: 45-55 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand how Tempo stores distributed traces
✅ Learn TraceQL query language
✅ Know how to find traces efficiently
✅ Understand trace sampling strategies
✅ Learn about trace retention and storage

---

## What Is Tempo?

### The Simple Definition

**Tempo** is a **distributed tracing backend** that stores and queries traces with minimal configuration and cost.

**Created by**: Grafana Labs (same team as Loki and Grafana)

**Design philosophy**:
- Cheap and easy to operate (like Loki)
- No indexes except trace ID (ultra-low cost)
- Integrates seamlessly with Grafana, Prometheus, and Loki

**Tagline**: "Massively scalable distributed tracing backend"

---

### Why Tempo?

**Before Tempo**, distributed tracing backends were:
- **Expensive**: Required extensive indexing
- **Complex**: Hard to set up and operate
- **Limited**: Sampling required for cost control

**Tempo's innovation**:
- Store traces in **object storage** (S3, GCS, local disk)
- Index **only trace IDs** (minimal storage)
- Find traces via **correlation** (from metrics or logs → trace ID)
- **Cheap**: Pay only for object storage, not indexes

---

## How Tempo Works

### The Core Concept

**Traditional tracing systems** (Jaeger, Zipkin):
```
┌─────────────────────────────────────┐
│ Index everything:                   │
│ - service names                     │
│ - operation names                   │
│ - tags/attributes                   │
│ - durations                         │
│                                     │
│ ✅ Search by any field              │
│ ❌ Expensive indexes                │
└─────────────────────────────────────┘
```

**Tempo**:
```
┌─────────────────────────────────────┐
│ Index ONLY trace IDs:               │
│ - 7f8a9b0c1d2e3f4a → location       │
│                                     │
│ ✅ Ultra-cheap                       │
│ ⚠️  Need trace ID to find trace     │
│ ✅ TraceQL for filtering            │
└─────────────────────────────────────┘
```

---

### How Do You Find Traces?

**Three ways to discover trace IDs**:

1. **From Metrics**:
   ```promql
   # Find slow requests in Prometheus
   rate(neuro_process_duration_seconds_bucket[5m]) > 5
   # Then click "Exemplars" to see trace IDs
   ```

2. **From Logs**:
   ```logql
   # Find errors in Loki
   {service_name="neuro-preprocess", level="ERROR"}
   # Click trace_id link to open trace
   ```

3. **TraceQL**:
   ```traceql
   # Search traces directly
   {duration > 5s && status = error}
   ```

---

## Tempo's Storage Architecture

### Data Flow

```
1. App generates trace
        ↓
2. Sent to OTel Collector (OTLP)
        ↓
3. Collector forwards to Tempo
        ↓
4. Tempo writes to:
   - Memory (recent traces, fast)
   - Local disk (buffer)
   - Object storage (long-term)
```

---

### Storage Tiers

**Tier 1: Memory (last ~1 minute)**
- Ultra-fast access
- Recent traces
- Lost on restart

**Tier 2: Local Disk (last ~1 hour)**
- Fast access
- WAL (Write-Ahead Log)
- Buffer before upload

**Tier 3: Object Storage (weeks/months)**
- Cheap, durable storage
- S3, GCS, Azure Blob, or local filesystem
- Compressed blocks

---

### Block Format

Tempo stores traces in **blocks**:

```
Block = Multiple traces compressed together
- Size: ~100MB - 1GB
- Compression: Gzip or Snappy
- Format: Parquet (columnar)
- Immutable: Once written, never modified
```

**Example**:

```
block-01.parquet   [10,000 traces, 500MB compressed]
block-02.parquet   [10,000 traces, 500MB compressed]
block-03.parquet   [10,000 traces, 500MB compressed]
...
```

**To find a trace**: Tempo checks which block contains that trace ID, then reads just that block.

---

## TraceQL: Trace Query Language

**TraceQL** is Tempo's query language for searching traces (added in Tempo 2.0+).

### Basic Structure

```traceql
{span.attribute = "value"}
```

---

### Search by Span Attributes

```traceql
# Find traces where any span has status = error
{status = error}

# Find traces where any span has duration > 5 seconds
{duration > 5s}

# Find traces for a specific file
{span.file_path = "sub-001_T1w.nii.gz"}
```

---

### Search by Resource Attributes

Resource attributes are set at the application level:

```traceql
# Find traces from a specific service
{resource.service.name = "neuro-preprocess"}

# Find traces from a specific environment
{resource.deployment.environment = "production"}
```

---

### Combine Conditions

```traceql
# Slow traces that errored
{duration > 5s && status = error}

# Traces from neuro-preprocess with errors
{resource.service.name = "neuro-preprocess" && status = error}

# Large files (>100MB)
{span.file_size_mb > 100}
```

---

### Span-Level Queries

```traceql
# Find traces where "skull_strip" span took > 1s
{name = "skull_strip" && duration > 1s}

# Find traces with specific span attribute
{span.stage = "process_image"}
```

---

### Aggregations

```traceql
# Count traces matching criteria
count({status = error})

# Average duration of traces
avg(duration) by (resource.service.name)

# P95 duration
quantile(duration, 0.95)
```

---

## Searching Traces in Grafana

### Method 1: Search by Service

1. Open Grafana → Explore → Tempo
2. Select "Search" tab
3. Choose service: `neuro-preprocess`
4. Click "Run Query"
5. Browse recent traces

---

### Method 2: TraceQL Query

1. Open Grafana → Explore → Tempo
2. Switch to "TraceQL" tab
3. Enter query:
   ```traceql
   {duration > 2s}
   ```
4. Click "Run Query"
5. See matching traces

---

### Method 3: Direct Trace ID

1. Copy trace ID from logs or metrics
2. Open Grafana → Explore → Tempo
3. Paste trace ID in search box
4. View the trace

---

### Method 4: From Logs (Correlation)

1. Open Grafana → Explore → Loki
2. Query logs:
   ```logql
   {service_name="neuro-preprocess"} |= "ERROR"
   ```
3. Click on a log entry
4. Click the "Tempo" button (trace_id link)
5. Trace opens automatically

---

### Method 5: From Metrics (Exemplars)

1. Open Grafana → Explore → Prometheus
2. Query with exemplars:
   ```promql
   histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))
   ```
3. Click "Show Exemplars"
4. See trace IDs for sampled requests
5. Click a trace ID to open

---

## Real Queries for Our Project

### Query 1: All Recent Traces

**In Grafana Search**:
- Service: `neuro-preprocess`
- Time range: Last 1 hour

---

### Query 2: Slow Traces

```traceql
{duration > 5s}
```

---

### Query 3: Failed Traces

```traceql
{status = error}
```

---

### Query 4: Slow "skull_strip" Operations

```traceql
{name = "skull_strip" && duration > 1s}
```

---

### Query 5: Large Files

```traceql
{span.file_size_mb > 10}
```

---

### Query 6: Specific File

```traceql
{span.file_path =~ ".*sub-001.*"}
```

---

### Query 7: Traces in Last 10 Minutes with Errors

**In Grafana**:
- Time range: Last 10 minutes
- TraceQL:
  ```traceql
  {status = error}
  ```

---

## Trace Sampling

### Why Sampling?

**Problem**: High-traffic applications generate millions of traces per day.

**Cost**: Storing every trace is expensive.

**Solution**: Sample a percentage of traces.

---

### Sampling Strategies

#### 1. Head-Based Sampling (Decided at Start)

**Decision**: At the beginning of the trace, decide "keep" or "drop".

**Example**: Keep 10% of all traces

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Keep 10% of traces
sampler = TraceIdRatioBased(0.1)
```

**Pros**:
- ✅ Simple
- ✅ Predictable storage costs

**Cons**:
- ❌ Might drop interesting traces (errors, slow requests)

---

#### 2. Tail-Based Sampling (Decided at End)

**Decision**: After the trace completes, decide based on properties.

**Example**: Keep all errors + 1% of successes

**Pros**:
- ✅ Keep important traces (errors, slow)
- ✅ Drop boring traces (fast, successful)

**Cons**:
- ❌ More complex (need collector or backend support)
- ❌ Higher memory usage (buffer all traces temporarily)

---

#### 3. Adaptive Sampling

**Decision**: Adjust sampling rate based on traffic.

**Example**:
- Low traffic: Keep 100%
- High traffic: Keep 1%

**Pros**:
- ✅ Always have data
- ✅ Cost-controlled at scale

---

### Our Project (No Sampling)

**Current setup**: Keep **100%** of traces (no sampling).

**Why?**
- Learning environment
- Low traffic
- Want to see all traces

**In production**, you'd enable sampling to control costs.

---

## Trace Retention

**How long to keep traces?**

### Default Retention

Our Tempo config stores traces for **7 days** by default.

---

### Configure Retention

In `configs/tempo-config.yaml`:

```yaml
compactor:
  compaction:
    block_retention: 168h  # 7 days (168 hours)
```

**Options**:
- `24h` = 1 day
- `168h` = 7 days (default)
- `720h` = 30 days
- `2160h` = 90 days

**Trade-off**: Longer retention = more storage cost.

---

### Retention Strategy

**Typical strategy**:
- **Recent traces (last 24h)**: Keep 100%
- **1-7 days**: Keep 10% (sampled)
- **7-30 days**: Keep 1% (errors only)
- **>30 days**: Delete

---

## Tempo Configuration

Our Tempo config (`configs/tempo-config.yaml`):

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
  max_block_bytes: 1_000_000
  max_block_duration: 5m

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks
    wal:
      path: /tmp/tempo/wal

compactor:
  compaction:
    block_retention: 168h  # 7 days
```

**Key settings**:
- **Receiver**: OTLP gRPC on port 4317
- **Storage**: Local filesystem (`/tmp/tempo/blocks`)
- **WAL**: Write-Ahead Log for durability
- **Retention**: 7 days

---

## Tempo vs. Jaeger vs. Zipkin

| Feature | Tempo | Jaeger | Zipkin |
|---------|-------|--------|--------|
| **Storage** | Object storage | Elasticsearch, Cassandra | Elasticsearch, Cassandra |
| **Index** | Trace ID only | Full indexing | Full indexing |
| **Cost** | Very low | High | High |
| **Query** | TraceQL, correlation | UI search | UI search |
| **Scalability** | Massive | Good | Good |
| **Setup** | Simple | Moderate | Moderate |
| **Best for** | Cost-effective at scale | Feature-rich UI | Simple setup |

---

### When to Use Tempo

✅ Cost is a concern
✅ High trace volumes
✅ Already using Grafana/Prometheus/Loki
✅ Object storage available (S3, GCS)
✅ Correlation with metrics/logs

---

### When to Use Jaeger

✅ Need rich search UI
✅ Want to search by any tag
✅ Don't have metrics/logs correlation
✅ Lower trace volumes

---

## Trace Data Model in Tempo

Each trace stored includes:

```json
{
  "traceId": "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
  "spans": [
    {
      "spanId": "1111111111111111",
      "parentSpanId": null,
      "name": "process_file",
      "startTimeUnixNano": 1637427600000000000,
      "endTimeUnixNano": 1637427602500000000,
      "attributes": {
        "file.path": "sub-001_T1w.nii.gz",
        "file.size_mb": 4.9
      },
      "status": {
        "code": "OK"
      }
    },
    {
      "spanId": "2222222222222222",
      "parentSpanId": "1111111111111111",
      "name": "load_file",
      "startTimeUnixNano": 1637427600000000000,
      "endTimeUnixNano": 1637427600200000000,
      "attributes": {
        "array.shape": "(256, 256, 256)"
      },
      "status": {
        "code": "OK"
      }
    }
  ],
  "resource": {
    "attributes": {
      "service.name": "neuro-preprocess",
      "service.version": "1.0.0"
    }
  }
}
```

**Stored compressed** in Parquet format for efficiency.

---

## Try It Yourself

### Exercise 1: Find a Trace by ID

1. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

2. **Check logs for trace ID**:
   ```bash
   docker-compose logs app | grep trace_id
   ```

3. **Open Grafana**: http://localhost:3000

4. **Navigate to**: Explore → Tempo

5. **Paste the trace ID** and press Enter

6. **View the trace waterfall diagram**

---

### Exercise 2: Search with TraceQL

1. **Generate varied traces**:
   ```bash
   ./scripts/run_demo.sh sizes  # Mix of small and large files
   ```

2. **Open Grafana**: Explore → Tempo

3. **Switch to TraceQL tab**

4. **Try these queries**:

   Slow traces:
   ```traceql
   {duration > 3s}
   ```

   Traces with errors:
   ```traceql
   {status = error}
   ```

   Slow skull_strip operations:
   ```traceql
   {name = "skull_strip" && duration > 800ms}
   ```

---

### Exercise 3: Trace-to-Logs Correlation

1. **Find a trace** in Tempo (any trace)

2. **Click on a span**

3. **Look for "Logs for this span"** button

4. **Click it** to see related logs in Loki

5. **Observe**: Same trace_id in both!

---

### Exercise 4: Logs-to-Trace Correlation

1. **Open Loki** (Explore → Loki)

2. **Query for errors**:
   ```logql
   {service_name="neuro-preprocess"} |= "ERROR"
   ```

3. **Click on a log entry**

4. **Find the trace_id** field

5. **Click the trace_id** (should be a link)

6. **Trace opens** in Tempo

---

### Exercise 5: Metrics-to-Trace (Exemplars)

**Note**: Exemplars require additional setup, but here's how they work:

1. **Open Prometheus** (Explore → Prometheus)

2. **Query with histogram**:
   ```promql
   histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))
   ```

3. **If exemplars are enabled**, you'll see small dots on the graph

4. **Hover over dots** to see trace IDs

5. **Click a trace ID** to open in Tempo

---

## Understanding Trace Waterfall Diagrams

When you open a trace in Grafana, you see a **waterfall diagram**:

```
Timeline (horizontal):
0ms        500ms       1000ms      1500ms      2000ms
│           │           │           │           │
process_file (root) ═══════════════════════════════ 2000ms
├─ load_file ══════                                  500ms
├─ process_image ══════════════════                  1000ms
│  ├─ skull_strip ════════                           400ms
│  ├─ bias_correction ═══════                        350ms
│  └─ normalization ════                             250ms
└─ write_output ════════                             500ms
```

**How to read it**:
- **X-axis**: Time (relative to trace start)
- **Y-axis**: Span hierarchy (parent above children)
- **Bar length**: Duration of the span
- **Color**: Status (green=OK, red=error)
- **Gaps**: Waiting or overhead (not captured)

---

## Performance Analysis with Traces

### Find Bottlenecks

1. **Look for longest spans**
2. **Check if they're in series or parallel**
3. **Optimize the slowest operations**

**Example**:

```
Total: 2000ms
├─ load_file: 500ms    (25%)
├─ process_image: 1000ms (50%) ← Bottleneck!
└─ write_output: 500ms (25%)
```

**Action**: Optimize `process_image` to reduce total time.

---

### Identify Errors

**Red spans** = Errors

1. Click on the red span
2. See error message in span details
3. Check span attributes for context
4. Jump to logs for stack traces

---

### Compare Fast vs. Slow Traces

1. Find a fast trace (e.g., 1s)
2. Find a slow trace (e.g., 10s)
3. Compare side-by-side
4. Identify which spans are slower

**Example finding**: "Large files spend 90% of time in skull_strip"

---

## Key Takeaways

1. **Tempo** stores traces cheaply by indexing only trace IDs
2. **Find traces** via correlation (logs, metrics) or TraceQL
3. **TraceQL** enables searching by span attributes and duration
4. **Storage tiers**: Memory → Disk → Object storage
5. **Sampling** controls costs at scale (head-based, tail-based)
6. **Retention**: Configure how long to keep traces
7. **Waterfall diagrams** visualize trace timelines
8. **Correlation**: Traces ↔ Logs ↔ Metrics via trace_id
9. **Tempo vs. Jaeger**: Cheaper and simpler, but less search features

---

## Quiz

1. **Why doesn't Tempo index span attributes like Jaeger does?**
   <details>
   <summary>Click to see answer</summary>
   Cost. Indexing all attributes is expensive. Tempo relies on correlation (find trace ID from logs/metrics, then look up the trace) and TraceQL for filtering, keeping indexes minimal.
   </details>

2. **What are the three ways to find a trace in Tempo?**
   <details>
   <summary>Click to see answer</summary>
   1) From logs (click trace_id link)
   2) From metrics (exemplars)
   3) Direct search with TraceQL
   </details>

3. **What's the difference between head-based and tail-based sampling?**
   <details>
   <summary>Click to see answer</summary>
   Head-based: Decide at the start of the trace (simple, may miss important traces).
   Tail-based: Decide after the trace completes based on properties (smarter, keeps errors/slow traces, but more complex).
   </details>

4. **How do traces correlate with logs?**
   <details>
   <summary>Click to see answer</summary>
   Both share the same trace_id. Click a trace_id in logs to open the trace, or click a span in a trace to see related logs.
   </details>

---

## Next Steps

🎉 **Congratulations!** You've completed the Storage Backends section!

**Next**: [Lesson 9: OTel Collector →](09-otel-collector.md)

In the next lesson, you'll learn:
- OTel Collector architecture
- Receivers, processors, exporters
- Pipeline configuration
- How the collector routes data between app and backends

---

**Progress**: ✅ Lessons 1-8 complete (Storage Backends Done!) | ⬜ 6 lessons remaining
