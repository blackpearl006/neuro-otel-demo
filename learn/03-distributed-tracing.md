# Lesson 3: Distributed Tracing

**Estimated time**: 45-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand what spans and traces are
✅ Know how trace IDs and span IDs work
✅ Understand parent-child span relationships
✅ Learn about span attributes, events, and status
✅ Be able to read trace waterfall diagrams

---

## What Is a Trace?

### The Simple Definition

A **trace** is the complete journey of a single request through your system.

**Analogy**: Think of a trace like a **FedEx package tracking number**:

```
Tracking #: ABC123456789                    [Trace ID]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nov 20, 08:00 AM - Package received         [Span 1]
Nov 20, 10:30 AM - In transit (truck)       [Span 2]
Nov 20, 02:00 PM - Arrived at hub           [Span 3]
Nov 20, 03:15 PM - Out for delivery         [Span 4]
Nov 20, 05:00 PM - Delivered                [Span 5]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 9 hours
```

Each step in the journey is a **span**, and together they form a **trace**.

---

## What Is a Span?

### The Simple Definition

A **span** represents a **single operation** within a trace.

**Key attributes of a span**:
- **Name**: What operation this represents (`"load_file"`, `"process_image"`)
- **Start time**: When it began
- **End time**: When it finished
- **Duration**: End time - Start time
- **Parent span ID**: Which span called this one (if any)
- **Attributes**: Additional metadata (file size, error messages)
- **Events**: Things that happened during the span
- **Status**: Success, error, or unset

**Analogy**: A span is like a **function call** in your code:

```python
def process_file(path):              # Span starts
    data = load_file(path)           # Child span
    result = process_image(data)     # Another child span
    write_output(result)             # Another child span
    return result                    # Span ends
```

---

## Trace IDs and Span IDs

Every span has two critical identifiers:

### Trace ID

**What it is**: A unique identifier for the entire trace.

**Format**: 128-bit hex string (32 characters)

**Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

**Purpose**: Links all spans that belong to the same request.

### Span ID

**What it is**: A unique identifier for this specific span.

**Format**: 64-bit hex string (16 characters)

**Example**: `1234567890abcdef`

**Purpose**: Uniquely identifies this operation within the trace.

### Parent Span ID

**What it is**: The span ID of the parent span (if any).

**Purpose**: Creates the parent-child hierarchy.

**Example**:

```
Trace ID: abc123...

Span A: ID=111, Parent=null       (root span)
Span B: ID=222, Parent=111        (child of A)
Span C: ID=333, Parent=111        (child of A)
Span D: ID=444, Parent=222        (child of B, grandchild of A)
```

**Hierarchy**:

```
Span A (111)
├─ Span B (222)
│  └─ Span D (444)
└─ Span C (333)
```

---

## Trace Structure in Our Project

Let's look at a real trace from our neuroimaging pipeline:

### Example Trace

