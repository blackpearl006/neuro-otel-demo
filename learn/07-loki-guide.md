# Lesson 7: Loki Guide

**Estimated time**: 50-60 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand how Loki stores and indexes logs
✅ Learn LogQL query language
✅ Know the difference between Loki and Elasticsearch
✅ Master stream selectors, filters, and parsers
✅ Be able to extract metrics from logs

---

## What Is Loki?

### The Simple Definition

**Loki** is a **log aggregation system** designed to be **cost-effective** and **easy to operate**.

**Created by**: Grafana Labs (same team as Grafana)

**Inspired by**: Prometheus (for metrics) → Loki (for logs)

**Tagline**: "Like Prometheus, but for logs"

---

### Analogy: Library vs. Bookstore

**Traditional systems (Elasticsearch)** = **Detailed library catalog**
- Index every word in every book
- Search any phrase instantly
- Expensive (lots of storage for indexes)
- Complex to operate

**Loki** = **Organized bookstore**
- Index only labels (genre, author, publication year)
- Search within a section (grep through books)
- Cheap (minimal indexes)
- Simple to operate

---

## How Loki Works

### The Key Insight: Labels, Not Full-Text Index

**Traditional approach (Elasticsearch)**:
- Index **every word** in every log
- Fast full-text search
- **Expensive**: Index size can exceed log size

**Loki's approach**:
- Index only **labels** (metadata)
- Store logs as compressed **chunks**
- Search = "Find logs with these labels, then grep"
- **Cheap**: Tiny indexes, brute-force search on selected streams

```
┌─────────────────────────────────────────────────┐
│  Traditional (Elasticsearch)                    │
├─────────────────────────────────────────────────┤
│  Index EVERYTHING:                              │
│  "Loading", "file", "sub-001", "nii.gz", ...   │
│                                                 │
│  ✅ Super fast search                           │
│  ❌ Expensive storage                           │
│  ❌ Complex operations                          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Loki                                           │
├─────────────────────────────────────────────────┤
│  Index ONLY labels:                             │
│  service_name="neuro-preprocess"                │
│  level="INFO"                                   │
│                                                 │
│  ✅ Fast label-based filtering                  │
│  ✅ Cheap storage                               │
│  ✅ Simple operations                           │
│  ⚠️  Slower full-text search                    │
└─────────────────────────────────────────────────┘
```

---

## Loki's Data Model

### Streams

A **stream** is a set of logs with the **same labels**.

**Example**:

```
Stream 1: {service_name="neuro-preprocess", level="INFO"}
  2025-11-20 14:00:00  Loading file: sub-001
  2025-11-20 14:00:02  Processing completed
  2025-11-20 14:00:05  File written successfully

Stream 2: {service_name="neuro-preprocess", level="ERROR"}
  2025-11-20 14:01:30  Failed to load file: permission denied
  2025-11-20 14:03:15  Out of memory error

Stream 3: {service_name="web-server", level="INFO"}
  2025-11-20 14:00:00  HTTP GET /api/files
  2025-11-20 14:00:10  HTTP POST /api/process
```

**Each unique label combination = One stream**

---

### Labels in Loki

**Labels** are indexed metadata that identify streams.

**Good labels** (low cardinality):
- `service_name` (neuro-preprocess, web-server)
- `level` (INFO, ERROR, WARNING)
- `environment` (dev, staging, prod)
- `host` (server-01, server-02)

**Bad labels** (high cardinality):
- `user_id` (thousands of users)
- `request_id` (every request is unique)
- `file_path` (every file is different)

**Why?** Each unique label combination creates a new stream. Too many streams = slow queries and high costs.

---

### Log Structure

Each log entry has:
- **Timestamp**: When it happened
- **Labels**: Stream identifier
- **Content**: The actual log message (can be JSON, plain text, etc.)

```json
{
  "timestamp": "2025-11-20T14:00:00Z",
  "stream": {
    "service_name": "neuro-preprocess",
    "level": "INFO"
  },
  "message": "Processing file: sub-001_T1w.nii.gz"
}
```

---

## LogQL: Loki Query Language

**LogQL** is Loki's query language, inspired by PromQL.

### Query Structure

```
{stream_selector} | filter | parser | aggregation
```

