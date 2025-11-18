# Glossary - Technical Terms Explained Simply

This document explains all the technical terms used in this project in simple, everyday language.

---

## Core Concepts

### **Observability**
**Simple explanation**: The ability to understand what's happening inside your software by looking at the data it produces.

**Think of it like**: A doctor using X-rays, blood tests, and heart monitors to understand what's happening inside your body. Observability gives you "X-rays" for your software.

---

### **Telemetry**
**Simple explanation**: Data that your software automatically sends out about what it's doing.

**Think of it like**: The dashboard in your car that shows speed, fuel level, temperature, etc. Your car's computer is sending you telemetry.

**In our project**: The preprocessing pipeline sends information about:
- How long each step takes
- Which files are being processed
- Whether operations succeeded or failed

---

## The Three Pillars of Observability

### **1. Traces**
**Simple explanation**: A timeline showing the complete journey of a single request or operation through your system.

**Think of it like**: A detailed receipt from a restaurant showing:
- 2:00 PM - Order received
- 2:05 PM - Food preparation started
- 2:15 PM - Food cooked
- 2:18 PM - Plate assembled
- 2:20 PM - Delivered to table

**In our project**: When you process a brain scan file, a trace shows:
- Load file (0.15 seconds)
  - Validate data (0.02 seconds)
- Process image (1.3 seconds)
  - Skull strip (0.7 seconds)
  - Bias correction (0.5 seconds)
  - Normalization (0.1 seconds)
- Write output (0.5 seconds)

**Key terms**:
- **Span**: One step in the trace (like "Load file")
- **Root span**: The first/main span that contains all others
- **Child span**: A span inside another span
- **Trace ID**: A unique identifier for the entire operation

---

### **2. Metrics**
**Simple explanation**: Numbers that measure things over time (like temperature, speed, count).

**Think of it like**:
- Your car's odometer showing total miles driven
- A thermometer showing temperature every hour
- A step counter showing steps per day

**In our project**: Metrics track:
- **Counters**: How many files processed total
- **Histograms**: Distribution of processing times (how many took 1s, 2s, 3s, etc.)
- **Gauges**: Current values (like files currently being processed)

**Examples**:
- "File size processed: 5.2 MB"
- "Average processing time: 2.1 seconds"
- "95th percentile load time: 0.3 seconds" (95% of files load in under 0.3s)

---

### **3. Logs**
**Simple explanation**: Text messages that your software writes down about what it's doing.

**Think of it like**: A diary entry or a captain's log on a ship.

**Example log entry**:
```
2025-11-18 21:40:14 - INFO - Loading file: sub-001_T1w.nii.gz
2025-11-18 21:40:15 - INFO - Successfully loaded in 0.15s
```

**Log levels** (from least to most serious):
- **DEBUG**: Detailed information, usually only useful for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Something unexpected happened, but the program can continue
- **ERROR**: A serious problem that prevented something from working
- **CRITICAL**: A very serious error that might stop the whole program

**Special feature in our project**: **Trace correlation**
- Each log message includes the trace ID
- Click on a log → jump to the related trace
- Click on a trace → see all related logs
- This is like having page numbers in a book that let you jump between chapters!

---

## Technologies & Tools

### **Docker**
**Simple explanation**: A way to package software with everything it needs to run, like a complete shipping container.

**Think of it like**: A food delivery container that includes the food, utensils, napkins, and heating element all in one sealed box. No matter where you open it, everything you need is inside.

**In our project**: Each part of the observability stack (Grafana, Prometheus, etc.) runs in its own Docker container.

---

### **Docker Compose**
**Simple explanation**: A tool to start and manage multiple Docker containers that work together.

**Think of it like**: A conductor directing an orchestra - making sure all the musicians (containers) start playing (running) at the right time and work together.

**Command we use**: `docker-compose up` = "Start all containers"

---

### **OpenTelemetry**
**Simple explanation**: An industry-standard way for software to generate and export telemetry data.

**Think of it like**: USB - a universal standard so any device can connect to any computer. OpenTelemetry is a universal standard so any software can send telemetry to any monitoring system.

