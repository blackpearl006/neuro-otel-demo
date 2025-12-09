# Lesson 13: Production Practices

**Estimated time**: 45-55 minutes

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

✅ Know how to run observability in production
✅ Understand cost optimization strategies
✅ Learn retention and storage policies
✅ Know security best practices
✅ Understand high availability and scaling

---

## Running in Production

Taking observability from development to production requires careful planning.

---

## Cost Optimization

**Problem**: Observability can be expensive at scale.

**Key costs**:
- Storage (traces, metrics, logs)
- Compute (collector, backends)
- Network (data transfer)

---

### Strategy 1: Sampling

**Reduce trace volume** without losing critical data.

#### Head-Based Sampling

Keep a percentage of all traces:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Keep 10% of traces
sampler = TraceIdRatioBased(0.1)
```

**Pros**: Simple, predictable costs
**Cons**: May lose important traces (errors, slow requests)

---

#### Tail-Based Sampling (Recommended)

Keep all errors and slow traces, sample the rest:

**Collector config**:

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: slow
        type: latency
        latency:
          threshold_ms: 2000  # > 2 seconds
      - name: sample_rest
        type: probabilistic
        probabilistic:
          sampling_percentage: 5  # Only 5% of normal traces
```

**Result**:
- 100% of errors kept
- 100% of slow requests kept
- 5% of fast, successful requests kept
- **~80-90% cost reduction**

---

### Strategy 2: Reduce Metric Cardinality

**Problem**: High cardinality = many time series = expensive.

**Bad**:

```python
# ❌ Creates 100,000 time series (one per user)
requests_counter.add(1, {"user_id": user_id})
```

**Good**:

```python
# ✅ Creates 3 time series (one per tier)
requests_counter.add(1, {"user_tier": "free|pro|enterprise"})
```

**Best practice**:
- Keep label cardinality < 100 per label
- Use aggregations instead of per-entity metrics
- Drop unnecessary labels

---

### Strategy 3: Retention Policies

**Don't keep data forever** - it's expensive.

#### Prometheus Retention

```yaml
# docker-compose.yml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Keep 30 days
    - '--storage.tsdb.retention.size=50GB'  # Or 50GB max
```

**Recommendation**: 15-30 days for metrics

---

#### Loki Retention

```yaml
# loki-config.yaml
compactor:
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

limits_config:
  retention_period: 168h  # 7 days
```

**Recommendation**: 7-14 days for logs

---

#### Tempo Retention

```yaml
# tempo-config.yaml
compactor:
  compaction:
    block_retention: 168h  # 7 days
```

**Recommendation**: 7-14 days for traces

---

### Strategy 4: Compress and Optimize

**Enable compression** everywhere:

```yaml
# Collector
exporters:
  otlp:
    compression: gzip  # Reduces network traffic by ~70%
```

**Use object storage**:
- S3, GCS, Azure Blob (cheap long-term storage)
- Lifecycle policies (move old data to cheaper tiers)

---

### Strategy 5: Filter Unnecessary Data

**Drop health checks and debug endpoints**:

```yaml
processors:
  filter:
    traces:
      span:
        - 'attributes["http.target"] =~ "/health|/ping|/debug"'
```

**Result**: 20-30% reduction in trace volume for typical web apps.

---

## Security Best Practices

### 1. Don't Log Sensitive Data

**Bad**:

```python
logger.info(f"User logged in: email={email}, password={password}")  # ❌
```

**Good**:

```python
logger.info(f"User logged in: user_id={user_id}")  # ✅
```

**Always scrub**:
- Passwords
- API keys
- Credit card numbers
- SSNs
- PII (personal identifiable information)

---

### 2. Redact in the Collector

**Add processor** to remove sensitive attributes:

```yaml
processors:
  attributes:
    actions:
      - key: password
        action: delete
      - key: credit_card
        action: delete
      - key: ssn
        action: delete
      - key: email
        action: hash  # Hash instead of plaintext
```

---

### 3. Enable TLS

**Encrypt data in transit**:

```yaml
exporters:
  otlp:
    endpoint: tempo:4317
    tls:
      insecure: false  # Enable TLS
      cert_file: /certs/client.crt
      key_file: /certs/client.key
```

---

### 4. Implement Access Control

**Grafana**:
- Enable authentication
- Use RBAC (Role-Based Access Control)
- Limit dashboard editing to admins
- Audit logs for access

**Backends**:
- Enable authentication on Prometheus, Loki, Tempo
- Use API keys or OAuth
- Network policies (firewall rules)

---

### 5. Data Retention and Privacy

**Comply with regulations** (GDPR, HIPAA):
- Delete data after retention period
- Provide user data deletion on request
- Anonymize user identifiers
- Document what data is collected

---

## High Availability and Scaling

### Collector Scaling

**Problem**: Single collector is a bottleneck and single point of failure.

**Solution**: Deploy multiple collectors.

#### Horizontal Scaling (Multiple Instances)

```
App 1 ──┐
App 2 ──┼──→ Load Balancer ──┬──→ Collector 1 ──┐
App 3 ──┘                     ├──→ Collector 2 ──┼──→ Backends
                              └──→ Collector 3 ──┘
```

**Benefits**:
- High availability (one dies, others continue)
- Load distribution
- Horizontal scalability

**Implementation**:
- Use Kubernetes with multiple collector pods
- Use load balancer (round-robin or least connections)
- Stateless collectors (no local state)

---

#### Agent + Gateway Architecture

```
App 1 → Agent 1 ──┐
App 2 → Agent 2 ──┼──→ Gateway Collectors ──→ Backends
App 3 → Agent 3 ──┘
```

**Agent (on each host)**:
- Local buffering
- Initial processing (filtering, sampling)
- Resilience to gateway failures

**Gateway (centralized)**:
- Advanced processing
- Routing to multiple backends
- Cost optimization (sampling, filtering)

---

### Backend Scaling

#### Prometheus

**Single instance** is often enough for small-medium deployments.

**For larger scale**:
- **Thanos**: Multi-cluster, long-term storage
- **Cortex**: Horizontally scalable Prometheus
- **Mimir**: Grafana's scalable metrics backend

---

#### Loki

**Modes**:
- **Monolithic**: Single binary (small scale)
- **Microservices**: Separate components (large scale)
  - Distributor (receives logs)
  - Ingester (writes to storage)
  - Querier (handles queries)
  - Compactor (compacts blocks)

**Scaling**:
- Add more ingesters for write throughput
- Add more queriers for read throughput
- Use object storage (S3, GCS)

---

#### Tempo

**Modes**:
- **Monolithic**: Single binary (small scale)
- **Microservices**: Separate components (large scale)

**Scaling**:
- Horizontal scaling of each component
- Object storage for traces
- Memcached for caching

---

## Alerting Strategies

### What to Alert On

**Do alert on**:
- High error rate (> 5%)
- High latency (P95 > SLA)
- Service down (up metric = 0)
- Disk/memory near capacity (> 85%)
- Certificate expiration (< 7 days)

**Don't alert on**:
- Individual errors (too noisy)
- Small latency blips (< 1 second)
- Metrics that auto-recover
- Development/test environments

---

### Alert Severity Levels

**Critical (P0)**:
- Service completely down
- Data loss occurring
- Security breach

**Action**: Page on-call engineer immediately

---

**High (P1)**:
- Degraded service (> 10% error rate)
- SLA breach imminent

**Action**: Page during business hours, alert off-hours

---

**Medium (P2)**:
- Elevated errors (5-10%)
- Performance degradation

**Action**: Ticket created, investigate next business day

---

**Low (P3)**:
- Warning signs (increasing errors)
- Resource utilization high

**Action**: Monitor, investigate when convenient

---

### Alert Fatigue Prevention

**Problem**: Too many alerts → ignored alerts → real issues missed.

**Solutions**:

1. **Reduce noise**: Only alert on actionable issues
2. **Group alerts**: Combine related alerts
3. **Silence during maintenance**: Temporary mutes
4. **Tune thresholds**: Adjust based on false positives
5. **Escalation policies**: Route based on severity

---

## Monitoring the Monitoring

