# Lesson 2: OpenTelemetry Basics

**Estimated time**: 30-45 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand what OpenTelemetry is and why it was created
✅ Know the core components: API, SDK, Collector, Exporters
✅ Understand how OTel unifies the three pillars
✅ Recognize OTel components in our project

---

## What Is OpenTelemetry?

### The Simple Definition

**OpenTelemetry (OTel)** is an **open-source framework** for collecting **traces, metrics, and logs** from your applications in a **standardized way**.

Think of it as:

```
┌─────────────────────────────────────────┐
│   Before OpenTelemetry                  │
├─────────────────────────────────────────┤
│  App → Vendor1's format → Vendor1 tool  │
│  App → Vendor2's format → Vendor2 tool  │
│  App → Vendor3's format → Vendor3 tool  │
│                                         │
│  Problem: Lock-in, complexity, cost     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│   With OpenTelemetry                    │
├─────────────────────────────────────────┤
│  App → OTel format → Any backend        │
│                                         │
│  ✅ Vendor neutral                      │
│  ✅ Single instrumentation              │
│  ✅ Flexible backends                   │
└─────────────────────────────────────────┘
```

---

## Why Was OpenTelemetry Created?

### The Problem: Fragmentation

Before OpenTelemetry, observability was a mess:

**Problem 1: Vendor Lock-In**
```
You instrument with Datadog → Switching to Honeycomb requires rewriting all code
You instrument with New Relic → Moving to Prometheus requires new libraries
```

**Problem 2: Multiple Standards**
```
Traces: OpenTracing, OpenCensus, Jaeger formats
Metrics: Prometheus, StatsD, vendor formats
Logs: Everyone did their own thing
```

**Problem 3: Complexity**
```
Different libraries for:
- Traces (OpenTracing)
- Metrics (OpenCensus)
- Logs (custom solutions)

= More dependencies, more maintenance, more bugs
```

### The Solution: OpenTelemetry

In **2019**, the Cloud Native Computing Foundation (CNCF) merged **OpenTracing** and **OpenCensus** into **OpenTelemetry**.

**Goals**:
1. ✅ **Vendor-neutral**: Works with any backend (Jaeger, Prometheus, commercial tools)
2. ✅ **Unified**: One framework for traces, metrics, and logs
3. ✅ **High-quality**: Production-grade, battle-tested
4. ✅ **Interoperable**: Standardized formats and protocols

**Result**: You instrument **once** with OpenTelemetry, then send data **anywhere**.

---

## The OpenTelemetry Architecture

OpenTelemetry consists of several components:

```
┌──────────────────────────────────────────────────┐
│              YOUR APPLICATION                    │
│                                                  │
│  ┌────────────────────────────────────┐         │
│  │  OTel API (instrument your code)   │         │
│  └────────────┬───────────────────────┘         │
│               │                                  │
│  ┌────────────▼───────────────────────┐         │
│  │  OTel SDK (collects telemetry)     │         │
│  └────────────┬───────────────────────┘         │
└───────────────┼──────────────────────────────────┘
                │ OTLP (standard protocol)
                ▼
┌───────────────────────────────────────────────────┐
│       OTel Collector (optional middleware)        │
│  Receives → Processes → Exports telemetry         │
└───────────────┬───────────────────────────────────┘
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
   ┌────────┐ ┌────┐ ┌──────┐
   │Prometheus│ │Loki│ │Tempo │
   └────────┘ └────┘ └──────┘
```

Let's break down each component:

---

### Component 1: OTel API

**What it is**: The programming interface you use to instrument your code.

**Purpose**: Defines **what** you can do, not **how** it's done.

**Example from our project**:

```python
from opentelemetry import trace

# Get a tracer (API)
tracer = trace.get_tracer(__name__)

# Create a span (API)
with tracer.start_as_current_span("load_file"):
    # Your code here
    data = load_nifti_file(path)
```

**Key point**: The API is **stable** and rarely changes. You can swap out the implementation (SDK) without changing your code.

---

### Component 2: OTel SDK

**What it is**: The actual implementation that collects and exports telemetry.

**Purpose**: Defines **how** telemetry is created, processed, and sent.

