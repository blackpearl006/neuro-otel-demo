#!/bin/bash

# build_all.sh - Build all Docker containers for the observability stack
# Usage: ./build_all.sh [--no-cache]

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Building Docker Observability Stack${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: docker command not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}ERROR: docker-compose not found${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine which compose command to use
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

echo "Docker version:"
docker --version
echo ""
echo "Compose command: $COMPOSE_CMD"
$COMPOSE_CMD version
echo ""

# Build flags
BUILD_FLAGS=""
if [ "$1" == "--no-cache" ]; then
    BUILD_FLAGS="--no-cache"
    echo -e "${YELLOW}Building with --no-cache flag${NC}"
    echo ""
fi

# List of services to build (excludes app for now)
declare -a SERVICES=(
    "otel-collector"
    "prometheus"
    "loki"
    "tempo"
    "grafana"
    # "app"  # Uncomment when app code is ready in Phase 3
)

echo -e "${YELLOW}Building the following services:${NC}"
for service in "${SERVICES[@]}"; do
    echo "  - $service"
done
echo ""

# Build all services
echo -e "${YELLOW}Starting build process...${NC}"
echo ""

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}Building ${service}...${NC}"

    if $COMPOSE_CMD build $BUILD_FLAGS "$service"; then
        echo -e "${GREEN}✓ Successfully built ${service}${NC}"
        echo ""
    else
        echo -e "${RED}✗ Failed to build ${service}${NC}"
        exit 1
    fi
done

# Summary
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}All containers built successfully!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Show image sizes
echo "Container image sizes:"
$COMPOSE_CMD images
echo ""

echo -e "${GREEN}Next steps:${NC}"
echo "1. Start the stack: ${YELLOW}docker-compose up -d${NC}"
echo "2. View logs: ${YELLOW}docker-compose logs -f${NC}"
echo "3. Access Grafana: ${YELLOW}http://localhost:3000${NC} (admin/admin)"
echo "4. Access Prometheus: ${YELLOW}http://localhost:9090${NC}"
echo "5. Stop the stack: ${YELLOW}docker-compose down${NC}"
echo ""
