# Cumulative Observability Dashboard Guide

## Overview

The **Cumulative Observability Dashboard** provides a comprehensive view of your neuroimaging preprocessing pipeline with proper handling of counter resets across application restarts. It integrates all three pillars of observability: metrics (Prometheus), logs (Loki), and traces (Tempo).

## Accessing the Dashboard

1. Start the observability stack: `docker-compose up -d`
2. Open Grafana: http://localhost:3000 (admin/admin)
3. Navigate to: **Dashboards → Neuroimaging → Neuro-Preprocess: Cumulative Observability Dashboard**

## Dashboard Sections

### 📊 Top Statistics Row

**Total Files Processed (All Time)**
- Uses `increase(neuro_files_processed_total[$__range])` to calculate cumulative total
- Properly handles app restarts by summing all increments
- Shows total across entire time range selected

**Total Data Processed (MB)**
- Cumulative sum of all file sizes processed
- Uses `increase(neuro_file_size_sum[$__range])`
- Displays in megabytes

**Total Files Failed**
- Cumulative count of processing failures
- Color-coded: green (0), orange (1+), red (5+)

### ⚡ Processing Rate Over Time

- Real-time processing rate in files per minute
- Uses `rate()` function to calculate instantaneous rate
- Shows processing velocity during active sessions

### 📈 Cumulative Files Processed Timeline

- Line graph showing total files processed over time
- Separate lines for successful vs failed files
- Properly accumulates across app restarts using `increase()`
- Updates every 1 minute interval

### ⏱️ Stage Duration Breakdown

- Median (p50) processing time for each pipeline stage:
  - Load stage (reading files)
  - Process stage (simulated processing)
  - Write stage (writing output)
- Stacked bar chart shows relative time spent in each stage
- Uses histogram quantiles for accurate percentile calculation

### 📝 Application Logs (Loki)

**Features:**
- Real-time log streaming from Loki
- Shows all logs from `neuro-preprocess` service
- Each log line includes:
  - Timestamp
  - Log level (INFO, ERROR, etc.)
  - Message
  - Structured fields (trace_id, span_id, filename, etc.)

**Filtering:**
```logql
# Show only errors
{service_name="neuro-preprocess"} |= "ERROR"

# Show only file processing logs
{service_name="neuro-preprocess"} |= "Processing file"

# Show logs for specific trace
{service_name="neuro-preprocess"} |= "trace_id=abc123"
```

**Trace Correlation:**
- Click on any `trace_id` value in a log line
- Grafana will automatically jump to that trace in Tempo
- See the complete distributed trace for that operation

### 🔍 Recent Traces (Tempo)

- Shows last 20 traces from neuro-preprocess service
- Table view with trace ID, duration, and span count
- Click any trace to open detailed trace view

**Trace Exploration:**
1. Click a trace ID to open trace details
2. See the full span hierarchy (parent-child relationships)
3. Click any span to see:
   - Span attributes (file.name, file.path, etc.)
   - Events (errors, checkpoints)
   - Correlated logs
4. Use "Logs for this span" button to jump to related logs

### 📦 File Size Distribution

- Histogram showing distribution of processed file sizes
- Helps identify common file size patterns
- Useful for capacity planning and performance analysis

## Key Features

### ✅ Proper Counter Reset Handling

Unlike the basic dashboard, this one uses PromQL functions that handle counter resets:

```promql
# ❌ WRONG - Shows current session value only
sum(neuro_files_processed_total)

# ✅ CORRECT - Shows cumulative total across restarts
sum(increase(neuro_files_processed_total[$__range]))
```

### 🔗 Three-Way Correlation

The dashboard demonstrates the power of OpenTelemetry's correlation:

**Workflow 1: Logs → Traces**
1. Find an interesting log line in the Logs panel
2. Click on the `trace_id` field value
3. Jump directly to the full distributed trace

**Workflow 2: Traces → Logs**
1. Open a trace in Tempo
2. Click on any span
3. Click "Logs for this span" button
4. See all logs emitted during that span's execution

**Workflow 3: Metrics → Traces**
1. Notice spike in processing duration graph
2. Note the timestamp
3. Go to Traces panel, filter by that time range
4. Investigate slow traces to find root cause

## Demo Scenarios

### Scenario 1: Watch Cumulative Stats Grow