```
Trace ID: 7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c

┌─ Span: process_file                    [0.00s → 2.50s]  Duration: 2.50s
│  trace_id: 7f8a9b0c...
│  span_id: 1111111111111111
│  parent_id: null (root)
│  status: OK
│  attributes:
│    - file_path: "sub-001_T1w.nii.gz"
│    - file_size_mb: 4.9
│
├──┬─ Span: load_file                    [0.00s → 0.20s]  Duration: 0.20s
│  │  trace_id: 7f8a9b0c...
│  │  span_id: 2222222222222222
│  │  parent_id: 1111111111111111
│  │  status: OK
│  │  attributes:
│  │    - array_shape: "(256, 256, 256)"
│  │
├──┬─ Span: process_image                [0.20s → 1.70s]  Duration: 1.50s
│  │  trace_id: 7f8a9b0c...
│  │  span_id: 3333333333333333
│  │  parent_id: 1111111111111111
│  │  status: OK
│  │
│  ├──┬─ Span: skull_strip               [0.20s → 0.90s]  Duration: 0.70s
│  │  │  trace_id: 7f8a9b0c...
│  │  │  span_id: 4444444444444444
│  │  │  parent_id: 3333333333333333
│  │  │  status: OK
│  │  │
│  ├──┬─ Span: bias_correction           [0.90s → 1.40s]  Duration: 0.50s
│  │  │  trace_id: 7f8a9b0c...
│  │  │  span_id: 5555555555555555
│  │  │  parent_id: 3333333333333333
│  │  │  status: OK
│  │  │
│  └──┬─ Span: normalization             [1.40s → 1.70s]  Duration: 0.30s
│     │  trace_id: 7f8a9b0c...
│     │  span_id: 6666666666666666
│     │  parent_id: 3333333333333333
│     │  status: OK
│     │
└──┬─ Span: write_output                 [1.70s → 2.50s]  Duration: 0.80s
   │  trace_id: 7f8a9b0c...
   │  span_id: 7777777777777777
   │  parent_id: 1111111111111111
   │  status: OK
   │  attributes:
   │    - output_path: "/output/sub-001_processed.nii.gz"
```

**Key observations**:
1. All spans share the same **trace_id**
2. Each span has a unique **span_id**
3. Child spans reference their parent's **span_id** as **parent_id**
4. Times are relative to the start of the trace
5. Total trace duration = Root span duration (2.50s)

---

## Creating Spans in Code

### Basic Span Creation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

# Create a span
with tracer.start_as_current_span("my_operation"):
    # Your code here
    result = do_something()
```

**What happens**:
1. Span starts when entering the `with` block
2. Span name is set to `"my_operation"`
3. Code executes
4. Span ends when exiting the `with` block
5. Duration is automatically calculated

---

### Nested Spans (Parent-Child)

```python
with tracer.start_as_current_span("parent"):
    print("In parent span")

    # This automatically becomes a child span
    with tracer.start_as_current_span("child_1"):
        print("In child 1")

    # This is also a child of parent (sibling of child_1)
    with tracer.start_as_current_span("child_2"):
        print("In child 2")
```

**Result**:

```
Span: parent
├─ Span: child_1
└─ Span: child_2
```

**Context propagation** automatically handles the parent-child relationship!

---

### Adding Attributes to Spans

Attributes are **key-value pairs** that provide context about the operation.

```python
with tracer.start_as_current_span("load_file") as span:
    # Add attributes
    span.set_attribute("file.path", "/data/sub-001.nii.gz")
    span.set_attribute("file.size_mb", 4.9)
    span.set_attribute("file.format", "nifti")

    data = load_nifti_file(path)

    span.set_attribute("array.shape", str(data.shape))
    span.set_attribute("array.dtype", str(data.dtype))
```

**In Grafana**, you can **filter traces** by attributes:

```
Show me all traces where file.size_mb > 10
Show me all traces where file.format = "nifti"
```

---

### Adding Events to Spans

Events are **timestamped messages** that happened during the span.

```python
with tracer.start_as_current_span("process_image") as span:
    span.add_event("Starting skull stripping")

    skull_strip(data)

    span.add_event("Skull stripping complete")

    bias_correction(data)

    span.add_event("Bias correction complete")
```

**Events appear in the trace timeline** with their timestamps, helping you understand what happened when.

---

### Setting Span Status

Spans can have three statuses:

1. **UNSET** (default): Nothing went wrong, but not explicitly OK
2. **OK**: Operation succeeded
3. **ERROR**: Operation failed

```python
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("risky_operation") as span:
    try:
        result = might_fail()
        span.set_status(Status(StatusCode.OK))
    except Exception as e:
        span.set_status(Status(StatusCode.ERROR, str(e)))
        span.record_exception(e)  # Also record the exception
        raise
