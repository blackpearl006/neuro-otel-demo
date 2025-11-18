# Troubleshooting Guide - Common Problems and Solutions

This guide helps you fix common issues with the observability stack and preprocessing pipeline.

---

## Quick Diagnostic Checklist

Before diving into specific problems, run this quick check:

```bash
# 1. Are all containers running?
docker-compose ps

# 2. Check container health
docker-compose ps | grep -E "healthy|unhealthy"

# 3. Are there any error logs?
docker-compose logs --tail=50

# 4. Is the app installed?
pip show neuro-preprocess

# 5. Can you reach Grafana?
curl -I http://localhost:3000
```

**Expected results**:
1. All 5 services should show "Up"
2. All services should be "healthy"
3. Logs should not show repeated errors
4. Should show package info
5. Should return HTTP 200

---

## Docker and Container Issues

### Problem 1: "docker: command not found"

**Symptoms**: Can't run docker or docker-compose commands

**Solution**:
```bash
# macOS - Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Linux - Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Problem 2: "Permission denied" on Docker

**Symptoms**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution**:
```bash
# Linux - Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in for changes to take effect
# Or run:
newgrp docker

# macOS - Start Docker Desktop application
open -a Docker
```

### Problem 3: Containers won't start

**Symptoms**: `docker-compose up` fails or containers immediately exit

**Diagnosis**:
```bash
# Check which container is failing
docker-compose ps

# View logs for the failing container
docker-compose logs prometheus    # Replace with failing service
```

**Common causes and fixes**:

**A. Port already in use**
```
Error: Bind for 0.0.0.0:3000 failed: port is already allocated
```
**Fix**: Stop the conflicting service or change the port in docker-compose.yml
```bash
# Find what's using the port
lsof -i :3000    # macOS/Linux
netstat -ano | findstr :3000    # Windows

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
grafana:
  ports:
    - "3001:3000"    # Changed host port to 3001
```

**B. Configuration file error**
```
Error: failed to parse config: ...
```
**Fix**: Check the config file mentioned in the error
```bash
# Validate YAML syntax
docker-compose config

# Check specific config file
cat configs/prometheus.yml
# Look for indentation errors, missing colons, etc.
```

**C. Volume permission error**
```
mkdir: cannot create directory '/tmp/tempo/blocks': Permission denied
```
**Fix**: Already fixed in docker-compose.yml with `user: "0:0"`, but if you see this:
```bash
# Give container write permissions
sudo chown -R 0:0 data/telemetry/tempo/
```

### Problem 4: Containers keep restarting

**Symptoms**: `docker-compose ps` shows containers continuously restarting

**Diagnosis**:
```bash
# Watch logs in real-time
docker-compose logs -f prometheus    # Replace with restarting service

# Common errors:
# - "failed to load config"
# - "connection refused"
# - "no such file or directory"
```

**Solution**:
1. **Fix configuration errors**: Check the logs for config file issues
2. **Wait for dependencies**: Some services need others to start first
   ```bash
   # Restart in order
   docker-compose up -d otel-collector
   sleep 10
   docker-compose up -d prometheus loki tempo
   sleep 10
   docker-compose up -d grafana
   ```
3. **Check disk space**:
   ```bash
   df -h    # Need at least 1GB free
   ```

### Problem 5: "Out of memory" errors

**Symptoms**: Containers killed with "OOMKilled" status

**Solution**:
```bash
# Check Docker memory limit
docker info | grep -i memory

# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory → Increase to 4GB or more

# Or reduce Prometheus retention
# In configs/prometheus.yml (via command args):
--storage.tsdb.retention.time=7d    # Reduce from 15d
```

---

## Telemetry Not Appearing

### Problem 6: No traces in Tempo

**Symptoms**: Explore → Tempo shows "No data"

**Step-by-step diagnosis**:

**Step 1: Did you run the pipeline?**
```bash
# Process a file
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output
```

**Step 2: Check if app is sending telemetry**
```bash
# Look for telemetry initialization message
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output 2>&1 | grep -i otel

