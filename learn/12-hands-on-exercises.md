# Lesson 12: Hands-On Exercises

**Estimated time**: 90-120 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Build custom Grafana dashboards
✅ Create alerts for important events
✅ Implement trace sampling
✅ Practice debugging with observability
✅ Apply everything you've learned

---

## Overview

This lesson is **100% hands-on**. You'll complete 8 practical exercises that simulate real-world scenarios.

**Prerequisites**:
- Docker running
- Stack started (`docker-compose up -d`)
- Completed Lessons 1-11

---

## Exercise 1: Build a Custom Dashboard

**Goal**: Create a Grafana dashboard for monitoring file processing.

### Step 1: Create a New Dashboard

1. **Open Grafana**: http://localhost:3000
2. **Navigate**: Dashboards → New → New Dashboard
3. **Click**: "Add visualization"

---

### Step 2: Add Panel - Total Files Processed

1. **Select datasource**: Prometheus
2. **Query**:
   ```promql
   sum(neuro_files_processed_total)
   ```
3. **Panel title**: "Total Files Processed"
4. **Visualization**: Stat
5. **Unit**: none
6. **Click**: Apply

---

### Step 3: Add Panel - Processing Rate

1. **Add another panel**
2. **Query**:
   ```promql
   rate(neuro_files_processed_total[5m])
   ```
3. **Panel title**: "Files Per Second"
4. **Visualization**: Time series
5. **Unit**: ops/sec (Operations per second)
6. **Legend**: `{{status}}` (shows success vs failed)
7. **Click**: Apply

---

### Step 4: Add Panel - P95 Duration

1. **Add another panel**
2. **Query**:
   ```promql
   histogram_quantile(0.95,
     sum by (le) (rate(neuro_process_duration_seconds_bucket[5m]))
   )
   ```
3. **Panel title**: "P95 Processing Duration"
4. **Visualization**: Time series
5. **Unit**: seconds (s)
6. **Thresholds**:
   - Green: < 3s
   - Yellow: 3s - 5s
   - Red: > 5s
7. **Click**: Apply

---

### Step 5: Add Panel - Error Rate

1. **Add another panel**
2. **Query**:
   ```promql
   (
     rate(neuro_files_processed_total{status="failed"}[5m])
     /
     rate(neuro_files_processed_total[5m])
   ) * 100
   ```
3. **Panel title**: "Error Rate %"
4. **Visualization**: Gauge
5. **Unit**: percent (0-100)
6. **Thresholds**:
   - Green: < 1%
   - Yellow: 1% - 5%
   - Red: > 5%
7. **Click**: Apply

---

### Step 6: Add Panel - Recent Logs

1. **Add another panel**
2. **Select datasource**: Loki
3. **Query**:
   ```logql
   {service_name="neuro-preprocess"} | json | line_format "{{.timestamp}} [{{.level}}] {{.message}}"
   ```
4. **Panel title**: "Recent Logs"
5. **Visualization**: Logs
6. **Options**: Enable live streaming (auto-refresh)
7. **Click**: Apply

---

### Step 7: Save Dashboard

1. **Click**: Save dashboard (icon in top right)
2. **Name**: "File Processing Monitor"
3. **Click**: Save

---

### Step 8: Test Your Dashboard

1. **Process some files**:
   ```bash
   ./scripts/run_demo.sh normal
   ```

2. **Watch your dashboard** update in real-time!

---

## Exercise 2: Create an Alert

**Goal**: Alert when error rate exceeds 10%.

### Step 1: Create Alert Rule

1. **Navigate**: Alerting → Alert rules → New alert rule

---

### Step 2: Configure Query

1. **Name**: "High Error Rate"
2. **Select datasource**: Prometheus
3. **Query A**:
   ```promql
   (
     rate(neuro_files_processed_total{status="failed"}[5m])
     /
     rate(neuro_files_processed_total[5m])
   ) * 100
   ```
4. **Condition**: WHEN last() OF A IS ABOVE 10

---

### Step 3: Set Evaluation

1. **Folder**: Create new "Alerts"
2. **Evaluation group**: Create new "file-processing"
3. **Evaluation interval**: 1m (check every minute)
4. **Pending period**: 2m (alert after 2 minutes)

