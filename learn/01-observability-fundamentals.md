# Lesson 1: Observability Fundamentals

**Estimated time**: 30-45 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Understand what observability means
✅ Know the difference between monitoring and observability
✅ Understand the three pillars of observability
✅ Know when to use traces vs. metrics vs. logs

---

## What Is Observability?

### The Simple Definition

**Observability** is the ability to understand what's happening inside your system by looking at the data it produces.

Think of it like this:

```
┌─────────────────────────────────────┐
│   Your Application (Black Box)      │
│                                     │
│   ┌──────────────────────┐         │
│   │  Something happened  │         │
│   │  But what exactly?   │         │
│   └──────────────────────┘         │
│                                     │
│   Outputs: Traces, Metrics, Logs   │
└─────────────────────────────────────┘
              ↓
   You examine these outputs
              ↓
  You understand what happened!
```

### Real-World Analogy

**Your body** is observable:
- **Temperature** (metric) - Is it normal? High? Low?
- **Symptoms** (logs) - "My head hurts", "I feel tired"
- **Medical history** (trace) - Timeline of what happened leading to now

A doctor uses **all three** to diagnose you. Same with software!

---

## Monitoring vs. Observability

### Monitoring: "Known Unknowns"

**Monitoring** answers questions you **already know to ask**:
- ✅ "Is the server up?"
- ✅ "Is CPU usage above 80%?"
- ✅ "Are there any errors in the logs?"

You set up dashboards and alerts for **expected problems**.

### Observability: "Unknown Unknowns"

**Observability** lets you investigate questions you **didn't know you'd need to ask**:
- 🤔 "Why did this specific user request take 10 seconds?"
- 🤔 "What changed between yesterday and today?"
- 🤔 "Why is this edge case failing?"

You explore data to **discover unexpected problems**.

### Comparison Table

| Aspect | Monitoring | Observability |
|--------|-----------|---------------|
| **Questions** | Pre-defined | Ad-hoc, exploratory |
| **Approach** | Dashboards, alerts | Query, filter, correlate |
| **Use Case** | "Is everything OK?" | "Why is this failing?" |
| **Example** | CPU usage graph | "Show me all slow requests from user X" |
| **Tools** | Nagios, basic metrics | OTel, Grafana, advanced queries |

**Key Insight**: You need **both**! Monitoring tells you **that** something is wrong. Observability helps you figure out **why**.

---

## The Three Pillars of Observability

Observability rests on three types of telemetry:

```
        ┌───────────────────────────┐
        │    OBSERVABILITY          │
        └───────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
   │ TRACES │ │ METRICS│ │  LOGS  │
   └────────┘ └────────┘ └────────┘
```

Let's understand each one.

---

### Pillar 1: Traces

**What is a trace?**
A trace is the **complete journey** of a single request through your system.

**Analogy**: Like a receipt from a restaurant:
```
ORDER #1234                 [Trace ID]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
14:00  Order received       [Span 1]
14:02  Chef started cooking [Span 2]
14:15  Food ready           [Span 3]
14:17  Delivered to table   [Span 4]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 17 minutes
```

**In our project**: When you process a brain scan file:
```
Trace: process sub-001.nii.gz  [ID: abc123]
├─ load_file (0.15s)
├─ process_image (1.31s)
│  ├─ skull_strip (0.70s)
│  ├─ bias_correction (0.50s)
│  └─ normalization (0.11s)
└─ write_output (0.50s)
Total: 1.96s
```

**Use traces when**:
- ✅ You want to see the **timeline** of operations
- ✅ You need to find **bottlenecks**
- ✅ You're debugging **slow requests**
- ✅ You want to understand **dependencies** between services

---

### Pillar 2: Metrics

**What are metrics?**
Metrics are **numerical measurements** over time.

**Analogy**: Like a car's dashboard:
```
Speed:     65 mph  [Right now]
Fuel:      50%     [Current level]
Miles:     45,231  [Total, always increasing]
Temp:      195°F   [Current reading]
```

**Types of metrics**:

1. **Counter**: Always goes up (like an odometer)
   - Example: Total files processed
   - Example: Total errors

2. **Gauge**: Goes up and down (like a thermometer)
   - Example: Current memory usage
   - Example: Active connections

