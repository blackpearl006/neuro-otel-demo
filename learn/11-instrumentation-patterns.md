# Lesson 11: Instrumentation Patterns

**Estimated time**: 50-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Know the difference between automatic and manual instrumentation
✅ Learn common instrumentation patterns
✅ Understand best practices for adding observability
✅ Be able to instrument your own code
✅ Know what to instrument and what to skip

---

## What Is Instrumentation?

### The Simple Definition

**Instrumentation** is the process of adding **observability code** to your application so it generates telemetry (traces, metrics, logs).

**Analogy**: Like adding **gauges and sensors** to a car:
- Speedometer (metric: current speed)
- Trip computer (trace: journey timeline)
- Dashboard warnings (logs: check engine light)

Without instrumentation, your app is a **black box**. With it, you can see inside!

---

## Automatic vs. Manual Instrumentation

### Automatic Instrumentation

**What it is**: Libraries that automatically add telemetry to popular frameworks.

**Examples**:
- HTTP libraries (requests, urllib3, aiohttp)
- Database drivers (psycopg2, pymongo, mysql-connector)
- Web frameworks (Flask, Django, FastAPI)
- Message queues (Kafka, RabbitMQ)

**How it works**:

```python
# Just install and enable!
from opentelemetry.instrumentation.requests import RequestsInstrumentor

RequestsInstrumentor().instrument()

# Now all requests library calls are automatically traced
import requests
response = requests.get("https://api.example.com/data")
# ↑ This creates a span automatically!
```

**Pros**:
- ✅ Zero code changes
- ✅ Quick to set up
- ✅ Standard span names and attributes

**Cons**:
- ❌ Generic spans (not application-specific)
- ❌ May not capture business logic
- ❌ Limited control

---

### Manual Instrumentation

**What it is**: Explicitly adding telemetry code to your application.

**Example**:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_file(filepath):
    # Manual span creation
    with tracer.start_as_current_span("process_file") as span:
        # Add custom attributes
        span.set_attribute("file.path", filepath)

        # Your business logic
        data = load_file(filepath)
        result = process(data)
        save(result)

        span.set_attribute("result.size", len(result))
        return result
```

**Pros**:
- ✅ Full control
- ✅ Business-specific spans and attributes
- ✅ Capture domain logic

**Cons**:
- ❌ Requires code changes
- ❌ More work
- ❌ Maintenance burden

---

### Hybrid Approach (Best Practice)

**Use both**:
1. **Automatic** for frameworks and libraries
2. **Manual** for business logic

```python
# Automatic instrumentation for HTTP and DB
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

RequestsInstrumentor().instrument()
Psycopg2Instrumentor().instrument()

# Manual instrumentation for business logic
with tracer.start_as_current_span("process_order"):
    # Your code here
    pass
```

**Result**: Infrastructure automatically traced + business logic manually traced.

---

## Common Instrumentation Patterns

### Pattern 1: Function-Level Spans

**When**: Important business functions

**Example**:

```python
def process_file(filepath):
    with tracer.start_as_current_span("process_file") as span:
        span.set_attribute("file.path", filepath)

        # Function logic
        result = do_processing(filepath)

        span.set_attribute("result.status", "success")
        return result
```

**Best for**: Top-level business operations

---

### Pattern 2: Nested Spans (Parent-Child)

**When**: Breaking down complex operations

**Example**:

```python
def process_file(filepath):
    with tracer.start_as_current_span("process_file"):  # Parent

        with tracer.start_as_current_span("load_file"):  # Child 1
            data = load_file(filepath)

        with tracer.start_as_current_span("transform"):  # Child 2
            transformed = transform(data)

        with tracer.start_as_current_span("save_file"):  # Child 3
            save_file(transformed)
```

**Result**:

```
process_file (parent)
├─ load_file (child)
├─ transform (child)
└─ save_file (child)
```

**Best for**: Multi-stage operations

---

### Pattern 3: Decorator-Based Instrumentation

**When**: Reusable instrumentation

**Example**:

```python
from functools import wraps

