# Lesson 14: Advanced Topics

**Estimated time**: 60-75 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand advanced sampling strategies
✅ Know how to handle cardinality explosion
✅ Learn about custom exporters and processors
✅ Understand OpenTelemetry SDK internals
✅ Explore cutting-edge observability patterns

---

## Advanced Sampling Strategies

### Adaptive Sampling

**Goal**: Adjust sampling rate dynamically based on traffic.

**Concept**:
- Low traffic (< 100 req/sec): Keep 100%
- Medium traffic (100-1000 req/sec): Keep 10%
- High traffic (> 1000 req/sec): Keep 1%

**Implementation** (Collector):

```yaml
processors:
  probabilistic_sampler:
    hash_seed: 22
    sampling_percentage: 10  # Base rate

  # Custom processor to adjust based on rate
  # (requires custom collector build)
```

**Benefits**:
- Always have data (never 0% sampling)
- Control costs at scale
- Automatic adjustment

---

### Sampling by Span Attributes

**Goal**: Sample differently based on span properties.

**Example**: Keep all traces for premium users, sample free users.

**Collector config**:

```yaml
processors:
  tail_sampling:
    policies:
      - name: premium_users
        type: string_attribute
        string_attribute:
          key: user.tier
          values: ["premium", "enterprise"]
        # 100% for premium users
      - name: free_users
        type: string_attribute
        string_attribute:
          key: user.tier
          values: ["free"]
      - name: sample_free
        type: probabilistic
        probabilistic:
          sampling_percentage: 1  # 1% for free users
```

---

### Composite Sampling

**Goal**: Combine multiple sampling strategies.

**Example**: Keep errors OR slow OR premium users OR 1% of the rest.

```yaml
processors:
  tail_sampling:
    policies:
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: slow
        type: latency
        latency:
          threshold_ms: 2000
      - name: premium
        type: string_attribute
        string_attribute:
          key: user.tier
          values: ["premium"]
      - name: composite
        type: and  # All conditions must match
        and:
          and_sub_policy:
            - name: not_premium
              type: string_attribute
              string_attribute:
                key: user.tier
                values: ["free"]
                invert_match: true  # NOT premium
            - name: sample
              type: probabilistic
              probabilistic:
                sampling_percentage: 1
```

**Result**: Smart sampling that keeps important traces.

---

## Cardinality Explosion

### The Problem

**High cardinality** = Too many unique label combinations = Storage explosion.

**Example**:

```python
# ❌ Creates 1 million time series!
requests_counter.add(1, {
    "user_id": user_id,  # 100,000 users
    "endpoint": endpoint,  # 10 endpoints
})
# 100,000 * 10 = 1,000,000 time series
```

**Result**:
- Slow queries
- High storage costs
- Out of memory errors

---

### Detection

**Query Prometheus** for high cardinality:

```promql
# Count time series per metric
count by (__name__) ({__name__=~".+"})

# Top 10 metrics by cardinality
topk(10, count by (__name__) ({__name__=~".+"}))

# Time series with many labels
count by (metric_name) (
  count without (instance, job) ({__name__=~".+"})
)
```

---

### Solutions

#### Solution 1: Reduce Label Values

**Bad**:
```python
counter.add(1, {"user_id": user_id})  # 100,000 values
```

**Good**:
```python
counter.add(1, {"user_tier": get_tier(user_id)})  # 3 values
```

---

#### Solution 2: Aggregate at Query Time

**Instead of**:
```python
# Store per-user metrics
counter.add(1, {"user_id": user_id})
```

**Do**:
```python
# Store aggregate
counter.add(1)  # No user_id label
```

**Then query**:
```promql
sum(requests_total)  # Total across all users
```

---

#### Solution 3: Use Exemplars

**Exemplars** link metrics to traces without creating new time series.

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.view import View

