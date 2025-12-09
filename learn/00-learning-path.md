# OpenTelemetry Learning Path

Welcome to your journey into modern observability! This tutorial series will take you from complete beginner to confident practitioner.

---

## 🎯 What You'll Learn

By the end of this series, you will:

✅ **Understand** what observability is and why it matters
✅ **Master** the three pillars: traces, metrics, and logs
✅ **Use** Prometheus, Loki, and Tempo like a pro
✅ **Instrument** your own applications with OpenTelemetry
✅ **Debug** production issues using telemetry data
✅ **Optimize** performance and reduce costs

---

## 📚 Learning Path (15 Lessons)

### 🟢 **Part 1: Foundations** (Start Here!)

**Time**: ~2-3 hours

1. **[01-observability-fundamentals.md](01-observability-fundamentals.md)**
   *What is observability? Why do we need it?*
   - Monitoring vs. Observability
   - The three pillars explained
   - When to use each pillar

2. **[02-opentelemetry-basics.md](02-opentelemetry-basics.md)**
   *What is OpenTelemetry and why does it exist?*
   - History and motivation
   - Architecture overview
   - Key components

---

### 🟡 **Part 2: The Three Pillars Deep Dive**

**Time**: ~4-5 hours

3. **[03-distributed-tracing.md](03-distributed-tracing.md)**
   *Understanding distributed traces and spans*
   - What is a trace?
   - Spans and context propagation
   - Trace IDs and parent-child relationships

4. **[04-metrics-deep-dive.md](04-metrics-deep-dive.md)**
   *Counters, histograms, and gauges explained*
   - Metric types and when to use them
   - Aggregations and percentiles
   - Cardinality considerations

5. **[05-structured-logging.md](05-structured-logging.md)**
   *Logging with context and correlation*
   - Structured vs. unstructured logs
   - Log levels and when to use them
   - Correlating logs with traces

---

### 🔵 **Part 3: The Storage Backends**

**Time**: ~4-5 hours

6. **[06-prometheus-guide.md](06-prometheus-guide.md)**
   *How Prometheus stores and queries metrics*
   - Time-series databases explained
   - PromQL query language
   - Scraping vs. pushing metrics

7. **[07-loki-guide.md](07-loki-guide.md)**
   *How Loki aggregates and searches logs*
   - Label-based indexing
   - LogQL query language
   - Loki vs. Elasticsearch

8. **[08-tempo-guide.md](08-tempo-guide.md)**
   *How Tempo stores and queries traces*
   - Trace storage strategies
   - TraceQL query language
   - Finding traces efficiently

---

### 🟣 **Part 4: The Glue - OpenTelemetry Collector**

**Time**: ~3-4 hours

9. **[09-otel-collector.md](09-otel-collector.md)**
   *The central hub for all your telemetry*
   - Collector architecture
   - Receivers, processors, exporters
   - Pipeline configuration

10. **[10-data-flow-explained.md](10-data-flow-explained.md)**
    *How all the pieces communicate*
    - End-to-end data flow
    - OTLP protocol
    - Network topology

---

### 🟠 **Part 5: Practical Skills**

**Time**: ~4-5 hours

11. **[11-instrumentation-patterns.md](11-instrumentation-patterns.md)**
    *How to instrument your code*
    - Manual vs. automatic instrumentation
    - Common patterns
    - Best practices

12. **[12-hands-on-exercises.md](12-hands-on-exercises.md)**
    *Practice with real examples*
    - Exercise 1: Add custom metrics
    - Exercise 2: Create custom spans
    - Exercise 3: Build a dashboard

---

### 🔴 **Part 6: Advanced Topics**

**Time**: ~3-4 hours

13. **[13-production-practices.md](13-production-practices.md)**
    *Running observability in production*
    - Cost optimization
    - Retention policies
    - Alerting strategies

14. **[14-advanced-topics.md](14-advanced-topics.md)**
    *Advanced concepts and techniques*
    - Sampling strategies
    - Cardinality explosion
    - Tail-based sampling

---

## 🗺️ Recommended Learning Paths

### Path A: **"I'm New to Observability"**

**Timeline**: 2-3 weeks (1-2 hours/day)

```
Week 1: Lessons 1-5 (Foundations + Three Pillars)
Week 2: Lessons 6-10 (Storage + Collector)
Week 3: Lessons 11-14 (Practical + Advanced)
```

**Approach**:
- Read each lesson thoroughly
- Run the hands-on examples in our project
- Complete the quizzes
- Build one dashboard per week

---

### Path B: **"I Know Monitoring, New to OTel"**

**Timeline**: 1 week (2-3 hours/day)

```
Day 1-2: Lessons 1-3 (Skim fundamentals, focus on OTel)
Day 3-4: Lessons 6-10 (Storage backends + collector)
Day 5-7: Lessons 11-14 (Instrumentation + advanced)
```

**Approach**:
- Skim familiar concepts
- Focus on OTel-specific patterns
- Build 2-3 dashboards
- Instrument a real project

---

### Path C: **"I Want Hands-On First"**

**Timeline**: 1-2 weeks (flexible)

```
Start: Lesson 12 (Hands-on exercises)
Then: Lessons 1-5 (Go back and learn theory)
Then: Lessons 6-11 (Deep dives)
Finally: Lessons 13-14 (Advanced)
```

**Approach**:
- Start by doing
- Learn theory when you hit questions
- Iterate between practice and learning

---

## 🎓 How to Use This Tutorial

### Before Each Lesson

