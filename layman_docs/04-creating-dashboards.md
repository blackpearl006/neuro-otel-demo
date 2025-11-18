# Creating Dashboards - Step-by-Step Tutorial

This guide teaches you how to build custom dashboards in Grafana to monitor your preprocessing pipeline.

---

## What Is a Dashboard?

**Think of it like**: A customized control panel in a car - you choose which gauges to show and where to place them.

**A dashboard is**:
- A collection of **panels** (graphs, numbers, tables)
- Each panel shows one piece of information (a metric, logs, traces)
- You arrange panels however you want
- It updates automatically

**Why create dashboards?**
- See the most important info at a glance
- Monitor performance over time
- Spot problems quickly
- Share with your team

---

## Part 1: Creating Your First Dashboard

### Step 1: Create a New Dashboard

1. **Open Grafana**: http://localhost:3000
2. Click the **"+" icon** in the left sidebar
3. Select **"New Dashboard"**
4. You'll see a blank canvas with a button **"Add visualization"**

**What you'll see**: An empty dashboard waiting for panels!

### Step 2: Add Your First Panel

5. Click **"Add visualization"**
6. **Select datasource**: Choose **"Prometheus"**
7. You'll see the panel editor with:
   - **Query builder** (bottom): Where you define what data to show
   - **Preview** (top): Live preview of the visualization
   - **Settings panel** (right): Customization options

### Step 3: Configure the Query

Let's create a panel showing **total files processed**.

8. In the query builder (bottom), look for **"Metric"** dropdown
9. Type or select: `neuro_files_processed_total`
10. You should see a line graph appear in the preview

**What you're seeing**: A graph showing how many files have been processed over time

### Step 4: Customize the Visualization

11. **Change the visualization type**:
    - Top right corner, click the visualization type dropdown (currently "Time series")
    - Select **"Stat"** (this shows a big number)

**Now you see**: A big number showing the total count

12. **Customize the appearance**:
    - In the right panel, find **"Panel options"**
    - Change **"Title"** to: `Total Files Processed`
    - Scroll down to **"Stat styles"**
    - Change **"Graph mode"** to: `None` (removes the small sparkline)
    - Change **"Text mode"** to: `Value and name`

### Step 5: Save the Panel

13. Click **"Apply"** (top right)

**What happens**: You return to the dashboard with your first panel!

### Step 6: Save the Dashboard

14. Click the **💾 Save dashboard** icon (top right)
15. Give it a name: `Neuroimaging Pipeline Overview`
16. Click **"Save"**

🎉 **Congratulations!** You created your first dashboard!

---

## Part 2: Adding More Panels

Let's add more panels to make the dashboard useful.

### Panel 2: Average Processing Time

1. Click **"Add" → "Visualization"** (top right)
2. Select datasource: **Prometheus**
3. **Query**:
   ```
   rate(neuro_process_duration_sum[5m]) / rate(neuro_process_duration_count[5m])
   ```
4. **Visualization type**: Keep as **"Time series"** (line graph)
5. **Panel options**:
   - **Title**: `Average Processing Time`
   - **Unit**: Under "Standard options" → **"seconds (s)"**
   - **Min**: `0` (so graph starts at zero)
6. Click **"Apply"**

**What this shows**: A line graph of how long files take to process on average

### Panel 3: Processing Rate

1. Add another visualization
2. Datasource: **Prometheus**
3. **Query**:
   ```
   rate(neuro_files_processed_total[5m])
   ```
4. **Visualization type**: **"Time series"**
5. **Panel options**:
   - **Title**: `Processing Rate`
   - **Unit**: `requests/sec` (under Standard options → Unit → Throughput)
6. Click **"Apply"**

**What this shows**: Files processed per second

### Panel 4: Recent Error Logs

1. Add another visualization
2. Datasource: **Loki**
3. **Query**:
   ```
   {service_name="neuro-preprocess", level="ERROR"}
   ```
4. **Visualization type**: **"Logs"**
5. **Panel options**:
   - **Title**: `Recent Errors`
6. Click **"Apply"**

**What this shows**: A list of recent error logs (if any)

### Panel 5: Processing Duration Distribution (Heatmap)

1. Add another visualization
2. Datasource: **Prometheus**
3. **Query**:
   ```
   rate(neuro_process_duration_bucket[5m])
   ```
4. **Visualization type**: **"Heatmap"**
5. **Panel options**:
   - **Title**: `Processing Duration Distribution`
6. Under **"Heatmap"** settings:
   - **Y Axis** → **Unit**: `seconds (s)`
7. Click **"Apply"**

**What this shows**: A heatmap showing which processing times are most common (darker = more common)

### Panel 6: Pipeline Stages Breakdown

Let's create a panel showing how long each stage takes.

