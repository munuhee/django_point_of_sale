@echo off
REM Ensure Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed or not running. Please install and start Docker.
    pause
    exit /b
)

REM Run Docker Compose
docker-compose up -d

REM Open the browser to localhost:8000
start "" "http://localhost:8000"

REM You can add a delay if needed
timeout /t 5 >nul

REM Additional commands can be added here if needed

REM To stop the containers, you can use:
REM docker-compose down
