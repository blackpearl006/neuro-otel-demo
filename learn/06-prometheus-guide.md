# Lesson 6: Prometheus Guide

**Estimated time**: 50-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand how Prometheus stores time-series data
✅ Learn the basics of PromQL query language
✅ Know the difference between scraping and pushing metrics
✅ Be able to write queries for our project metrics
✅ Understand labels, aggregations, and functions

---

## What Is Prometheus?

### The Simple Definition

**Prometheus** is an **open-source time-series database** and monitoring system designed for storing and querying **metrics**.

**Analogy**: Prometheus is like a **stock market tracker**:
- Records stock prices over time (time-series data)
- Lets you query historical data ("What was Apple's stock price last week?")
- Provides aggregations ("What's the average price over 30 days?")
- Alerts when thresholds are crossed ("Alert me if price drops 10%")

---

## Time-Series Data Model

### What Is a Time Series?

A **time series** is a sequence of numerical data points indexed by time.

**Example**: CPU usage over time

```
Time                CPU Usage
─────────────────────────────
2025-11-20 14:00:00   45%
2025-11-20 14:01:00   52%
2025-11-20 14:02:00   48%
2025-11-20 14:03:00   61%
2025-11-20 14:04:00   55%
```

**Plotted**:

```
CPU %
 70│
 60│              ●
 50│     ●              ●
 40│ ●       ●
 30│
 20│
   └────────────────────────→ Time
     14:00  14:01  14:02  14:03  14:04
```

---

### Prometheus Data Model

Each time series in Prometheus is identified by:

1. **Metric name**: What you're measuring (`cpu_usage`)
2. **Labels**: Dimensions that distinguish different instances
3. **Timestamp**: When the measurement was taken
4. **Value**: The numerical measurement

**Format**:

```
metric_name{label1="value1", label2="value2"} value timestamp
```

**Example**:

```
# Two different time series for the same metric
http_requests_total{method="GET", status="200"} 1234 1637427600
http_requests_total{method="POST", status="200"} 456 1637427600
http_requests_total{method="GET", status="500"} 12 1637427600
```

**Each unique combination of metric name + labels = One time series**

---

### Labels: The Power of Dimensions

**Labels** add dimensions to your metrics, allowing you to slice and dice data.

**Example from our project**:

```
neuro_files_processed_total{status="success"} 95
neuro_files_processed_total{status="failed"} 5
```

**You can now query**:
- Total files: `sum(neuro_files_processed_total)` = 100
- Only successful: `neuro_files_processed_total{status="success"}` = 95
- Success rate: `rate(neuro_files_processed_total{status="success"}[5m])` / `rate(neuro_files_processed_total[5m])`

---

### Label Cardinality (Revisited)

**Cardinality** = Number of unique time series

**Example 1: Low cardinality** (Good ✅)

```
http_requests_total{method="GET"}   # 1 time series
http_requests_total{method="POST"}  # 1 time series
http_requests_total{method="PUT"}   # 1 time series
Total: 3 time series
```

**Example 2: High cardinality** (Bad ❌)

```
http_requests_total{user_id="user_001"}  # 1 time series
http_requests_total{user_id="user_002"}  # 1 time series
...
http_requests_total{user_id="user_999999"}  # 1 time series
Total: 999,999 time series  ← Explodes storage!
```

**Rule**: Keep label values **low cardinality** (< 100 unique values per label).

---

## Scraping vs. Pushing Metrics

### Pull Model: Scraping (Prometheus Default)

**How it works**: Prometheus **pulls** (scrapes) metrics from your application.

```
┌─────────────┐            HTTP GET /metrics           ┌─────────────┐
│             │  ────────────────────────────────────→  │             │
│ Prometheus  │                                         │ Application │
│             │  ←────────────────────────────────────  │             │
└─────────────┘    Returns metrics in text format      └─────────────┘
```

