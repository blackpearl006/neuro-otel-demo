#!/bin/bash

# Demo Scenarios for OpenTelemetry Observability Learning
# This script runs different scenarios to generate interesting telemetry patterns

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INPUT_DIR="data/input"
OUTPUT_DIR="data/output"

# Ensure directories exist
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

# Helper function to print colored messages
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

# Check if neuro-preprocess is installed
if ! command -v neuro-preprocess &> /dev/null; then
    print_error "neuro-preprocess is not installed!"
    echo "Please install it first:"
    echo "  cd app && pip install -e ."
    exit 1
fi

# Check if observability stack is running
check_stack() {
    print_info "Checking if observability stack is running..."

    if ! docker-compose ps | grep -q "Up"; then
        print_error "Observability stack is not running!"
        echo ""
        echo "Please start it first:"
        echo "  docker-compose up -d"
        exit 1
    fi

    print_success "Observability stack is running"
}

# Generate dummy input files if they don't exist
generate_test_files() {
    local count=$1
    print_info "Generating $count test files..."

    for i in $(seq 1 $count); do
        local filename=$(printf "sub-%03d_T1w.nii.gz" $i)
        local filepath="$INPUT_DIR/$filename"

        if [ ! -f "$filepath" ]; then
            # Create a dummy file with random size (1-10 MB)
            local size=$((RANDOM % 9 + 1))
            dd if=/dev/urandom of="$filepath" bs=1M count=$size status=none 2>/dev/null
        fi
    done

    print_success "Generated $count test files"
}

# Scenario 1: Normal Processing
scenario_normal() {
    print_header "SCENARIO 1: Normal Processing"
    echo "Description: Process 10 files with default settings"
    echo "Expected telemetry:"
    echo "  - 10 successful traces"
    echo "  - Consistent processing times"
    echo "  - INFO level logs only"
    echo ""

    generate_test_files 10

    print_info "Processing files..."

    for i in $(seq 1 10); do
        local filename=$(printf "sub-%03d_T1w.nii.gz" $i)
        local filepath="$INPUT_DIR/$filename"

        echo "[$i/10] Processing $filename..."
        neuro-preprocess process "$filepath" -o "$OUTPUT_DIR" || true
    done

    print_success "Normal scenario completed"
    echo ""
    print_info "View results in Grafana:"
    echo "  - Traces: http://localhost:3000/explore → Tempo"
    echo "  - Logs: http://localhost:3000/explore → Loki"
    echo "  - Metrics: http://localhost:3000/explore → Prometheus"
    echo ""
}

# Scenario 2: Batch Processing
scenario_batch() {
    print_header "SCENARIO 2: Batch Processing"
    echo "Description: Process all files in a directory at once"
    echo "Expected telemetry:"
    echo "  - Multiple traces in sequence"
    echo "  - Batch processing metrics"
    echo ""

    generate_test_files 5

    print_info "Running batch processing..."

    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR" --pattern "sub-*.nii.gz"

    print_success "Batch scenario completed"
    echo ""
}

# Scenario 3: Mixed File Sizes
scenario_mixed_sizes() {
    print_header "SCENARIO 3: Mixed File Sizes"
    echo "Description: Process files of varying sizes to see duration distribution"
    echo "Expected telemetry:"
    echo "  - Wide distribution in load times"
    echo "  - File size histogram shows variety"
    echo ""

    print_info "Generating files with different sizes..."

    # Small files (1-2 MB)
    for i in 1 2 3; do
        local filename=$(printf "small-%03d_T1w.nii.gz" $i)
        dd if=/dev/urandom of="$INPUT_DIR/$filename" bs=1M count=$((RANDOM % 2 + 1)) status=none 2>/dev/null
    done

    # Medium files (5-7 MB)
    for i in 1 2 3; do
        local filename=$(printf "medium-%03d_T1w.nii.gz" $i)
        dd if=/dev/urandom of="$INPUT_DIR/$filename" bs=1M count=$((RANDOM % 3 + 5)) status=none 2>/dev/null
    done

    # Large files (10-15 MB)
    for i in 1 2; do
        local filename=$(printf "large-%03d_T1w.nii.gz" $i)
        dd if=/dev/urandom of="$INPUT_DIR/$filename" bs=1M count=$((RANDOM % 6 + 10)) status=none 2>/dev/null
    done

    print_success "Generated files with varying sizes"

    print_info "Processing all files..."
    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR" --pattern "*-*.nii.gz"

    print_success "Mixed sizes scenario completed"
    echo ""
    print_info "Check the file_size histogram in Prometheus!"
    echo ""
}

# Scenario 4: Stress Test
scenario_stress() {
    print_header "SCENARIO 4: Stress Test"
    echo "Description: Process 20 files to stress test the observability stack"
    echo "Expected telemetry:"
    echo "  - High volume of traces"
    echo "  - Test collector batching"
    echo "  - Test storage backends under load"
    echo ""

    generate_test_files 20

    print_info "Processing 20 files..."

    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR" --pattern "sub-*.nii.gz"

    print_success "Stress test scenario completed"
    echo ""
    print_info "Monitor resource usage:"
    echo "  docker stats"
    echo ""
}

