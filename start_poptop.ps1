# POPTOP Fleet Tracker - Startup Script
# Starts API server and opens dashboard

Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     POPTOP FLEET TRACKER - Enhanced Telemetry Dashboard      ║" -ForegroundColor Cyan
Write-Host "║     Connected to Timescale Cloud Pipeline                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.x" -ForegroundColor Red
    pause
    exit 1
}

# Check if required packages are installed
Write-Host ""
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow

$requiredPackages = @("flask", "flask-cors", "psycopg2")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $installed = pip list 2>&1 | Select-String -Pattern "^$package\s"
    if (-not $installed) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "❌ Missing packages: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Yellow
    
    foreach ($package in $missingPackages) {
        if ($package -eq "psycopg2") {
            pip install psycopg2-binary
        } else {
            pip install $package
        }
    }
    Write-Host "✅ All packages installed!" -ForegroundColor Green
} else {
    Write-Host "✅ All dependencies installed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  STARTING POPTOP DASHBOARD                    ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start API server in background
Write-Host "🚀 Starting API Server on port 5000..." -ForegroundColor Cyan
$apiPath = Join-Path $scriptDir "api_server_NEW.py"

if (-not (Test-Path $apiPath)) {
    Write-Host "❌ Error: api_server_NEW.py not found!" -ForegroundColor Red
    Write-Host "   Expected location: $apiPath" -ForegroundColor Red
    pause
    exit 1
}

# Start the API server
Start-Process python -ArgumentList $apiPath -WindowStyle Normal

# Wait for server to start
Write-Host "⏳ Waiting for API server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test API server
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ API Server is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  API Server may not have started correctly" -ForegroundColor Yellow
    Write-Host "   Check the Python window for errors" -ForegroundColor Yellow
}

# Open dashboard in default browser
Write-Host ""
Write-Host "🌐 Opening dashboard in browser..." -ForegroundColor Cyan
$dashboardPath = Join-Path $scriptDir "dashboard_ENHANCED.html"

if (Test-Path $dashboardPath) {
    Start-Process $dashboardPath
    Write-Host "✅ Dashboard opened!" -ForegroundColor Green
} else {
    Write-Host "❌ Error: dashboard_ENHANCED.html not found!" -ForegroundColor Red
    Write-Host "   Expected location: $dashboardPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                   POPTOP IS NOW RUNNING!                      ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard Features:" -ForegroundColor Cyan
Write-Host "  📍 Live GPS tracking on interactive map" -ForegroundColor White
Write-Host "  📊 All 53 IO elements displayed in categories" -ForegroundColor White
Write-Host "  🚗 3 device fleet (switchable in dropdown)" -ForegroundColor White
Write-Host "  ⚡ Real-time updates every 5 seconds" -ForegroundColor White
Write-Host "  🗺️  Trip history with full telemetry" -ForegroundColor White
Write-Host ""
Write-Host "API Server: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Dashboard: Browser window opened" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in the Python window to stop the API server" -ForegroundColor Gray
Write-Host ""
pause