3. **Histogram**: Distribution of values
   - Example: Processing time (most files: 2s, some: 10s)
   - Example: File sizes (small, medium, large)

**In our project**:
```
neuro_files_processed_total = 42      [Counter]
neuro_processing_current = 2           [Gauge]
neuro_process_duration_bucket {...}   [Histogram]
```

**Use metrics when**:
- ✅ You want to see **trends over time**
- ✅ You need **aggregated data** (average, percentiles)
- ✅ You're monitoring **system health**
- ✅ You want **alerting** on thresholds

---

### Pillar 3: Logs

**What are logs?**
Logs are **text messages** about events that happened.

**Analogy**: Like a ship's captain log:
```
Captain's Log, Stardate 2025.11.20:
- 08:00: Departed from port
- 10:30: Encountered rough seas
- 12:00: Engine temperature rose to 95°C
- 14:00: Arrived at destination
```

**Types of logs**:

| Level | Purpose | Example |
|-------|---------|---------|
| **DEBUG** | Detailed info for debugging | "Function X called with params Y" |
| **INFO** | Normal operations | "File processing started" |
| **WARNING** | Something unexpected but OK | "Retry attempt 2 of 3" |
| **ERROR** | Something failed | "Failed to write file: permission denied" |
| **CRITICAL** | System is broken | "Database connection lost" |

**In our project**:
```
2025-11-19 14:30:15 INFO  Loading file: sub-001.nii.gz
2025-11-19 14:30:15 INFO  File size: 4.90 MB
2025-11-19 14:30:17 INFO  Processing completed in 1.96s
```

**Use logs when**:
- ✅ You need **detailed context** about what happened
- ✅ You're investigating **specific error messages**
- ✅ You want to **search** for particular events
- ✅ You need **forensic evidence** of what occurred

---

## When to Use Which Pillar?

### Question Decision Tree

```
"Something is wrong!"
       │
       ├─ Is it a system-wide issue?
       │  YES → Start with METRICS
       │  │     (CPU, memory, request rate)
       │  │
       │  NO → Is it affecting specific requests?
       │        YES → Start with TRACES
       │              (find slow/failed traces)
       │              │
       │              └─ Need more details?
       │                 YES → Jump to LOGS
       │                       (error messages, stack traces)
```

### Scenario Examples

**Scenario 1**: "The system is slow"

1. **Start with METRICS**: Check CPU, memory, request rate
   ```promql
   rate(requests_total[5m])  # Is traffic high?
   ```

2. **Then TRACES**: Find slow requests
   ```
   Find traces > 5 seconds
   ```

3. **Then LOGS**: Look for errors in slow traces
   ```
   {trace_id="abc123"} | level="ERROR"
   ```

**Scenario 2**: "A specific file failed to process"

1. **Start with LOGS**: Search for the file name
   ```
   {service_name="neuro-preprocess"} |= "sub-042.nii.gz"
   ```

2. **Then TRACE**: Click the trace_id from logs
   ```
   See which stage failed
   ```

3. **Then METRICS**: Check if this is a pattern
   ```
   rate(errors_total{stage="process"}[1h])
   ```

---

## Why All Three?

Each pillar answers different questions:

| Pillar | Answers | Example |
|--------|---------|---------|
| **Metrics** | "How much?" "How often?" | "Average processing time is 2.5s" |
| **Traces** | "What happened?" "In what order?" | "Processing took 10s because skull_strip was slow" |
| **Logs** | "Why?" "What exactly?" | "skull_strip failed because: insufficient memory" |

**Together** they give you complete visibility:

```
Metrics: "Error rate increased 10 minutes ago"
    ↓
Traces: "These 5 specific requests failed"
    ↓
Logs: "Failed because: database timeout"
    ↓
Solution: Scale database or add retry logic
```

---

## The Power of Correlation

The **magic** happens when you link the three pillars:

### Example from Our Project

**Metric** shows a problem:
```promql
rate(neuro_files_failed_total[5m]) > 0.1
```
"10% of files are failing!"

**Trace** shows where:
```
Trace abc123: FAILED
├─ load_file: OK (0.15s)
├─ process_image: OK (1.3s)
└─ write_output: FAILED (0.01s)
```
"Failures happen in write_output stage!"