def traced(func):
    """Decorator to automatically trace a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("function.module", func.__module__)
            result = func(*args, **kwargs)
            return result
    return wrapper

# Use it!
@traced
def process_file(filepath):
    # Function logic
    pass
```

**Best for**: Consistent instrumentation across many functions

---

### Pattern 4: Context Manager for Resources

**When**: Operations with setup/teardown (file I/O, connections)

**Example**:

```python
class TracedFileLoader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.span = None

    def __enter__(self):
        self.span = tracer.start_span("load_file")
        self.span.set_attribute("file.path", self.filepath)
        self.file = open(self.filepath, 'r')
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        self.span.end()
        self.file.close()

# Use it!
with TracedFileLoader("/data/file.txt") as f:
    data = f.read()
```

**Best for**: Resource management (files, connections, locks)

---

### Pattern 5: Async/Await Instrumentation

**When**: Async Python code

**Example**:

```python
async def process_file_async(filepath):
    with tracer.start_as_current_span("process_file_async") as span:
        span.set_attribute("file.path", filepath)

        # Async operations
        data = await load_file_async(filepath)
        result = await process_async(data)

        return result
```

**Key**: Context propagates automatically through `await` calls.

---

### Pattern 6: Error Handling and Recording

**When**: Capturing exceptions

**Example**:

```python
def process_file(filepath):
    with tracer.start_as_current_span("process_file") as span:
        try:
            result = risky_operation(filepath)
            span.set_status(Status(StatusCode.OK))
            return result
        except FileNotFoundError as e:
            span.set_status(Status(StatusCode.ERROR, "File not found"))
            span.record_exception(e)  # Records stack trace
            raise
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
```

**Result**: Failed spans are marked with status=ERROR and include exception details.

---

### Pattern 7: Adding Events to Spans

**When**: Important milestones within an operation

**Example**:

```python
def process_large_file(filepath):
    with tracer.start_as_current_span("process_large_file") as span:

        span.add_event("Loading started")
        data = load_file(filepath)

        span.add_event("Processing started", attributes={"data_size": len(data)})
        result = process(data)

        span.add_event("Saving started")
        save(result)

        span.add_event("Processing completed")
```

**Result**: Timeline with milestones visible in Grafana.

---

### Pattern 8: Conditional Instrumentation

**When**: Only trace in certain conditions

**Example**:

```python
def process_file(filepath, trace_enabled=True):
    if trace_enabled:
        with tracer.start_as_current_span("process_file"):
            return _process_file_impl(filepath)
    else:
        return _process_file_impl(filepath)

def _process_file_impl(filepath):
    # Actual logic (no tracing code)
    pass
```

**Better approach**: Use sampling at the SDK level instead.

---

## Metrics Instrumentation Patterns

### Pattern 1: Counter for Operations

**When**: Counting occurrences

**Example**:

```python
# Setup
meter = metrics.get_meter(__name__)
files_processed = meter.create_counter(
    name="files.processed",
    description="Total files processed",
    unit="files"
)

# Usage
def process_file(filepath):
    try:
        result = do_processing(filepath)
        files_processed.add(1, {"status": "success"})
    except Exception:
        files_processed.add(1, {"status": "failed"})
        raise
```

---

### Pattern 2: Histogram for Durations

**When**: Recording operation durations

**Example**:

```python
# Setup
duration_histogram = meter.create_histogram(
    name="process.duration",
    description="File processing duration",
    unit="seconds"
)

# Usage
import time

def process_file(filepath):
    start = time.time()
    try:
        result = do_processing(filepath)
        duration = time.time() - start
        duration_histogram.record(duration, {"status": "success"})
        return result
    except Exception:
        duration = time.time() - start
        duration_histogram.record(duration, {"status": "failed"})
        raise
```

---

### Pattern 3: Gauge for Current State

**When**: Tracking current values (active connections, queue size)

**Example**:

```python
active_tasks = []

def get_active_tasks():
    return len(active_tasks)

# Setup (Observable Gauge)
active_gauge = meter.create_observable_gauge(
    name="tasks.active",
    description="Currently active tasks",
    callbacks=[lambda options: [Observation(get_active_tasks())]]
)

# The callback is called automatically by the SDK
```

---

## Logging Instrumentation Patterns

### Pattern 1: Structured Logging

**Example**:

```python
import logging

logger = logging.getLogger(__name__)

def process_file(filepath):
    logger.info(
        "Processing started",
        extra={
            "file_path": filepath,
            "file_size": os.path.getsize(filepath)
        }
    )

    # Process...

    logger.info(
        "Processing completed",
        extra={
            "duration_seconds": duration
        }
    )
```

**Result**: Structured logs with searchable fields.

---

### Pattern 2: Log Levels

**Example**:

```python
def process_file(filepath):
    logger.debug(f"Entering process_file with {filepath}")  # DEBUG

    logger.info(f"Processing file: {filepath}")  # INFO

    if size > 100_000_000:
        logger.warning(f"Large file detected: {size} bytes")  # WARNING

    try:
        result = do_processing(filepath)
    except Exception as e:
        logger.error(f"Processing failed", exc_info=True)  # ERROR
        raise
```

---

### Pattern 3: Correlation with Traces

**Automatic with OTel**:

```python
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Enable once at startup
LoggingInstrumentor().instrument()

# Now all logs automatically include trace_id and span_id!
with tracer.start_as_current_span("process_file"):
    logger.info("Processing file")  # Includes trace context
```

---

## What to Instrument

### ✅ DO Instrument

**1. Business operations**
- Order processing
- File uploads
- Data transformations
- Report generation

**2. External calls**
- HTTP API requests
- Database queries
- Message queue operations
- File I/O

**3. Important stages**
- Authentication/authorization
- Data validation
- Critical calculations
- State changes

**4. Errors and failures**
- Exception handling
- Validation failures
- Retry attempts

---

### ❌ DON'T Instrument

**1. Trivial operations**
```python
# ❌ Don't do this
with tracer.start_as_current_span("add_two_numbers"):
    result = a + b
```

**2. Tight loops**
```python
# ❌ Don't do this
for item in millions_of_items:
    with tracer.start_as_current_span("process_item"):
        process(item)  # Creates millions of spans!
```

**Better**:
```python
# ✅ Span around the loop, not inside
with tracer.start_as_current_span("process_items") as span:
    span.set_attribute("item_count", len(items))
    for item in items:
        process(item)
```

**3. Getters/setters**
```python
# ❌ Too granular
with tracer.start_as_current_span("get_name"):
    return self.name
```

---

## Attribute Best Practices

### ✅ Good Attributes

```python
span.set_attribute("file.path", "/data/input.txt")  # ✅ Semantic
span.set_attribute("file.size_bytes", 1024)  # ✅ Descriptive units
span.set_attribute("http.status_code", 200)  # ✅ Standard
span.set_attribute("user.role", "admin")  # ✅ Low cardinality
```

---

### ❌ Bad Attributes

```python
span.set_attribute("data", str(data))  # ❌ Too much data
span.set_attribute("temp", 42)  # ❌ Meaningless name
span.set_attribute("user_id", "user_12345")  # ❌ High cardinality
span.set_attribute("password", password)  # ❌ Sensitive data!
```

---

## Real Example: Our Project

Let's review how our project is instrumented (`app/neuro_preprocess/pipeline.py`):

```python
class NeuroPipeline:
    def __init__(self):
        # Get tracer and meter
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.files_counter = self.meter.create_counter(
            name="neuro.files.processed",
            description="Total files processed"
        )
        self.duration_histogram = self.meter.create_histogram(
            name="neuro.process.duration",
            description="Processing duration"
        )

    def process_file(self, filepath: str) -> dict:
        """Process a single file with full telemetry."""
        start_time = time.time()

        # Create root span
        with self.tracer.start_as_current_span("process_file") as span:
            # Add attributes
            span.set_attribute("file.path", filepath)

            try:
                # Child span: load
                loader_result = self.loader.load(filepath)
                data = loader_result['data']

                # Record file size metric
                span.set_attribute("file.size_mb", loader_result['file_size_mb'])

                # Child span: process
                processed = self.processor.process_image(data)

                # Child span: write
                writer_result = self.writer.write(processed, output_path)

                # Record metrics
                duration = time.time() - start_time
                self.duration_histogram.record(duration, {"status": "success"})
                self.files_counter.add(1, {"status": "success"})

                # Set span status
                span.set_status(Status(StatusCode.OK))

                # Log success
                logger.info(
                    "Processing completed",
                    extra={"duration_seconds": duration}
                )

                return {"status": "success", "duration": duration}

            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                self.duration_histogram.record(duration, {"status": "failed"})
                self.files_counter.add(1, {"status": "failed"})

                # Record exception on span
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)

                # Log error
                logger.error(
                    "Processing failed",
                    extra={"error": str(e)},
                    exc_info=True
                )

                raise
```

**What this demonstrates**:
1. ✅ Root span for the operation
2. ✅ Child spans created in loader, processor, writer
3. ✅ Attributes on spans (file path, size)
4. ✅ Metrics recorded (counter, histogram)
5. ✅ Error handling (status, exceptions)
6. ✅ Structured logging with context

---

## Try It Yourself

### Exercise 1: Add a Custom Span

1. **Open**: `app/neuro_preprocess/writer.py`

2. **Find** the `write()` method

3. **Add a span** around metadata JSON writing:

```python
def write(self, data, output_path, metadata=None):
    with self.tracer.start_as_current_span("write_output"):

        # Add span for metadata writing
        with self.tracer.start_as_current_span("write_metadata") as span:
            metadata_path = output_path.replace('.nii.gz', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            span.set_attribute("metadata.path", metadata_path)
            span.set_attribute("metadata.size_bytes", os.path.getsize(metadata_path))

        # Rest of the code...
```

4. **Rebuild and test**:
   ```bash
   cd app && pip install -e . && cd ..
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

5. **View the trace** in Grafana - see your new span!

---

### Exercise 2: Add a Custom Metric

1. **Open**: `app/neuro_preprocess/processor.py`

2. **Add a metric** for stage execution count:

```python
def __init__(self, ...):
    # Existing code...

    # Add metric
    self.stage_counter = meter.create_counter(
        name="neuro.stages.executed",
        description="Count of stage executions",
        unit="executions"
    )

def process_image(self, data):
    with self.tracer.start_as_current_span("process_image"):
        result = data.copy()

        if "skull_strip" in self.stages:
            with self.tracer.start_as_current_span("skull_strip"):
                result = self._skull_strip(result)
                self.stage_counter.add(1, {"stage": "skull_strip"})  # ← Add this

        # Similar for other stages...
```

3. **Rebuild and test**

4. **Query in Prometheus**:
   ```promql
   neuro_stages_executed_total
   ```

---

### Exercise 3: Add Structured Logging

1. **Open**: `app/neuro_preprocess/loader.py`

2. **Add structured logs**:

```python
import logging
logger = logging.getLogger(__name__)

def load(self, filepath):
    with self.tracer.start_as_current_span("load_file"):

        logger.info(
            "Loading file",
            extra={
                "file_path": filepath,
                "file_exists": os.path.exists(filepath)
            }
        )

        # Load logic...

        logger.info(
            "File loaded successfully",
            extra={
                "file_size_mb": file_size_mb,
                "array_shape": str(data.shape)
            }
        )
```

3. **Rebuild and test**

4. **Query in Loki**:
   ```logql
   {service_name="neuro-preprocess"} |= "Loading file"
   ```

---

## Key Takeaways

1. **Automatic instrumentation**: Quick setup for frameworks/libraries
2. **Manual instrumentation**: Full control for business logic
3. **Hybrid approach**: Use both for best results
4. **Common patterns**: Function spans, nested spans, decorators, error handling
5. **What to instrument**: Business operations, external calls, errors
6. **What to skip**: Trivial operations, tight loops, getters/setters
7. **Attribute best practices**: Semantic names, low cardinality, no sensitive data
8. **Our project**: Demonstrates all patterns with traces, metrics, and logs

---

## Quiz

1. **What's the difference between automatic and manual instrumentation?**
   <details>
   <summary>Click to see answer</summary>
   Automatic: Libraries automatically add telemetry to frameworks (HTTP, databases). No code changes.
   Manual: You explicitly add tracing code for your business logic. Full control.
   </details>

2. **Should you instrument every function?**
   <details>
   <summary>Click to see answer</summary>
   No. Only instrument important business operations, external calls, and error paths. Skip trivial operations and tight loops.
   </details>

3. **How do you record exceptions in spans?**
   <details>
   <summary>Click to see answer</summary>
   ```python
   span.set_status(Status(StatusCode.ERROR, str(e)))
   span.record_exception(e)
   ```
   </details>

4. **Why avoid high-cardinality attributes?**
   <details>
   <summary>Click to see answer</summary>
   High cardinality (many unique values like user_id) creates many time series, increasing storage costs and slowing queries.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now know how to instrument your code!

**Next**: [Lesson 12: Hands-On Exercises →](12-hands-on-exercises.md)

In the next lesson, you'll:
- Build custom dashboards
- Create alerts
- Implement sampling
- Practice real-world scenarios

---

**Progress**: ✅ Lessons 1-11 complete | ⬜ 3 lessons remaining