# Should see:
# ✓ OpenTelemetry enabled → http://localhost:4317
```

**Step 3: Check if collector received the traces**
```bash
# View collector logs
docker-compose logs otel-collector --tail=100

# Should see lines like:
# "TracesExporter" "traces"
# "Traces" {"dropped_spans": 0}
```

**Step 4: Check if Tempo is running**
```bash
docker-compose ps tempo

# Should show "Up (healthy)"
```

**Step 5: Check Tempo logs**
```bash
docker-compose logs tempo --tail=50

# Should see:
# "tempo started"
# No errors about "failed to write"
```

**Step 6: Verify data is stored**
```bash
# Check if trace files exist
ls -lh data/telemetry/tempo/

# Should see files/directories
```

**Step 7: Check time range in Grafana**
- Set time range to "Last 1 hour"
- Or "Last 5 minutes" if you just ran the pipeline

**If still no data**:
```bash
# Restart the stack
docker-compose restart

# Wait 30 seconds
sleep 30

# Process a file again
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output

# Check Grafana after 10 seconds
```

### Problem 7: No logs in Loki

**Symptoms**: Explore → Loki shows "No data" or empty results

**Quick check**:
```bash
# Test if Loki is receiving logs
docker-compose logs loki --tail=20 | grep -i "POST /otlp"

# Should see POST requests
```

**Common causes**:

**A. Wrong query syntax**
```
# ❌ Wrong
service_name="neuro-preprocess"

# ✅ Correct
{service_name="neuro-preprocess"}
```
Note the curly braces!

**B. Time range issue**
- Set to "Last 1 hour" instead of "Last 5 minutes"
- Logs might be slightly delayed

**C. Loki not receiving logs**
```bash
# Check if OTel collector is sending to Loki
docker-compose logs otel-collector | grep -i loki

# Should see:
# "otlphttp/loki" exporter
```

**Fix**: Restart the collector
```bash
docker-compose restart otel-collector
```

### Problem 8: No metrics in Prometheus

**Symptoms**: Explore → Prometheus shows "No data"

**Check Prometheus targets**:
1. Open: http://localhost:9090
2. Click **Status → Targets**
3. Should see `otel-collector` target with **State: UP**

**If target is DOWN**:
```bash
# Check if collector metrics endpoint is working
curl http://localhost:8889/metrics

# Should return metrics text
```

**Common cause**: Prometheus scrape interval (15 seconds delay)

**Solution**: Wait 15-20 seconds after running pipeline, then refresh Prometheus

**If still no data**:
```bash
# Check if metrics exist
curl http://localhost:8889/metrics | grep neuro_

# Should see lines like:
# neuro_files_processed_total 42
```

**If you see metrics in curl but not Grafana**:
```bash
# Restart Prometheus
docker-compose restart prometheus

# Wait 30 seconds
sleep 30

# Check Grafana again
```

---

## Connection and Network Issues

### Problem 9: Grafana can't connect to datasources

**Symptoms**: "Error: dial tcp: lookup prometheus on 127.0.0.11:53: no such host"

**Cause**: Services can't find each other on Docker network

**Solution**:
```bash
# 1. Check all services are on the same network
docker network inspect neuro-otel-demo_otel-network

# Should list all 5 containers

# 2. If network doesn't exist, recreate it
docker-compose down
docker-compose up -d

# 3. Test connectivity from Grafana to Prometheus
docker-compose exec grafana ping prometheus

# Should succeed
```

### Problem 10: "Connection refused" from application

**Symptoms**: App shows error connecting to `localhost:4317`

**Check 1: Is collector accessible?**
```bash
# Check if port is open
nc -zv localhost 4317

# Or on macOS
telnet localhost 4317
```

**Check 2: Is collector listening?**
```bash
docker-compose exec otel-collector netstat -ln | grep 4317

