# Lesson 4: Metrics Deep Dive

**Estimated time**: 45-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand the three main metric types (Counter, Gauge, Histogram)
✅ Know when to use each metric type
✅ Learn how to create and record metrics in code
✅ Understand aggregations, rates, and percentiles
✅ Know about cardinality and its impact

---

## What Are Metrics?

### The Simple Definition

**Metrics** are **numerical measurements** collected over time.

**Analogy**: Metrics are like your **car's dashboard**:

```
┌────────────────────────────────┐
│      CAR DASHBOARD             │
├────────────────────────────────┤
│ Speed:    65 mph    [Gauge]    │  Goes up and down
│ Odometer: 45,231 mi [Counter]  │  Always increases
│ Fuel:     50%       [Gauge]    │  Goes up and down
│ Trip:     142 mi    [Counter]  │  Always increases
└────────────────────────────────┘
```

Each measurement tells you something different about your car's state.

---

## The Three Main Metric Types

```
┌─────────────────────────────────┐
│         METRIC TYPES            │
├─────────────────────────────────┤
│                                 │
│  📈 Counter   (always up)       │
│  📊 Gauge     (up and down)     │
│  📉 Histogram (distributions)   │
│                                 │
└─────────────────────────────────┘
```

Let's explore each one in detail.

---

## Metric Type 1: Counter

### What Is a Counter?

A **counter** is a metric that **only goes up** (monotonically increasing).

**Examples**:
- Total files processed
- Total HTTP requests
- Total errors
- Total bytes sent

**Analogy**: Like an **odometer** in your car - it only increases, never decreases.

```
Time:  0s    10s   20s   30s   40s
       │     │     │     │     │
Files: 0 →→→ 5 →→→ 12 →→ 18 →→ 25
       └──────────────────────────→
            Always increasing
```

---

### Creating a Counter

```python
from opentelemetry import metrics

# Get a meter
meter = metrics.get_meter(__name__)

# Create a counter
files_counter = meter.create_counter(
    name="neuro.files.processed",
    description="Total number of files processed",
    unit="files"
)
```

### Recording Values

```python
# Add 1 to the counter
files_counter.add(1)

# Add multiple
files_counter.add(5)

# You can NEVER subtract (this will be ignored or error)
# files_counter.add(-1)  # ❌ Wrong!
```

**Key point**: Always use `add()` with positive numbers. Counters never decrease.

---

### Using Counters: Rate Calculations

**Raw counter values** aren't usually useful by themselves. You typically calculate the **rate of change**.

**Example**:

```
Counter value at 0s:  0 files
Counter value at 60s: 120 files

Rate = (120 - 0) / 60 = 2 files/second
```

**In Prometheus (PromQL)**:

```promql
# Calculate rate over the last 5 minutes
rate(neuro_files_processed_total[5m])
```

This gives you "files per second" rather than the raw count.

---

### Counter Best Practices

**Good counter names** (past tense or plural):
- `requests_total`
- `files_processed_total`
- `errors_total`
- `bytes_sent_total`

