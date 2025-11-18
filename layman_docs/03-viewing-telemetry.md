# Viewing Telemetry in Grafana - Step-by-Step Guide

This document shows you how to actually use Grafana to explore your telemetry data.

---

## Getting Started

### Step 1: Open Grafana

1. Make sure the observability stack is running:
   ```bash
   docker-compose up -d
   ```

2. Open your web browser and go to: **http://localhost:3000**

3. Login with:
   - **Username**: `admin`
   - **Password**: `admin`

4. (Optional) Skip the "change password" prompt by clicking "Skip"

**You should see**: The Grafana home page with a sidebar on the left

---

## Understanding the Grafana Interface

### The Sidebar (Left Side)

The key sections you'll use:

- **🏠 Home**: Main page
- **🔍 Explore**: The main tool for viewing telemetry (we'll use this a lot!)
- **📊 Dashboards**: Saved collections of graphs and visualizations
- **⚙️ Configuration**: Settings, data sources

### The Top Bar

- **Time range picker** (top right): Choose what time period to look at
  - "Last 5 minutes"
  - "Last 1 hour"
  - "Last 24 hours"
  - Or custom range
- **Refresh button**: Reload the data

---

## Using Explore - Your Main Tool

**Explore** is where you'll spend most of your time. It's like a search engine for your telemetry.

### Opening Explore

1. Click **🔍 Explore** in the left sidebar
2. You'll see a page with:
   - **Datasource dropdown** (top left): Choose Prometheus, Loki, or Tempo
   - **Query builder**: Where you search for data
   - **Results area**: Where data appears

---

## Part 1: Viewing Traces (Using Tempo)

Traces show the complete journey of each file through your pipeline.

### Step-by-Step: Finding a Trace

1. **Open Explore**: Click 🔍 Explore in sidebar
2. **Select datasource**: Click dropdown at top left, choose **"Tempo"**
3. **Choose time range**: Top right, select **"Last 1 hour"** (or when you last ran the pipeline)

### Method 1: Search by Service Name

4. In the query builder, you'll see "Query type" - make sure it's on **"Search"**
5. Click **"Service Name"** dropdown
6. Select **"neuro-preprocess"**
7. Click the blue **"Run query"** button (top right)

**What you'll see**: A list of traces, each representing one file processed

**The trace list shows**:
- **Trace ID**: Unique identifier (like a tracking number)
- **Duration**: How long the operation took
- **Spans**: Number of operations in the trace
- **Timestamp**: When it happened

### Viewing a Trace in Detail

8. **Click on any trace** in the list

**What you'll see**: A waterfall diagram showing the timeline

**Reading the waterfall**:
```
preprocess_file               ████████████████████████ 2.01s
├─ load_file                  ███ 0.15s
│  └─ validate_data           █ 0.02s
├─ process_image              ███████████████ 1.31s
│  ├─ skull_strip             ████████ 0.70s
│  ├─ bias_correction         ██████ 0.50s
│  └─ normalization           ██ 0.11s
└─ write_output               ████ 0.50s
```

- **Each bar** = one operation (span)
- **Bar width** = how long it took
- **Indentation** = parent-child relationship
- **Gaps between bars** = waiting time

### Understanding Span Details

9. **Click on any span** (e.g., click on "load_file")

**What you'll see**: A detail panel on the right with:

**Tags (Attributes)**:
- `file.name`: "sub-001_T1w.nii.gz"
- `file.size_mb`: 4.9
- `image.shape`: "(128, 128, 100)"

**Process**: Information about the service
- `service.name`: "neuro-preprocess"
- `service.version`: "0.1.0"

**Timing**:
- Start time
- Duration

**Logs**: Any logs written during this span (if correlation is working!)

### Searching for Specific Traces

**By Duration**: Find slow operations
```
Query type: Search
Service Name: neuro-preprocess
Min Duration: 3s  (finds traces that took > 3 seconds)
```

**By Trace ID**: If you have a specific trace ID from logs
```
Query type: TraceQL
Query: { trace.id = "abc123..." }
```

**By Span Name**: Find traces with specific operations
```
Query type: TraceQL
Query: { span.name = "process_image" }
```

---

## Part 2: Viewing Logs (Using Loki)

Logs are text messages your application wrote about what it's doing.

### Step-by-Step: Viewing Logs

1. **Open Explore**: Click 🔍 Explore in sidebar
2. **Select datasource**: Choose **"Loki"** from dropdown
3. **Choose time range**: Select **"Last 1 hour"**

### Method 1: Basic Log Search

4. In the query builder, you'll see a text box with: `{}`
5. Change it to:
   ```
   {service_name="neuro-preprocess"}
   ```
6. Click **"Run query"**

**What you'll see**: All logs from your preprocessing pipeline, newest first

**Each log shows**:
- **Timestamp**: When the log was written
- **Level**: INFO, WARNING, ERROR
- **Message**: The actual log text
- **Labels**: Metadata (service_name, level, etc.)

### Method 2: Filtering Logs

**Show only errors**:
```
{service_name="neuro-preprocess"} |= "error"
```
This means: "Show logs from neuro-preprocess that contain the word 'error'"

**Show only a specific file**:
```
{service_name="neuro-preprocess"} |= "sub-001_T1w.nii.gz"
```

**Show INFO level only**:
```
{service_name="neuro-preprocess", level="INFO"}
```

**Show processing stage only**:
```
{service_name="neuro-preprocess"} |= "Processing"
```

**Exclude certain messages**:
```
{service_name="neuro-preprocess"} != "Loading"
```
This excludes any log containing "Loading"

### Method 3: Live Tail (Real-time Logs)

This is like watching logs scroll by in real-time!

1. Make sure you're in Loki datasource
2. Click the **"Live"** button (top right, near Run query)
3. Run your pipeline in another terminal:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```
4. Watch logs appear in Grafana in real-time!

**To stop live tail**: Click "Stop" button

### Viewing Log Details

5. **Click on any log line**

**What you'll see**: Expanded view showing:
- Full message
- All labels (service_name, level, trace_id, span_id, etc.)
- Detected fields (file names, durations, etc.)

**Look for**:
- `trace_id`: The trace this log belongs to
- `span_id`: The specific span this log was written in

---

## Part 3: Trace-to-Logs Correlation (The Magic!)

This is one of the most powerful features - jumping between traces and logs.

### From Trace → Logs

1. **View a trace in Tempo** (see Part 1)
2. **Click on a span** (e.g., "load_file")
3. **Look at the right panel** - you'll see span details
4. **Scroll down** to the "Logs for this span" section
5. **Click "Logs for this span"** button (or the link)

**What happens**: Grafana switches to Loki and shows ONLY the logs from that specific span!

**The query it generates**:
```
{service_name="neuro-preprocess"} | trace_id = "a1b2c3d4..." and span_id = "1234..."
```

**Why this is amazing**: Instead of searching through thousands of logs, you instantly see exactly the logs related to this operation.

### From Logs → Trace

1. **View logs in Loki** (see Part 2)
2. **Click on any log line** to expand it
3. **Look for the trace_id field** in the labels
4. **Click on the trace_id value** - it should be a clickable link

**What happens**: Grafana switches to Tempo and shows the full trace for that log!

**Why this is amazing**: You see a single error log, click it, and instantly see the entire timeline of what happened.

---

## Part 4: Viewing Metrics (Using Prometheus)

Metrics are numbers measured over time (file sizes, processing times, counts).

### Step-by-Step: Viewing Metrics

1. **Open Explore**: Click 🔍 Explore in sidebar
2. **Select datasource**: Choose **"Prometheus"** from dropdown
3. **Choose time range**: Select **"Last 1 hour"**

### Method 1: Browsing Available Metrics

4. In the query builder, you'll see "Metric" dropdown
5. Click it - you'll see all available metrics:
   - `neuro_load_duration_bucket`
   - `neuro_load_file_size_bucket`
   - `neuro_process_duration_bucket`
   - `neuro_write_duration_bucket`
   - Many others...

6. **Select** `neuro_load_duration_bucket`
7. Click **"Run query"**

**What you'll see**: A graph showing the distribution of load times over time

### Method 2: Writing PromQL Queries

PromQL is Prometheus's query language. Here are useful queries:

**Average processing time**:
```
rate(neuro_process_duration_sum[5m]) / rate(neuro_process_duration_count[5m])
```
This shows: "What's the average processing time per file in the last 5 minutes?"

**Total files processed**:
```
sum(neuro_files_processed_total)
```

**Processing rate (files per second)**:
```
rate(neuro_files_processed_total[5m])
```

**95th percentile load time**:
```
histogram_quantile(0.95, rate(neuro_load_duration_bucket[5m]))
```
This shows: "95% of files load faster than this"

**File size distribution**:
```
histogram_quantile(0.50, rate(neuro_load_file_size_bucket[5m]))
```
This is the median file size

### Understanding the Graph

**Y-axis**: The value (time in seconds, count, size in MB, etc.)
**X-axis**: Time
**Lines**: Different series (if you have labels)

**Hover over the graph**: See exact values at that time

**Controls**:
- **Zoom**: Click and drag on the graph
- **Reset zoom**: Double-click the graph
- **Legend**: Click series names to show/hide them

---

## Part 5: Practical Examples

Let's do some real scenarios!

### Scenario 1: "How long did my file take to process?"

1. **Go to Explore → Tempo**
2. Search: Service Name = "neuro-preprocess"
3. In the results, find your file by timestamp
4. Click on the trace
5. Look at the top-level "preprocess_file" span
6. The duration shows total time: **2.01s**
7. Click on individual child spans to see breakdown:
   - load_file: 0.15s
   - process_image: 1.31s
   - write_output: 0.50s

### Scenario 2: "Where did my file fail?"

1. **Go to Explore → Loki**
2. Query:
   ```
   {service_name="neuro-preprocess", level="ERROR"}
   ```
3. You'll see error logs
4. Click on an error log to expand
5. Note the error message
6. **Click the trace_id** to jump to the trace
7. In the trace, look for spans with error indicators (usually red/orange)
8. Click the error span to see details

### Scenario 3: "What's the average processing time today?"

1. **Go to Explore → Prometheus**
2. Set time range to "Today"
3. Query:
   ```
   rate(neuro_process_duration_sum[1h]) / rate(neuro_process_duration_count[1h])
   ```
4. You'll see a graph of average processing time over the day
5. Hover over recent data to see current average

### Scenario 4: "Show me all logs from the 'skull_strip' operation"

1. **Go to Explore → Loki**
2. Query:
   ```
   {service_name="neuro-preprocess"} |= "skull_strip"
   ```
3. Or, if you have the span name in logs:
   ```
   {service_name="neuro-preprocess", otelSpanName="skull_strip"}
   ```

### Scenario 5: "Is my pipeline getting slower over time?"

1. **Go to Explore → Prometheus**
2. Set time range to "Last 7 days"
3. Query for 95th percentile:
   ```
   histogram_quantile(0.95, rate(neuro_process_duration_bucket[1h]))
   ```
4. Look at the graph trend:
   - **Flat line**: Consistent performance
   - **Upward slope**: Getting slower
   - **Downward slope**: Getting faster

---

## Part 6: Split View (Advanced)

You can view two datasources side-by-side!

1. In Explore, click the **"Split"** button (top right)
2. You now have two panels
3. **Left panel**: Choose Tempo, search for a trace
4. **Right panel**: Choose Loki, show logs for the same time range
5. **Result**: See traces and logs simultaneously!

**Use case**: Compare what the trace shows (timing) with what the logs say (details)

---

## Part 7: Common Queries Cheat Sheet

### Loki (Logs)

**All logs from the app**:
```
{service_name="neuro-preprocess"}
```

**Only errors**:
```
{service_name="neuro-preprocess", level="ERROR"}
```

**Logs containing specific text**:
```
{service_name="neuro-preprocess"} |= "scan.nii.gz"
```

**Logs NOT containing text**:
```
{service_name="neuro-preprocess"} != "Loading"
```

**Logs with multiple filters**:
```
{service_name="neuro-preprocess"} |= "Processing" |= "completed"
```

**Logs for a specific trace**:
```
{service_name="neuro-preprocess"} | trace_id = "abc123..."
```

### Tempo (Traces)

**All traces from service** (use Search mode):
- Service Name: neuro-preprocess
- Click Run query

**Slow traces** (use Search mode):
- Service Name: neuro-preprocess
- Min Duration: 3s

**Traces with errors** (use TraceQL mode):
```
{ status = error }
```

**Traces for specific operation** (use TraceQL mode):
```
{ span.name = "process_image" }
```

**Traces with specific attribute** (use TraceQL mode):
```
{ span.file.name = "sub-001_T1w.nii.gz" }
```

### Prometheus (Metrics)

**Total files processed**:
```
neuro_files_processed_total
```

**Files processed in last 5 minutes**:
```
increase(neuro_files_processed_total[5m])
```

**Processing rate (per second)**:
```
rate(neuro_files_processed_total[5m])
```

**Average processing duration**:
```
rate(neuro_process_duration_sum[5m]) / rate(neuro_process_duration_count[5m])
```

**95th percentile processing time**:
```
histogram_quantile(0.95, rate(neuro_process_duration_bucket[5m]))
```

**Median file size**:
```
histogram_quantile(0.50, rate(neuro_load_file_size_bucket[5m]))
```

---

## Tips and Tricks

### Tip 1: Use Keyboard Shortcuts

- **Ctrl/Cmd + K**: Open command palette
- **Ctrl/Cmd + Shift + E**: Open Explore
- **Escape**: Close panels

### Tip 2: Share Your Queries

After running a query:
1. Click the **"Share"** icon (top right)
2. Choose "Link to query"
3. Copy the URL
4. Anyone with access to Grafana can view this exact query

### Tip 3: Save Your Time Range

If you keep using the same time range:
1. Set the time range
2. Click the time picker
3. Click the **star icon** to add to favorites

### Tip 4: Use Variables in Queries

Instead of hardcoding values, use variables:
```
{service_name="$service"}
```
Then you can change `$service` without rewriting the query.

### Tip 5: Refresh on Interval

Top right, next to time picker:
- Click the refresh dropdown
- Choose "5s" or "10s"
- Grafana will auto-refresh the data

---

## Troubleshooting

### "No data" in Tempo

**Problem**: Can't find any traces

**Check**:
1. Did you actually run the pipeline? Traces only appear when you process files.
2. Is the time range correct? Try "Last 1 hour"
3. Run this in your terminal:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```
4. Wait 10 seconds, then refresh Grafana

### "No data" in Loki

**Problem**: Can't find logs

**Check**:
1. Same as Tempo - did you run the pipeline recently?
2. Try query: `{service_name="neuro-preprocess"}` (copy exactly)
3. Check time range

### "No data" in Prometheus

**Problem**: Can't find metrics

**Check**:
1. Metrics take **15 seconds** to appear (Prometheus scrape interval)
2. Run the pipeline
3. Wait 15-20 seconds
4. Refresh Prometheus
5. Try query: `neuro_files_processed_total`

### Grafana shows "datasource not found"

**Problem**: Can't connect to Tempo/Loki/Prometheus

**Solution**:
1. Check services are running:
   ```bash
   docker-compose ps
   ```
2. All should show "Up (healthy)"
3. If not, restart:
   ```bash
   docker-compose restart
   ```

### Trace-to-logs correlation not working

**Problem**: No "Logs for this span" button

**Check**:
1. Make sure `grafana/datasources.yaml` has the derivedFields configuration
2. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```
3. Refresh your browser (Ctrl/Cmd + Shift + R)

---

## Next Steps

Now that you know how to view telemetry, you're ready to:

1. **Create custom dashboards** → Read `04-creating-dashboards.md`
2. **Understand common problems** → Read `05-troubleshooting.md`
3. **Experiment**: Try processing files and exploring the data!

---

## Summary Checklist

Can you:

- ✅ Open Grafana and log in?
- ✅ Use Explore to view traces in Tempo?
- ✅ Use Explore to view logs in Loki?
- ✅ Use Explore to view metrics in Prometheus?
- ✅ Jump from a trace to related logs?
- ✅ Jump from a log to its trace?
- ✅ Write basic queries in each datasource?
- ✅ Change the time range?

If yes, you're ready to build dashboards! If not, re-read the relevant sections and try the examples.

---

## Practice Exercise

**Your mission**: Process a file and then find the following information in Grafana:

1. **In Tempo**: What was the total duration of preprocessing?
2. **In Tempo**: Which operation took the longest (skull_strip, bias_correction, or normalization)?
3. **In Loki**: How many INFO logs were generated?
4. **In Loki**: What was the exact log message when the file finished loading?
5. **In Prometheus**: What was the file size in MB?
6. **Correlation**: Click on a span in Tempo, jump to logs, then find the trace_id in the logs

**Answers**: You should be able to find all of these in Grafana after processing a file!
