# Project Overview - What Is What?

This document explains what each part of this project does in simple terms.

---

## What Is This Project?

This is a **learning project** to understand **observability** - the practice of monitoring what your software is doing.

Think of it like this:
- You have a car (the preprocessing pipeline)
- You want to add a dashboard, speedometer, and diagnostic tools (observability)
- This project teaches you how to build and use those tools

---

## The Two Main Parts

### Part 1: The Application (What We're Monitoring)

**Location**: `app/` folder

**What it does**: A simulated brain scan preprocessing pipeline that:
1. Loads brain scan files
2. Processes them (skull stripping, bias correction, normalization)
3. Saves the processed output

**Why "simulated"?**: Real brain processing uses complex medical imaging libraries. We simulate it with fake data so you can focus on learning observability, not neuroscience.

**Key files**:
```
app/
├── neuro_preprocess/
│   ├── cli.py                    # Command-line interface (what you run)
│   ├── pipeline.py               # Orchestrates the whole process
│   ├── stages/
│   │   ├── loader.py             # Loads files
│   │   ├── processor.py          # Processes images
│   │   └── writer.py             # Saves output
│   └── telemetry/
│       ├── tracer_setup.py       # Sets up tracing
│       ├── metrics_setup.py      # Sets up metrics
│       └── logger_setup.py       # Sets up logging
```

**How to use it**:
```bash
# Process one file
neuro-preprocess process data/input/scan.nii.gz -o data/output

# Process all files in a folder
neuro-preprocess batch data/input -o data/output
```

---

### Part 2: The Observability Stack (What Monitors The Application)

**Location**: `containers/` and `configs/` folders

**What it does**: A collection of services that receive, store, and visualize telemetry data.

**Key Components**:

1. **Grafana** (Port 3000)
   - **What**: Web dashboard where you see everything
   - **Like**: The screen in a car showing speed, fuel, etc.
   - **Access**: http://localhost:3000
   - **Login**: admin/admin

2. **OpenTelemetry Collector** (Port 4317)
   - **What**: Receives telemetry from your app
   - **Like**: A post office receiving mail
   - **You don't interact directly**: Works in the background

3. **Prometheus** (Port 9090)
   - **What**: Stores metrics (numbers over time)
   - **Like**: A spreadsheet tracking measurements
   - **Access**: http://localhost:9090 (but usually use Grafana instead)

4. **Loki** (Port 3100)
   - **What**: Stores logs (text messages)
   - **Like**: A searchable diary
   - **Access**: Through Grafana (not directly)

5. **Tempo** (Port 3200)
   - **What**: Stores traces (complete operation timelines)
   - **Like**: A receipt for each file processed
   - **Access**: Through Grafana (not directly)

---

## How They Connect

```
┌─────────────────────────────────────────────┐
│  YOUR APPLICATION                            │
│  (neuro-preprocess)                          │
│                                              │
│  When it runs, it sends:                     │
│  - Traces (timelines of operations)          │
│  - Metrics (measurements)                    │
│  - Logs (text messages)                      │
└──────────────────┬───────────────────────────┘
                   │
                   │ Sends via OTLP
                   │ (Port 4317)
                   ▼
┌─────────────────────────────────────────────┐
│  OPENTELEMETRY COLLECTOR                     │
│                                              │
│  Receives all telemetry and sorts it:        │
│  - Sends traces → Tempo                      │
│  - Sends metrics → Prometheus                │
│  - Sends logs → Loki                         │
└──────┬─────────────┬───────────────┬─────────┘
       │             │               │
       ▼             ▼               ▼
   ┌──────┐     ┌────────┐      ┌──────┐
   │ Tempo│     │Promethe│      │ Loki │
   │      │     │  us    │      │      │
   └──┬───┘     └───┬────┘      └───┬──┘
      │             │               │
      └─────────────┼───────────────┘
                    │
                    │ All data queried by
                    ▼
         ┌────────────────────┐
         │     GRAFANA        │
         │                    │
         │  You view          │
         │  everything here!  │
         └────────────────────┘
```

---

## The Directory Structure Explained

```
neuro-otel-demo/
│
├── app/                              # The application being monitored
│   ├── neuro_preprocess/             # Main Python package
│   │   ├── cli.py                    # Run this to process files
│   │   ├── pipeline.py               # Main logic
│   │   ├── stages/                   # Processing steps
│   │   └── telemetry/                # OpenTelemetry setup
│   ├── requirements.txt              # Python dependencies
│   └── pyproject.toml                # Project configuration
│
├── containers/                       # Docker definitions
│   ├── Dockerfile.grafana            # How to build Grafana
│   ├── Dockerfile.prometheus         # How to build Prometheus
│   ├── Dockerfile.loki               # How to build Loki
│   ├── Dockerfile.tempo              # How to build Tempo
│   ├── Dockerfile.otel-collector     # How to build Collector
│   └── build_all.sh                  # Script to build everything
│
├── configs/                          # Configuration files
│   ├── grafana/
│   │   └── datasources.yaml          # Tells Grafana where data is
│   ├── prometheus.yml                # Prometheus config
│   ├── loki-config.yaml              # Loki config
│   ├── tempo-config.yaml             # Tempo config
│   └── otel-collector-config.yaml    # Collector routing rules
│
├── data/                             # Data files
│   ├── input/                        # Put scan files here
│   ├── output/                       # Processed files go here
│   └── telemetry/                    # Stored telemetry data
│       ├── prometheus/               # Metrics database
│       ├── loki/                     # Logs database
│       ├── tempo/                    # Traces database
│       └── grafana/                  # Grafana database
│
├── docker-compose.yml                # Starts all services together
│
├── layman_docs/                      # This documentation!
│   ├── 00-glossary.md                # Definitions of terms
│   ├── 01-overview.md                # This file
│   ├── 02-how-it-works.md            # How everything works
│   ├── 03-viewing-telemetry.md       # Using Grafana
│   ├── 04-creating-dashboards.md     # Building custom dashboards
│   └── 05-troubleshooting.md         # Common problems & fixes
│
└── README.md                         # Main project documentation
```

