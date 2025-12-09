#!/bin/bash

# Health Check Script for Observability Stack

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "OBSERVABILITY STACK HEALTH CHECK"
echo "========================================"
echo ""

# Check if containers are running
echo "Container Status:"
docker-compose ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null | grep -v "SERVICE"

echo ""
echo "Service Health Checks:"

# Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Grafana: Running (http://localhost:3000)"
else
    echo -e "${RED}✗${NC} Grafana: Not responding"
fi

# Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Prometheus: Running (http://localhost:9090)"
else
    echo -e "${RED}✗${NC} Prometheus: Not responding"
fi

# Loki
if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Loki: Running (http://localhost:3100)"
else
    echo -e "${YELLOW}⚠${NC} Loki: Not ready (may be starting up)"
fi

# Tempo
if curl -s http://localhost:3200/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Tempo: Running (http://localhost:3200)"
else
    echo -e "${YELLOW}⚠${NC} Tempo: Not ready (may be starting up)"
fi

# OTel Collector (check if receiving port is open)
if nc -z localhost 4317 2>/dev/null; then
    echo -e "${GREEN}✓${NC} OTel Collector: Running (port 4317 open)"
else
    echo -e "${RED}✗${NC} OTel Collector: Not responding on port 4317"
fi

echo ""
echo "Data Verification:"

# Check if Prometheus has targets
TARGETS=$(curl -s "http://localhost:9090/api/v1/targets" 2>/dev/null | jq -r '.data.activeTargets | length' 2>/dev/null)
if [ "$TARGETS" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Prometheus: Scraping $TARGETS target(s)"
else
    echo -e "${YELLOW}⚠${NC} Prometheus: No active targets"
fi

# Check if metrics exist
METRICS=$(curl -s "http://localhost:9090/api/v1/query?query=neuro_files_processed_total" 2>/dev/null | jq -r '.data.result | length' 2>/dev/null)
if [ "$METRICS" -gt 0 ]; then
    VALUE=$(curl -s "http://localhost:9090/api/v1/query?query=neuro_files_processed_total" 2>/dev/null | jq -r '.data.result[0].value[1]' 2>/dev/null)
    echo -e "${GREEN}✓${NC} Metrics: $VALUE files processed (data flowing)"
else
    echo -e "${YELLOW}⚠${NC} Metrics: No data yet (process a file first)"
fi

# Check dashboard
DASHBOARD=$(curl -s "http://localhost:3000/api/dashboards/uid/neuroimaging-pipeline" -u admin:admin 2>/dev/null | jq -r '.dashboard.title' 2>/dev/null)
if [ "$DASHBOARD" = "Neuroimaging Pipeline Overview" ]; then
    echo -e "${GREEN}✓${NC} Dashboard: Provisioned successfully"
else
    echo -e "${YELLOW}⚠${NC} Dashboard: Not found or not provisioned"
fi

echo ""
echo "========================================"
echo "QUICK LINKS"
echo "========================================"
echo "Grafana Dashboard: http://localhost:3000/d/neuroimaging-pipeline"
echo "Grafana Explore: http://localhost:3000/explore"
echo "Prometheus: http://localhost:9090"
echo ""
echo "Login: admin / admin"
echo ""