**Example**:

```logql
{service_name="neuro-preprocess"}
  | json
  | level="ERROR"
  | line_format "{{.timestamp}} {{.message}}"
```

Let's break down each part:

---

## Part 1: Stream Selectors

**Select streams** by their labels.

### Basic Selection

```logql
# All logs from neuro-preprocess service
{service_name="neuro-preprocess"}

# Only errors
{service_name="neuro-preprocess", level="ERROR"}

# Multiple services (OR)
{service_name=~"neuro-preprocess|web-server"}
```

---

### Label Matching Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Exact match | `level="ERROR"` |
| `!=` | Not equal | `level!="DEBUG"` |
| `=~` | Regex match | `service_name=~"neuro.*"` |
| `!~` | Regex not match | `level!~"DEBUG\|TRACE"` |

**Examples**:

```logql
# Exact match
{service_name="neuro-preprocess", level="INFO"}

# Regex: Any level except DEBUG or TRACE
{service_name="neuro-preprocess", level!~"DEBUG|TRACE"}

# Regex: Services starting with "neuro"
{service_name=~"neuro.*"}
```

---

## Part 2: Log Filters

**Filter log lines** by content (after selecting streams).

### Line Filters

| Operator | Meaning | Example |
|----------|---------|---------|
| `\|=` | Contains | `\|= "error"` |
| `!=` | Does not contain | `!= "success"` |
| `\|~` | Regex match | `\|~ "failed\|error"` |
| `!~` | Regex not match | `!~ "debug\|trace"` |

**Examples**:

```logql
# Logs containing "error"
{service_name="neuro-preprocess"} |= "error"

# Logs NOT containing "success"
{service_name="neuro-preprocess"} != "success"

# Logs matching regex (failed OR error)
{service_name="neuro-preprocess"} |~ "failed|error"

# Case-insensitive search
{service_name="neuro-preprocess"} |~ "(?i)error"
```

---

### Chaining Filters

```logql
# Logs containing "processing" AND "file" but NOT "success"
{service_name="neuro-preprocess"}
  |= "processing"
  |= "file"
  != "success"
```

**Order matters**: Filters are applied left to right.

---

## Part 3: Parsers

**Extract structured data** from log lines.

### JSON Parser

If logs are JSON, extract fields:

```logql
# Parse JSON and filter by field
{service_name="neuro-preprocess"}
  | json
  | duration_seconds > 5
```

**Example log**:

```json
{"level": "INFO", "message": "Processing completed", "duration_seconds": 1.96}
```

**After `| json`**, you can reference fields: `duration_seconds`, `level`, `message`.

---

### logfmt Parser

For logs in `key=value` format:

```
level=info message="Processing file" duration=1.96s
```

```logql
{service_name="neuro-preprocess"}
  | logfmt
  | duration > 1
```

---

### Pattern Parser

Extract fields using patterns:

```logql
{service_name="neuro-preprocess"}
  | pattern "<level> <timestamp> <message>"
  | level = "ERROR"
```

**Example log**:

```
ERROR 2025-11-20T14:00:00Z Failed to process file
```

---

### regexp Parser

Use regex to extract fields:

```logql
{service_name="neuro-preprocess"}
  | regexp "duration: (?P<duration>\\d+\\.\\d+)s"
  | duration > 2
```

**Extracts**: `duration` field from log line.

---

## Part 4: Line Formatting

**Format output** for better readability.

```logql
{service_name="neuro-preprocess"}
  | json
  | line_format "{{.timestamp}} [{{.level}}] {{.message}}"
```

**Result**:

```
2025-11-20T14:00:00Z [INFO] Processing file
2025-11-20T14:00:02Z [INFO] Processing completed
```

---

## Part 5: Metrics from Logs

**Aggregate logs** to create metrics (like PromQL).

### count_over_time

Count log lines over time:

```logql
# Logs per second over last 5 minutes
count_over_time({service_name="neuro-preprocess"}[5m])
```

---

### rate

Logs per second:

```logql
# Error rate (errors per second)
rate({service_name="neuro-preprocess", level="ERROR"}[5m])
```

---

### sum_over_time

Sum extracted numeric values:

```logql
# Total processing time (sum of durations)
sum_over_time({service_name="neuro-preprocess"} | json | unwrap duration_seconds [5m])
```

**`unwrap`** extracts numeric field for aggregation.

---

### avg_over_time

Average of numeric values:

```logql
# Average processing duration
avg_over_time({service_name="neuro-preprocess"} | json | unwrap duration_seconds [5m])
```

---

### quantile_over_time

Calculate percentiles:

```logql
# P95 duration (from logs!)
quantile_over_time(0.95,
  {service_name="neuro-preprocess"}
  | json
  | unwrap duration_seconds
  [5m]
)
```

---

## Real Queries for Our Project

### Query 1: All Logs from Our Service

```logql
{service_name="neuro-preprocess"}
```

---

### Query 2: Only Error Logs

```logql
{service_name="neuro-preprocess", level="ERROR"}
```

Or:

```logql
{service_name="neuro-preprocess"} | json | level="ERROR"
```

---

### Query 3: Logs for a Specific File

```logql
{service_name="neuro-preprocess"} |= "sub-001_T1w.nii.gz"
```

---

### Query 4: Logs with Slow Processing (>5s)

```logql
{service_name="neuro-preprocess"}
  | json
  | duration_seconds > 5
```

---

### Query 5: Logs for a Specific Trace

```logql
{service_name="neuro-preprocess"}
  | json
  | trace_id="7f8a9b0c1d2e3f4a"
```

**This links logs to traces!**

---

### Query 6: Error Rate Over Time

```logql
sum(rate({service_name="neuro-preprocess", level="ERROR"}[5m]))
```

**Creates a metric from logs!**

---

### Query 7: Top Error Messages

```logql
topk(5,
  sum by (message) (
    count_over_time({service_name="neuro-preprocess", level="ERROR"}[1h])
  )
)
```

**Shows the 5 most common error messages.**

---

### Query 8: Average Processing Duration (from logs)

```logql
avg_over_time({service_name="neuro-preprocess"}
  | json
  | unwrap duration_seconds
  [5m]
)
```

---

## Loki vs. Elasticsearch

| Feature | Loki | Elasticsearch |
|---------|------|---------------|
| **Index** | Labels only | Full-text |
| **Search speed** | Fast (label filter) + Slow (grep) | Very fast (all searches) |
| **Storage cost** | Low | High |
| **Complexity** | Simple | Complex |
| **Use case** | Metrics-driven debugging | Full-text search, analytics |
| **Best for** | Known queries, label-based filtering | Unknown queries, exploratory search |

---

### When to Use Loki

✅ Cost-effective log storage
✅ Already using Prometheus (similar concepts)
✅ Label-based queries (filter by service, level, etc.)
✅ Integration with Grafana
✅ Simple operations

---

### When to Use Elasticsearch

✅ Full-text search across all fields
✅ Complex analytics and aggregations
✅ Need to search arbitrary text
✅ Willing to pay for storage and operations

---

## Try It Yourself

### Exercise 1: Basic Log Queries

1. **Open Grafana**: http://localhost:3000

2. **Navigate to Explore → Select Loki**

3. **Try these queries**:

   All logs:
   ```logql
   {service_name="neuro-preprocess"}
   ```

   Only errors:
   ```logql
   {service_name="neuro-preprocess", level="ERROR"}
   ```

   Logs containing "failed":
   ```logql
   {service_name="neuro-preprocess"} |= "failed"
   ```

---

### Exercise 2: Parse JSON Logs

1. **Query with JSON parsing**:
   ```logql
   {service_name="neuro-preprocess"}
     | json
     | line_format "{{.timestamp}} [{{.level}}] {{.message}}"
   ```

2. **Filter by field**:
   ```logql
   {service_name="neuro-preprocess"}
     | json
     | duration_seconds > 2
   ```

---

### Exercise 3: Link Logs to Traces

1. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

2. **Find a trace in Tempo** (Explore → Tempo → Search)

3. **Copy the trace_id** (e.g., `7f8a9b0c...`)

4. **Query logs for that trace** in Loki:
   ```logql
   {service_name="neuro-preprocess"}
     | json
     | trace_id="7f8a9b0c1d2e3f4a"
   ```

5. **See all logs** for that specific request!

