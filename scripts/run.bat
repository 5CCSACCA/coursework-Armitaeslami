@echo off
REM Run script for Cloud AI SaaS Application (Windows)
REM This script starts all services using Docker Compose

echo =========================================
echo Starting Cloud AI SaaS Application
echo =========================================

REM Check if firebase_key.json exists
if not exist "firebase_key.json" (
    echo.
    echo WARNING: firebase_key.json not found!
    echo Firebase authentication will run in mock mode.
    echo To enable Firebase, place your firebase_key.json in the project root.
    echo.
)

REM Check if .env exists, if not copy from example
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
    )
)

echo.
echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo =========================================
echo Services Started!
echo =========================================
echo.
echo Available endpoints:
echo   - API Gateway:    http://localhost:8000
echo   - API Docs:       http://localhost:8000/docs
echo   - YOLO Service:   http://localhost:8001
echo   - LLM Service:    http://localhost:8002
echo   - RabbitMQ:       http://localhost:15672 (guest/guest)
echo   - Prometheus:     http://localhost:9090
echo   - Grafana:        http://localhost:3000 (admin/admin)
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop:
echo   docker-compose down