**Bad counter names**:
- `request` (not clear it's a count)
- `current_files` (sounds like a gauge)
- `process_file` (sounds like an action)

**Convention**: Prometheus counters often end with `_total`.

---

## Metric Type 2: Gauge

### What Is a Gauge?

A **gauge** is a metric that can **go up or down**.

**Examples**:
- Current memory usage
- Active connections
- Queue length
- Temperature

**Analogy**: Like a **speedometer** or **fuel gauge** - can increase or decrease.

```
Time:     0s    10s   20s   30s   40s
          │     │     │     │     │
Memory:   50 →→ 75 →→ 60 →→ 85 →→ 70 MB
          └──────────────────────────→
              Goes up and down
```

---

### Creating a Gauge

In OpenTelemetry, gauges are typically created using **Observables** (callback-based):

```python
from opentelemetry import metrics
import psutil

meter = metrics.get_meter(__name__)

# Callback function that returns the current value
def get_memory_usage():
    return psutil.Process().memory_info().rss / (1024 * 1024)  # MB

# Create observable gauge
memory_gauge = meter.create_observable_gauge(
    name="process.memory.usage",
    description="Current memory usage",
    unit="MB",
    callbacks=[lambda options: [Observation(get_memory_usage())]]
)
```

**Key difference**: You don't manually record values. The callback is called periodically, and it returns the **current value**.

---

### Alternative: UpDownCounter

For cases where you want to manually increment/decrement:

```python
# Create an up-down counter
queue_size = meter.create_up_down_counter(
    name="queue.size",
    description="Current queue size",
    unit="items"
)

# Increment when adding to queue
queue_size.add(1)

# Decrement when removing from queue
queue_size.add(-1)
```

---

### Using Gauges

**Gauges** are useful for:
- Current state (memory, CPU, queue size)
- Snapshots (active connections, running tasks)
- Levels (cache hit rate, disk usage)

**In Prometheus**:

```promql
# Current memory usage
process_memory_usage_bytes

# Average over last 5 minutes
avg_over_time(process_memory_usage_bytes[5m])
```

---

### Gauge Best Practices

**Good gauge names** (present tense):
- `memory_usage_bytes`
- `active_connections`
- `queue_length`
- `cpu_usage_percent`

**Bad gauge names**:
- `memory_total` (sounds like a counter)
- `connections_made` (sounds like a counter)

---

## Metric Type 3: Histogram

### What Is a Histogram?

A **histogram** records the **distribution** of values, not just individual measurements.

**Example**: File processing durations

```
10 files processed:
- 5 files took ~2 seconds
- 3 files took ~5 seconds
- 2 files took ~10 seconds

Histogram buckets:
  <= 1s:  0 files
  <= 2s:  5 files
  <= 5s:  8 files (5 + 3)
  <= 10s: 10 files (5 + 3 + 2)
```

**Why it matters**: You can calculate **percentiles** (P50, P95, P99).

**Analogy**: Like a **histogram chart** showing the distribution of test scores:

```
Students
10 │     █
 9 │     █
 8 │     █
 7 │     █     █
 6 │     █     █
 5 │ █   █     █
 4 │ █   █     █
 3 │ █   █     █
 2 │ █   █     █
 1 │ █   █     █
   └─────────────
     F   C     A
      Grades
```

---

### Creating a Histogram

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create a histogram
duration_histogram = meter.create_histogram(
    name="neuro.process.duration",
    description="File processing duration",
    unit="seconds"
)
```

### Recording Values

```python
import time

start = time.time()

# Do work
process_file(path)

duration = time.time() - start

# Record the duration
duration_histogram.record(duration)
```

**Each recording** is placed into buckets, allowing statistical analysis.

---

### Histogram Buckets

Histograms divide values into **buckets** (ranges):

**Example buckets** for duration:
```
  <= 0.1s  (bucket 1)
  <= 0.5s  (bucket 2)
  <= 1.0s  (bucket 3)
  <= 2.0s  (bucket 4)
  <= 5.0s  (bucket 5)
  <= 10.0s (bucket 6)
  +Inf     (bucket 7 - everything else)
```

**When you record 1.5s**:
- It goes into the "≤ 2.0s" bucket (and all larger buckets)

**Result in Prometheus**:

```promql
neuro_process_duration_bucket{le="0.1"}  = 0
neuro_process_duration_bucket{le="0.5"}  = 2
neuro_process_duration_bucket{le="1.0"}  = 5
neuro_process_duration_bucket{le="2.0"}  = 8  ← 1.5s falls here
neuro_process_duration_bucket{le="5.0"}  = 10
neuro_process_duration_bucket{le="10.0"} = 10
neuro_process_duration_bucket{le="+Inf"} = 10
```

---

### Calculating Percentiles

**P50 (median)**: 50% of values are below this
**P95**: 95% of values are below this (outliers excluded)
**P99**: 99% of values are below this (only 1% slower)

**In Prometheus**:

```promql
# P50 (median) processing duration
histogram_quantile(0.50, rate(neuro_process_duration_bucket[5m]))

# P95 (95th percentile)
histogram_quantile(0.95, rate(neuro_process_duration_bucket[5m]))

# P99 (99th percentile)
histogram_quantile(0.99, rate(neuro_process_duration_bucket[5m]))
```

**Why percentiles matter**:
- **Average** can be misleading (10 files at 1s, 1 file at 100s → avg = 10s)
- **P95** shows what most users experience (ignoring outliers)
- **P99** shows worst-case (still excluding top 1%)

---

### Histogram vs Counter vs Gauge

| Aspect | Counter | Gauge | Histogram |
|--------|---------|-------|-----------|
| **Direction** | Only up | Up and down | Distribution |
| **Example** | Total requests | Current memory | Request duration |
| **Question** | "How many?" | "How much right now?" | "What's the distribution?" |
| **Use** | Counts, totals | Current state | Latencies, sizes |
| **Aggregation** | Rate | Average, current | Percentiles |

---

## Metrics in Our Project

Let's look at our neuroimaging pipeline metrics:

### Counters

```python
# Total files processed (always increases)
self.files_counter = meter.create_counter(
    name="neuro.files.processed",
    description="Total files processed",
    unit="files"
)

# Total files failed (always increases)
self.errors_counter = meter.create_counter(
    name="neuro.files.failed",
    description="Total files failed",
    unit="files"
)

# Record
self.files_counter.add(1, {"status": "success"})
self.errors_counter.add(1, {"error_type": "out_of_memory"})
```

---

### Histograms

```python
# Processing duration distribution
self.duration_histogram = meter.create_histogram(
    name="neuro.process.duration",
    description="File processing duration",
    unit="seconds"
)

# File size distribution
self.file_size_histogram = meter.create_histogram(
    name="neuro.file.size",
    description="Input file size",
    unit="MB"
)

# Record
self.duration_histogram.record(2.5, {"stage": "total"})
self.file_size_histogram.record(4.9)
```

---

### Gauges (Observable)

```python
# Current files being processed
def get_active_files():
    return len(active_processing_tasks)

meter.create_observable_gauge(
    name="neuro.processing.current",
    description="Files currently being processed",
    callbacks=[lambda options: [Observation(get_active_files())]]
)
```

---

## Metric Attributes (Labels)

**Attributes** (also called **labels** in Prometheus) add dimensions to metrics.

### Without Attributes

```python
files_counter.add(1)
```

**Result**: One time series

```promql
neuro_files_processed_total = 42
```

---

### With Attributes

```python
files_counter.add(1, {"status": "success", "format": "nifti"})
files_counter.add(1, {"status": "failed", "format": "dicom"})
```

**Result**: Multiple time series (one per unique combination)

```promql
neuro_files_processed_total{status="success", format="nifti"} = 35
neuro_files_processed_total{status="failed", format="nifti"}  = 5
neuro_files_processed_total{status="success", format="dicom"} = 2
```

**You can now query**:

```promql
# Only successful files
neuro_files_processed_total{status="success"}

# Only failures
neuro_files_processed_total{status="failed"}

# Only nifti files
neuro_files_processed_total{format="nifti"}
```

---

### Cardinality Warning

**Cardinality** = Number of unique time series

**Problem**: High cardinality = expensive storage and slow queries

**Example**:

```python
# ❌ BAD: user_id has thousands of unique values
files_counter.add(1, {"user_id": "user_12345"})

# ✅ GOOD: status has only 2-3 values
files_counter.add(1, {"status": "success"})
```

**Rule of thumb**: Attributes should have **low cardinality** (< 100 unique values).

**Good attributes**:
- `status` (success, failed, timeout)
- `environment` (dev, staging, prod)
- `version` (v1.0, v1.1, v1.2)

**Bad attributes** (high cardinality):
- `user_id` (thousands of users)
- `file_path` (every file is unique)
- `timestamp` (every second is unique)

---

## Aggregations and Queries

### Rate (for Counters)

**Question**: "How many files per second are we processing?"

```promql
# Files per second over last 5 minutes
rate(neuro_files_processed_total[5m])
```

**Result**: `2.5` (files/sec)

---

### Sum (across labels)

**Question**: "Total files processed across all statuses?"

```promql
sum(neuro_files_processed_total)
```

**Result**: `42`

---

### Average (for Gauges/Histograms)

**Question**: "Average memory usage over last hour?"

```promql
avg_over_time(process_memory_usage_bytes[1h])
```

---

### Percentiles (for Histograms)

**Question**: "What's the P95 processing time?"

```promql
histogram_quantile(0.95, rate(neuro_process_duration_bucket[5m]))
```

**Result**: `3.2` seconds (95% of files finish in ≤3.2s)

---

## Real Example from Our Project

From `app/neuro_preprocess/pipeline.py`:

```python
def process_file(self, filepath: str) -> dict:
    """Process a single file with full telemetry."""

    start_time = time.time()

    with self.tracer.start_as_current_span("process_file") as span:
        try:
            # Load file
            loader_result = self.loader.load(filepath)
            data = loader_result['data']

            # Record file size (histogram)
            self.file_size_histogram.record(
                loader_result['file_size_mb'],
                {"format": "nifti"}
            )

            # Process image
            processed = self.processor.process_image(data)

            # Write output
            writer_result = self.writer.write(processed, output_path)

            # Record duration (histogram)
            duration = time.time() - start_time
            self.duration_histogram.record(
                duration,
                {"status": "success"}
            )

            # Increment success counter
            self.files_counter.add(1, {"status": "success"})

            return {"status": "success", "duration": duration}

        except Exception as e:
            # Record duration (histogram)
            duration = time.time() - start_time
            self.duration_histogram.record(
                duration,
                {"status": "failed"}
            )

            # Increment error counter
            self.errors_counter.add(1, {"error_type": type(e).__name__})

            raise
```

**This generates**:
- **Counter**: `neuro_files_processed_total{status="success"}` = 1
- **Counter**: `neuro_files_failed_total{error_type="MemoryError"}` = 0
- **Histogram**: `neuro_process_duration_bucket` with value 2.5s
- **Histogram**: `neuro_file_size_bucket` with value 4.9 MB

---

## Try It Yourself

### Exercise 1: View Metrics in Prometheus

1. **Start the stack**:
   ```bash
   docker-compose up -d
   ```

2. **Generate metrics**:
   ```bash
   ./scripts/run_demo.sh normal
   ```

3. **Open Prometheus**: http://localhost:9090

4. **Try these queries**:

   **Total files processed**:
   ```promql
   neuro_files_processed_total
   ```

   **Files per second** (rate):
   ```promql
   rate(neuro_files_processed_total[5m])
   ```

   **P50 (median) duration**:
   ```promql
   histogram_quantile(0.50, rate(neuro_process_duration_seconds_bucket[5m]))
   ```

   **P95 duration**:
   ```promql
   histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))
   ```

---

### Exercise 2: Understand Histogram Buckets

1. **Query histogram buckets**:
   ```promql
   neuro_process_duration_seconds_bucket
   ```

2. **Answer**:
   - How many buckets are there?
   - What are the bucket boundaries (le labels)?
   - How many samples fell into the "≤2.0s" bucket?

---

### Exercise 3: Add a Custom Metric

1. **Open**: `app/neuro_preprocess/processor.py`

2. **Add a counter** for each processing stage:

```python
# In __init__
self.stage_counter = meter.create_counter(
    name="neuro.stages.executed",
    description="Number of times each stage executed",
    unit="executions"
)