---

### Step 4: Add Annotations

1. **Summary**: "Error rate is {{ $value }}%"
2. **Description**:
   ```
   File processing error rate has exceeded 10%.
   Current rate: {{ $value }}%
   Check logs and traces for details.
   ```

---

### Step 5: Save Alert

1. **Click**: Save rule and exit

---

### Step 6: Test the Alert

1. **Generate errors** (modify code to fail):
   ```bash
   # Process files that will fail
   ./scripts/run_demo.sh stress
   ```

2. **Wait 2-3 minutes**

3. **Check**: Alerting → Alert rules
   - Should show "Firing" when error rate > 10%

---

## Exercise 3: Implement Trace Sampling

**Goal**: Sample 50% of traces to reduce storage.

### Step 1: Modify App Configuration

1. **Open**: `app/neuro_preprocess/telemetry.py`

2. **Add sampling**:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

def setup_telemetry():
    # Create tracer provider with sampling
    provider = TracerProvider(
        sampler=TraceIdRatioBased(0.5),  # Keep 50% of traces
        resource=Resource.create({
            "service.name": "neuro-preprocess",
            "service.version": "1.0.0"
        })
    )

    # Rest of setup...
```

---

### Step 2: Test Sampling

1. **Rebuild**:
   ```bash
   cd app && pip install -e . && cd ..
   ```

2. **Process 20 files**:
   ```bash
   ./scripts/run_demo.sh batch
   ```

3. **Check Tempo**: Search for traces
   - Should see ~10 traces (50% of 20)

4. **Check Prometheus**: Metrics still show all 20
   - Sampling affects traces only, not metrics!

---

## Exercise 4: Debug a Slow Request

**Goal**: Find and fix a performance bottleneck.

### Scenario

You notice some file processing requests are very slow (>5 seconds).

### Step 1: Find Slow Requests (Metrics)

1. **Open Grafana**: Prometheus datasource

2. **Query**:
   ```promql
   histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[10m]))
   ```

3. **Result**: P95 = 5.2s (some requests are slow!)

---

### Step 2: Find Slow Traces

1. **Switch to Tempo**

2. **TraceQL**:
   ```traceql
   {duration > 5s}
   ```

3. **Find traces** that took > 5 seconds

4. **Click one** to open

---

### Step 3: Analyze the Trace

1. **Look at the waterfall diagram**

2. **Identify**:
   - Which span took the longest?
   - Is it `skull_strip`, `bias_correction`, or `normalization`?

3. **Check span attributes**:
   - What's the `file_size_mb`?
   - Any warnings or errors?

---

### Step 4: Correlate with Logs

1. **Click**: "Logs for this span" (or use trace_id)

2. **Query in Loki**:
   ```logql
   {service_name="neuro-preprocess"} | json | trace_id="<paste_trace_id>"
   ```

3. **Look for**:
   - Warnings about large files
   - Memory pressure
   - Any errors

---

### Step 5: Hypothesis

Based on your findings:
- **If** large files are slow → Need to optimize for large files
- **If** `skull_strip` is slow → Optimize skull_strip algorithm
- **If** memory warnings → Increase memory or add streaming

**Document your findings!**

---

## Exercise 5: Create a Service Level Indicator (SLI)

**Goal**: Define and monitor "95% of requests complete in < 3 seconds".

### Step 1: Define the SLI

**SLI**: Percentage of requests faster than 3 seconds

**PromQL**:

```promql
(
  sum(rate(neuro_process_duration_seconds_bucket{le="3.0"}[5m]))
  /
  sum(rate(neuro_process_duration_seconds_count[5m]))
) * 100
```

---

### Step 2: Create Dashboard Panel

1. **Add panel** to your dashboard

2. **Query**: Use the SLI query above

3. **Panel title**: "SLI: % Requests < 3s"

4. **Visualization**: Gauge

5. **Unit**: percent (0-100)

6. **Thresholds**:
   - Red: < 90%
   - Yellow: 90% - 95%
   - Green: > 95%

7. **Target**: 95% (draw a line at 95)

---

### Step 3: Monitor SLI

1. **Process files**:
   ```bash
   ./scripts/run_demo.sh normal
   ```

2. **Watch the SLI**:
   - Are you meeting the 95% target?
   - If not, what needs optimization?

---

## Exercise 6: Build a "RED Dashboard"

**Goal**: Create a dashboard with Rate, Errors, Duration (RED metrics).

### The RED Method

- **Rate**: Requests per second
- **Errors**: Error percentage
- **Duration**: P50, P95, P99 latency

---

### Step 1: Create New Dashboard

1. **Create**: "RED Metrics Dashboard"

---

### Step 2: Add Rate Panel

**Query**:
```promql
sum(rate(neuro_files_processed_total[5m]))
```

**Title**: "Request Rate (files/sec)"
**Visualization**: Time series
**Unit**: ops/sec

---

### Step 3: Add Errors Panel

**Query**:
```promql
(
  rate(neuro_files_processed_total{status="failed"}[5m])
  /
  rate(neuro_files_processed_total[5m])
) * 100
```

**Title**: "Error Rate %"
**Visualization**: Time series
**Unit**: percent

---

### Step 4: Add Duration Panel (3 Percentiles)

**Query A (P50)**:
```promql
histogram_quantile(0.50, sum by (le) (rate(neuro_process_duration_seconds_bucket[5m])))
```

**Query B (P95)**:
```promql
histogram_quantile(0.95, sum by (le) (rate(neuro_process_duration_seconds_bucket[5m])))
```

**Query C (P99)**:
```promql
histogram_quantile(0.99, sum by (le) (rate(neuro_process_duration_seconds_bucket[5m])))
```

**Title**: "Duration (P50, P95, P99)"
**Visualization**: Time series
**Unit**: seconds
**Legend**: `P50`, `P95`, `P99`

---

### Step 5: Test the Dashboard

1. **Run**: `./scripts/run_demo.sh normal`
2. **Watch** all three metrics update
3. **Observe** the relationship between rate, errors, and duration

---

## Exercise 7: Implement Tail-Based Sampling (Collector)

**Goal**: Keep all error traces, sample only 10% of successful traces.

### Step 1: Add Tail Sampling Processor

**Edit**: `configs/otel-collector-config.yaml`

```yaml
processors:
  batch:
    timeout: 1s

  # Add tail sampling
  tail_sampling:
    decision_wait: 10s  # Wait to see full trace
    num_traces: 1000
    policies:
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]  # Keep all errors
      - name: slow
        type: latency
        latency:
          threshold_ms: 5000  # Keep all slow traces
      - name: sample_rest
        type: probabilistic
        probabilistic:
          sampling_percentage: 10  # Sample 10% of the rest

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling, batch]  # Add tail_sampling
      exporters: [otlp]