1. Add visualization
2. Datasource: **Prometheus**
3. **Add multiple queries** (we'll add 3):

   **Query A** (Load duration):
   ```
   rate(neuro_load_duration_sum[5m]) / rate(neuro_load_duration_count[5m])
   ```
   - Click the **"A"** label on the query
   - Add **Legend**: `Load`

   **Query B** (Process duration):
   - Click **"+ Query"** to add another
   ```
   rate(neuro_process_duration_sum[5m]) / rate(neuro_process_duration_count[5m])
   ```
   - **Legend**: `Process`

   **Query C** (Write duration):
   - Click **"+ Query"** again
   ```
   rate(neuro_write_duration_sum[5m]) / rate(neuro_write_duration_count[5m])
   ```
   - **Legend**: `Write`

4. **Visualization type**: **"Time series"**
5. **Panel options**:
   - **Title**: `Pipeline Stage Durations`
   - **Unit**: `seconds (s)`
6. **Legend**: Under "Legend" settings, set **Mode** to `List` and **Placement** to `Bottom`
7. Click **"Apply"**

**What this shows**: Three lines showing how long each stage takes over time

### Save Your Progress

Click **💾 Save dashboard** (top right)

---

## Part 3: Arranging Panels

Now you have 6 panels, but they might be stacked vertically. Let's arrange them nicely!

### Resizing Panels

1. **Hover over the edge** of any panel
2. You'll see a **resize handle** (cursor changes)
3. **Click and drag** to resize

### Moving Panels

1. **Click and hold** the panel title bar
2. **Drag** the panel to a new position
3. Other panels will move automatically to make space

### Suggested Layout

**Top row** (big numbers):
- Panel 1: Total Files Processed (small, stat panel)
- Panel 3: Processing Rate (small, stat panel - change to Stat type)

**Second row** (main graphs):
- Panel 2: Average Processing Time (medium width)
- Panel 6: Pipeline Stage Durations (medium width)

**Third row**:
- Panel 5: Processing Duration Distribution (full width)

**Bottom row**:
- Panel 4: Recent Errors (full width)

### Example Layout

```
┌──────────────────┬──────────────────┐
│ Total Files: 42  │ Rate: 2.1/s      │  ← Stat panels
├──────────────────┴──────────────────┤
│ Average Processing Time              │  ← Line graph
│ [graph with time on x-axis]          │
├──────────────────────────────────────┤
│ Pipeline Stage Durations             │  ← Multi-line graph
│ [graph with 3 lines: Load, Process,  │
│  Write]                              │
├──────────────────────────────────────┤
│ Processing Duration Distribution     │  ← Heatmap
│ [heatmap showing distribution]       │
├──────────────────────────────────────┤
│ Recent Errors                        │  ← Log panel
│ [log entries]                        │
└──────────────────────────────────────┘
```

**Save** after arranging!

---

## Part 4: Advanced Panel Configuration

### Adding Thresholds (Color Coding)

Let's make the "Average Processing Time" panel turn red if it's too slow.

1. **Edit the panel**: Click the panel title → **Edit**
2. In the right sidebar, find **"Thresholds"**
3. You'll see default thresholds (green/red at 80)
4. **Change the values**:
   - Base: Green (0)
   - Add threshold: Yellow at `2` (2 seconds)
   - Add threshold: Red at `5` (5 seconds)
5. **Change color mode**: Under "Graph styles", set **Line color** to `Thresholds`
6. Click **"Apply"**

**What this does**: The line turns yellow if average time > 2s, red if > 5s

### Adding Units and Formatting

Make numbers more readable:

1. **Edit a panel** with numbers (like Total Files Processed)
2. In **"Standard options"**:
   - **Unit**: Choose appropriate unit
     - For file counts: `short` (adds K, M suffixes)
     - For bytes: `bytes`
     - For time: `seconds (s)` or `milliseconds (ms)`
     - For percentages: `percent (0-100)`
3. **Decimals**: Set how many decimal places to show (usually 1-2)
4. Click **"Apply"**

### Adding Links

Add a link from a panel to Explore for deeper investigation:

1. **Edit a panel**
2. Scroll down in the right sidebar to **"Panel links"**
3. Click **"Add link"**
4. **Title**: `Explore in detail`
5. **URL**: Click **"Open in Explore"** (this auto-generates the URL)
6. Click **"Apply"**

**What this does**: Adds a clickable link on the panel that opens the query in Explore

### Adding Transformations

Transform data before displaying:

**Example**: Show only the last value (not a time series)

1. **Edit a panel**
2. In the query editor, click the **"Transform"** tab (next to Query)
3. Click **"Add transformation"**
4. Select **"Reduce"**
5. **Calculation**: `Last` (shows only the most recent value)
6. Click **"Apply"**

---

## Part 5: Complete Example Dashboard

Let's build a comprehensive monitoring dashboard from scratch.

### Dashboard Name: "Neuroimaging Pipeline Monitoring"

**Panels to create**:

#### Row 1: Key Metrics (Stat Panels)

**Panel 1.1: Total Files Processed**
- **Datasource**: Prometheus
- **Query**: `neuro_files_processed_total`
- **Type**: Stat
- **Unit**: short

**Panel 1.2: Files Processing Now**
- **Datasource**: Prometheus
- **Query**: `neuro_files_processing_current` (if you have this metric)
- **Type**: Stat
- **Unit**: short

**Panel 1.3: Error Rate**
- **Datasource**: Prometheus
- **Query**: `rate(neuro_files_failed_total[5m])`
- **Type**: Stat
- **Unit**: percentunit
- **Thresholds**: Green < 0.01, Yellow < 0.05, Red >= 0.05

**Panel 1.4: Avg Processing Time**
- **Datasource**: Prometheus
- **Query**: `rate(neuro_process_duration_sum[5m]) / rate(neuro_process_duration_count[5m])`
- **Type**: Stat
- **Unit**: seconds (s)
- **Thresholds**: Green < 2, Yellow < 5, Red >= 5

#### Row 2: Performance Over Time

**Panel 2.1: Processing Duration Percentiles**
- **Datasource**: Prometheus
- **Queries** (add 3):
  - **P50**: `histogram_quantile(0.50, rate(neuro_process_duration_bucket[5m]))`
  - **P95**: `histogram_quantile(0.95, rate(neuro_process_duration_bucket[5m]))`
  - **P99**: `histogram_quantile(0.99, rate(neuro_process_duration_bucket[5m]))`
- **Type**: Time series
- **Unit**: seconds (s)
- **Legend**: P50, P95, P99

**Panel 2.2: Throughput**
- **Datasource**: Prometheus
- **Query**: `rate(neuro_files_processed_total[5m])`
- **Type**: Time series
- **Unit**: ops/sec

#### Row 3: Pipeline Details

**Panel 3.1: Stage Duration Breakdown**
- Same as Panel 6 from Part 2 (Load, Process, Write)

**Panel 3.2: File Size Distribution**
- **Datasource**: Prometheus
- **Query**: `rate(neuro_load_file_size_bucket[5m])`
- **Type**: Heatmap
- **Unit**: MB

#### Row 4: Logs and Traces

**Panel 4.1: Recent Logs**
- **Datasource**: Loki
- **Query**: `{service_name="neuro-preprocess"} |= ""`
- **Type**: Logs
- **Options**: Show time, Show labels (collapsed)

**Panel 4.2: Error Logs**
- **Datasource**: Loki
- **Query**: `{service_name="neuro-preprocess", level="ERROR"}`
- **Type**: Logs

**Panel 4.3: Trace Volume**
- **Datasource**: Prometheus (via Tempo metrics)
- **Query**: (if available) Count of traces per minute
- **Type**: Bar chart

### Organizing with Rows

You can group panels into collapsible rows:

1. In dashboard edit mode, click **"Add" → "Row"**
2. **Title** the row: `Key Metrics`
3. **Drag panels** into the row
4. The row becomes collapsible

**Suggested rows**:
- **Key Metrics**: Stat panels
- **Performance Over Time**: Time series graphs
- **Pipeline Details**: Stage breakdowns, file sizes
- **Logs and Errors**: Log panels
- **System Health**: (if you add system metrics)

---

## Part 6: Dashboard Settings

### Time Range and Refresh

**Set default time range**:
1. Click **⚙️ Dashboard settings** (gear icon, top right)
2. **Time options**:
   - **Timezone**: Browser time or specific timezone
   - **Auto refresh**: `5s`, `10s`, `30s`, `1m`, etc.
   - **Now delay**: Delay data by N seconds (useful for slow backends)
   - **Hide time picker**: Hide the time range selector
3. **Save**

### Variables (Dynamic Dashboards)

Variables make dashboards flexible. For example, filter by file name.

1. **Dashboard settings** → **Variables**
2. Click **"Add variable"**
3. **Variable settings**:
   - **Name**: `filename`
   - **Type**: `Query`
   - **Datasource**: Prometheus
   - **Query**: `label_values(neuro_files_processed_total, file_name)`
   - **Multi-value**: Enabled (allow selecting multiple files)
4. **Save**

**Using the variable**:
- In any panel query, use: `{file_name="$filename"}`
- A dropdown appears at the top of the dashboard to select files

### Annotations (Mark Events)

Show when deployments or incidents happened:

1. **Dashboard settings** → **Annotations**
2. Click **"Add annotation query"**
3. **Name**: `Deployments`
4. **Datasource**: Loki
5. **Query**: (query for deployment logs)
6. **Save**

**What this does**: Vertical lines appear on graphs showing when events occurred

---

## Part 7: Sharing and Exporting

### Sharing a Dashboard

**Method 1: Share Link**
1. Click **Share** icon (top right)
2. **Link** tab
3. Choose options:
   - Lock time range
   - Shorten URL
4. **Copy** the link

**Method 2: Export as JSON**
1. **Dashboard settings** → **JSON Model**
2. **Copy** the JSON
3. Share the JSON file
4. Others can import it via **+ → Import**

**Method 3: Export as PDF/PNG**
(Requires Grafana Enterprise or plugins)

### Making a Dashboard Public

1. **Dashboard settings** → **General**
2. **Tags**: Add tags like `neuroimaging`, `monitoring`
3. **Make default**: Set as your default dashboard
4. **Starred**: Star it for quick access

---

## Part 8: Dashboard Best Practices

### Do's

✅ **Group related panels together**: Put all timing metrics in one row

✅ **Use consistent colors**: Same metric = same color across panels

✅ **Add descriptions**: Panel descriptions help explain what you're seeing
   - Edit panel → Panel options → Description

✅ **Set appropriate time ranges**:
   - Real-time monitoring: Last 5-15 minutes
   - Performance analysis: Last 24 hours or 7 days

✅ **Use templates**: Create one good dashboard, then duplicate and modify

✅ **Add units**: Always set units for metrics (seconds, bytes, etc.)

✅ **Test with different time ranges**: Make sure panels work for 5m, 1h, 1d

### Don'ts

❌ **Don't overcrowd**: 8-12 panels max per dashboard

❌ **Don't use cryptic titles**: "avg_proc_t" → "Average Processing Time"

❌ **Don't forget to save**: Save frequently!

❌ **Don't use too many colors**: Stick to a palette

❌ **Don't show raw bucket metrics**: Use histogram_quantile() instead

---

## Part 9: Troubleshooting Dashboard Issues

### Panel shows "No data"

**Check**:
1. **Time range**: Is it set to when you have data?
2. **Query syntax**: Any typos in the query?
3. **Datasource**: Is it running? (Check datasource settings)
4. **Data exists**: Go to Explore and test the same query

### Panel is very slow

**Solutions**:
1. **Reduce time range**: Query last 1h instead of last 7d
2. **Increase interval**: Change query to `[5m]` instead of `[1m]`
3. **Limit data points**: Under Query options → Max data points

### Graphs look weird

**Issues and fixes**:
- **Jagged lines**: Increase step interval
- **Gaps**: Missing data - check if service was down
- **Spikes**: Might be real! Investigate in Explore
- **Flat line**: Query might be wrong or no data

### Dashboard won't save

**Check**:
1. **Permissions**: Do you have edit rights?
2. **Name conflict**: Dashboard name already exists?
3. **Browser console**: Open dev tools (F12) for errors

---

## Part 10: Pre-built Dashboard Template

Here's a complete JSON template you can import:

**To import**:
1. Copy the JSON from `grafana/dashboards/neuroimaging-overview.json` (if it exists)
2. **+ → Import** in Grafana
3. Paste JSON
4. **Load**
5. **Import**

**Or create it manually** using the panels described in Part 5.

---

## Practice Exercise

**Build a mini dashboard** with these requirements:

1. **Title**: "My Pipeline Monitor"
2. **3 panels**:
   - Total files processed (Stat)
   - Average processing time over time (Time series)
   - Recent logs (Logs panel)
3. **Time range**: Last 30 minutes
4. **Auto refresh**: 10 seconds
5. **Save** the dashboard

**Bonus**:
- Add a threshold to the processing time panel
- Change colors to your preference
- Add a panel description

---

## Summary Checklist

Can you:

- ✅ Create a new dashboard?
- ✅ Add panels with different visualizations?
- ✅ Configure queries for Prometheus, Loki, Tempo?
- ✅ Resize and rearrange panels?
- ✅ Set units and thresholds?
- ✅ Save and share dashboards?
- ✅ Use variables for dynamic filtering?

If yes, you're a dashboard pro! If not, re-read the relevant sections.

---

## Next Steps

1. **Read** `05-troubleshooting.md` for common problems and solutions
2. **Experiment**: Build different dashboards for different needs:
   - Operations dashboard (for daily monitoring)
   - Performance dashboard (for optimization)
   - Error dashboard (for debugging)
3. **Customize**: Make dashboards that work for YOUR workflow

Remember: Dashboards are personal. What works for one person might not work for another. Experiment and find what helps YOU understand your data!