# In process_image method
if "skull_strip" in self.stages:
    with self.tracer.start_as_current_span("skull_strip"):
        result = self._skull_strip(result)
        self.stage_counter.add(1, {"stage": "skull_strip"})  # ← Add this

if "bias_correction" in self.stages:
    with self.tracer.start_as_current_span("bias_correction"):
        result = self._bias_correction(result)
        self.stage_counter.add(1, {"stage": "bias_correction"})  # ← Add this
```

3. **Rebuild and test**:
   ```bash
   cd app && pip install -e . && cd ..
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

4. **Query in Prometheus**:
   ```promql
   neuro_stages_executed_total
   ```

---

## Real-World Scenarios

### Scenario 1: Performance Regression

**Problem**: "Processing is slower than last week."

**Solution with metrics**:

```promql
# Compare P95 duration this week vs last week
histogram_quantile(0.95, rate(neuro_process_duration_bucket[7d]))
```

**Result**: "P95 was 2s last week, now it's 5s" → Performance regression!

---

### Scenario 2: Error Rate Spike

**Problem**: "Are we seeing more errors?"

**Solution with metrics**:

```promql
# Error rate over time
rate(neuro_files_failed_total[5m])

# Error percentage
rate(neuro_files_failed_total[5m]) / rate(neuro_files_processed_total[5m]) * 100
```