```

**In Grafana**, you can **filter for failed traces**:

```
Show me all traces with status = ERROR
```

---

## Real Example from Our Project

Let's look at how we create spans in `app/neuro_preprocess/processor.py`:

```python
def process_image(self, data: np.ndarray) -> np.ndarray:
    """Process image with tracing."""
    with self.tracer.start_as_current_span("process_image") as span:
        # Add attributes
        span.set_attribute("array.shape", str(data.shape))
        span.set_attribute("stages.enabled", str(self.stages))

        result = data.copy()

        # Child span 1
        if "skull_strip" in self.stages:
            with self.tracer.start_as_current_span("skull_strip") as child_span:
                start = time.time()
                result = self._skull_strip(result)
                duration = time.time() - start
                child_span.set_attribute("duration_seconds", duration)

        # Child span 2
        if "bias_correction" in self.stages:
            with self.tracer.start_as_current_span("bias_correction") as child_span:
                start = time.time()
                result = self._bias_correction(result)
                duration = time.time() - start
                child_span.set_attribute("duration_seconds", duration)

        # Child span 3
        if "normalization" in self.stages:
            with self.tracer.start_as_current_span("normalization") as child_span:
                start = time.time()
                result = self._normalize(result)
                duration = time.time() - start
                child_span.set_attribute("duration_seconds", duration)

        return result
```

**This creates the hierarchy**:

```
process_image (parent)
├─ skull_strip (child)
├─ bias_correction (child)
└─ normalization (child)
```

---

## Reading Trace Waterfall Diagrams

Traces are visualized as **waterfall diagrams** in Grafana:

```
Time →  0ms    500ms   1000ms  1500ms  2000ms  2500ms
        │       │       │       │       │       │
┌───────────────────────────────────────────────────────┐
│ process_file                                          │ 2500ms
├───────────────────────────────────────────────────────┤
│ load_file      │                                       │ 200ms
├────────────────┴───────────────────────────────────────┤
│                process_image                          │ 1500ms
│                ├────────────────┐                      │
│                │ skull_strip    │                      │ 700ms
│                ├────────────────┴─────┐                │
│                │ bias_correction      │                │ 500ms
│                ├──────────────────────┴───┐            │
│                │ normalization            │            │ 300ms
├────────────────────────────────────────────┴───────────┤
│                                            write_output│ 800ms
└───────────────────────────────────────────────────────┘
```

**How to read it**:

1. **X-axis**: Time (starts at 0)
2. **Y-axis**: Span hierarchy (parent above children)
3. **Bar length**: Duration of the span
4. **Indentation**: Child spans are nested under parents
5. **Gaps**: Time when nothing was happening (or waiting)

**Analysis**:
- `skull_strip` takes the longest (700ms) → Optimization opportunity
- `load_file` and `write_output` happen sequentially (no overlap)
- Total time = 2500ms (sum of non-overlapping operations)

---

## Span Lifecycle

Understanding the lifecycle of a span:

```python
# 1. Span is created (start time recorded)
with tracer.start_as_current_span("my_span") as span:

    # 2. Span is active (can add attributes, events)
    span.set_attribute("key", "value")
    span.add_event("Something happened")

    # 3. Do work
    result = do_something()

    # 4. Span ends automatically (end time recorded, duration calculated)

# 5. Span is exported to the collector
```

**Key points**:
- Start time: When `start_as_current_span()` is called
- End time: When exiting the `with` block
- Duration: Calculated automatically
- Export: Happens asynchronously (batched for efficiency)

---

## Context Propagation

**Context** is how OpenTelemetry tracks which span is currently active.

### Within a Process

```python
# No span active
print(trace.get_current_span())  # <NonRecordingSpan>

with tracer.start_as_current_span("A"):
    # Span A is current
    print(trace.get_current_span().name)  # "A"

    with tracer.start_as_current_span("B"):
        # Span B is current (child of A)
        print(trace.get_current_span().name)  # "B"

    # Span A is current again
    print(trace.get_current_span().name)  # "A"