1. ✅ Make sure Docker is running
2. ✅ Start the observability stack: `./scripts/start_stack.sh`
3. ✅ Open Grafana in your browser: http://localhost:3000

### During Each Lesson

1. 📖 **Read actively** - Don't just skim
2. 💻 **Try the examples** - Run every code snippet
3. 🤔 **Ask yourself** - Answer the quiz questions
4. 🧪 **Experiment** - Try variations of the examples

### After Each Lesson

1. ✅ Complete the "Try It Yourself" section
2. ✅ Check your understanding with the quiz
3. ✅ Optionally: Take notes on what you learned
4. ✅ Move to the next lesson (or take a break!)

---

## 📝 Prerequisites

### Required Knowledge

- **Basic programming** (Python preferred, but any language works)
- **Command line basics** (cd, ls, running scripts)
- **Basic understanding of** web applications and APIs

### Optional but Helpful

- Docker basics
- HTTP/REST APIs
- Basic statistics (mean, median, percentiles)

### No Experience Needed With

- ❌ OpenTelemetry (we'll teach you!)
- ❌ Prometheus, Loki, or Tempo
- ❌ Distributed systems
- ❌ Observability concepts

---

## 🛠️ Setup Your Environment

Before starting, ensure you have:

1. **This project cloned and running**
   ```bash
   cd neuro-otel-demo
   docker-compose up -d
   ```

2. **Python app installed**
   ```bash
   cd app/
   pip install -e .
   ```

3. **Verify everything works**
   ```bash
   ./scripts/check_health.sh
   ```

---

## 💡 Learning Tips

### 1. **Learn by Doing**
Don't just read - run every example. Modify them. Break them. Fix them.

### 2. **Use Our Project**
This project is your sandbox. Every lesson references it. Process files, view dashboards, run queries.

### 3. **Visualize Everything**
Always have Grafana open. See how your code changes affect the dashboards.

### 4. **Ask "Why?"**
Don't memorize - understand. If something doesn't make sense, go back and re-read.

### 5. **Take Breaks**
Observability is deep. Don't rush. Better to learn 1 lesson well than skim 10.

### 6. **Build Something**
The best way to learn is to build. By Lesson 12, start instrumenting your own project.

---

## 🎯 Learning Goals by Part

### After Part 1 (Foundations)
You will be able to:
- ✅ Explain what observability is
- ✅ Describe the three pillars
- ✅ Understand why OpenTelemetry exists

### After Part 2 (Three Pillars)
You will be able to:
- ✅ Read and understand trace waterfall diagrams
- ✅ Choose the right metric type for your use case
- ✅ Write structured logs with proper context

### After Part 3 (Storage Backends)
You will be able to:
- ✅ Write PromQL queries to analyze metrics
- ✅ Write LogQL queries to search logs
- ✅ Find traces in Tempo using TraceQL

### After Part 4 (Collector)
You will be able to:
- ✅ Configure the OTel Collector
- ✅ Understand how data flows through the system
- ✅ Debug telemetry pipeline issues

### After Part 5 (Practical)
You will be able to:
- ✅ Instrument a Python application with OTel
- ✅ Add custom metrics and spans
- ✅ Build Grafana dashboards

### After Part 6 (Advanced)
You will be able to:
- ✅ Implement sampling strategies
- ✅ Optimize costs and performance
- ✅ Run observability in production

---

## 📚 Additional Resources

### During the Tutorial

- **Our Project Docs**: See `layman_docs/` for beginner explanations
- **Grafana**: http://localhost:3000 (keep this open!)
- **Code Examples**: All lessons reference `app/neuro_preprocess/`

### After the Tutorial

- **Official OTel Docs**: https://opentelemetry.io/docs/
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **Community**: OpenTelemetry Slack, GitHub Discussions

---

## 🆘 Getting Help

### If You're Stuck

1. **Re-read the lesson** - Sometimes it clicks on the second read
2. **Check `layman_docs/`** - Simpler explanations of the same concepts
3. **Run `check_health.sh`** - Maybe something is broken
4. **Look at the code** - See how we implemented it in `app/`
5. **Check troubleshooting** - See `layman_docs/05-troubleshooting.md`

### Common Issues

- **No data in Grafana?** → Process some files first
- **Container errors?** → Check Docker logs: `docker-compose logs`
- **Query errors?** → Start with simple queries, build up complexity

---

## 🚀 Ready to Start?

Great! Here's your first step:

**👉 Start with [Lesson 1: Observability Fundamentals](01-observability-fundamentals.md)**

Take your time, experiment, and most importantly - **have fun learning!**

Remember: The goal isn't to memorize everything. The goal is to build intuition about observability and confidence in using these tools.

Good luck! 🎓✨

---

## 📊 Track Your Progress

Use this checklist to track your learning:

- [ ] Lesson 1: Observability Fundamentals
- [ ] Lesson 2: OpenTelemetry Basics
- [ ] Lesson 3: Distributed Tracing
- [ ] Lesson 4: Metrics Deep Dive
- [ ] Lesson 5: Structured Logging
- [ ] Lesson 6: Prometheus Guide
- [ ] Lesson 7: Loki Guide
- [ ] Lesson 8: Tempo Guide
- [ ] Lesson 9: OTel Collector
- [ ] Lesson 10: Data Flow Explained
- [ ] Lesson 11: Instrumentation Patterns
- [ ] Lesson 12: Hands-On Exercises
- [ ] Lesson 13: Production Practices
- [ ] Lesson 14: Advanced Topics

**Completion Goal**: ___ / 14 lessons

---

**Next**: [Lesson 1: Observability Fundamentals →](01-observability-fundamentals.md)
