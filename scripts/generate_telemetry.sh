#!/bin/bash

# Generate Telemetry Data Script
# This script continuously runs neuro-preprocess to generate telemetry data
# for viewing in Grafana dashboards

set -e

# Default values
ITERATIONS=20
SLEEP_TIME=2
FILE_SIZE="small"
INPUT_DIR="data/input"
OUTPUT_DIR="data/output"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --iterations NUM    Number of iterations (default: 20)"
    echo "  -s, --sleep NUM         Sleep time between runs in seconds (default: 2)"
    echo "  -f, --file-size SIZE    File size: small, medium, large, mixed (default: small)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run 20 iterations with small files"
    echo "  $0 -n 50 -s 1                         # Run 50 iterations with 1s sleep"
    echo "  $0 -f mixed -n 30                     # Run 30 iterations with mixed file sizes"
    echo "  $0 -f large -n 10 -s 5                # Run 10 iterations with large files, 5s sleep"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        -s|--sleep)
            SLEEP_TIME="$2"
            shift 2
            ;;
        -f|--file-size)
            FILE_SIZE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Select input file based on size
case $FILE_SIZE in
    small)
        INPUT_FILE="$INPUT_DIR/small-001_T1w.nii.gz"
        ;;
    medium)
        INPUT_FILE="$INPUT_DIR/medium-001_T1w.nii.gz"
        ;;
    large)
        INPUT_FILE="$INPUT_DIR/large-001_T1w.nii.gz"
        ;;
    mixed)
        INPUT_FILE="mixed"
        ;;
    *)
        echo -e "${YELLOW}Unknown file size: $FILE_SIZE. Using small.${NC}"
        INPUT_FILE="$INPUT_DIR/small-001_T1w.nii.gz"
        ;;
esac

# Print configuration
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Telemetry Generation Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Iterations:    ${GREEN}$ITERATIONS${NC}"
echo -e "Sleep time:    ${GREEN}${SLEEP_TIME}s${NC}"
echo -e "File size:     ${GREEN}$FILE_SIZE${NC}"
echo -e "Output:        ${GREEN}$OUTPUT_DIR${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop at any time${NC}"
echo ""
sleep 2

# Main loop
for i in $(seq 1 $ITERATIONS); do
    echo -e "${BLUE}[Run $i/$ITERATIONS]${NC} Processing file..."

    # Select file for mixed mode
    if [ "$INPUT_FILE" == "mixed" ]; then
        case $((i % 3)) in
            0)
                CURRENT_FILE="$INPUT_DIR/small-001_T1w.nii.gz"
                ;;
            1)
                CURRENT_FILE="$INPUT_DIR/medium-001_T1w.nii.gz"
                ;;
            2)
                CURRENT_FILE="$INPUT_DIR/large-001_T1w.nii.gz"
                ;;
        esac
    else
        CURRENT_FILE="$INPUT_FILE"
    fi

    # Run neuro-preprocess
    if neuro-preprocess process "$CURRENT_FILE" -o "$OUTPUT_DIR" 2>&1 | grep -q "Total time"; then
        echo -e "${GREEN}✓ Run $i completed${NC}"
    else
        echo -e "${YELLOW}⚠ Run $i had warnings/errors${NC}"
    fi

    # Sleep between iterations (except for the last one)
    if [ $i -lt $ITERATIONS ]; then
        sleep $SLEEP_TIME
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Completed $ITERATIONS runs!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "View your telemetry data at:"
echo "  Grafana:    http://localhost:3000/d/dashboard-16-12-2025"
echo "  Prometheus: http://localhost:9090"
echo "  Tempo:      http://localhost:3200"
echo ""
