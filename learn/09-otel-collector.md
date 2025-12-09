# Lesson 9: OpenTelemetry Collector

**Estimated time**: 50-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand the OTel Collector architecture
✅ Know the three components: Receivers, Processors, Exporters
✅ Learn how to configure pipelines
✅ Understand why the collector is useful
✅ Be able to read and modify collector configurations

---

## What Is the OTel Collector?

### The Simple Definition

The **OpenTelemetry Collector** is a **vendor-agnostic proxy** that receives, processes, and exports telemetry data.

**Analogy**: The collector is like a **post office sorting center**:

```
┌──────────────────────────────────────────┐
│         POST OFFICE ANALOGY              │
├──────────────────────────────────────────┤
│                                          │
│  📬 Receiving Desk  →  Receivers         │
│     (Accept mail from senders)           │
│                                          │
│  📦 Sorting Area    →  Processors        │
│     (Sort, label, filter mail)           │
│                                          │
│  🚚 Delivery Trucks →  Exporters         │
│     (Send to destinations)               │
│                                          │
└──────────────────────────────────────────┘
```

---

## Why Use a Collector?

### Without a Collector

```
┌──────────┐       OTLP        ┌────────────┐
│          │  ───────────────→  │ Prometheus │
│   App    │                    └────────────┘
│          │       OTLP        ┌────────────┐
│          │  ───────────────→  │    Loki    │
│          │                    └────────────┘
│          │       OTLP        ┌────────────┐
│          │  ───────────────→  │   Tempo    │
└──────────┘                    └────────────┘
```

**Problems**:
- ❌ App needs to know all backends
- ❌ App must handle retries and failures
- ❌ Adding a new backend requires code changes
- ❌ No central place for processing (filtering, sampling)

---

### With a Collector

```
┌──────────┐                   ┌─────────────────┐
│          │       OTLP        │   Collector     │
│   App    │  ───────────────→ │                 │  ───→ Prometheus
│          │                   │  (Receives,     │  ───→ Loki
└──────────┘                   │   Processes,    │  ───→ Tempo
                               │   Exports)      │
                               └─────────────────┘
```

**Benefits**:
- ✅ App sends to one place (collector)
- ✅ Collector handles retries and buffering
- ✅ Add backends without changing app code
- ✅ Central place for processing (filtering, sampling, enrichment)
- ✅ Collect from multiple apps and aggregate

---

## Collector Architecture

The collector has **three main components**:

```
┌────────────────────────────────────────────┐
│         OTEL COLLECTOR                     │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐                          │
│  │  Receivers   │  ← Receive telemetry     │
│  └──────┬───────┘                          │
│         │                                  │
│         ▼                                  │
│  ┌──────────────┐                          │
│  │  Processors  │  ← Process data          │
│  └──────┬───────┘                          │
│         │                                  │
│         ▼                                  │
│  ┌──────────────┐                          │
│  │  Exporters   │  ← Export to backends    │
│  └──────────────┘                          │
│                                            │
└────────────────────────────────────────────┘
```

Let's explore each component:

---

## Component 1: Receivers

**Receivers** accept telemetry data from various sources.

### Common Receivers

| Receiver | Purpose | Port |
|----------|---------|------|
| **otlp** | OpenTelemetry Protocol (gRPC/HTTP) | 4317 (gRPC), 4318 (HTTP) |
| **prometheus** | Scrape Prometheus metrics | 9090 |
| **jaeger** | Accept Jaeger traces | 14250 |
| **zipkin** | Accept Zipkin traces | 9411 |
| **hostmetrics** | Collect host metrics (CPU, memory) | N/A |

---

### OTLP Receiver (Most Common)

**Configuration**:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317  # Listen on all interfaces, port 4317
      http:
        endpoint: 0.0.0.0:4318  # Listen on all interfaces, port 4318
```

**What it does**:
- Listens on port **4317** for gRPC connections
- Listens on port **4318** for HTTP connections
- Accepts traces, metrics, and logs in OTLP format
- Used by OpenTelemetry SDKs

---

### Prometheus Receiver

**Configuration**:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'my-app'
          scrape_interval: 15s
          static_configs:
            - targets: ['app:8080']
```

**What it does**:
- Scrapes Prometheus metrics from apps
- Converts to OpenTelemetry format
- Allows mixing Prometheus and OTel metrics

---

### Host Metrics Receiver

**Configuration**:

```yaml
receivers:
  hostmetrics:
    collection_interval: 10s
    scrapers:
      cpu:
      memory:
      disk:
      network:
```

