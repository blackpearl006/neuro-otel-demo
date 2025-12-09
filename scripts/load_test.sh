#!/bin/bash

# Load Testing Script for Observability Stack
# Tests performance under high volume

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Configuration
INPUT_DIR="data/input"
OUTPUT_DIR="data/output/load_test"
NUM_FILES=${1:-50}  # Default: 50 files

print_header "Load Testing - $NUM_FILES Files"

# Check if neuro-preprocess is installed
if ! command -v neuro-preprocess &> /dev/null; then
    print_error "neuro-preprocess is not installed!"
    exit 1
fi

# Check if observability stack is running
if ! docker-compose ps | grep -q "Up"; then
    print_error "Observability stack is not running!"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

# Create directories
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

# Generate test files
print_info "Generating $NUM_FILES test files..."

for i in $(seq 1 $NUM_FILES); do
    filename=$(printf "load-test-%03d_T1w.nii.gz" $i)
    filepath="$INPUT_DIR/$filename"

    if [ ! -f "$filepath" ]; then
        # Create files with random sizes (1-10 MB)
        size=$((RANDOM % 9 + 1))
        dd if=/dev/urandom of="$filepath" bs=1M count=$size status=none 2>/dev/null
    fi

    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo -ne "\r  Generated $i/$NUM_FILES files"
    fi
done

echo ""
print_success "Generated $NUM_FILES test files"
echo ""

# Pre-test metrics check
print_info "Recording baseline metrics..."
BASELINE_TIME=$(date +%s)
sleep 2

# Run load test
print_header "Starting Load Test"
echo ""
print_info "Processing $NUM_FILES files..."
echo ""

START_TIME=$(date +%s)

# Process all files
neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR" --pattern "load-test-*.nii.gz"

END_TIME=$(date +%s)

# Calculate statistics
TOTAL_TIME=$((END_TIME - START_TIME))
AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $NUM_FILES" | bc)
THROUGHPUT=$(echo "scale=2; $NUM_FILES / $TOTAL_TIME" | bc)

echo ""
print_header "Load Test Results"
echo ""
echo "Total files processed: $NUM_FILES"
echo "Total time: ${TOTAL_TIME}s"
echo "Average time per file: ${AVG_TIME}s"
echo "Throughput: ${THROUGHPUT} files/sec"
echo ""

# Check resource usage
print_info "Resource Usage:"
echo ""

# Docker stats (snapshot)
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6

echo ""

# Check data in backends
print_info "Checking data in backends..."
echo ""

# Check Prometheus
PROM_METRICS=$(curl -s http://localhost:9090/api/v1/query?query=neuro_files_processed_total | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
echo "  Prometheus - Total files processed: $PROM_METRICS"

# Check Loki (count log lines)
# Note: This is approximate
echo "  Loki - Check logs in Grafana"

# Check Tempo (count traces)
echo "  Tempo - Check traces in Grafana"

echo ""

# Performance analysis
print_header "Performance Analysis"
echo ""

if (( $(echo "$THROUGHPUT < 0.5" | bc -l) )); then
    print_error "Low throughput detected (< 0.5 files/sec)"
    echo "  Consider:"
    echo "  - Reducing processing complexity"
    echo "  - Optimizing telemetry batching"
    echo "  - Checking collector/backend performance"
elif (( $(echo "$THROUGHPUT < 1.0" | bc -l) )); then
    echo -e "${YELLOW}⚠ Moderate throughput ($THROUGHPUT files/sec)${NC}"
    echo "  Performance is acceptable but could be improved"
else
    print_success "Good throughput ($THROUGHPUT files/sec)"
fi

echo ""

# Memory check
GRAFANA_MEM=$(docker stats grafana --no-stream --format "{{.MemUsage}}" | awk '{print $1}')
PROMETHEUS_MEM=$(docker stats prometheus --no-stream --format "{{.MemUsage}}" | awk '{print $1}')

echo "Memory usage:"
echo "  Grafana: $GRAFANA_MEM"
echo "  Prometheus: $PROMETHEUS_MEM"

echo ""

# Recommendations
print_header "Recommendations"
echo ""

echo "1. View detailed metrics in Grafana:"
echo "   http://localhost:3000/d/neuroimaging-pipeline"
echo ""
echo "2. Check for slow queries in Prometheus:"
echo "   http://localhost:9090/graph"
echo ""
echo "3. Analyze trace patterns in Tempo via Grafana Explore"
echo ""
echo "4. Monitor resource usage:"
echo "   docker stats"
echo ""

# Cleanup option
echo ""
read -p "Clean up test files? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Cleaning up..."
    rm -f "$INPUT_DIR"/load-test-*.nii.gz
    rm -rf "$OUTPUT_DIR"
    print_success "Cleanup complete"
fi

print_success "Load test completed!"
