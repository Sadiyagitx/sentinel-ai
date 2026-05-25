# SentinelAI Local Startup Script
# This script starts the Next.js frontend, FastAPI backend, and Simulator locally if Docker is unavailable.

Write-Host "=========================================="
Write-Host " Starting SentinelAI Platform "
Write-Host "=========================================="

# Check for Docker
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerInstalled) {
    Write-Host "Docker is available. Starting via Docker Compose..."
    docker compose up -d --build
    Write-Host "SentinelAI started successfully on Docker!"
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "Backend API: http://localhost:8000"
    exit
}

Write-Host "Docker is NOT installed. Running services locally in background jobs..."

# Install and start backend
Write-Host "1. Starting Backend API..."
Start-Job -Name "SentinelAI-API" -ScriptBlock {
    Set-Location "$env:PWD\apps\api-gateway"
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000
}

# Install and start frontend
Write-Host "2. Starting Frontend Web App..."
Start-Job -Name "SentinelAI-Web" -ScriptBlock {
    Set-Location "$env:PWD\apps\web"
    npm install
    npm run dev
}

# Start Simulator
Write-Host "3. Starting Telemetry Simulator..."
Start-Job -Name "SentinelAI-Simulator" -ScriptBlock {
    Set-Location "$env:PWD\apps\simulator"
    pip install redis
    python engine.py
}

Write-Host "=========================================="
Write-Host " All services are starting up! "
Write-Host "=========================================="
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend API: http://localhost:8000"
Write-Host "Websocket Stream: ws://localhost:8000/ws"
Write-Host "=========================================="
Write-Host "Press Ctrl+C to exit, or run 'Stop-Job -Name SentinelAI-*' to terminate."