**What it does**:
- Collects system metrics (CPU, memory, disk, network)
- Useful for monitoring the collector itself or host machines

---

## Component 2: Processors

**Processors** transform, filter, or enrich telemetry data.

### Common Processors

| Processor | Purpose |
|-----------|---------|
| **batch** | Batch data for efficiency |
| **memory_limiter** | Prevent out-of-memory crashes |
| **resource** | Add/modify resource attributes |
| **attributes** | Add/modify span/log attributes |
| **filter** | Drop unwanted data |
| **sampling** | Sample traces |
| **spanmetrics** | Generate metrics from spans |

---

### Batch Processor (Essential)

**Configuration**:

```yaml
processors:
  batch:
    timeout: 1s        # Send batch every 1 second
    send_batch_size: 1024  # Or when 1024 items collected
```

**What it does**:
- Batches multiple telemetry items together
- Reduces network overhead (1 request vs. 1000 requests)
- **Always use this** - it's critical for performance

---

### Memory Limiter Processor (Essential)

**Configuration**:

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512       # Soft limit: 512 MB
    spike_limit_mib: 128  # Allow spikes up to 640 MB (512+128)
```

**What it does**:
- Monitors collector memory usage
- Drops data if memory exceeds limits
- Prevents collector crashes from out-of-memory

**Best practice**: Always place this **first** in the pipeline.

---

### Resource Processor

**Configuration**:

```yaml
processors:
  resource:
    attributes:
      - key: environment
        value: production
        action: insert
      - key: cluster
        value: us-west-1
        action: insert
```

**What it does**:
- Adds resource attributes to all telemetry
- Enriches data with context (environment, region, cluster)

---

### Attributes Processor

**Configuration**:

```yaml
processors:
  attributes:
    actions:
      - key: password
        action: delete  # Remove sensitive field
      - key: user_id
        action: hash    # Hash PII data
      - key: region
        value: us-east-1
        action: insert
```

**What it does**:
- Modify span/log attributes
- Remove sensitive data
- Add context

---

### Filter Processor

**Configuration**:

```yaml
processors:
  filter:
    traces:
      span:
        - 'attributes["http.url"] =~ ".*health.*"'  # Drop health checks
```

**What it does**:
- Drop unwanted telemetry
- Filter by attributes, service name, etc.
- Reduce data volume and costs

---

### Probabilistic Sampler Processor

**Configuration**:

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 10  # Keep 10% of traces
```

**What it does**:
- Sample traces probabilistically
- Reduce trace volume for high-traffic apps

---

### Span Metrics Processor

**Configuration**:

```yaml
processors:
  spanmetrics:
    metrics_exporter: prometheus
    latency_histogram_buckets: [100ms, 200ms, 500ms, 1s, 2s, 5s]
```

**What it does**:
- Generate metrics **from spans**
- Creates duration histograms and request counts
- Automatically derive RED metrics (Rate, Errors, Duration)

---

## Component 3: Exporters

**Exporters** send telemetry data to backends.

### Common Exporters

| Exporter | Sends To | Protocol |
|----------|----------|----------|
| **otlp** | OTel-compatible backends (Tempo) | gRPC/HTTP |
| **prometheus** | Prometheus | HTTP (scrape endpoint) |
| **prometheusremotewrite** | Prometheus (push) | Remote Write |
| **loki** | Loki | HTTP |
| **jaeger** | Jaeger | gRPC |
| **zipkin** | Zipkin | HTTP |
| **logging** | Console/file (debugging) | N/A |

---

### OTLP Exporter

**Configuration**:

```yaml
exporters:
  otlp:
    endpoint: tempo:4317  # Send to Tempo
    tls:
      insecure: true      # No TLS (for local dev)
```

**What it does**:
- Sends traces, metrics, or logs via OTLP
- Used to forward to Tempo or other OTel-compatible backends

---

### Prometheus Exporter

**Configuration**:

```yaml
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889  # Expose metrics on port 8889
```

**What it does**:
- Exposes metrics at `/metrics` endpoint
- Prometheus scrapes from this endpoint
- Converts OTel metrics to Prometheus format

---

### Loki Exporter

**Configuration**:

```yaml
exporters:
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      resource:
        service.name: "service_name"
      attributes:
        level: "level"
```

**What it does**:
- Pushes logs to Loki
- Maps OTel log fields to Loki labels

---

### Logging Exporter (Debugging)

**Configuration**:

```yaml
exporters:
  logging:
    loglevel: debug  # Print to console
```