**Responsibilities**:
- Creating spans, metrics, logs
- Sampling decisions (should we keep this trace?)
- Batching data for efficiency
- Sending data to exporters

**Example from our project**:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up the SDK
provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)

# Make it the default
trace.set_tracer_provider(provider)
```

**Analogy**:
- **API** = The steering wheel and pedals in your car (interface)
- **SDK** = The engine and transmission (implementation)

You interact with the steering wheel, but the engine does the work.

---

### Component 3: Exporters

**What they are**: Plugins that send telemetry to specific backends.

**Purpose**: Convert OTel data to backend-specific formats and transmit it.

**Common exporters**:

| Exporter | Sends To | Protocol |
|----------|----------|----------|
| **OTLP** | OTel Collector, Tempo | gRPC or HTTP |
| **Prometheus** | Prometheus | HTTP scraping |
| **Jaeger** | Jaeger | Thrift or gRPC |
| **Zipkin** | Zipkin | HTTP JSON |
| **Console** | stdout (for debugging) | Text |

**In our project**, we use the **OTLP Exporter**:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# These send data to the OTel Collector via gRPC
trace_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
metric_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317")
```

---

### Component 4: OTel Collector (Optional but Powerful)

**What it is**: A standalone service that receives, processes, and forwards telemetry.

**Purpose**: Acts as a **middleman** between your app and backends.

```
App → Collector → Multiple backends
```

**Why use a collector?**

1. **Decoupling**: App doesn't need to know about backends
2. **Processing**: Filter, sample, enrich data before storage
3. **Multiple backends**: Send data to many places at once
4. **Load balancing**: Distribute data across backend instances
5. **Retries**: Handle backend failures gracefully

**Our project's collector** (`configs/otel-collector-config.yaml`):

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317   # Receive from apps

processors:
  batch:
    timeout: 1s                  # Batch for efficiency

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889       # Export metrics
  loki:
    endpoint: http://loki:3100/loki/api/v1/push  # Export logs
  otlp:
    endpoint: tempo:4317         # Export traces

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]           # → Tempo
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]     # → Prometheus
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [loki]           # → Loki
```

**Analogy**: The collector is like a **post office sorting center**:
- Receives mail (telemetry) from many sources (apps)
- Sorts it (processing)
- Delivers to the right destinations (backends)

---

## OTLP: The Universal Protocol

**OTLP (OpenTelemetry Protocol)** is the standardized way to transmit telemetry.

### Two Flavors

1. **gRPC** (binary, fast, efficient) - Default choice
2. **HTTP** (text, compatible, easier debugging)

**In our project**, apps use **OTLP over gRPC** to send data to the collector:

```python
# Application code
OTEL_EXPORTER_OTLP_ENDPOINT = "http://otel-collector:4317"  # gRPC port
```

**Ports in our stack**:
- `4317`: OTLP gRPC (apps → collector)
- `4318`: OTLP HTTP (alternative)

---

## How OTel Unifies the Three Pillars

Before OpenTelemetry, you needed separate libraries for traces, metrics, and logs.

**With OpenTelemetry**, everything is unified:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
import logging

# 1. Define your service (shared resource)
resource = Resource.create({"service.name": "neuro-preprocess"})

# 2. Set up tracing
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# 3. Set up metrics
metric_provider = MeterProvider(resource=resource)
metrics.set_meter_provider(metric_provider)

# 4. Set up logging (uses same trace context)
logging.basicConfig(level=logging.INFO)
```

**Key insight**: All three pillars share:
- The same **service.name** and **resource attributes**
- The same **trace_id** (for correlation)
- The same **exporters** and **collector**

This makes **correlation** easy:

```
Metric spike at 14:00
  ↓ (filter by time)
Traces from 14:00
  ↓ (click trace)
Logs for that trace_id
```

---

## OpenTelemetry in Our Project

Let's identify OTel components in our neuroimaging pipeline:

### 1. Application Side (`app/neuro_preprocess/telemetry.py`)

