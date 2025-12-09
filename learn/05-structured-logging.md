# Lesson 5: Structured Logging

**Estimated time**: 40-50 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand structured vs unstructured logs
✅ Know the five log levels and when to use them
✅ Learn how to correlate logs with traces
✅ Understand log context and attributes
✅ Know logging best practices

---

## What Are Logs?

### The Simple Definition

**Logs** are **text messages** that describe events that happened in your application.

**Analogy**: Logs are like a **ship captain's logbook**:

```
Captain's Log - Stardate 2025.11.20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
08:00 - Departed from port
10:30 - Encountered rough seas, wind speed 45 knots
12:00 - Engine temperature rose to 95°C, within normal range
14:00 - Arrived at destination, 6 hours total voyage
```

Each entry captures:
- **When** it happened (timestamp)
- **What** happened (message)
- **Context** (wind speed, temperature)

---

## Unstructured vs Structured Logs

### Unstructured Logs (Old Way)

**Plain text** messages:

```
2025-11-20 14:30:15 Loading file: sub-001_T1w.nii.gz
2025-11-20 14:30:15 File size: 4.90 MB
2025-11-20 14:30:17 Processing completed in 1.96 seconds
2025-11-20 14:30:17 Output written to: /output/sub-001_processed.nii.gz
```

**Problems**:
- ❌ Hard to parse programmatically
- ❌ Hard to search ("find all logs where duration > 2s")
- ❌ Hard to filter ("show only errors for user X")
- ❌ Context is embedded in the message string

---

### Structured Logs (Modern Way)

**JSON** format with key-value pairs:

```json
{
  "timestamp": "2025-11-20T14:30:15Z",
  "level": "INFO",
  "message": "Loading file",
  "file_path": "sub-001_T1w.nii.gz",
  "file_size_mb": 4.90,
  "trace_id": "7f8a9b0c1d2e3f4a",
  "span_id": "1111111111111111"
}
```

```json
{
  "timestamp": "2025-11-20T14:30:17Z",
  "level": "INFO",
  "message": "Processing completed",
  "duration_seconds": 1.96,
  "output_path": "/output/sub-001_processed.nii.gz",
  "trace_id": "7f8a9b0c1d2e3f4a",
  "span_id": "1111111111111111"
}
```

**Benefits**:
- ✅ Easy to parse and query
- ✅ Easy to filter by any field
- ✅ Easy to correlate with traces (trace_id)
- ✅ Consistent structure

---

## The Five Log Levels

Logs have **severity levels** that indicate importance:

```
┌─────────────────────────────────┐
│       LOG LEVELS                │
│  (from least to most severe)    │
├─────────────────────────────────┤
│  🔍 DEBUG    - Detailed info    │
│  ℹ️  INFO     - Normal events    │
│  ⚠️  WARNING  - Unexpected       │
│  ❌ ERROR    - Something failed │
│  🔥 CRITICAL - System broken    │
└─────────────────────────────────┘
```

Let's explore each level:

---

### DEBUG Level

**When to use**: Detailed information for diagnosing problems.

**Examples**:
```python
logger.debug("Function process_image() called with shape=(256, 256, 256)")
logger.debug("Entering skull_strip stage")
logger.debug("Intermediate result min=0.0, max=255.0, mean=127.5")
```

**Characteristics**:
- Most verbose
- Usually disabled in production (too much noise)
- Useful during development and debugging

**Analogy**: Like a **play-by-play sports commentary** - every detail.

---

### INFO Level

**When to use**: Normal operational events worth noting.

**Examples**:
```python
logger.info("Processing started for file: sub-001_T1w.nii.gz")
logger.info("File loaded successfully, size: 4.90 MB")
logger.info("Processing completed in 1.96 seconds")
```

**Characteristics**:
- Normal operations
- Key milestones
- Default log level in production

**Analogy**: Like **news headlines** - important events, not every detail.

---

### WARNING Level

**When to use**: Something unexpected happened, but the system can continue.

**Examples**:
```python
logger.warning("File size 250 MB exceeds recommended 100 MB, may be slow")
logger.warning("Retry attempt 2 of 3 after network timeout")
logger.warning("Disk space low: only 500 MB remaining")
```

**Characteristics**:
- Unexpected but not critical
- System still functioning
- Should be investigated eventually

**Analogy**: Like a **yellow traffic light** - caution, slow down.

---

### ERROR Level

**When to use**: Something failed, but the system can still run.

