#!/bin/bash
# Run benchmark and extract errors automatically
# Usage: ./run_and_extract_errors.sh <problem_id> <output_dir>

set -e  # Exit on error

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <problem_id> <output_dir> [model] [dataset]"
    echo ""
    echo "Examples:"
    echo "  $0 cvdp_copilot_16qam_mapper_0001 work_test"
    echo "  $0 cvdp_copilot_16qam_mapper_0001 work_test gpt-4o-mini"
    echo "  $0 cvdp_copilot_16qam_mapper_0001 work_test gpt-4o-mini dataset/my_dataset.jsonl"
    exit 1
fi

PROBLEM_ID="$1"
OUTPUT_DIR="$2"
MODEL="${3:-gpt-4o-mini}"  # Default to gpt-4o-mini
DATASET="${4:-dataset/cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl}"  # Default dataset

echo "=========================================="
echo "Running Benchmark"
echo "=========================================="
echo "Problem ID: $PROBLEM_ID"
echo "Output Dir: $OUTPUT_DIR"
echo "Model: $MODEL"
echo "Dataset: $DATASET"
echo ""

# Run the benchmark
./run_benchmark.py -f "$DATASET" -l -m "$MODEL" -i "$PROBLEM_ID" -p "$OUTPUT_DIR"

# Check if benchmark completed
if [ $? -ne 0 ]; then
    echo "Error: Benchmark failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Extracting Errors from Reports"
echo "=========================================="

# Remove last 5 characters from problem ID to get directory name
DIR_NAME="${PROBLEM_ID:0:-5}"

# Find all report files
REPORT_DIR="${OUTPUT_DIR}/${DIR_NAME}/reports"

if [ ! -d "$REPORT_DIR" ]; then
    echo "Error: Report directory not found: $REPORT_DIR"
    exit 1
fi

# Create errors directory
ERROR_DIR="${OUTPUT_DIR}/${DIR_NAME}/extracted_errors"
mkdir -p "$ERROR_DIR"

# Extract errors from each report file
for report_file in "$REPORT_DIR"/*.txt; do
    if [ -f "$report_file" ]; then
        report_name=$(basename "$report_file" .txt)
        error_file="${ERROR_DIR}/${report_name}_errors.txt"
        
        echo "Processing: $report_file"
        cvdp_env/bin/python3 tools/extract_traceback.py "$report_file" > "$error_file" 2>&1
        
        # Check if errors were found
        if [ -s "$error_file" ]; then
            echo "  ✓ Errors saved to: $error_file"
        else
            echo "  ✓ No errors found"
            rm "$error_file"  # Remove empty file
        fi
    fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Benchmark completed: $OUTPUT_DIR"
echo "Errors extracted to: $ERROR_DIR"
echo ""

# Show error count
error_count=$(find "$ERROR_DIR" -name "*_errors.txt" 2>/dev/null | wc -l)
if [ $error_count -gt 0 ]; then
    echo "Found $error_count report(s) with errors:"
    ls -lh "$ERROR_DIR"/*.txt 2>/dev/null || true
else
    echo "No errors found in any reports!"
fi

echo ""
echo "Done!"