**Don't forget to monitor your observability stack!**

### Collector Health

**Metrics to watch**:
```promql
# Collector receiving data?
otelcol_receiver_accepted_spans

# Collector exporting data?
otelcol_exporter_sent_spans

# Collector errors?
otelcol_exporter_send_failed_spans

# Collector memory usage?
process_resident_memory_bytes{job="otel-collector"}
```

**Alerts**:
- Collector not receiving data (input problem)
- Collector not exporting data (output problem)
- High error rate on exports (backend issues)
- High memory usage (resource pressure)

---

### Backend Health

**Prometheus**:
```promql
# Prometheus up?
up{job="prometheus"}

# Scrape success rate?
up{job="otel-collector"}

# Query duration?
prometheus_engine_query_duration_seconds
```

**Loki**:
```promql
# Loki up?
up{job="loki"}

# Ingester accepting logs?
loki_distributor_bytes_received_total
```

**Tempo**:
```promql
# Tempo up?
up{job="tempo"}

# Traces ingested?
tempo_ingester_traces_created_total
```

---

## Capacity Planning

### Estimating Storage Needs

**Metrics (Prometheus)**:
- **Formula**: `samples/sec * retention_days * bytes_per_sample`
- **Example**: 100k samples/sec * 30 days * 2 bytes = 518GB

**Logs (Loki)**:
- **Formula**: `logs/sec * avg_log_size * retention_days`
- **Example**: 1000 logs/sec * 500 bytes * 7 days = 302GB

**Traces (Tempo)**:
- **Formula**: `traces/sec * avg_trace_size * retention_days * (1 - sampling_rate)`
- **Example**: 100 traces/sec * 50KB * 7 days * 0.1 = 302GB

---

### Estimating Compute Needs

**Collector**:
- CPU: 1 core per 10k spans/sec
- Memory: 2GB baseline + 1GB per 10k spans/sec

**Prometheus**:
- CPU: 1 core per 1M samples/sec
- Memory: 2GB per 1M active time series

**Loki**:
- CPU: 1 core per 100MB/sec ingest
- Memory: 4GB baseline + scale with query load

**Tempo**:
- CPU: 1 core per 500 traces/sec
- Memory: 4GB baseline + scale with query load

---

## Disaster Recovery

### Backup Strategy

**What to back up**:
- ✅ Grafana dashboards (export JSON)
- ✅ Alert rules (export YAML)
- ✅ Collector configs (version control)
- ✅ Datasource configs (version control)

**What NOT to back up**:
- ❌ Metrics (ephemeral, recreated from apps)
- ❌ Logs (ephemeral, recreated from apps)
- ❌ Traces (ephemeral, recreated from apps)

**Exception**: If observability data is business-critical (audit logs), back up to cold storage.

---

### Recovery Procedures

**Collector failure**:
1. Deploy new collector instance
2. Point apps to new collector
3. Data loss: Only data during outage

**Prometheus failure**:
1. Deploy new Prometheus
2. Data loss: Only data during outage
3. Historical data: Gone (use remote write to backup)

**Grafana failure**:
1. Deploy new Grafana
2. Import backed-up dashboards
3. Reconnect datasources

---

## Cost Monitoring

### Track Observability Costs

**Set up billing alerts**:
- Storage costs (GB stored)
- Compute costs (CPU/memory hours)
- Network costs (data transfer)

**Optimize based on trends**:
- If storage growing: Reduce retention or sampling
- If compute growing: Optimize queries or scale backends
- If network growing: Enable compression

---

### Cost Per Service

**Tag resources** by service:

```yaml
resource:
  attributes:
    - key: service.name
      value: neuro-preprocess
    - key: cost.center
      value: research
```

**Query costs** by service:
```promql
sum by (service_name) (storage_bytes)
```

**Chargeback**: Bill teams based on their observability usage.

---

## Best Practices Summary

### Configuration Management

✅ Store configs in version control (Git)
✅ Use infrastructure as code (Terraform, Ansible)
✅ Document all changes
✅ Test configs in staging before production

---

### Performance