**What it does**:
- Prints telemetry to stdout
- **Very useful** for debugging configurations

---

## Pipelines: Connecting the Pieces

**Pipelines** define how telemetry flows through the collector.

### Pipeline Structure

```yaml
service:
  pipelines:
    <telemetry_type>:
      receivers: [list of receivers]
      processors: [list of processors]
      exporters: [list of exporters]
```

**Telemetry types**: `traces`, `metrics`, `logs`

---

### Example: Traces Pipeline

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]              # Receive from apps via OTLP
      processors: [memory_limiter, batch]  # Limit memory, batch data
      exporters: [otlp]              # Export to Tempo
```

**Data flow**:

```
App → OTLP Receiver → Memory Limiter → Batch → OTLP Exporter → Tempo
```

---

### Example: Metrics Pipeline

```yaml
service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

**Data flow**:

```
App → OTLP Receiver → Memory Limiter → Batch → Prometheus Exporter → Prometheus (scrapes)
```

---

### Example: Logs Pipeline

```yaml
service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [loki]
```

**Data flow**:

```
App → OTLP Receiver → Memory Limiter → Batch → Resource → Loki Exporter → Loki
```

---

## Our Project's Collector Configuration

Let's analyze our actual config (`configs/otel-collector-config.yaml`):

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317  # Accept OTLP from apps

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889  # Prometheus scrapes here

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

  otlp:
    endpoint: tempo:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]  # → Tempo

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]  # → Prometheus

    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [loki]  # → Loki
```

---

### Data Flow in Our Project

```
┌──────────────────┐
│  App (Python)    │
│  neuro-preprocess│
└────────┬─────────┘
         │ OTLP (gRPC:4317)
         │
         ▼
┌──────────────────────────────────────┐
│      OTel Collector                  │
│                                      │
│  Receiver: otlp (4317)               │
│      ↓                               │
│  Processor: batch                    │
│      ↓                               │
│  Exporters:                          │
│    - traces  → otlp   (Tempo)        │
│    - metrics → prometheus (Prom)     │
│    - logs    → loki   (Loki)         │
└──────┬───────┬───────┬───────────────┘
       │       │       │
       ▼       ▼       ▼
    Tempo   Prom    Loki
```

---

## Advanced Configurations

### Multiple Receivers

Accept telemetry from multiple sources:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
  jaeger:
    protocols:
      grpc:
        endpoint: 0.0.0.0:14250  # Accept Jaeger too

service:
  pipelines:
    traces:
      receivers: [otlp, jaeger]  # Both receivers
      processors: [batch]
      exporters: [otlp]
```

---

### Multiple Exporters

Send to multiple backends:

```yaml
exporters:
  otlp/tempo:
    endpoint: tempo:4317
  jaeger:
    endpoint: jaeger:14250

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo, jaeger]  # Send to both!
```

---

### Multiple Pipelines

Different processing for different data:

```yaml
service:
  pipelines:
    # Production traces: full processing
    traces/production:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [otlp/tempo]

    # Debug traces: log to console
    traces/debug:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
```

---

### Conditional Processing

Use processors to filter or route:

```yaml
processors:
  filter/health:
    traces:
      span:
        - 'attributes["http.target"] == "/health"'  # Drop health checks

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [filter/health, batch]  # Filter, then batch
      exporters: [otlp]
```

---

## Collector Deployment Modes

### Mode 1: Agent (Sidecar)

**Deploy**: One collector per app instance

```
App Instance 1 → Collector 1 ─┐
App Instance 2 → Collector 2 ─┼→ Central Collector → Backends
App Instance 3 → Collector 3 ─┘
```

**Pros**:
- ✅ Local buffering
- ✅ Lower latency
- ✅ Scales with apps

**Cons**:
- ❌ More resource usage
- ❌ More complexity

---

### Mode 2: Gateway (Centralized)

**Deploy**: One collector for all apps

```
App 1 ─┐
App 2 ─┼→ Central Collector → Backends
App 3 ─┘
```

**Pros**:
- ✅ Single point of configuration
- ✅ Easier to manage
- ✅ Lower resource usage

**Cons**:
- ❌ Single point of failure
- ❌ Network hop

---

### Mode 3: Hybrid

**Deploy**: Agent collectors + Gateway collector

```
App 1 → Collector 1 ─┐
App 2 → Collector 2 ─┼→ Gateway Collector → Backends
App 3 → Collector 3 ─┘
```

**Pros**:
- ✅ Best of both worlds
- ✅ Local buffering + central processing