```python
from opentelemetry import trace, metrics        # OTel API
from opentelemetry.sdk.trace import TracerProvider        # OTel SDK
from opentelemetry.sdk.metrics import MeterProvider       # OTel SDK
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter   # Exporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter # Exporter

# Initialize the SDK
setup_telemetry()

# Use the API in your code
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

with tracer.start_as_current_span("process"):
    files_counter.add(1)
    # ... your code ...
```

### 2. Collector Side (`configs/otel-collector-config.yaml`)

```yaml
receivers:
  otlp:                    # Receives OTLP from apps
    protocols:
      grpc:

exporters:
  prometheus:              # Exports metrics to Prometheus
  otlp:                    # Exports traces to Tempo
  loki:                    # Exports logs to Loki
```

### 3. Storage Backends

```
Prometheus (http://localhost:9090) - Stores metrics
Loki (http://localhost:3100)       - Stores logs
Tempo (http://localhost:3200)      - Stores traces
```

### 4. Visualization (Grafana)

```
Grafana (http://localhost:3000) - Queries and visualizes all three
```

---

## Data Flow in Our Stack

Here's the complete journey of telemetry in our project:

```
┌─────────────────────────────────────────────────────┐
│ 1. YOUR CODE                                        │
│    with tracer.start_as_current_span("process"):    │
│        counter.add(1)                               │
│        logger.info("Processing file")               │
└───────────────────┬─────────────────────────────────┘
                    │ OTel API calls
┌───────────────────▼─────────────────────────────────┐
│ 2. OTel SDK                                         │
│    - Creates span objects                           │
│    - Records metric values                          │
│    - Captures log records                           │
│    - Batches for efficiency                         │
└───────────────────┬─────────────────────────────────┘
                    │ OTLP over gRPC (port 4317)
┌───────────────────▼─────────────────────────────────┐
│ 3. OTel Collector                                   │
│    Pipelines:                                       │
│    - traces:  otlp → batch → otlp (Tempo)          │
│    - metrics: otlp → batch → prometheus            │
│    - logs:    otlp → batch → loki                  │
└──────────┬──────────┬──────────┬───────────────────┘
           │          │          │
    ┌──────▼──┐  ┌────▼────┐  ┌─▼─────┐
    │  Tempo  │  │  Loki   │  │ Prom  │
    │  :3200  │  │  :3100  │  │ :9090 │
    └──────▲──┘  └────▲────┘  └─▲─────┘
           │          │          │
           └──────────┼──────────┘
                  ┌───▼────┐
                  │ Grafana│
                  │  :3000 │
                  └────────┘
```

**Step-by-step**:
1. Your code calls OTel API (`tracer.start_span()`)
2. OTel SDK creates the actual span and batches it
3. OTLP Exporter sends via gRPC to Collector (port 4317)
4. Collector routes traces → Tempo, metrics → Prometheus, logs → Loki
5. Grafana queries all three backends and displays the data

---

## OTel's Key Concepts

### 1. Resources

**Resources** describe **what** is producing telemetry.

```python
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": "neuro-preprocess",
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "host.name": "server-01"
})
```

All traces, metrics, and logs from this app will have these attributes.

**Why it matters**: You can filter by service, environment, or host in Grafana.

---

### 2. Context Propagation

**Context** is how trace information flows through your code.

```python
# Span A starts
with tracer.start_as_current_span("parent"):

    # Span B starts (automatically becomes child of A)
    with tracer.start_as_current_span("child"):

        # This log automatically gets the trace_id and span_id
        logger.info("Inside child span")
```

**Result**:
```
Trace ID: abc123
├─ Span A (parent)
│  └─ Span B (child)
│     └─ Log: "Inside child span" [trace_id=abc123, span_id=xyz]
```

**Why it matters**: You can click a trace in Grafana and see all related logs.

---

### 3. Instrumentation Libraries

OpenTelemetry provides **automatic instrumentation** for popular libraries:

```python
# Automatically traces HTTP requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor
RequestsInstrumentor().instrument()

# Automatically traces database calls
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
Psycopg2Instrumentor().instrument()
```

**Our project uses manual instrumentation** to teach the concepts, but in production, auto-instrumentation saves time.

---

## Try It Yourself

### Exercise 1: Explore the OTel Configuration