**Logs** show why:
```
ERROR: Failed to write file: disk full
```
"Disk is full!"

**Solution**: Clear disk space or increase storage.

**Total time to diagnosis**: ~5 minutes (vs. hours without observability!)

---

## Observability in Practice

### Without Observability

User: "The app is slow"

You:
1. SSH into server
2. Check logs manually: `tail -f app.log`
3. Grep for errors: `grep ERROR app.log`
4. Check CPU: `top`
5. ???
6. Restart server and hope for the best

**Time**: Hours or days
**Success rate**: 50%

### With Observability

User: "The app is slow"

You:
1. Check metrics dashboard: "Ah, high latency on /process endpoint"
2. Find slow traces: "These 10 requests took >10s"
3. Click one trace: "skull_strip stage is slow"
4. Check logs for that trace: "Out of memory warning"
5. Fix: Increase memory or optimize algorithm

**Time**: Minutes
**Success rate**: 95%

---

## Real-World Examples

### Example 1: E-commerce Site

**Without observability**:
- "Checkout is broken sometimes"
- Can't reproduce the issue
- No idea which users are affected

**With observability**:
```
Metrics: 5% of checkouts failing
Traces: Only users from Europe affected
Logs: Payment API timeout for EU region
Solution: Increase timeout for EU payment gateway
```

### Example 2: Data Pipeline (Like Our Project!)

**Without observability**:
- "Some files fail to process"
- No pattern identified
- Manual testing of random files

**With observability**:
```
Metrics: Failures increased after 2pm
Traces: Only large files (>500MB) failing
Logs: Out of memory in skull_strip
Solution: Increase memory or process large files separately
```

---

## Try It Yourself

### Exercise 1: Observe Our Project

1. **Start the stack**:
   ```bash
   ./scripts/start_stack.sh
   ```

2. **Process a file**:
   ```bash
   neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
   ```

3. **Find the telemetry**:
   - **Metrics**: http://localhost:9090 → Query: `neuro_files_processed_total`
   - **Traces**: http://localhost:3000 → Explore → Tempo → Search
   - **Logs**: http://localhost:3000 → Explore → Loki → `{service_name="neuro-preprocess"}`

4. **Answer these questions**:
   - How many files have been processed? (Metric)
   - How long did processing take? (Trace)
   - What was logged during processing? (Logs)

### Exercise 2: Compare the Pillars

Process 3 files and observe:

```bash
./scripts/run_demo.sh normal
```

Then explore:
1. **Metrics**: What's the average processing time?
2. **Traces**: Which stage takes the longest?
3. **Logs**: Are there any warnings?

---

## Key Takeaways

1. **Observability** = Understanding your system through its outputs
2. **Three pillars**:
   - **Metrics**: Numbers over time (trends, aggregates)
   - **Traces**: Request timelines (bottlenecks, dependencies)
   - **Logs**: Detailed events (context, errors)

3. **Each pillar answers different questions** - you need all three
4. **Correlation** between pillars gives you superpowers
5. **Observability saves time** in debugging and understanding systems

---

## Quiz

Test your understanding:

1. **What's the difference between monitoring and observability?**
   <details>
   <summary>Click to see answer</summary>
   Monitoring answers pre-defined questions ("is it up?"). Observability lets you explore and answer questions you didn't anticipate.
   </details>

2. **Which pillar would you use to find slow requests?**
   <details>
   <summary>Click to see answer</summary>
   Traces - they show the timeline and duration of each operation in a request.
   </details>

3. **Which pillar would you use to see error trends over the last week?**
   <details>
   <summary>Click to see answer</summary>
   Metrics - they're great for aggregated data over time.
   </details>

4. **You see "Error rate spiking" in metrics. What's your next step?**
   <details>
   <summary>Click to see answer</summary>
   Look at traces to find specific failed requests, then check logs for those trace IDs to see error messages.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now understand observability fundamentals!

**Next**: [Lesson 2: OpenTelemetry Basics →](02-opentelemetry-basics.md)

In the next lesson, you'll learn:
- What OpenTelemetry is and why it was created
- How it unifies the three pillars
- The architecture of an OTel-instrumented system

---

**Progress**: ✅ Lesson 1 complete | ⬜ 13 lessons remaining
