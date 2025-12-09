@echo off
REM Test script for Cloud AI SaaS Application (Windows)
REM This script runs all unit tests

setlocal enabledelayedexpansion

echo =========================================
echo Running Tests for Cloud AI SaaS
echo =========================================

REM Track failures
set FAILED=0

REM Get the project root directory
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo Project root: %PROJECT_ROOT%

REM Function to run tests for a service
call :run_tests "YOLO Service" "yolo-service"
call :run_tests "LLM Service" "llm-service"
call :run_tests "API Gateway" "api-gateway"
call :run_tests "Postprocessor Service" "postprocessor-service"

echo.
echo =========================================
if %FAILED%==0 (
    echo All tests passed!
) else (
    echo Some tests failed!
    exit /b 1
)
echo =========================================

goto :eof

:run_tests
set SERVICE_NAME=%~1
set SERVICE_DIR=%~2

echo.
echo ----------------------------------------
echo Testing: %SERVICE_NAME%
echo ----------------------------------------

if exist "%SERVICE_DIR%" (
    cd /d "%SERVICE_DIR%"
    
    REM Create virtual environment if it doesn't exist
    if not exist ".venv" (
        python -m venv .venv 2>nul
    )
    
    REM Activate virtual environment
    call .venv\Scripts\activate.bat 2>nul
    
    REM Install dependencies
    if exist "requirements.txt" (
        pip install -q -r requirements.txt
        pip install -q pytest pytest-cov pytest-asyncio
    )
    
    REM Run tests
    python -m pytest tests/ -v --tb=short
    if errorlevel 1 (
        echo [31m✗ %SERVICE_NAME% tests failed[0m
        set FAILED=1
    ) else (
        echo [32m✓ %SERVICE_NAME% tests passed[0m
    )
    
    REM Deactivate virtual environment
    call deactivate 2>nul
    
    cd /d "%PROJECT_ROOT%"
) else (
    echo Directory %SERVICE_DIR% not found, skipping...
)

goto :eof