# No span active
```

**This is how parent-child relationships are automatically created!**

---

### Across Services (Distributed Tracing)

When a request crosses service boundaries, the trace context must be **propagated**.

**Example**: Service A calls Service B

```python
# Service A
with tracer.start_as_current_span("call_service_b") as span:
    # Extract trace context
    trace_id = span.get_span_context().trace_id
    span_id = span.get_span_context().span_id

    # Send in HTTP headers
    headers = {
        "traceparent": f"00-{trace_id:032x}-{span_id:016x}-01"
    }

    response = requests.get("http://service-b/api", headers=headers)
```

```python
# Service B
# Extract trace context from headers
trace_id = extract_from_header(request.headers["traceparent"])

# Create span with same trace ID
with tracer.start_as_current_span("handle_request") as span:
    # This span is now part of the same trace!
    pass
```

**Result**: One continuous trace across both services.

**In our project**, we use a single application, but the principle is the same when calling external APIs or microservices.

---

## Span Best Practices

### 1. Name Spans Clearly

**Good**:
```python
with tracer.start_as_current_span("load_nifti_file"):
with tracer.start_as_current_span("skull_strip_bet2"):
with tracer.start_as_current_span("save_to_s3"):
```

**Bad**:
```python
with tracer.start_as_current_span("operation"):
with tracer.start_as_current_span("do_stuff"):
with tracer.start_as_current_span("step_1"):
```

**Why**: Span names appear in Grafana. Clear names help you understand what's happening.

---

### 2. Add Useful Attributes

**Good**:
```python
span.set_attribute("file.path", "/data/sub-001.nii.gz")
span.set_attribute("file.size_mb", 4.9)
span.set_attribute("processing.stages", "skull_strip,bias_correction")
```

**Bad**:
```python
span.set_attribute("data", str(data))  # Too much data!
span.set_attribute("temp", 42)  # Meaningless name
```

**Why**: Attributes help you filter and debug. Use semantic names and avoid high-cardinality values.

---

### 3. Span Granularity

**Too coarse**:
```python
with tracer.start_as_current_span("process_everything"):
    load_file()
    process_image()
    write_output()
# Can't see which step is slow!
```

**Too fine**:
```python
with tracer.start_as_current_span("add_two_numbers"):
    result = a + b
# Too much overhead for trivial operations
```

**Just right**:
```python
with tracer.start_as_current_span("process_file"):
    with tracer.start_as_current_span("load_file"):
        data = load_file(path)

    with tracer.start_as_current_span("process_image"):
        result = process_image(data)

    with tracer.start_as_current_span("write_output"):
        write_output(result)
# Clear hierarchy, meaningful operations
```

**Rule of thumb**: Span operations that take > 10ms or are important for understanding the system.

---

### 4. Record Exceptions

```python
with tracer.start_as_current_span("risky_operation") as span:
    try:
        result = might_fail()
    except Exception as e:
        span.set_status(Status(StatusCode.ERROR, str(e)))
        span.record_exception(e)  # Captures stack trace
        raise
```

**Why**: Exception details appear in the trace, making debugging easier.

---

## Try It Yourself

### Exercise 1: View a Trace in Grafana

1. **Start the stack**:
   ```bash
   docker-compose up -d
   ```

2. **Generate a trace**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

3. **Open Grafana**: http://localhost:3000
   - Navigate to **Explore**
   - Select **Tempo** datasource
   - Click **Search**
   - Select service: `neuro-preprocess`
   - Click **Run Query**

4. **Click on a trace** to see the waterfall diagram

5. **Explore**:
   - Which span took the longest?
   - How many child spans does `process_image` have?
   - What attributes are on the `load_file` span?

---

### Exercise 2: Understand Trace Hierarchy

Given this code:

```python
with tracer.start_as_current_span("A"):
    with tracer.start_as_current_span("B"):
        with tracer.start_as_current_span("C"):
            pass
    with tracer.start_as_current_span("D"):
        pass