**Examples**:
```python
logger.error("Failed to process file: sub-042_T1w.nii.gz", exc_info=True)
logger.error("Database connection timeout after 30 seconds")
logger.error("Permission denied: cannot write to /output directory")
```

**Characteristics**:
- Operation failed
- Needs attention
- System still running (other requests unaffected)

**Analogy**: Like a **car's check engine light** - something's wrong, needs fixing.

---

### CRITICAL Level

**When to use**: System is in a critical state, may not be able to continue.

**Examples**:
```python
logger.critical("Out of memory, cannot allocate array")
logger.critical("Database connection pool exhausted")
logger.critical("All worker threads have crashed")
```

**Characteristics**:
- System-wide failure
- Immediate action required
- May require restart

**Analogy**: Like a **fire alarm** - emergency, evacuate now.

---

## Log Level Guidelines

| Level | Production? | Development? | When to Use |
|-------|------------|--------------|-------------|
| **DEBUG** | ❌ No (too noisy) | ✅ Yes | Detailed debugging info |
| **INFO** | ✅ Yes (default) | ✅ Yes | Normal operations, milestones |
| **WARNING** | ✅ Yes | ✅ Yes | Unexpected but OK, investigate later |
| **ERROR** | ✅ Yes | ✅ Yes | Operation failed, needs attention |
| **CRITICAL** | ✅ Yes (alerts!) | ✅ Yes | System failure, immediate action |

---

## Structured Logging in Python

### Basic Setup

```python
import logging
import json

# Configure Python logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Simple usage
logger.info("Processing file")
logger.error("Failed to load file")
```

---

### Adding Context (Extra Fields)

```python
# Log with extra context
logger.info(
    "Processing file",
    extra={
        "file_path": "sub-001_T1w.nii.gz",
        "file_size_mb": 4.90,
        "user_id": "user_123"
    }
)
```

**With OpenTelemetry**, this context is automatically included!

---

### Structured Logging with OpenTelemetry

OpenTelemetry's logging instrumentation **automatically adds trace context** to logs:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import logging

# Instrument logging (adds trace_id and span_id)
LoggingInstrumentor().instrument()

logger = logging.getLogger(__name__)

# Create a span
with trace.get_tracer(__name__).start_as_current_span("process_file"):

    # This log automatically gets trace_id and span_id!
    logger.info("Processing file: sub-001_T1w.nii.gz")

    # Do work
    process_file(path)

    logger.info("Processing completed")
```

**Output** (JSON format sent to Loki):

```json
{
  "timestamp": "2025-11-20T14:30:15Z",
  "level": "INFO",
  "message": "Processing file: sub-001_T1w.nii.gz",
  "trace_id": "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
  "span_id": "1111111111111111",
  "service_name": "neuro-preprocess"
}
```

**Key benefit**: You can now **jump from traces to logs** and vice versa!

---

## Correlating Logs with Traces

**The magic**: Logs and traces share the same **trace_id**.

### Workflow 1: Trace → Logs

1. Open a trace in Grafana/Tempo
2. Click "Logs for this trace"
3. See all logs with the same trace_id

**Example**:

```
Trace ID: 7f8a9b0c...

Span: process_file (2.5s)
├─ Span: load_file (0.2s)
│  └─ Log: "Loading file: sub-001_T1w.nii.gz" [INFO]
├─ Span: process_image (1.5s)
│  ├─ Log: "Starting skull stripping" [INFO]
│  ├─ Log: "Skull stripping completed" [INFO]
│  └─ Log: "Memory usage: 850 MB" [WARNING]
└─ Span: write_output (0.8s)
   └─ Log: "File written successfully" [INFO]
```

---

### Workflow 2: Logs → Trace

1. Search logs in Grafana/Loki
2. Find an interesting log (e.g., error)
3. Click the trace_id link
4. Open the full trace to see what happened

**Example**:

```
Log: "Failed to process image: out of memory"
trace_id: abc123...

→ Click trace_id
→ See full trace:
  - Which file was being processed?
  - How large was it?
  - Which stage failed?
  - What led up to the failure?