```bash
# Terminal 1: Run demo
./scripts/run_demo.sh normal  # Processes 10 files

# In Grafana: Note "Total Files Processed" shows 10

# Terminal 1: Run again
./scripts/run_demo.sh normal  # Processes 10 more

# In Grafana: "Total Files Processed" now shows 20 (not 10!)
```

### Scenario 2: Trace-to-Logs Correlation

```bash
# Run processing with 5 second delays to watch live
./scripts/run_demo.sh realtime
```

While running:
1. Open Grafana → Dashboard
2. Watch logs appear in real-time in Logs panel
3. Click on a `trace_id` in any log line
4. Opens full trace with all spans and timing
5. Click "Logs for this span" to see related logs

### Scenario 3: Performance Investigation

```bash
# Process files of different sizes
./scripts/run_demo.sh sizes
```

Then investigate:
1. Check "Stage Duration Breakdown" - which stage is slowest?
2. Look at "File Size Distribution" - do larger files take longer?
3. Open traces for large files to see span timings
4. Check logs for any warnings or errors during slow processing

## Time Range Selection

The dashboard queries use `$__range` variable which adapts to your selected time range:

- **Last 15 minutes**: Shows very recent activity
- **Last 1 hour**: Default view, good for current session
- **Last 24 hours**: See all processing from today
- **Last 7 days**: Weekly summary and trends

Change time range using the picker in top-right corner.

## Auto-Refresh

The dashboard refreshes every 5 seconds by default. You can:
- Change refresh interval: Top-right dropdown (5s, 10s, 30s, 1m, 5m)
- Enable "Live" mode for real-time log tailing
- Pause auto-refresh to investigate static data

## Troubleshooting

### "No data" in metrics panels

**Check:**
```bash
# Verify Prometheus is scraping metrics
curl http://localhost:9090/api/v1/query?query=neuro_files_processed_total

# Check OTel Collector is receiving data
curl http://localhost:8888/metrics | grep neuro
```

### "No logs" in Loki panel

**Check:**
```bash
# Test Loki API
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={service_name="neuro-preprocess"}' | jq

# Verify OTel Collector is forwarding logs
docker-compose logs otel-collector | grep loki
```

### "No traces" in Tempo panel

**Check:**
```bash
# Test Tempo API
curl http://localhost:3200/api/search?tags=service.name=neuro-preprocess

# Verify traces are being exported
docker-compose logs otel-collector | grep tempo
```

### Counter values seem low

Remember: The dashboard shows **incremental** data within the selected time range.

- If you select "Last 15 minutes" but ran demos 1 hour ago, you'll see 0
- Select a wider time range (Last 1 hour, Last 24 hours) to see historical data
- Use the timeline graphs to see when processing actually occurred

## Query Examples

### Custom Prometheus Queries

```promql
# Processing success rate (%)
(sum(increase(neuro_files_processed_total[1h])) /
 (sum(increase(neuro_files_processed_total[1h])) + sum(increase(neuro_files_failed_total[1h])))) * 100

# Average file size
sum(increase(neuro_file_size_sum[1h])) / sum(increase(neuro_file_size_count[1h]))

# 95th percentile pipeline duration
histogram_quantile(0.95, sum(rate(neuro_pipeline_duration_bucket[5m])) by (le))
```

### Custom Loki Queries

```logql
# Count errors per minute
sum(count_over_time({service_name="neuro-preprocess"} |= "ERROR" [1m]))

# Average processing time from logs (if logged)
avg_over_time({service_name="neuro-preprocess"} | json | unwrap duration [5m])

# Show only stage transitions
{service_name="neuro-preprocess"} |~ "Starting|Completed"
```

### Custom Tempo Queries (TraceQL)

```traceql
# Find slow traces (>1 second)
{ service.name="neuro-preprocess" && duration > 1s }

# Find traces with errors
{ service.name="neuro-preprocess" && status=error }

# Find traces for large files (if attribute exists)
{ service.name="neuro-preprocess" && span.file_size > 10 }
```

## Next Steps

1. **Customize**: Edit the dashboard to add your own panels
2. **Alert**: Set up Prometheus alerts for high failure rates or slow processing
3. **Export**: Share the dashboard JSON with your team
4. **Extend**: Add more metrics, logs, or traces as your application grows

## Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [LogQL Documentation](https://grafana.com/docs/loki/latest/logql/)
- [TraceQL Documentation](https://grafana.com/docs/tempo/latest/traceql/)