# Enable exemplars on histogram
meter_provider = MeterProvider(
    views=[
        View(
            instrument_type=Histogram,
            name="*",
            attribute_keys={"status"},  # Only keep "status" label
            exemplar_reservoir=AlignedHistogramBucketExemplarReservoir()
        )
    ]
)
```

**Result**: Low cardinality metrics + trace_id links for investigation.

---

#### Solution 4: Drop High-Cardinality Labels in Collector

```yaml
processors:
  attributes:
    actions:
      - key: user_id
        action: delete  # Remove high-cardinality label
      - key: request_id
        action: delete
```

---

#### Solution 5: Relabeling (Prometheus)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'app'
    metric_relabel_configs:
      - source_labels: [user_id]
        target_label: user_tier
        regex: '(premium|enterprise).*'
        replacement: '$1'
      - source_labels: [user_id]
        regex: 'free.*'
        target_label: user_tier
        replacement: 'free'
      - source_labels: [user_id]
        action: labeldrop  # Drop original user_id
```

---

## Custom Exporters and Processors

### Building a Custom Processor

**Use case**: Add custom enrichment (e.g., geo-location from IP).

**Example** (Python):

```python
from opentelemetry.sdk.trace import SpanProcessor

class GeoEnrichmentProcessor(SpanProcessor):
    def on_start(self, span, parent_context):
        # Called when span starts
        if span.attributes.get("http.client_ip"):
            ip = span.attributes["http.client_ip"]
            geo_data = self.lookup_geo(ip)  # Your geo lookup
            span.set_attribute("geo.country", geo_data["country"])
            span.set_attribute("geo.city", geo_data["city"])

    def on_end(self, span):
        # Called when span ends
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True

    def lookup_geo(self, ip):
        # Implement IP-to-geo lookup (GeoIP2, API, etc.)
        return {"country": "US", "city": "New York"}

# Register processor
tracer_provider.add_span_processor(GeoEnrichmentProcessor())
```

---

### Building a Custom Exporter

**Use case**: Export to a custom backend not supported by OTel.

**Example** (send to custom API):

```python
from opentelemetry.sdk.trace.export import SpanExporter

class CustomAPIExporter(SpanExporter):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def export(self, spans):
        # Convert spans to your format
        data = self.convert_spans(spans)

        # Send to your API
        response = requests.post(self.endpoint, json=data)

        if response.status_code == 200:
            return SpanExportResult.SUCCESS
        else:
            return SpanExportResult.FAILURE

    def shutdown(self):
        pass

    def convert_spans(self, spans):
        # Convert OTel spans to your format
        return [
            {
                "trace_id": span.context.trace_id,
                "span_id": span.context.span_id,
                "name": span.name,
                "duration_ms": (span.end_time - span.start_time) / 1_000_000,
                "attributes": dict(span.attributes)
            }
            for span in spans
        ]

# Use it
exporter = CustomAPIExporter("https://api.example.com/traces")
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
```

---

## OpenTelemetry SDK Internals

### How Span Creation Works

When you call `tracer.start_as_current_span()`:

1. **Sampler decides**: Keep or drop this span?
2. **Create Span object**: With trace_id, span_id, parent_id
3. **Store in Context**: Make it the "current" span
4. **On span.end()**:
   - Calculate duration
   - Call processors (on_end hooks)
   - Pass to exporter

```python
# Simplified internal flow
def start_as_current_span(name):
    # 1. Get sampling decision
    if sampler.should_sample():
        # 2. Create span
        span = Span(
            name=name,
            trace_id=current_trace_id or generate_trace_id(),
            span_id=generate_span_id(),
            parent_span_id=current_span_id
        )

        # 3. Set as current
        context.set_current_span(span)

        # 4. Notify processors
        for processor in processors:
            processor.on_start(span)

        return span
    else:
        return NonRecordingSpan()  # No-op span
```

---

### Batching and Exporting

**BatchSpanProcessor** buffers spans for efficiency:

```python
class BatchSpanProcessor:
    def __init__(self, exporter, max_queue_size=2048, schedule_delay_ms=5000):
        self.exporter = exporter
        self.queue = []
        self.max_queue_size = max_queue_size
        self.schedule_delay_ms = schedule_delay_ms

        # Background thread for exporting
        self.worker_thread = Thread(target=self.worker)
        self.worker_thread.start()

    def on_end(self, span):
        self.queue.append(span)

        # Export if queue full
        if len(self.queue) >= self.max_queue_size:
            self.export()

    def worker(self):
        while True:
            time.sleep(self.schedule_delay_ms / 1000)
            self.export()

    def export(self):
        if self.queue:
            batch = self.queue[:self.max_queue_size]
            self.queue = self.queue[self.max_queue_size:]

            self.exporter.export(batch)
```

**Key points**:
- Spans queued in memory
- Exported when queue full OR timeout reached
- Background thread for exporting
- Reduces network overhead

---

### Context Propagation

**Context** is how OTel tracks the current span.

**Python implementation** (simplified):

```python
from contextvars import ContextVar

# Thread-local storage for current span
_current_span = ContextVar("current_span", default=None)

def set_current_span(span):
    _current_span.set(span)

def get_current_span():
    return _current_span.get()

# When creating child span
def start_as_current_span(name):
    parent_span = get_current_span()

    child_span = Span(
        name=name,
        parent_span_id=parent_span.span_id if parent_span else None
    )

    set_current_span(child_span)  # Make it current
    return child_span
```

**Key**: Uses context variables (thread-local storage) to track current span.

---

## Advanced Observability Patterns

### Pattern 1: Distributed Context Propagation

**Problem**: Trace context must flow across service boundaries.

**Solution**: W3C Trace Context headers.

**HTTP Example**:

```python
# Service A: Inject trace context into HTTP headers
from opentelemetry.propagate import inject

headers = {}
inject(headers)  # Adds traceparent, tracestate headers

requests.get("http://service-b/api", headers=headers)
```

```python
# Service B: Extract trace context from HTTP headers
from opentelemetry.propagate import extract

context = extract(request.headers)
with tracer.start_as_current_span("handle_request", context=context):
    # This span is now part of the same trace!
    pass
```

**Result**: Traces span multiple services seamlessly.

---

### Pattern 2: Baggage (Cross-Cutting Concerns)

**Baggage** propagates arbitrary key-value pairs across traces.

**Use case**: User ID, tenant ID, experiment flag.

```python
from opentelemetry.baggage import set_baggage, get_baggage

# Service A: Set baggage
set_baggage("user_id", "user_12345")
set_baggage("experiment", "new_ui")

# Propagated to Service B automatically

# Service B: Read baggage
user_id = get_baggage("user_id")  # "user_12345"
span.set_attribute("user_id", user_id)
```

**Warning**: Baggage increases payload size. Keep it minimal (< 10 keys, < 1KB total).

---

### Pattern 3: Span Links

**Span links** connect related but independent traces.

**Use case**: Batch processing (one parent job, many child jobs).

```python
# Parent job creates trace
with tracer.start_as_current_span("batch_job") as parent_span:
    parent_context = parent_span.get_span_context()

    # Spawn child jobs
    for item in items:
        # Each child gets its own trace, but links to parent
        with tracer.start_as_current_span(
            "process_item",
            links=[Link(parent_context)]  # Link to parent
        ):
            process(item)
```

**Result**: Child traces are independent but linked to parent. View them together in Grafana.

---

### Pattern 4: Synthetic Monitoring (Canaries)

**Synthetic monitoring**: Automated tests that generate telemetry.

**Example**:

```python
import time
from opentelemetry import trace

tracer = trace.get_tracer("synthetic-monitor")

def run_health_check():
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("synthetic", True)

        # Test critical path
        try:
            response = requests.get("https://api.example.com/health")
            assert response.status_code == 200

            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

# Run every 1 minute
while True:
    run_health_check()
    time.sleep(60)
```