✅ Enable compression everywhere
✅ Use batching (collector processor)
✅ Implement sampling for high-traffic services
✅ Monitor collector/backend resource usage

---

### Reliability

✅ Deploy multiple collector instances
✅ Use load balancers
✅ Set up alerting on observability stack health
✅ Have disaster recovery procedures

---

### Security

✅ Scrub sensitive data (passwords, PII)
✅ Enable TLS for data in transit
✅ Implement access control
✅ Regular security audits

---

### Cost

✅ Implement sampling (tail-based)
✅ Set retention policies (7-30 days)
✅ Reduce metric cardinality
✅ Filter unnecessary data (health checks)
✅ Monitor and optimize costs regularly

---

## Real-World Production Setup

Here's a typical production architecture:

```
┌────────────────────────────────────────────────────┐
│              Applications (VMs/Pods)               │
│  App 1, App 2, App 3, ... App N                    │
└───────────────┬────────────────────────────────────┘
                │ OTLP
                ▼
┌────────────────────────────────────────────────────┐
│        Agent Collectors (on each host/pod)         │
│  • Local buffering                                 │
│  • Basic filtering                                 │
└───────────────┬────────────────────────────────────┘
                │ OTLP (compressed)
                ▼
┌────────────────────────────────────────────────────┐
│   Gateway Collectors (centralized, HA)             │
│  • Load balanced (3+ instances)                    │
│  • Tail-based sampling                             │
│  • Advanced filtering                              │
│  • Routing to backends                             │
└──────┬─────────────┬─────────────┬─────────────────┘
       │             │             │
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Tempo    │  │Prometheus│  │  Loki    │
│ (Scaled) │  │ (HA pair)│  │ (Scaled) │
│          │  │          │  │          │
│ S3       │  │ S3       │  │ S3       │
│ Storage  │  │ Remote   │  │ Storage  │
│          │  │ Write    │  │          │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      │             │             │
      └─────────────┼─────────────┘
                    │
              ┌─────▼─────┐
              │  Grafana  │
              │   (HA)    │
              └───────────┘
```

**Key features**:
- Agent collectors for local buffering
- Gateway collectors for centralized processing (HA)
- Object storage (S3) for cheap long-term storage
- Grafana HA for reliability
- Load balancers at every tier

---

## Key Takeaways

1. **Cost optimization**: Sampling, retention policies, cardinality reduction
2. **Security**: Scrub sensitive data, enable TLS, access control
3. **High availability**: Multiple collectors, load balancing, agent+gateway
4. **Alerting**: Alert on actionable issues, prevent alert fatigue
5. **Capacity planning**: Estimate storage and compute needs
6. **Monitor the monitoring**: Watch collector and backend health
7. **Disaster recovery**: Back up configs, not data
8. **Best practices**: Version control, IaC, testing, documentation

---

## Quiz

1. **What's the difference between head-based and tail-based sampling?**
   <details>
   <summary>Click to see answer</summary>
   Head-based: Decide at trace start (simple, may lose errors). Tail-based: Decide after trace completes (keeps errors/slow, more complex).
   </details>

2. **What should you set for retention policies?**
   <details>
   <summary>Click to see answer</summary>
   Metrics: 15-30 days, Logs: 7-14 days, Traces: 7-14 days. Balance between debuggability and cost.
   </details>

3. **What data should you back up in your observability stack?**
   <details>
   <summary>Click to see answer</summary>
   Dashboards, alert rules, configs, datasources. NOT metrics/logs/traces (ephemeral, recreated from apps).
   </details>

4. **How do you prevent alert fatigue?**
   <details>
   <summary>Click to see answer</summary>
   Only alert on actionable issues, group related alerts, tune thresholds, silence during maintenance, use escalation policies.
   </details>

---

## Next Steps

🎉 **Congratulations!** You now know how to run observability in production!

**Next**: [Lesson 14: Advanced Topics →](14-advanced-topics.md)

In the final lesson, you'll learn:
- Advanced sampling strategies
- Cardinality explosion and solutions
- Custom exporters and processors
- OpenTelemetry SDK internals

---

**Progress**: ✅ Lessons 1-13 complete | ⬜ 1 lesson remaining