# Should show:
# tcp  0  0  0.0.0.0:4317  0.0.0.0:*  LISTEN
```

**Solution**:
```bash
# Restart collector
docker-compose restart otel-collector

# Or restart entire stack
docker-compose restart
```

### Problem 11: "OTLP exporter timeout"

**Symptoms**: App logs show "context deadline exceeded" or timeout errors

**Causes**:
1. Collector is overloaded
2. Network issue
3. Exporter batching too large

**Solution 1**: Increase timeout in telemetry setup

Edit `app/neuro_preprocess/telemetry/tracer_setup.py`:
```python
otlp_exporter = OTLPSpanExporter(
    endpoint=otlp_endpoint,
    insecure=True,
    timeout=30  # Increase from default 10 seconds
)
```

**Solution 2**: Reduce batch size

Edit `configs/otel-collector-config.yaml`:
```yaml
processors:
  batch:
    timeout: 1s
    send_batch_size: 100    # Reduce from default
```

Then restart:
```bash
docker-compose restart otel-collector
```

---

## Application Issues

### Problem 12: "neuro-preprocess: command not found"

**Symptoms**: Shell doesn't recognize the command

**Solution**:
```bash
# Check if installed
pip show neuro-preprocess

# If not installed, install it
cd app
pip install -e .

# Verify
neuro-preprocess --version
```

**If using virtual environment**:
```bash
# Activate venv first
source venv/bin/activate    # Linux/macOS
# Or
venv\Scripts\activate       # Windows

# Then install
pip install -e app/
```

### Problem 13: Module import errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'opentelemetry'
ModuleNotFoundError: No module named 'neuro_preprocess'
```

**Solution**:
```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Reinstall the app
pip install -e .

# Verify imports work
python -c "import neuro_preprocess; print('OK')"
```

### Problem 14: Pipeline processing fails

**Symptoms**: File processing fails with errors

**Common errors and fixes**:

**A. "File not found"**
```bash
# Check file exists
ls -lh data/input/sub-001_T1w.nii.gz

# Use absolute path if relative doesn't work
neuro-preprocess process /full/path/to/file.nii.gz -o data/output
```

**B. "Permission denied" writing output**
```bash
# Check output directory permissions
ls -ld data/output

# Create directory if missing
mkdir -p data/output

# Fix permissions
chmod 755 data/output
```

**C. "Validation failed: data contains NaN"**
This is expected behavior if input file has invalid data. Either:
```bash
# Skip validation
neuro-preprocess process file.nii.gz --no-validate

# Or fix the input file
```

---

## Performance Issues

### Problem 15: Dashboard is very slow

**Symptoms**: Grafana takes 10+ seconds to load dashboards

**Solutions**:

**1. Reduce time range**
- Instead of "Last 7 days", use "Last 24 hours"

**2. Limit query data points**
- Edit panel → Query options → Max data points: 1000

**3. Increase query interval**
- Change `[1m]` to `[5m]` in queries
- Example: `rate(metric[5m])` instead of `rate(metric[1m])`

**4. Check Prometheus performance**
```bash
# Check Prometheus query performance
curl 'http://localhost:9090/api/v1/query?query=up' -s | jq '.status'

# Should return quickly
```

**5. Clear browser cache**
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Problem 16: High memory usage

**Symptoms**: Docker using 4GB+ memory, system slow

**Solutions**:

**1. Reduce Prometheus retention**
Edit `docker-compose.yml`:
```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=7d'  # Reduce from 15d
```

**2. Reduce Loki retention**
Edit `configs/loki-config.yaml`:
```yaml
limits_config:
  retention_period: 168h  # 7 days instead of 30
```

**3. Clean old data**
```bash
# Stop services
docker-compose down

# Remove old data
rm -rf data/telemetry/prometheus/*
rm -rf data/telemetry/loki/*
rm -rf data/telemetry/tempo/*

# Start fresh
docker-compose up -d
```