1. **Look at our telemetry setup**:
   ```bash
   cat app/neuro_preprocess/telemetry.py
   ```

2. **Find these components**:
   - Where is the `TracerProvider` created?
   - Where is the OTLP endpoint configured?
   - Where are the exporters defined?

3. **Answer**:
   - What protocol is used to send data? (Hint: Look at the exporter class names)

---

### Exercise 2: Trace the Data Flow

1. **Start the stack**:
   ```bash
   docker-compose up -d
   ```

2. **Check the collector is receiving data**:
   ```bash
   curl http://localhost:8888/metrics | grep otelcol_receiver_accepted
   ```

3. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **Check the collector exported data**:
   ```bash
   curl http://localhost:8888/metrics | grep otelcol_exporter_sent
   ```

5. **View in Grafana**: http://localhost:3000/explore
   - Select Tempo → Search for "neuro-preprocess"
   - Select Prometheus → Query: `neuro_files_processed_total`

---

### Exercise 3: Understand the Collector Config

1. **Read the collector configuration**:
   ```bash
   cat configs/otel-collector-config.yaml
   ```

2. **Answer these questions**:
   - How many receivers are configured?
   - How many exporters are configured?
   - Which exporter receives traces?
   - Which exporter receives metrics?

<details>
<summary>Click to see answers</summary>

- **Receivers**: 1 (otlp with gRPC and HTTP)
- **Exporters**: 3 (prometheus, loki, otlp for Tempo)
- **Traces**: Sent to otlp exporter (Tempo)
- **Metrics**: Sent to prometheus exporter
</details>

---

## Real-World Analogy: The Restaurant

Imagine a restaurant (your application):

**OpenTelemetry API** = The menu
- Standard interface for ordering (instrumenting)
- Same menu across restaurants (standard API)

**OpenTelemetry SDK** = The kitchen
- Actual preparation of food (telemetry)
- Can be swapped out (different SDK implementations)

**OTLP** = The delivery truck
- Standard format for transporting food (telemetry)
- Works with any restaurant and any delivery service

**OTel Collector** = The distribution center
- Receives orders from many restaurants
- Sorts and delivers to the right customers
- Can modify orders (processing)

**Backends (Prometheus, Loki, Tempo)** = The customers
- Receive the food (telemetry) in formats they expect
- Different customers prefer different foods (data types)

---

## Key Takeaways

1. **OpenTelemetry** is a vendor-neutral, open-source observability framework
2. **OTel unifies** traces, metrics, and logs under one standard
3. **Components**:
   - **API**: What you code against (stable interface)
   - **SDK**: How telemetry is created and sent
   - **Exporters**: Send data to specific backends
   - **Collector**: Optional middleware for routing and processing
4. **OTLP** is the standard protocol for transmitting telemetry
5. **In our project**: App → Collector → Prometheus/Loki/Tempo → Grafana

---

## Quiz

1. **What problem does OpenTelemetry solve?**
   <details>
   <summary>Click to see answer</summary>
   Vendor lock-in and fragmentation. Before OTel, you needed different libraries for different backends. OTel provides a single, vendor-neutral way to instrument once and send data anywhere.
   </details>

2. **What's the difference between the OTel API and SDK?**
   <details>
   <summary>Click to see answer</summary>
   API is the interface (what you code against), SDK is the implementation (how it works). You can swap SDKs without changing your code.
   </details>

3. **Why use an OTel Collector instead of sending directly to backends?**
   <details>
   <summary>Click to see answer</summary>
   Decoupling (app doesn't need to know backends), processing (filtering, sampling), multiple destinations, retries, and load balancing.
   </details>

4. **What protocol does our app use to send data to the collector?**
   <details>
   <summary>Click to see answer</summary>
   OTLP over gRPC on port 4317.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand OpenTelemetry basics!

**Next**: [Lesson 3: Distributed Tracing →](03-distributed-tracing.md)

In the next lesson, you'll learn:
- What a span is and how spans form traces
- Trace IDs and span IDs
- Parent-child relationships
- Context propagation across function calls

---

**Progress**: ✅ Lesson 1 complete | ✅ Lesson 2 complete | ⬜ 12 lessons remaining