**Benefits**:
- Proactive monitoring (find issues before users do)
- SLA verification
- Realistic traffic patterns

---

### Pattern 5: Profiling Integration

**Continuous profiling**: Capture CPU/memory profiles and link to traces.

**Tools**:
- **Pyroscope**: Continuous profiling platform
- **pprof**: Go profiling
- **py-spy**: Python profiling

**Integration**:

```python
with tracer.start_as_current_span("expensive_operation") as span:
    # Start profiler
    profiler.start()

    # Your code
    result = expensive_computation()

    # Stop profiler
    profile_data = profiler.stop()

    # Link profile to span
    span.set_attribute("profile.url", upload_profile(profile_data))
```

**Result**: Click span in Grafana → view CPU/memory flame graph.

---

## OpenTelemetry Ecosystem

### OTel Language Support

**Officially supported**:
- Python
- Java
- Go
- JavaScript/TypeScript
- .NET (C#)
- C++
- Ruby
- PHP
- Erlang/Elixir
- Rust
- Swift

**Status**: Most are GA (Generally Available), production-ready.

---

### OTel Instrumentation Libraries

**Automatic instrumentation** for popular frameworks:

**Python**:
- `opentelemetry-instrumentation-flask`
- `opentelemetry-instrumentation-django`
- `opentelemetry-instrumentation-fastapi`
- `opentelemetry-instrumentation-requests`
- `opentelemetry-instrumentation-psycopg2`
- `opentelemetry-instrumentation-redis`
- `opentelemetry-instrumentation-kafka-python`

**Install all**:
```bash
opentelemetry-bootstrap --action=install
```

---

### OTel-Compatible Backends

**Open source**:
- Grafana Stack (Tempo, Loki, Mimir)
- Jaeger
- Zipkin
- SigNoz
- Uptrace

**Commercial**:
- Datadog
- New Relic
- Honeycomb
- Lightstep
- Dynatrace
- Splunk

**All support OTLP** natively.

---

## Cutting-Edge Topics

### OpenTelemetry Profiling

**NEW**: OTel Profiling Signal (experimental)

**Goal**: Unified profiling data (CPU, memory, I/O) as a new signal.

**Status**: Early development, not yet production-ready.

---

### eBPF-Based Auto-Instrumentation

**eBPF**: Linux kernel technology for observability without code changes.

**Tools**:
- **Pixie**: Auto-instrumentation via eBPF
- **Parca**: Continuous profiling
- **Cilium**: Network observability

**Example**: Instrument applications without modifying code or restarting them.

---

### OpenTelemetry for Kubernetes

**Kubernetes Operators** for auto-instrumentation:

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: my-instrumentation
spec:
  exporter:
    endpoint: http://otel-collector:4317
  propagators:
    - tracecontext
    - baggage
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:latest
```

**Result**: Automatically instruments Python pods with OTel (no code changes).

---

### Serverless and Edge Observability

**Challenges**:
- Short-lived functions
- Cold starts
- Distributed by nature

**Solutions**:
- **AWS X-Ray**: Native tracing for Lambda
- **OTel Lambda Layers**: Auto-instrumentation
- **Edge tracing**: Cloudflare, Fastly support OTel

---

## Performance Optimization

### Reducing Overhead

**Sampling**: Keep 1-10% of traces (biggest impact)

**Async exporting**: Use background threads

**Batching**: Export in batches, not individually

**Compression**: Enable gzip on exporters

**Attribute filtering**: Only keep essential attributes

**Result**: < 1% performance overhead in most apps.

---

### Benchmarking

**Measure OTel overhead**:

```python
import time

# Without tracing
start = time.time()
for _ in range(10000):
    process_item()
baseline = time.time() - start

# With tracing
start = time.time()
for _ in range(10000):
    with tracer.start_as_current_span("process"):
        process_item()
with_tracing = time.time() - start

overhead = (with_tracing - baseline) / baseline * 100
print(f"Overhead: {overhead:.2f}%")
```

**Typical result**: 0.5-2% overhead.

---

## Key Takeaways

1. **Advanced sampling**: Adaptive, attribute-based, composite strategies
2. **Cardinality explosion**: Detect and fix with aggregation, relabeling
3. **Custom exporters/processors**: Extend OTel for custom needs
4. **SDK internals**: Understand batching, context propagation
5. **Advanced patterns**: Distributed context, baggage, span links, synthetic monitoring
6. **Cutting-edge**: eBPF, Kubernetes operators, serverless
7. **Performance**: Sampling, batching, compression keep overhead < 1%

---

## Where to Go from Here

### Practice More

- Instrument a real project (your own code)
- Build complex dashboards
- Set up production observability stack
- Contribute to OpenTelemetry

---

### Learn More

**Official Docs**:
- https://opentelemetry.io/docs/
- https://grafana.com/docs/
- https://prometheus.io/docs/

**Community**:
- OpenTelemetry Slack
- CNCF Events
- Local meetups

**Books**:
- "Distributed Tracing in Practice" (OpenTelemetry)
- "Prometheus: Up & Running"
- "Observability Engineering" (Honeycomb)

---

### Stay Current

**Follow**:
- OpenTelemetry blog
- Grafana blog
- CNCF newsletter

**Watch**:
- KubeCon/CloudNativeCon talks
- Observability YouTube channels

---

## Final Thoughts

**Observability is a journey, not a destination.**

You've learned:
- ✅ Observability fundamentals
- ✅ The three pillars (traces, metrics, logs)
- ✅ OpenTelemetry end-to-end
- ✅ Prometheus, Loki, Tempo
- ✅ The OTel Collector
- ✅ How everything connects
- ✅ Instrumentation patterns
- ✅ Hands-on practice
- ✅ Production best practices
- ✅ Advanced topics

**You're now ready to**:
- Implement observability in your own projects
- Debug production issues efficiently
- Build reliable, observable systems
- Continue learning and growing

**Remember**:
- Start small, iterate
- Instrument the critical path first
- Monitor, learn, improve
- Share knowledge with your team

---

## 🎉 Congratulations!

**You've completed the OpenTelemetry Learning Path!**

You now have the skills to:
- Build observable systems
- Debug production issues
- Optimize performance
- Reduce costs
- Implement best practices

**Thank you for learning with us!**

If this tutorial helped you, consider:
- ⭐ Star the repo
- 📝 Share with your team
- 🐛 Report issues
- 💡 Suggest improvements

**Happy observing!** 🔭

---

**Progress**: ✅ All 15 lessons complete! 🎓

---

## Quick Reference

### Essential Commands

```bash
# Start stack
docker-compose up -d

# Check health
./scripts/check_health.sh

# Process files
neuro-preprocess process <file> -o <output>

# Run demo
./scripts/run_demo.sh normal

# View logs
docker-compose logs -f <service>

# Stop stack
docker-compose down
```

---

### Essential Queries

**PromQL**:
```promql
# Rate
rate(neuro_files_processed_total[5m])

# P95
histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))

# Error rate
rate(neuro_files_failed_total[5m]) / rate(neuro_files_processed_total[5m])
```

**LogQL**:
```logql
# All logs
{service_name="neuro-preprocess"}

# Errors
{service_name="neuro-preprocess"} | json | level="ERROR"

# By trace
{service_name="neuro-preprocess"} | json | trace_id="abc123"
```

**TraceQL**:
```traceql
# Slow traces
{duration > 5s}

# Errors
{status = error}

# By attribute
{span.file_size_mb > 100}
```

---

### URLs

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200
- **OTel Collector**: http://localhost:4317 (gRPC)

---

**End of Tutorial Series** 🎓
