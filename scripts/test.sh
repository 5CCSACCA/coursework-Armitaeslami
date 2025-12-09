#!/bin/bash

# Test script for Cloud AI SaaS Application
# This script runs all unit tests

set -e

echo "========================================="
echo "Running Tests for Cloud AI SaaS"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run tests for a service
run_tests() {
    SERVICE_NAME=$1
    SERVICE_DIR=$2
    
    echo ""
    echo "----------------------------------------"
    echo "Testing: $SERVICE_NAME"
    echo "----------------------------------------"
    
    if [ -d "$SERVICE_DIR" ]; then
        cd "$SERVICE_DIR"
        
        # Install dependencies in a virtual environment
        python -m venv .venv 2>/dev/null || true
        source .venv/bin/activate 2>/dev/null || true
        
        if [ -f "requirements.txt" ]; then
            pip install -q -r requirements.txt
            pip install -q pytest pytest-cov pytest-asyncio
        fi
        
        # Run tests
        if python -m pytest tests/ -v --tb=short; then
            echo -e "${GREEN}✓ $SERVICE_NAME tests passed${NC}"
        else
            echo -e "${RED}✗ $SERVICE_NAME tests failed${NC}"
            FAILED=1
        fi
        
        deactivate 2>/dev/null || true
        cd - > /dev/null
    else
        echo "Directory $SERVICE_DIR not found, skipping..."
    fi
}

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

# Run tests for each service
run_tests "YOLO Service" "$PROJECT_ROOT/yolo-service"
run_tests "LLM Service" "$PROJECT_ROOT/llm-service"
run_tests "API Gateway" "$PROJECT_ROOT/api-gateway"
run_tests "Postprocessor Service" "$PROJECT_ROOT/postprocessor-service"

echo ""
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
echo "========================================="