**4. Use Docker Compose resource limits**
Edit `docker-compose.yml`:
```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 512M
```

### Problem 17: Disk space full

**Symptoms**: "no space left on device" errors

**Check disk usage**:
```bash
# Total disk space
df -h

# Docker disk usage
docker system df

# Telemetry data size
du -sh data/telemetry/*
```

**Solutions**:

**1. Prune unused Docker resources**
```bash
# Remove old containers, images, volumes
docker system prune -a

# Warning: This removes all unused data!
```

**2. Clean telemetry data**
```bash
# Remove old Prometheus data (older than 7 days)
docker-compose exec prometheus \
  promtool tsdb delete-series --dry-run \
  '{__name__=~".+"}' --time-range=0d:7d

# Actually delete (remove --dry-run)
```

**3. Reduce retention periods** (see Problem 16)

---

## Query and Visualization Issues

### Problem 18: "Parse error" in queries

**Symptoms**: Red error message when running queries

**Common mistakes**:

**Loki queries**:
```
# ❌ Wrong: Missing braces
service_name="neuro-preprocess"

# ✅ Correct
{service_name="neuro-preprocess"}

# ❌ Wrong: Wrong operator
{service_name="neuro-preprocess"} == "error"

# ✅ Correct
{service_name="neuro-preprocess"} |= "error"
```

**Prometheus queries**:
```
# ❌ Wrong: Missing brackets
rate(neuro_files_processed_total)

# ✅ Correct
rate(neuro_files_processed_total[5m])

# ❌ Wrong: Invalid function
avg_by(neuro_files_processed_total)

# ✅ Correct
avg(neuro_files_processed_total)
```

### Problem 19: Incorrect values in graphs

**Symptoms**: Graphs show unexpected values (negative, too large, etc.)

**Common causes**:

**A. Using cumulative counters directly**
```
# ❌ Wrong: Shows ever-increasing value
neuro_files_processed_total

# ✅ Correct: Shows rate of change
rate(neuro_files_processed_total[5m])
```

**B. Wrong histogram function**
```
# ❌ Wrong: Raw bucket counts
neuro_process_duration_bucket

# ✅ Correct: Calculate percentile
histogram_quantile(0.95, rate(neuro_process_duration_bucket[5m]))
```

**C. Aggregation issues**
```
# If you have multiple instances, use sum()
sum(rate(neuro_files_processed_total[5m]))
```

### Problem 20: Trace-to-logs correlation not working

**Symptoms**: Can't click from trace to logs

**Check datasource configuration**:
```bash
# Verify derivedFields in datasources.yaml
cat configs/grafana/datasources.yaml | grep -A 10 derivedFields
```

**Should contain**:
```yaml
derivedFields:
  - datasourceUid: tempo
    matcherRegex: "trace_id=(\\w+)"
    name: TraceID
    url: "$${__value.raw}"
```

**Solution**:
```bash
# Fix the config file
# Then restart Grafana
docker-compose restart grafana

# Clear browser cache and reload
```

---

## Data Retention and Storage

### Problem 21: Old data disappeared

**Symptoms**: Can't find data from last week

**Cause**: Data retention policies deleted old data

**Check retention settings**:

**Prometheus** (15 days by default in our setup):
```bash
# View retention in Prometheus UI
# http://localhost:9090 → Status → Runtime Information
# Look for "storage.tsdb.retention.time"
```

**Loki** (configured in loki-config.yaml):
```bash
cat configs/loki-config.yaml | grep retention
```

**Tempo** (default: unlimited, but may run out of space):
```bash
# Check disk usage
du -sh data/telemetry/tempo
```

**To keep data longer**: Edit configs and restart services

### Problem 22: Data not persisting after restart

**Symptoms**: After `docker-compose down`, all data is gone

**Cause**: Using `docker-compose down -v` (removes volumes)

**Solution**:
```bash
# Use this to stop (keeps data):
docker-compose down

# NOT this (deletes data):
docker-compose down -v

# To restore: Data is gone, can't recover
# Going forward: Don't use -v flag
```