**Why it matters**: You're not locked into one vendor. You can switch from Grafana to Datadog without changing your code.

**Components**:
- **API**: Functions your code calls to create traces/metrics/logs
- **SDK**: The implementation that actually sends the data
- **Exporter**: The part that sends data to the collector (in our case, OTLP)

---

### **OTLP (OpenTelemetry Protocol)**
**Simple explanation**: The language/format OpenTelemetry uses to send telemetry data.

**Think of it like**: HTTPS is the protocol for web traffic, OTLP is the protocol for telemetry traffic.

**In our project**: Your preprocessing app speaks OTLP to send data to the collector.

**Technical detail**: Uses gRPC on port 4317 (fast binary protocol) or HTTP on port 4318

---

## The Observability Stack Components

### **Grafana**
**Simple explanation**: A web dashboard where you can see all your telemetry data visually.

**Think of it like**: The control panel in a spaceship or the dashboard in a modern car - one place to see everything.

**What you can do**:
- View traces as waterfall charts
- See logs in real-time
- Create graphs of metrics over time
- Build custom dashboards
- Set up alerts

**How to access**: Open `http://localhost:3000` in your web browser

---

### **Prometheus**
**Simple explanation**: A database that specializes in storing metrics (numbers over time).

**Think of it like**: A specialized spreadsheet that's really good at:
- Storing time-series data (temperature readings every minute)
- Answering questions like "What was the average in the last hour?"
- Graphing trends

**What it stores**: All your metrics (file sizes, processing times, error counts)

**Query language**: PromQL (Prometheus Query Language) - like SQL but for time-series data

**Example query**:
```
rate(files_processed_total[5m])
```
= "How many files per second were processed in the last 5 minutes?"

---

### **Loki**
**Simple explanation**: A database that specializes in storing and searching logs.

**Think of it like**: Google search, but only for your application's log messages.

**What makes it special**: Indexes by labels (like file tags), not full-text content. This makes it fast and cheap.

**Query language**: LogQL (similar to PromQL but for logs)

**Example query**:
```
{service_name="neuro-preprocess"} |= "error"
```
= "Show me all logs from neuro-preprocess that contain the word 'error'"

---

### **Tempo**
**Simple explanation**: A database that specializes in storing distributed traces.

**Think of it like**: A filing system that keeps all the "receipts" (traces) of everything your application did, organized so you can find them quickly.

**What it stores**: Complete traces showing the journey of each file through your pipeline

**Query language**: TraceQL (query language for searching traces)

**Example search**: "Show me all traces that took longer than 3 seconds"

---

### **OpenTelemetry Collector**
**Simple explanation**: A central hub that receives telemetry from your applications and sends it to the right storage backends.

**Think of it like**: A post office sorting facility:
- Receives packages (telemetry) from many senders (your apps)
- Sorts them by type (traces, metrics, logs)
- Delivers to the right destination (Tempo, Prometheus, Loki)

**Why have this instead of sending directly?**:
- One endpoint for your app to send to (simpler)
- Can filter, transform, or batch data
- Can send to multiple backends
- Can buffer if a backend is down

**In our project**: Listens on port 4317 for OTLP data

---

## Data Flow Terms

### **Pipeline**
**Simple explanation**: A series of steps that data flows through in order.

**In our preprocessing**:
```
Input File → Load → Process → Write → Output File
```

**In our telemetry**:
```
Your App → Collector → Storage Backend → Grafana
```

---

### **Instrumentation**
**Simple explanation**: Adding code to your software to make it generate telemetry.

**Think of it like**: Installing sensors in a car to measure speed, RPM, temperature, etc.

**In our project**: We added code to create spans, record metrics, and write structured logs.

