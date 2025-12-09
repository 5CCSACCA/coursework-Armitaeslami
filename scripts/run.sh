#!/bin/bash

# Run script for Cloud AI SaaS Application
# This script starts all services using Docker Compose

set -e

echo "========================================="
echo "Starting Cloud AI SaaS Application"
echo "========================================="

# Check if firebase_key.json exists
if [ ! -f "firebase_key.json" ]; then
    echo ""
    echo "WARNING: firebase_key.json not found!"
    echo "Firebase authentication will run in mock mode."
    echo "To enable Firebase, place your firebase_key.json in the project root."
    echo ""
fi

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
    fi
fi

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "========================================="
echo "Services Started!"
echo "========================================="
echo ""
echo "Available endpoints:"
echo "  - API Gateway:    http://localhost:8000"
echo "  - API Docs:       http://localhost:8000/docs"
echo "  - YOLO Service:   http://localhost:8001"
echo "  - LLM Service:    http://localhost:8002"
echo "  - RabbitMQ:       http://localhost:15672 (guest/guest)"
echo "  - Prometheus:     http://localhost:9090"
echo "  - Grafana:        http://localhost:3000 (admin/admin)"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