```

---

### Step 2: Restart Collector

```bash
docker-compose restart otel-collector
```

---

### Step 3: Test

1. **Process mix of files**:
   ```bash
   ./scripts/run_demo.sh stress  # Generates errors
   ```

2. **Check Tempo**:
   - All error traces should be present
   - Only ~10% of successful traces kept

3. **Verify**: Query Tempo:
   ```traceql
   {status = error}
   ```
   All errors should appear.

---

## Exercise 8: Build a Troubleshooting Workflow

**Goal**: Practice the full workflow: Metrics → Traces → Logs.

### Scenario

Your monitoring shows an alert: "High Error Rate"

---

### Step 1: Check Metrics (What's Wrong?)

1. **Open Grafana → Prometheus**

2. **Query error rate**:
   ```promql
   rate(neuro_files_processed_total{status="failed"}[5m])
   ```

3. **Observe**: Spike in errors at 14:30

---

### Step 2: Check Traces (Which Requests Failed?)

1. **Switch to Tempo**

2. **Search**:
   - Time range: 14:25 - 14:35
   - TraceQL: `{status = error}`

3. **Find failed traces**

4. **Click one** to open

5. **Identify**:
   - Which span failed?
   - What were the span attributes?
   - File path? File size?

---

### Step 3: Check Logs (Why Did It Fail?)

1. **Copy trace_id** from the trace

2. **Switch to Loki**

3. **Query**:
   ```logql
   {service_name="neuro-preprocess"} | json | trace_id="<paste_trace_id>"
   ```

4. **Find error logs**:
   - Look for ERROR level
   - Read the error message
   - Check stack trace if available

---

### Step 4: Root Cause Analysis

Based on your investigation:

1. **What caused the error?**
   - File not found?
   - Out of memory?
   - Invalid format?

2. **Is it a pattern?**
   - All errors for the same file?
   - All errors during same time period?
   - All errors for large files?

3. **How to fix?**
   - Add validation?
   - Increase memory?
   - Fix file handling?

---

### Step 5: Document Your Findings

Create a summary:

```
Incident Report: High Error Rate

