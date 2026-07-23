# ============================================================
#  Personal Voice AI Agent — One-Click Startup Script
# ============================================================
# Run this in PowerShell: .\start.ps1
# Prerequisites: Python 3.11+, Node.js 20+, Docker Desktop
# ============================================================

Write-Host ""
Write-Host "Personal Voice AI Agent -- Starting Up..." -ForegroundColor Cyan
Write-Host "============================================================"

# --- Step 1: Create .env if not exists ---
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "Please edit .env and add your OPENAI_API_KEY before continuing!" -ForegroundColor Red
}

# --- Step 2: Start All Services in Docker (Backend, Frontend, and Databases) ---
Write-Host ""
Write-Host "Building and starting all services in Docker..." -ForegroundColor Cyan
docker-compose up -d --build

Write-Host "Waiting for services to initialize and become healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# --- Step 3: Open browser ---
Write-Host ""
Write-Host "============================================================"
Write-Host "Voice AI Agent stack is running in Docker!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "All containers are running in the background and will stay active (and restart automatically)." -ForegroundColor Cyan
Write-Host "============================================================"

# Try to open the frontend page
try {
    Start-Process "http://localhost:3000"
} catch {
    Write-Host "Could not open browser automatically. Please visit http://localhost:3000 manually." -ForegroundColor Yellow
}

# Keep the script running to stream logs. If user presses Ctrl+C, the script exits but containers remain UP.
Write-Host ""
Write-Host "Streaming logs from backend and frontend containers..." -ForegroundColor Green
Write-Host "Press [Ctrl+C] at any time to stop viewing logs (this will NOT stop the agents)." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker-compose logs -f backend frontend
} catch {
    Write-Host ""
    Write-Host "Stopped streaming logs. Containers are still running in the background." -ForegroundColor Yellow
}