# Scenario 5: Real-time Monitoring Demo
scenario_realtime() {
    print_header "SCENARIO 5: Real-time Monitoring Demo"
    echo "Description: Process files slowly while watching Grafana live"
    echo ""
    print_info "Instructions:"
    echo "  1. Open Grafana: http://localhost:3000"
    echo "  2. Go to Explore → Loki"
    echo "  3. Click 'Live' button in top right"
    echo "  4. Query: {service_name=\"neuro-preprocess\"}"
    echo "  5. Watch logs appear in real-time!"
    echo ""
    echo "Press ENTER to start processing..."
    read

    generate_test_files 5

    for i in $(seq 1 5); do
        local filename=$(printf "sub-%03d_T1w.nii.gz" $i)
        print_info "[$i/5] Processing $filename..."
        neuro-preprocess process "$INPUT_DIR/$filename" -o "$OUTPUT_DIR"

        if [ $i -lt 5 ]; then
            echo "Waiting 5 seconds before next file..."
            sleep 5
        fi
    done

    print_success "Real-time monitoring demo completed"
    echo ""
}

# Scenario 6: Trace Correlation Demo
scenario_correlation() {
    print_header "SCENARIO 6: Trace-to-Logs Correlation Demo"
    echo "Description: Demonstrate jumping between traces and logs"
    echo ""

    generate_test_files 3

    print_info "Processing 3 files..."

    for i in $(seq 1 3); do
        local filename=$(printf "sub-%03d_T1w.nii.gz" $i)
        neuro-preprocess process "$INPUT_DIR/$filename" -o "$OUTPUT_DIR"
    done

    print_success "Files processed"
    echo ""
    print_info "Try this in Grafana:"
    echo ""
    echo "1. Go to Explore → Tempo"
    echo "2. Search for service: neuro-preprocess"
    echo "3. Click on any trace"
    echo "4. Click on a span (e.g., 'load_file')"
    echo "5. Look for 'Logs for this span' button"
    echo "6. Click it to see correlated logs!"
    echo ""
    echo "Then try the reverse:"
    echo "1. Go to Explore → Loki"
    echo "2. Query: {service_name=\"neuro-preprocess\"}"
    echo "3. Click on any log line to expand"
    echo "4. Click on the trace_id value"
    echo "5. Jump to the full trace!"
    echo ""
}

# Scenario 7: Performance Comparison
scenario_performance() {
    print_header "SCENARIO 7: Performance Comparison"
    echo "Description: Compare processing with different configurations"
    echo ""

    generate_test_files 5

    print_info "Run 1: With all stages enabled"
    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR/run1" --pattern "sub-00[1-5]*.nii.gz"

    echo ""
    print_info "Run 2: Without skull stripping"
    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR/run2" --pattern "sub-00[1-5]*.nii.gz" --no-skull-strip

    echo ""
    print_info "Run 3: Without bias correction"
    neuro-preprocess batch "$INPUT_DIR" -o "$OUTPUT_DIR/run3" --pattern "sub-00[1-5]*.nii.gz" --no-bias-correction

    print_success "Performance comparison completed"
    echo ""
    print_info "Compare in Grafana:"
    echo "  - Look at processing duration differences"
    echo "  - Check which stages took longest"
    echo ""
}

# Cleanup old output
cleanup_output() {
    print_info "Cleaning up old output files..."
    rm -rf "$OUTPUT_DIR"/*
    print_success "Cleaned up output directory"
}

# Main menu
show_menu() {
    echo ""
    print_header "OpenTelemetry Demo Scenarios"
    echo ""
    echo "Available scenarios:"
    echo "  1) normal         - Normal processing (10 files)"
    echo "  2) batch          - Batch processing demo"
    echo "  3) sizes          - Mixed file sizes"
    echo "  4) stress         - Stress test (20 files)"
    echo "  5) realtime       - Real-time monitoring demo"
    echo "  6) correlation    - Trace-to-logs correlation demo"
    echo "  7) performance    - Performance comparison"
    echo "  8) all            - Run all scenarios"
    echo "  9) cleanup        - Clean output directory"
    echo ""
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_menu
    echo "Usage: $0 <scenario>"
    echo "Example: $0 normal"
    exit 0
fi

SCENARIO=$1

# Always check stack first (except for cleanup)
if [ "$SCENARIO" != "cleanup" ]; then
    check_stack
    echo ""
fi

# Run selected scenario
case $SCENARIO in
    normal)
        scenario_normal
        ;;
    batch)
        scenario_batch
        ;;
    sizes)
        scenario_mixed_sizes
        ;;
    stress)
        scenario_stress
        ;;
    realtime)
        scenario_realtime
        ;;
    correlation)
        scenario_correlation
        ;;
    performance)
        scenario_performance
        ;;
    all)
        print_header "Running ALL Scenarios"
        echo "This will take several minutes..."
        echo ""
        scenario_normal
        sleep 10
        scenario_batch
        sleep 10
        scenario_mixed_sizes
        sleep 10
        scenario_correlation
        print_success "All scenarios completed!"
        echo ""
        print_info "Explore the rich telemetry data in Grafana!"
        ;;
    cleanup)
        cleanup_output
        ;;
    *)
        print_error "Unknown scenario: $SCENARIO"
        show_menu
        exit 1
        ;;
esac

print_success "Demo completed successfully!"
echo ""
print_info "Next steps:"
echo "  - Open Grafana: http://localhost:3000"
echo "  - Explore the telemetry data"
echo "  - Build custom dashboards"
echo ""
