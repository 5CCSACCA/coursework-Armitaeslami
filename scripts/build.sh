#!/bin/bash

# Build script for Cloud AI SaaS Application
# This script builds all Docker images

set -e

echo "========================================="
echo "Building Cloud AI SaaS Application"
echo "========================================="

echo ""
echo "Building YOLO Service..."
docker-compose build yolo-service

echo ""
echo "Building LLM Service..."
docker-compose build llm-service

echo ""
echo "Building API Gateway..."
docker-compose build api-gateway

echo ""
echo "Building Postprocessor Service..."
docker-compose build postprocessor-service

echo ""
echo "========================================="
echo "Build Complete!"
echo "========================================="
echo ""
echo "To run the application, use:"
echo "  docker-compose up -d"
echo ""
echo "Or use the run script:"
echo "  ./scripts/run.sh"