```

---

## Logging Best Practices

### 1. Use Appropriate Log Levels

**Good**:
```python
logger.info("File processing started")          # Normal operation
logger.warning("File size 250 MB, may be slow")  # Unexpected but OK
logger.error("Failed to load file", exc_info=True)  # Operation failed
```

**Bad**:
```python
logger.info("Error occurred")  # ❌ Wrong level!
logger.error("File processing started")  # ❌ Not an error!
logger.debug("Critical system failure")  # ❌ Should be CRITICAL!
```

---

### 2. Include Useful Context

**Good**:
```python
logger.error(
    "Failed to process file",
    extra={
        "file_path": filepath,
        "file_size_mb": size,
        "error_type": type(e).__name__,
        "user_id": user_id
    },
    exc_info=True  # Include stack trace
)
```

**Bad**:
```python
logger.error("Error occurred")  # ❌ No context!
```

---

### 3. Don't Log Sensitive Data

**Bad**:
```python
logger.info(f"User logged in: password={password}")  # ❌ Security risk!
logger.info(f"Processing file: /users/john_doe/medical_records/...")  # ❌ PII!
logger.info(f"API key: {api_key}")  # ❌ Secrets leaked!
```

**Good**:
```python
logger.info(f"User logged in: user_id={user_id}")  # ✅ ID only
logger.info(f"Processing file: {hash(filepath)}")  # ✅ Hashed
logger.info("API call successful")  # ✅ No secrets
```

---

### 4. Use Structured Fields, Not String Interpolation

**Bad**:
```python
logger.info(f"Processed file {filename} in {duration}s, size {size} MB")
```

**Problem**: Can't query by duration or size programmatically.

**Good**:
```python
logger.info(
    "File processed successfully",
    extra={
        "filename": filename,
        "duration_seconds": duration,
        "file_size_mb": size
    }
)
```

**Benefit**: Can query in Loki:

```logql
{service_name="neuro-preprocess"} | json | duration_seconds > 5
```

---

### 5. Log at Boundaries

**Log**:
- When entering/exiting major operations
- Before/after external calls (database, API)
- On errors or exceptions
- On state changes

**Don't log**:
- Inside tight loops (too noisy)
- Trivial operations (variable assignments)
- Redundant information (already in traces)

**Example**:

```python
def process_file(filepath: str):
    logger.info("Processing started", extra={"filepath": filepath})  # ✅

    data = load_file(filepath)  # Don't log every byte read ❌

    logger.info("File loaded", extra={"size_mb": data.size})  # ✅

    result = process_image(data)

    logger.info("Processing completed")  # ✅

    return result