---

## What Each File Type Is

### Python Files (`.py`)
- **What**: Source code files written in Python programming language
- **Can you edit?**: Yes, but be careful!
- **To view**: Open in any text editor

### YAML Files (`.yaml` or `.yml`)
- **What**: Configuration files in human-readable format
- **Can you edit?**: Yes, these control how services behave
- **To view**: Open in any text editor
- **Syntax**: Indentation matters! Use spaces, not tabs

### Docker Files (`Dockerfile.*`)
- **What**: Instructions for building Docker containers
- **Can you edit?**: Generally no need to
- **To view**: Open in any text editor

### Shell Scripts (`.sh`)
- **What**: Automated command sequences
- **Can you edit?**: Yes, but usually don't need to
- **To run**: `./script_name.sh`

### Markdown Files (`.md`)
- **What**: Documentation written in Markdown format
- **Can you edit?**: Yes! Add notes, examples, etc.
- **To view**: Any text editor, or rendered on GitHub

---

## What Gets Created When You Run The App

### Output Files

When you process a file like `sub-001_T1w.nii.gz`, you get:

1. **`sub-001_T1w_preprocessed.nii.gz`**
   - The processed brain scan
   - In real scenario: ready for analysis
   - In our demo: simulated output

2. **`sub-001_T1w_preprocessed.npy`**
   - Numpy array format (for demo purposes)
   - Contains the actual processed data

3. **`sub-001_T1w_preprocessed.json`**
   - Metadata in JSON format
   - Contains:
     - Original file info
     - Processing statistics
     - Timestamps

4. **`sub-001_T1w_preprocessed.report.txt`**
   - Human-readable processing report
   - Shows what was done and how long it took

### Telemetry Data

While processing, telemetry is sent to the backends:

1. **Traces** → Stored in `data/telemetry/tempo/`
   - Timeline of the processing
   - View in Grafana Explore → Tempo

2. **Metrics** → Stored in `data/telemetry/prometheus/`
   - Measurements (file sizes, durations)
   - View in Grafana Explore → Prometheus

3. **Logs** → Stored in `data/telemetry/loki/`
   - Text log messages
   - View in Grafana Explore → Loki

---

## Quick Reference - What Goes Where

| I want to...                          | Look at...                          |
|---------------------------------------|-------------------------------------|
| Change how files are processed        | `app/neuro_preprocess/stages/`      |
| Change telemetry being collected      | `app/neuro_preprocess/telemetry/`   |
| Change Prometheus scraping            | `configs/prometheus.yml`            |
| Change log retention                  | `configs/loki-config.yaml`          |
| Change trace storage                  | `configs/tempo-config.yaml`         |
| Add/remove datasources in Grafana     | `configs/grafana/datasources.yaml`  |
| View processing outputs               | `data/output/`                      |
| Add input files to process            | `data/input/`                       |
| Start/stop the observability stack    | `docker-compose up/down`            |
| View telemetry visually               | http://localhost:3000 (Grafana)     |
| Learn about terms                     | `layman_docs/00-glossary.md`        |
| Understand the architecture           | `layman_docs/02-how-it-works.md`    |
| Learn to use Grafana                  | `layman_docs/03-viewing-telemetry.md` |
| Create custom dashboards              | `layman_docs/04-creating-dashboards.md` |
| Fix problems                          | `layman_docs/05-troubleshooting.md` |

---

## Next Steps

Now that you understand what everything is, you should:

1. **Read** `02-how-it-works.md` to understand the flow
2. **Read** `03-viewing-telemetry.md` to learn Grafana
3. **Try** processing some files and viewing the results
4. **Create** your own dashboard using `04-creating-dashboards.md`

---

## Questions to Ask Yourself

To check your understanding, can you answer these?

1. **What are the three types of telemetry?**
   - Answer: Traces, Metrics, Logs

2. **Where do you view all the telemetry?**
   - Answer: Grafana (http://localhost:3000)

3. **What does the OpenTelemetry Collector do?**
   - Answer: Receives telemetry from the app and routes it to storage backends

4. **Where are processed files saved?**
   - Answer: `data/output/`

5. **How do you start all the observability services?**
   - Answer: `docker-compose up -d`

If you can answer these, you're ready to move on! If not, re-read the relevant sections.
