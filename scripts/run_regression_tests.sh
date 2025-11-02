#!/usr/bin/env bash
# Script to run regression tests for GPX generation
# Use this before testing new settings or algorithms to ensure existing functionality still works

set -e

echo "=================================================="
echo "Running Jadlo Regression Tests"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "tests/test_gpx_regression.py" ]; then
    echo "Error: Please run this script from the repository root"
    exit 1
fi

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "Error: pytest is not installed. Install with: pip install pytest"
    exit 1
fi

echo "Running regression tests..."
echo ""

# Run the regression tests with verbose output
PYTHONPATH=. python -m pytest tests/test_gpx_regression.py -v

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "=================================================="
    echo "✓ All regression tests passed!"
    echo "=================================================="
    echo ""
    echo "Your changes are safe to test with new settings."
    echo ""
else
    echo "=================================================="
    echo "✗ Some regression tests failed!"
    echo "=================================================="
    echo ""
    echo "Please fix the failing tests before testing new settings."
    echo "Review the output above to see which tests failed."
    echo ""
    exit 1
fi