```

---

## Real Example from Our Project

From `app/neuro_preprocess/pipeline.py`:

```python
def process_file(self, filepath: str) -> dict:
    """Process a single file with full telemetry."""

    logger.info(
        "Processing started",
        extra={
            "filepath": filepath,
            "file_path": filepath,  # For Loki filtering
        }
    )

    with self.tracer.start_as_current_span("process_file") as span:
        try:
            # Load file
            loader_result = self.loader.load(filepath)
            data = loader_result['data']

            logger.info(
                "File loaded successfully",
                extra={
                    "file_size_mb": loader_result['file_size_mb'],
                    "array_shape": str(data.shape)
                }
            )

            # Process
            processed = self.processor.process_image(data)

            # Write
            writer_result = self.writer.write(processed, output_path)

            duration = time.time() - start_time

            logger.info(
                "Processing completed successfully",
                extra={
                    "duration_seconds": duration,
                    "output_path": writer_result['output_path']
                }
            )

            return {"status": "success", "duration": duration}

        except Exception as e:
            logger.error(
                "Processing failed",
                extra={
                    "filepath": filepath,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True  # Include stack trace
            )

            raise
```

**This generates structured logs** with:
- Consistent fields (filepath, duration, error_type)
- Appropriate log levels (INFO for success, ERROR for failures)
- Trace context (trace_id, span_id) added automatically
- Exception details when failures occur

---

## Querying Logs in Grafana/Loki

### Basic Query

```logql
# All logs from our service
{service_name="neuro-preprocess"}
```

---

### Filter by Level

```logql
# Only errors
{service_name="neuro-preprocess"} | json | level="ERROR"

# Warnings and errors
{service_name="neuro-preprocess"} | json | level=~"WARNING|ERROR"
```

---

### Filter by Field

```logql
# Logs for a specific file
{service_name="neuro-preprocess"} | json | filepath="sub-001_T1w.nii.gz"

# Logs where duration > 5 seconds
{service_name="neuro-preprocess"} | json | duration_seconds > 5
```

---

### Filter by Trace ID

```logql
# All logs for a specific trace
{service_name="neuro-preprocess"} | json | trace_id="7f8a9b0c1d2e3f4a"
```

**This is how you jump from trace to logs!**

---

### Search Message Content

```logql
# Logs containing "failed"
{service_name="neuro-preprocess"} |= "failed"

# Logs NOT containing "success"
{service_name="neuro-preprocess"} != "success"

# Regex search
{service_name="neuro-preprocess"} |~ "failed|error|timeout"
```

---

## Logs vs Traces vs Metrics

### When to Use Each

| Scenario | Use | Why |
|----------|-----|-----|
| "What's the error rate?" | **Metrics** | Aggregated numbers |
| "Show me all errors" | **Logs** | Detailed messages |
| "Why was this request slow?" | **Traces** | Timeline of operations |
| "What happened at 2pm?" | **Logs** | Events at that time |
| "Which stage is slowest?" | **Traces** | Span durations |
| "How many requests/sec?" | **Metrics** | Rate calculations |

---

### Complementary Use

**Together they're powerful**:

1. **Metric** shows problem: "Error rate increased"
2. **Logs** show which errors: "Out of memory errors"
3. **Traces** show where: "During skull_strip stage for large files"

---

## Try It Yourself

### Exercise 1: View Logs in Grafana

1. **Start the stack**:
   ```bash
   docker-compose up -d
   ```

2. **Generate logs**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

3. **Open Grafana**: http://localhost:3000
   - Navigate to **Explore**
   - Select **Loki** datasource
   - Query: `{service_name="neuro-preprocess"}`

4. **Explore**:
   - How many INFO logs vs ERROR logs?
   - Find a log and click the trace_id link
   - Filter logs by `level="INFO"`

---

### Exercise 2: Trace to Logs Correlation

1. **Find a trace** in Tempo (Explore → Tempo → Search)

2. **Click on a span**

3. **Look for "Logs for this span"** button (may need to configure in Grafana datasource)

4. **See all logs** with the same trace_id

---

### Exercise 3: Add Logging to Your Code

1. **Open**: `app/neuro_preprocess/processor.py`

2. **Add structured logging**:

```python
import logging

logger = logging.getLogger(__name__)

def _skull_strip(self, data: np.ndarray) -> np.ndarray:
    logger.info(
        "Starting skull stripping",
        extra={
            "input_shape": str(data.shape),
            "input_dtype": str(data.dtype)
        }
    )

    # Processing...
    mask = data > (data.mean() + 0.5 * data.std())
    result = data * mask

    logger.info(
        "Skull stripping completed",
        extra={
            "nonzero_voxels": int(np.count_nonzero(result)),
            "percent_retained": float(np.count_nonzero(result) / data.size * 100)
        }
    )

    return result
```

3. **Rebuild and test**:
   ```bash
   cd app && pip install -e . && cd ..
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **View your logs** in Loki:
   ```logql
   {service_name="neuro-preprocess"} |= "skull stripping"
   ```

---

## Key Takeaways

1. **Structured logs** (JSON) are better than unstructured (plain text)
2. **Five log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
3. **Correlate logs with traces** via trace_id and span_id
4. **Include context** (fields) for better filtering and searching
5. **Log levels matter**: Use INFO for normal operations, ERROR for failures
6. **Don't log sensitive data** (passwords, PII, secrets)
7. **Logs + Traces + Metrics** = Complete observability

---

## Quiz

1. **What's the difference between structured and unstructured logs?**
   <details>
   <summary>Click to see answer</summary>
   Structured logs use key-value pairs (JSON), making them easy to parse and query. Unstructured logs are plain text, hard to search programmatically.
   </details>

2. **When should you use INFO vs ERROR log level?**
   <details>
   <summary>Click to see answer</summary>
   INFO for normal operational events (file loaded, processing started). ERROR when an operation fails (file not found, out of memory).
   </details>

3. **How do logs correlate with traces?**
   <details>
   <summary>Click to see answer</summary>
   Both share the same trace_id and span_id. You can jump from a trace to its logs or from a log entry to its full trace in Grafana.
   </details>

4. **Why include context in logs?**
   <details>
   <summary>Click to see answer</summary>
   Context (file path, size, duration, etc.) enables filtering and searching. You can query "show logs where duration > 5s" instead of manually reading every log.
   </details>

---

## Next Steps

🎉 **Congratulations!** You've completed the Three Pillars Deep Dive!

**Next**: [Lesson 6: Prometheus Guide →](06-prometheus-guide.md)

In the next lesson, you'll learn:
- How Prometheus stores time-series data
- PromQL query language
- Scraping vs pushing metrics
- Building queries for our project

---

**Progress**: ✅ Lessons 1-5 complete (Three Pillars Done!) | ⬜ 9 lessons remaining
