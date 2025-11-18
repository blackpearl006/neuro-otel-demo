#!/bin/bash

# Stop the OpenTelemetry Observability Stack
# This script gracefully shuts down all services

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

print_header "Stopping OpenTelemetry Observability Stack"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed!${NC}"
    exit 1
fi

# Stop all services
print_info "Stopping all services..."
docker-compose down

print_success "All services stopped"

echo ""
print_info "Services have been stopped. Data is preserved in volumes."
echo ""
echo "To start again:"
echo "  docker-compose up -d"
echo ""
echo "To remove all data (WARNING: This deletes all telemetry!):"
echo "  docker-compose down -v"
echo ""