```

**Question**: Draw the span hierarchy.

<details>
<summary>Click to see answer</summary>

```
A (root)
├─ B (child of A)
│  └─ C (child of B, grandchild of A)
└─ D (child of A, sibling of B)
```
</details>

---

### Exercise 3: Add a Custom Span

1. **Open**: `app/neuro_preprocess/processor.py`

2. **Find** the `_skull_strip()` method

3. **Add attributes** to track the processing:

```python
def _skull_strip(self, data: np.ndarray) -> np.ndarray:
    with self.tracer.start_as_current_span("skull_strip_bet2") as span:
        # Add your attributes here
        span.set_attribute("input.min", float(data.min()))
        span.set_attribute("input.max", float(data.max()))
        span.set_attribute("input.mean", float(data.mean()))

        # Simulate skull stripping
        mask = data > (data.mean() + 0.5 * data.std())
        result = data * mask

        span.set_attribute("output.nonzero_voxels", int(np.count_nonzero(result)))

        return result
```

4. **Rebuild and test**:
   ```bash
   cd app && pip install -e . && cd ..
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

5. **View the trace** in Grafana and see your new attributes!

---

## Real-World Scenarios

### Scenario 1: Finding Slow Requests

**Problem**: "Some file processing takes 10 seconds, most take 2 seconds. Why?"

**Solution with traces**:
1. Query Tempo for traces with `duration > 5s`
2. Compare slow traces to fast traces
3. Identify which span is slower in slow traces
4. Check span attributes to find patterns (e.g., file size, specific processing stages)

**Example finding**: "Large files (>10MB) are slow in the `skull_strip` stage"

---

### Scenario 2: Debugging Errors

**Problem**: "Processing failed for sub-042. What went wrong?"

**Solution with traces**:
1. Search logs for "sub-042" to find the trace_id
2. Open that trace in Tempo
3. See which span has status=ERROR
4. View the exception details
5. Check attributes for context (file path, size, etc.)

**Example finding**: "Out of memory during `bias_correction` for 500MB file"

---

### Scenario 3: Understanding Execution Flow

**Problem**: "I'm new to the codebase. How does file processing work?"

**Solution with traces**:
1. Process a file
2. View the trace
3. See the complete execution flow visually
4. Understand which operations happen in sequence vs. parallel

**Result**: A visual map of how your code executes!

---

## Key Takeaways

1. **Trace** = Complete journey of a request (linked by trace_id)
2. **Span** = Single operation within a trace (identified by span_id)
3. **Parent-child relationships** create hierarchy via parent_id
4. **Attributes** provide context (key-value pairs)
5. **Events** mark important moments during a span
6. **Status** indicates success or failure
7. **Context propagation** automatically links spans
8. **Waterfall diagrams** visualize traces in Grafana

---

## Quiz

1. **What's the difference between a trace and a span?**
   <details>
   <summary>Click to see answer</summary>
   A trace is the entire journey of a request (all operations), while a span is a single operation within that trace.
   </details>

2. **How does a span know its parent?**
   <details>
   <summary>Click to see answer</summary>
   Each span has a parent_id field that references the span_id of its parent. OpenTelemetry handles this automatically via context propagation.
   </details>

3. **What are span attributes used for?**
   <details>
   <summary>Click to see answer</summary>
   Attributes provide metadata about the operation (file path, size, etc.) and enable filtering and searching traces in Grafana.
   </details>

4. **When should you create a new span?**
   <details>
   <summary>Click to see answer</summary>
   For operations that take >10ms or are important for understanding the system. Not for trivial operations like simple arithmetic.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand distributed tracing!

**Next**: [Lesson 4: Metrics Deep Dive →](04-metrics-deep-dive.md)

In the next lesson, you'll learn:
- The three types of metrics: Counters, Gauges, Histograms
- When to use each type
- How to record and query metrics
- Aggregations and percentiles

---

**Progress**: ✅ Lessons 1-3 complete | ⬜ 11 lessons remaining