**Configuration** (`configs/prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'otel-collector'
    scrape_interval: 15s  # Scrape every 15 seconds
    static_configs:
      - targets: ['otel-collector:8889']
```

**Every 15 seconds**, Prometheus requests metrics from `otel-collector:8889/metrics`.

---

### Push Model: Remote Write (Used in Our Project)

**How it works**: Application **pushes** metrics to Prometheus.

```
┌─────────────┐            OTLP (gRPC)                ┌─────────────┐
│             │  ←────────────────────────────────────  │             │
│ Prometheus  │                                         │ Application │
│             │                                         │             │
└─────────────┘                                        └─────────────┘
       ▲
       │
       │ Receives metrics via OTel Collector
       │
┌──────┴──────┐
│ OTel        │
│ Collector   │
└─────────────┘
```

**In our project**:
1. App sends metrics to OTel Collector (OTLP)
2. Collector exports to Prometheus exporter endpoint
3. Prometheus scrapes from Collector's exporter

**Why?** Decoupling - app doesn't need to know about Prometheus, only OTel Collector.

---

## PromQL: Prometheus Query Language

**PromQL** is the query language for retrieving and manipulating time-series data.

### Basic Queries

#### 1. Select a Metric

```promql
# Get current value
neuro_files_processed_total
```

**Returns**:

```
neuro_files_processed_total{status="success"} 95
neuro_files_processed_total{status="failed"} 5
```

---

#### 2. Filter by Labels

```promql
# Only successful files
neuro_files_processed_total{status="success"}

# Only failed files
neuro_files_processed_total{status="failed"}

# Multiple conditions (AND)
neuro_files_processed_total{status="success", format="nifti"}
```

---

#### 3. Label Matching Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Exact match | `status="success"` |
| `!=` | Not equal | `status!="failed"` |
| `=~` | Regex match | `status=~"success\|pending"` |
| `!~` | Regex not match | `status!~"failed\|error"` |

**Examples**:

```promql
# Status is "success" or "pending"
neuro_files_processed_total{status=~"success|pending"}

# Status is NOT "failed"
neuro_files_processed_total{status!="failed"}
```

---

### Time Ranges and Rates

#### Instant Vector vs. Range Vector

**Instant vector**: Value at a single point in time (now)

```promql
neuro_files_processed_total
```

**Range vector**: Values over a time range

```promql
neuro_files_processed_total[5m]
# Values from the last 5 minutes
```

**Time units**: `s` (seconds), `m` (minutes), `h` (hours), `d` (days)

---

#### Rate: Calculate Per-Second Rate

**Remember**: Counters always increase. To get meaningful data, calculate the **rate of change**.

```promql
# Files per second over last 5 minutes
rate(neuro_files_processed_total[5m])
```

**Example**:

```
Counter at t=0:    0 files
Counter at t=300:  150 files

Rate = (150 - 0) / 300 = 0.5 files/second
```

---

#### Increase: Total Increase Over Time

```promql
# Total files processed in the last 1 hour
increase(neuro_files_processed_total[1h])
```

**Example**:

```
Counter at t=0:    100 files
Counter at t=3600: 250 files

Increase = 250 - 100 = 150 files
```

---

### Aggregation Functions

**Combine multiple time series** into one.

#### sum: Add Them Up

```promql
# Total files processed (all statuses)
sum(neuro_files_processed_total)
```

---

#### avg: Average

```promql
# Average processing duration across all stages
avg(neuro_process_duration_seconds)
```

---

#### min / max

```promql
# Minimum processing duration
min(neuro_process_duration_seconds)

# Maximum processing duration
max(neuro_process_duration_seconds)
```

---

#### count: How Many Time Series

```promql
# How many different status labels exist?
count(neuro_files_processed_total)
```

---

#### Aggregation with "by"

**Group by** specific labels:

```promql
# Sum by status (shows separate sums for success vs failed)
sum by (status) (neuro_files_processed_total)
```

**Returns**:

```
{status="success"} 95
{status="failed"} 5
```

---

#### Aggregation with "without"

**Group by** everything except specific labels:

```promql
# Sum everything except instance
sum without (instance) (neuro_files_processed_total)
```

---

### Histogram Queries (Percentiles)

**Remember**: Histograms store data in buckets with `_bucket` suffix.

#### Quantile: Calculate Percentiles

```promql
# P50 (median) processing duration
histogram_quantile(
  0.50,
  rate(neuro_process_duration_seconds_bucket[5m])
)

# P95 (95th percentile)
histogram_quantile(
  0.95,
  rate(neuro_process_duration_seconds_bucket[5m])
)

# P99 (99th percentile)
histogram_quantile(
  0.99,
  rate(neuro_process_duration_seconds_bucket[5m])
)
```

**Interpretation**:
- P50 = 2.0s → 50% of files process in ≤2.0s
- P95 = 3.5s → 95% of files process in ≤3.5s
- P99 = 5.0s → 99% of files process in ≤5.0s

---

### Arithmetic Operations

#### Basic Math

```promql
# Success rate (percentage)
rate(neuro_files_processed_total{status="success"}[5m])
/
rate(neuro_files_processed_total[5m])
* 100

# Average file size
sum(neuro_file_size_bytes) / sum(neuro_files_processed_total)
```

---

#### Comparison Operators

```promql
# Find metrics where duration > 5 seconds
neuro_process_duration_seconds > 5

# Find metrics where error rate > 10%
(rate(neuro_files_failed_total[5m]) / rate(neuro_files_processed_total[5m]) * 100) > 10
```

---

### Time Offset

Query data from the past:

```promql
# Files processed now
neuro_files_processed_total

# Files processed 1 hour ago
neuro_files_processed_total offset 1h

# Files processed yesterday
neuro_files_processed_total offset 1d
```

**Compare current vs. past**:

```promql
# Difference from 1 hour ago
neuro_files_processed_total - (neuro_files_processed_total offset 1h)
```

---

## Common PromQL Patterns

### Pattern 1: Availability (Uptime)

```promql
# Is the service up?
up{job="neuro-preprocess"}

# Percentage uptime over last 24 hours
avg_over_time(up{job="neuro-preprocess"}[24h]) * 100
```

---

### Pattern 2: Request Rate (QPS)

```promql
# Requests per second
rate(http_requests_total[5m])

# Requests per minute
rate(http_requests_total[5m]) * 60
```

---

### Pattern 3: Error Rate

```promql
# Errors per second
rate(neuro_files_failed_total[5m])

# Error percentage
rate(neuro_files_failed_total[5m])
/
rate(neuro_files_processed_total[5m])
* 100
```

---

### Pattern 4: Latency Percentiles

```promql
# P50, P95, P99 (three separate queries)
histogram_quantile(0.50, rate(neuro_process_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(neuro_process_duration_seconds_bucket[5m]))
```

---

### Pattern 5: Top N

```promql
# Top 5 slowest stages
topk(5, neuro_process_duration_seconds)

# Bottom 5 (fastest)
bottomk(5, neuro_process_duration_seconds)
```

---

## Real Queries for Our Project

### Query 1: Total Files Processed

```promql
sum(neuro_files_processed_total)
```

**Result**: `100` (total across all statuses)

---

### Query 2: Files Per Second

```promql
sum(rate(neuro_files_processed_total[5m]))
```

**Result**: `2.5` (files/second)

---

### Query 3: Success Rate

```promql
sum(rate(neuro_files_processed_total{status="success"}[5m]))
/
sum(rate(neuro_files_processed_total[5m]))
* 100
```

**Result**: `95` (95% success rate)

---

### Query 4: P95 Processing Duration

```promql
histogram_quantile(
  0.95,
  sum by (le) (rate(neuro_process_duration_seconds_bucket[5m]))
)
```

**Result**: `3.2` (95% of files finish in ≤3.2 seconds)

---

### Query 5: Average File Size

```promql
avg(neuro_file_size_megabytes)
```

**Result**: `4.5` (MB)

---

### Query 6: Errors in Last Hour

```promql
increase(neuro_files_failed_total[1h])
```

**Result**: `5` (5 errors in the last hour)

---

### Query 7: Processing Rate by Stage

```promql
sum by (stage) (rate(neuro_stages_executed_total[5m]))
```

**Result**:

```
{stage="skull_strip"} 2.5
{stage="bias_correction"} 2.5
{stage="normalization"} 2.5
```

---

## Try It Yourself

### Exercise 1: Explore Prometheus UI

1. **Open Prometheus**: http://localhost:9090

2. **Navigate to Graph tab**

3. **Try these queries**:

   a. View all metrics:
   ```promql
   {job="otel-collector"}
   ```

   b. Total files processed:
   ```promql
   neuro_files_processed_total
   ```

   c. Files per second:
   ```promql
   rate(neuro_files_processed_total[5m])
   ```

4. **Switch between "Table" and "Graph" views**

---

### Exercise 2: Calculate Success Rate

1. **Process some files** (mix of success and failure):
   ```bash
   ./scripts/run_demo.sh normal
   ```

2. **Query in Prometheus**:

   Success count:
   ```promql
   neuro_files_processed_total{status="success"}
   ```

   Total count:
   ```promql
   sum(neuro_files_processed_total)
   ```

   Success rate:
   ```promql
   neuro_files_processed_total{status="success"}
   /
   sum(neuro_files_processed_total)
   * 100
   ```

3. **What's your success rate?**

---

### Exercise 3: Find Slow Processing

1. **Query P95 duration**:
   ```promql
   histogram_quantile(0.95, rate(neuro_process_duration_seconds_bucket[10m]))
   ```

2. **Query P99 duration**:
   ```promql
   histogram_quantile(0.99, rate(neuro_process_duration_seconds_bucket[10m]))
   ```

3. **Compare**: How much slower is P99 than P95?

---

### Exercise 4: Time Comparison

1. **Process files now**:
   ```bash
   ./scripts/run_demo.sh normal
   ```

2. **Wait 5 minutes**

3. **Process more files**:
   ```bash
   ./scripts/run_demo.sh normal
   ```

4. **Query**:

   Current rate:
   ```promql
   rate(neuro_files_processed_total[5m])
   ```

   Rate 5 minutes ago:
   ```promql
   rate(neuro_files_processed_total[5m] offset 5m)
   ```

5. **Compare**: Is processing rate increasing or decreasing?

---

## Prometheus Configuration

Let's look at our Prometheus config (`configs/prometheus.yml`):

```yaml
global:
  scrape_interval: 15s       # How often to scrape targets
  evaluation_interval: 15s   # How often to evaluate rules

scrape_configs:
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape OTel Collector
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

**What this does**:
- Every 15 seconds, Prometheus scrapes `http://otel-collector:8889/metrics`
- Metrics from our app flow: App → Collector → Prometheus

---

## Prometheus Storage

### How Data Is Stored

Prometheus stores data in **two places**:

1. **Memory**: Recent data (last ~2 hours) for fast queries
2. **Disk**: Historical data in compressed blocks

**Data directory**: `/prometheus` (in our Docker container)

---

### Retention

**Default**: Keep data for **15 days**

**Configure retention** in `docker-compose.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Keep for 30 days
    - '--storage.tsdb.retention.size=10GB' # Or until 10GB
```

---

### Data Compaction

Prometheus automatically **compresses** old data:

```
Recent data (2h blocks):    ~500 MB
Compacted data (2h → 12h):  ~200 MB
Compacted data (12h → 7d):  ~50 MB
```

**Result**: Efficient long-term storage.

---

## Key Takeaways

1. **Prometheus** stores time-series metrics data
2. **Data model**: metric_name{labels} value timestamp
3. **Labels** add dimensions (status, environment, etc.)
4. **PromQL** is the query language for retrieving data
5. **rate()** calculates per-second rate for counters
6. **histogram_quantile()** calculates percentiles (P50, P95, P99)
7. **Aggregations** (sum, avg, max) combine multiple time series
8. **Scraping** is Prometheus's default (pull model)
9. **In our project**: App → OTel Collector → Prometheus

---

## Quiz

1. **What's the difference between an instant vector and a range vector?**
   <details>
   <summary>Click to see answer</summary>
   Instant vector returns a single value at the current time. Range vector returns values over a time range (e.g., `[5m]` = last 5 minutes).
   </details>

2. **Why use rate() instead of the raw counter value?**
   <details>
   <summary>Click to see answer</summary>
   Counters always increase, so the raw value isn't meaningful. rate() calculates the per-second rate of change, giving you "requests per second" or similar.
   </details>

3. **How do you calculate the 95th percentile (P95) for a histogram?**
   <details>
   <summary>Click to see answer</summary>
   ```promql
   histogram_quantile(0.95, rate(metric_name_bucket[5m]))
   ```
   </details>

4. **What is cardinality and why does it matter?**
   <details>
   <summary>Click to see answer</summary>
   Cardinality is the number of unique time series. High cardinality (too many unique label combinations) increases storage and slows queries. Keep label values low cardinality.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand Prometheus and PromQL!

**Next**: [Lesson 7: Loki Guide →](07-loki-guide.md)

In the next lesson, you'll learn:
- How Loki stores and indexes logs
- LogQL query language
- Loki vs. Elasticsearch
- Building queries for our project logs

---

**Progress**: ✅ Lessons 1-6 complete | ⬜ 8 lessons remaining