**Types**:
- **Automatic**: Libraries automatically create telemetry (we'd need special libraries for this)
- **Manual**: You write the code to create telemetry (what we did)

---

### **Span**
**Simple explanation**: A single operation in a trace with a start time and end time.

**Think of it like**: One line item on a receipt showing what happened and how long it took.

**Attributes of a span**:
- **Name**: What operation this is (e.g., "load_file")
- **Start time**: When it started
- **End time**: When it finished
- **Duration**: How long it took (end - start)
- **Parent span**: The span this is inside of (if any)
- **Attributes**: Extra information (file name, size, etc.)
- **Status**: Success or error
- **Events**: Things that happened during the span

---

### **Correlation**
**Simple explanation**: Linking related pieces of data together so you can jump between them.

**Think of it like**: Hyperlinks on a webpage - click to jump to related content.

**In our project**:
- Logs have trace IDs → click to see the full trace
- Traces have span IDs → click to see related logs
- This creates a "web" of related information

---

## Query & Visualization Terms

### **Dashboard**
**Simple explanation**: A custom page showing the most important metrics and visualizations for your needs.

**Think of it like**: The homepage of a news website, showing the top stories at a glance.

**In Grafana**: You can create dashboards with:
- Graphs showing metrics over time
- Tables showing recent traces
- Log streams
- Alerts

---

### **Time Range**
**Simple explanation**: The period of time you want to look at.

**Examples**:
- "Last 5 minutes"
- "Last 24 hours"
- "November 1 to November 15"
- "Last hour"

**Why it matters**: Looking at too much data is slow. Looking at too little might miss the problem.

---

### **Visualization Types**

**Time series graph**: Line graph showing how a value changes over time
- Example: Processing time from 1 PM to 5 PM

**Histogram**: Bar chart showing distribution
- Example: How many files took 1s, 2s, 3s, etc.

**Heatmap**: Grid showing values with colors
- Example: Processing time by hour of day and day of week (darker = slower)

**Table**: Rows and columns of data
- Example: List of recent traces with columns for duration, file name, status

**Stat panel**: Big number showing a single value
- Example: "Total files processed: 1,247"

---

## Performance Terms

### **Latency**
**Simple explanation**: How long something takes (delay time).

**Example**: "The latency of loading a file is 0.15 seconds"

---

### **Throughput**
**Simple explanation**: How much you can process in a given time.

**Example**: "The throughput is 30 files per minute"

---

### **Percentile**
**Simple explanation**: A way to understand distribution by saying "X% of values are below this number".

**Examples**:
- **50th percentile (median)**: Half are faster, half are slower
- **95th percentile (P95)**: 95% of requests are faster than this
- **99th percentile (P99)**: 99% of requests are faster than this

**Why P95/P99 matter more than average**:
- Average can hide problems
- If most requests are fast but a few are super slow, average looks okay
- P95 tells you about the worst 5% of experiences

**Example**:
- Average processing time: 2 seconds
- P95 processing time: 5 seconds
- This means 95% finish in under 5s, but some take much longer!

---

## File & Data Terms

### **JSON**
**Simple explanation**: A text format for storing data that's easy for both humans and computers to read.

**Looks like**:
```json
{
  "filename": "scan.nii.gz",
  "size_mb": 5.2,
  "processed": true
}
```

**In our project**: Metadata files are stored as JSON

---

### **YAML**
**Simple explanation**: Another text format for storing configuration, similar to JSON but easier for humans to read/write.

**Looks like**:
```yaml
filename: scan.nii.gz
size_mb: 5.2
processed: true
```

**In our project**: All config files (prometheus.yml, loki-config.yaml, etc.) use YAML

---

### **Port**
**Simple explanation**: A number that identifies a specific service on a computer, like an apartment number in a building.

**Think of it like**: The IP address is the building address, the port is the apartment number.

**Our ports**:
- **3000**: Grafana web interface
- **4317**: OpenTelemetry Collector (gRPC)
- **9090**: Prometheus
- **3100**: Loki
- **3200**: Tempo

**How to access**: `http://localhost:PORT` (e.g., `http://localhost:3000`)

---

## This Should Help!

Whenever you encounter an unfamiliar term in the other docs or in Grafana, come back to this glossary!

**Pro tip**: Print this out or keep it open in another window while exploring Grafana.