Time: 14:30 - 14:35
Duration: 5 minutes
Impact: 15% error rate

Root Cause:
- Processing files > 500MB
- skull_strip step runs out of memory
- Files: sub-042, sub-099, sub-150

Evidence:
- Metric: error_rate spiked to 15%
- Traces: All failed in skull_strip span
- Logs: "MemoryError: cannot allocate array"

Resolution:
- Increase worker memory from 2GB to 4GB
- Add file size validation (reject > 500MB)
- Add retry with streaming mode for large files

Prevention:
- Add alert for large files
- Monitor memory usage
- Add file size distribution metric
```

---

## Bonus Exercise: Performance Testing

**Goal**: Measure system capacity.

### Step 1: Run Load Test

```bash
./scripts/load_test.sh 100  # Process 100 files
```

---

### Step 2: Monitor During Load

Open Grafana and watch:

1. **Request rate** (files/sec)
2. **Error rate** (%)
3. **P95 duration** (seconds)
4. **Memory usage** (if you added this metric)

---

### Step 3: Find Breaking Point

Run increasing loads:

```bash
./scripts/load_test.sh 50
./scripts/load_test.sh 100
./scripts/load_test.sh 200
./scripts/load_test.sh 500
```

**Observe**:
- At what point does error rate increase?
- At what point does P95 duration degrade?
- What's the maximum sustainable throughput?

---

### Step 4: Capacity Report

Document:

```
Load Test Results

Configuration:
- Workers: 1
- Memory: 2GB
- CPU: 2 cores

Results:
| Load (files) | Rate (files/sec) | Error Rate | P95 Duration |
|--------------|------------------|------------|--------------|
| 50           | 5.2              | 0%         | 2.1s         |
| 100          | 5.3              | 0%         | 2.3s         |
| 200          | 5.2              | 2%         | 3.5s         |
| 500          | 4.8              | 15%        | 8.2s         |

Findings:
- System handles up to 200 files without issues
- Beyond 200, error rate increases (memory pressure)
- Sustainable capacity: ~150 files (buffer for spikes)

Recommendations:
- Add horizontal scaling (more workers)
- Increase memory allocation
- Implement queue system for smoothing load spikes
```

---

## Key Takeaways

After completing these exercises, you should be able to:

1. ✅ Build custom Grafana dashboards
2. ✅ Create alerts for important metrics
3. ✅ Implement sampling strategies
4. ✅ Debug performance issues using traces
5. ✅ Follow the Metrics → Traces → Logs workflow
6. ✅ Perform load testing and capacity planning
7. ✅ Apply observability to real-world problems

---

## What You've Built

By now, you have:

- 📊 **Custom dashboard** monitoring file processing
- 🚨 **Alert rules** for error rates
- 🎯 **SLI tracking** (95% of requests < 3s)
- 📈 **RED dashboard** (Rate, Errors, Duration)
- 🔍 **Troubleshooting workflow** (end-to-end investigation)
- ⚡ **Load test results** (capacity planning)

---

## Next Steps

🎉 **Congratulations!** You've completed all hands-on exercises!

**Next**: [Lesson 13: Production Practices →](13-production-practices.md)

In the next lesson, you'll learn:
- Running observability in production
- Cost optimization strategies
- Retention policies
- Security best practices

---

**Progress**: ✅ Lessons 1-12 complete (Hands-On Done!) | ⬜ 2 lessons remaining