---

## Advanced Troubleshooting

### Problem 23: Debugging with logs

**View real-time logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prometheus

# Filter logs
docker-compose logs grafana | grep -i error

# Last N lines
docker-compose logs --tail=100 otel-collector
```

### Problem 24: Checking service health

**Manual health checks**:
```bash
# Grafana
curl http://localhost:3000/api/health

# Prometheus
curl http://localhost:9090/-/healthy

# Loki
curl http://localhost:3100/ready

# Tempo
curl http://localhost:3200/ready

# OTel Collector
curl http://localhost:13133/
```

### Problem 25: Resetting everything

**Nuclear option**: Start completely fresh

```bash
# 1. Stop all containers
docker-compose down -v

# 2. Remove telemetry data
rm -rf data/telemetry/*

# 3. Rebuild containers
docker-compose build --no-cache

# 4. Start fresh
docker-compose up -d

# 5. Wait for all services to be healthy
watch docker-compose ps

# 6. Reinstall app
cd app
pip install -e .

# 7. Test with a file
neuro-preprocess process data/input/sub-001_T1w.nii.gz -o data/output

# 8. Check Grafana after 30 seconds
```

---

## Getting Help

### Check the docs

1. **Glossary**: `00-glossary.md` - What does this term mean?
2. **Overview**: `01-overview.md` - What is this component?
3. **How it works**: `02-how-it-works.md` - How does X work?
4. **Viewing telemetry**: `03-viewing-telemetry.md` - How do I see my data?
5. **Creating dashboards**: `04-creating-dashboards.md` - How do I build a dashboard?

### Enable debug logging

**For the application**:
```bash
export OTEL_LOG_LEVEL=debug
neuro-preprocess process file.nii.gz -o data/output
```

**For the collector**:
Edit `configs/otel-collector-config.yaml`:
```yaml
service:
  telemetry:
    logs:
      level: debug
```

Then restart:
```bash
docker-compose restart otel-collector
docker-compose logs -f otel-collector
```

### Check official documentation

- **OpenTelemetry**: https://opentelemetry.io/docs/
- **Grafana**: https://grafana.com/docs/grafana/latest/
- **Prometheus**: https://prometheus.io/docs/
- **Loki**: https://grafana.com/docs/loki/latest/
- **Tempo**: https://grafana.com/docs/tempo/latest/

### Common command reference

```bash
# Start everything
docker-compose up -d

# Stop everything (keeps data)
docker-compose down

# Restart one service
docker-compose restart prometheus

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Rebuild after config changes
docker-compose up -d --force-recreate

# Check resource usage
docker stats

# Enter a container shell
docker-compose exec grafana sh

# Validate docker-compose.yml
docker-compose config
```

---

## Preventive Maintenance

To avoid issues:

**Weekly**:
- Check disk space: `df -h`
- Check logs for errors: `docker-compose logs --tail=100 | grep -i error`

**Monthly**:
- Restart services: `docker-compose restart`
- Clean unused Docker resources: `docker system prune`

**When making changes**:
- Test config syntax before restarting: `docker-compose config`
- Back up working configs: `cp configs/prometheus.yml configs/prometheus.yml.backup`
- Read logs after restart: `docker-compose logs --tail=50`

---

## Summary

**Most common issues**:
1. ✅ Services not running → `docker-compose up -d`
2. ✅ No data in Grafana → Check time range, run pipeline
3. ✅ Connection errors → Restart services
4. ✅ Slow performance → Reduce time range, increase intervals
5. ✅ Out of disk space → Reduce retention, prune old data

**Remember**:
- Check logs first: `docker-compose logs`
- Most issues are fixed by restarting: `docker-compose restart`
- When in doubt, check time range in Grafana
- Wait 15-30 seconds after running pipeline for data to appear

**Still stuck?** Go back to the relevant docs or check the official documentation for each component.

Good luck! 🍀
