#!/bin/bash

# Start the OpenTelemetry Observability Stack
# This script starts all backend services and waits for them to be ready

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_header "Starting OpenTelemetry Observability Stack"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed!"
    echo ""
    echo "Please install Docker Desktop or docker-compose"
    exit 1
fi

# Check if already running
if docker-compose ps | grep -q "Up"; then
    print_info "Services are already running. Restarting..."
    docker-compose restart
else
    print_info "Starting all services..."
    docker-compose up -d
fi

echo ""
print_info "Waiting for services to be healthy..."
echo ""

# Wait for services to be ready (max 60 seconds)
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if all services are healthy
    HEALTHY=$(docker-compose ps | grep -c "(healthy)" || true)
    TOTAL=$(docker-compose ps | grep -c "Up" || true)

    if [ "$HEALTHY" -eq 5 ]; then
        echo ""
        print_success "All services are healthy!"
        break
    fi

    echo -ne "\r  Healthy: $HEALTHY/5  (waiting ${ELAPSED}s)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo ""
    print_error "Timeout waiting for services to be healthy"
    echo ""
    echo "Check service status with:"
    echo "  docker-compose ps"
    echo "  docker-compose logs"
    exit 1
fi

# Show service status
echo ""
print_info "Service Status:"
docker-compose ps

echo ""
print_success "Observability stack is ready!"
echo ""
echo "Access points:"
echo "  Grafana:     http://localhost:3000  (admin/admin)"
echo "  Prometheus:  http://localhost:9090"
echo "  Loki:        http://localhost:3100"
echo "  Tempo:       http://localhost:3200"
echo "  Collector:   http://localhost:4317  (OTLP gRPC)"
echo ""
echo "Next steps:"
echo "  1. Run a demo scenario:"
echo "     ./scripts/run_demo.sh normal"
echo ""
echo "  2. Or process a file manually:"
echo "     neuro-preprocess process data/input/file.nii.gz -o data/output"
echo ""
echo "  3. View telemetry in Grafana:"
echo "     - Dashboard: http://localhost:3000/d/neuroimaging-pipeline"
echo "     - Explore: http://localhost:3000/explore"
echo ""