---

### Exercise 4: Create Metrics from Logs

1. **Error rate**:
   ```logql
   rate({service_name="neuro-preprocess", level="ERROR"}[5m])
   ```

2. **Average duration** (from logs):
   ```logql
   avg_over_time({service_name="neuro-preprocess"}
     | json
     | unwrap duration_seconds
     [5m]
   )
   ```

3. **P95 duration** (from logs):
   ```logql
   quantile_over_time(0.95,
     {service_name="neuro-preprocess"}
     | json
     | unwrap duration_seconds
     [5m]
   )
   ```

4. **Compare** with metrics from Prometheus. Do they match?

---

## Loki Configuration

Our Loki config (`configs/loki-config.yaml`):

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h  # 1 week
```

**Key settings**:
- **Storage**: Local filesystem (`/loki/chunks`)
- **Retention**: 1 week (configurable)
- **Index**: BoltDB (embedded database)

---

## Best Practices

### 1. Use Low-Cardinality Labels

**Good**:
```
{service_name="neuro-preprocess", level="ERROR"}  # Few unique values
```

**Bad**:
```
{service_name="neuro-preprocess", file_path="/data/sub-001.nii.gz"}  # High cardinality!
```

**Solution**: Use filters instead of labels for high-cardinality data:

```logql
{service_name="neuro-preprocess"} |= "sub-001.nii.gz"
```

---

### 2. Limit Query Time Range

**Bad**:
```logql
{service_name="neuro-preprocess"}[30d]  # Queries 30 days!
```

**Good**:
```logql
{service_name="neuro-preprocess"}[1h]  # Only last hour
```

**Why**: Loki scans logs linearly. Smaller time ranges = faster queries.

---

### 3. Filter Early

**Bad**:
```logql
{service_name="neuro-preprocess"} | json | level="ERROR"  # Parse everything, then filter
```

**Good**:
```logql
{service_name="neuro-preprocess", level="ERROR"} | json  # Filter at label level first
```

Or even better:

```logql
{service_name="neuro-preprocess"} |= "ERROR" | json  # Line filter before parsing
```

---

### 4. Use Structured Logs

**Makes LogQL easier**:
- JSON logs can be parsed with `| json`
- Extract and filter fields easily
- Consistent structure = easier queries

---

## Key Takeaways

1. **Loki** indexes labels, not full-text (cost-effective)
2. **Streams** are sets of logs with the same labels
3. **LogQL** structure: `{selector} | filter | parser | aggregation`
4. **Labels** should be low-cardinality
5. **Filters** search log content (like grep)
6. **Parsers** extract structured fields from logs
7. **Metrics from logs**: count_over_time, rate, sum, quantiles
8. **Trace correlation**: Query logs by trace_id
9. **Loki vs. Elasticsearch**: Cheaper, simpler, but slower for full-text search

---

## Quiz

1. **Why doesn't Loki index every word in logs?**
   <details>
   <summary>Click to see answer</summary>
   Cost and simplicity. Indexing every word requires huge storage and complex operations. Loki only indexes labels and uses brute-force search on filtered streams, making it much cheaper and simpler.
   </details>

2. **What's the difference between a label and a filter?**
   <details>
   <summary>Click to see answer</summary>
   Labels are indexed metadata (service_name, level) that identify streams. Filters (|=, |~) search the log content after selecting streams. Labels are fast, filters are slower but more flexible.
   </details>

3. **How do you link logs to traces in Grafana?**
   <details>
   <summary>Click to see answer</summary>
   Query logs by trace_id:
   ```logql
   {service_name="neuro-preprocess"} | json | trace_id="abc123"
   ```
   </details>

4. **Can you create metrics from logs?**
   <details>
   <summary>Click to see answer</summary>
   Yes! Use aggregations like rate(), count_over_time(), quantile_over_time() with unwrap to extract numeric fields.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand Loki and LogQL!

**Next**: [Lesson 8: Tempo Guide →](08-tempo-guide.md)

In the next lesson, you'll learn:
- How Tempo stores distributed traces
- TraceQL query language
- Trace sampling and retention
- Finding traces efficiently

---

**Progress**: ✅ Lessons 1-7 complete | ⬜ 7 lessons remaining