**Cons**:
- ❌ Most complex

---

### Our Project (Gateway Mode)

```
App → Single Collector → Prometheus/Loki/Tempo
```

**Why?**
- Simple learning environment
- Single application
- Easy to manage

---

## Troubleshooting the Collector

### Check Collector Health

```bash
# Check if collector is running
curl http://localhost:13133/

# Collector metrics (useful for debugging)
curl http://localhost:8888/metrics
```

---

### Enable Debug Logging

Add to `otel-collector-config.yaml`:

```yaml
service:
  telemetry:
    logs:
      level: debug  # Enable debug logs
```

**Then check logs**:

```bash
docker-compose logs otel-collector
```

---

### Common Issues

**Issue 1: Connection Refused**
```
Error: connection refused to localhost:4317
```

**Solution**: Check that the collector is running and port 4317 is exposed.

---

**Issue 2: Exporter Timeout**
```
Error: context deadline exceeded exporting to tempo:4317
```

**Solution**: Check that Tempo is running and reachable from the collector.

---

**Issue 3: Out of Memory**
```
Collector killed (OOMKilled)
```

**Solution**: Add or adjust memory_limiter processor:

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
```

---

## Try It Yourself

### Exercise 1: View Collector Metrics

1. **Check collector health**:
   ```bash
   curl http://localhost:8888/metrics | grep otelcol_receiver_accepted
   ```

2. **Look for**:
   - `otelcol_receiver_accepted_spans` (traces received)
   - `otelcol_receiver_accepted_metric_points` (metrics received)
   - `otelcol_exporter_sent_spans` (traces exported)

---

### Exercise 2: Add Debug Logging

1. **Edit** `configs/otel-collector-config.yaml`:

   ```yaml
   exporters:
     logging:
       loglevel: debug

   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [batch]
         exporters: [otlp, logging]  # Add logging exporter
   ```

2. **Restart collector**:
   ```bash
   docker-compose restart otel-collector
   ```

3. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **View logs**:
   ```bash
   docker-compose logs otel-collector | tail -50
   ```

5. **See traces** printed to console!

---

### Exercise 3: Add Resource Attributes

1. **Edit** `configs/otel-collector-config.yaml`:

   ```yaml
   processors:
     batch:
       timeout: 1s

     resource:
       attributes:
         - key: environment
           value: development
           action: insert

   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [resource, batch]  # Add resource processor
         exporters: [otlp]
   ```

2. **Restart collector**:
   ```bash
   docker-compose restart otel-collector
   ```

3. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **View trace** in Grafana

5. **See new attribute** `environment=development` on all spans!

---

## Key Takeaways

1. **Collector** is the central hub for telemetry routing
2. **Three components**:
   - **Receivers**: Accept telemetry (OTLP, Jaeger, Prometheus)
   - **Processors**: Transform data (batch, filter, enrich)
   - **Exporters**: Send to backends (Prometheus, Loki, Tempo)
3. **Pipelines** connect receivers → processors → exporters
4. **Batch processor** is essential for performance
5. **Memory limiter** prevents OOM crashes
6. **Gateway mode**: Single collector for all apps (our project)
7. **Agent mode**: One collector per app (production)
8. **Debugging**: Use logging exporter to see data flowing

---

## Quiz

1. **What are the three main components of the collector?**
   <details>
   <summary>Click to see answer</summary>
   Receivers (accept telemetry), Processors (transform data), Exporters (send to backends).
   </details>

2. **Why is the batch processor important?**
   <details>
   <summary>Click to see answer</summary>
   It batches multiple telemetry items together, reducing network overhead. Without it, each span/metric/log would be sent individually, creating thousands of network requests.
   </details>

3. **What's the difference between gateway and agent deployment modes?**
   <details>
   <summary>Click to see answer</summary>
   Gateway: One central collector for all apps (simpler, single point of failure).
   Agent: One collector per app (local buffering, scales with apps, more complex).
   </details>

4. **How do you debug what data is flowing through the collector?**
   <details>
   <summary>Click to see answer</summary>
   Add the logging exporter to your pipeline to print data to stdout:
   ```yaml
   exporters:
     logging:
       loglevel: debug
   ```
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand the OTel Collector!

**Next**: [Lesson 10: Data Flow Explained →](10-data-flow-explained.md)

In the next lesson, you'll learn:
- Complete end-to-end data flow
- How all three databases communicate
- Network topology and protocols
- Putting it all together

---

**Progress**: ✅ Lessons 1-9 complete | ⬜ 5 lessons remaining