**Result**: "Error rate jumped from 1% to 10%" → Investigate recent changes!

---

### Scenario 3: Capacity Planning

**Problem**: "How many files can we process per day?"

**Solution with metrics**:

```promql
# Current throughput (files/sec)
rate(neuro_files_processed_total[1h])

# Extrapolate to daily
rate(neuro_files_processed_total[1h]) * 86400
```

**Result**: "At current rate, we can handle 200,000 files/day"

---

## Key Takeaways

1. **Three metric types**:
   - **Counter**: Always increases (use for totals, counts)
   - **Gauge**: Up and down (use for current state)
   - **Histogram**: Distributions (use for durations, sizes)

2. **Use rates** for counters (not raw values)
3. **Use percentiles** for histograms (P50, P95, P99)
4. **Attributes** add dimensions but increase cardinality
5. **Low cardinality** is critical (< 100 unique values per attribute)
6. **Histograms** enable statistical analysis without storing every value

---

## Quiz

1. **When should you use a Counter vs a Gauge?**
   <details>
   <summary>Click to see answer</summary>
   Use a Counter for values that only increase (total requests, files processed). Use a Gauge for values that go up and down (memory usage, active connections).
   </details>

2. **Why use histograms instead of just recording every value?**
   <details>
   <summary>Click to see answer</summary>
   Histograms are space-efficient (store buckets, not individual values) and enable percentile calculations without keeping all data points.
   </details>

3. **What is cardinality and why does it matter?**
   <details>
   <summary>Click to see answer</summary>
   Cardinality is the number of unique time series (unique combinations of metric + labels). High cardinality increases storage costs and slows queries. Keep label values low (< 100 unique values).
   </details>

4. **What does P95 latency mean?**
   <details>
   <summary>Click to see answer</summary>
   P95 means 95% of requests completed faster than this value. It's better than average for understanding user experience because it excludes outliers.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand metrics in depth!

**Next**: [Lesson 5: Structured Logging →](05-structured-logging.md)

In the next lesson, you'll learn:
- Structured vs unstructured logs
- Log levels and when to use them
- Correlating logs with traces
- Best practices for logging

---

**Progress**: ✅ Lessons 1-4 complete | ⬜ 10 lessons remaining
