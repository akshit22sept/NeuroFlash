# NeuroFlash - Development Server Startup Script
# PowerShell version

Clear-Host
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   NeuroFlash - Development Server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[Step 1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check Node.js
Write-Host "[Step 2/4] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Found: Node $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js 16+ from https://nodejs.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Setup Backend
Write-Host "[Step 3/4] Setting up Backend..." -ForegroundColor Yellow
Set-Location -Path "$PSScriptRoot\backend"

if (-not (Test-Path "temp_uploads")) { New-Item -ItemType Directory -Path "temp_uploads" | Out-Null }
if (-not (Test-Path "results")) { New-Item -ItemType Directory -Path "results" | Out-Null }

Write-Host "Installing Python requirements..." -ForegroundColor Gray
pip install -r requirements.txt -q
Write-Host "Backend setup complete!" -ForegroundColor Green
Write-Host ""

# Setup Frontend
Write-Host "[Step 4/4] Setting up Frontend..." -ForegroundColor Yellow
Set-Location -Path "$PSScriptRoot\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies (first run, 5-10 min)..." -ForegroundColor Gray
    npm install
} else {
    Write-Host "Frontend dependencies already installed" -ForegroundColor Gray
}
Write-Host "Frontend setup complete!" -ForegroundColor Green
Write-Host ""

# Start servers
Set-Location -Path $PSScriptRoot
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Starting Servers..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:5005" -ForegroundColor White
Write-Host ""
Write-Host "Two windows will open - do NOT close them!" -ForegroundColor Yellow
Write-Host ""

# Start Backend
Write-Host "Starting Backend..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py" -WindowStyle Normal

# Wait for backend
Start-Sleep -Seconds 5

# Start Frontend  
Write-Host "Starting Frontend..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm start" -WindowStyle Normal

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Servers Starting!" -ForegroundColor Cyan
Write-Host "============================================"  -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening browser in 10 seconds..." -ForegroundColor Gray
Write-Host ""
Write-Host "To stop: Close both PowerShell windows" -ForegroundColor Yellow
Write-Host "This window can be closed safely." -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Wait then open browser
Start-Sleep -Seconds 10
Start-Process "http://localhost:5005"

Write-Host "Done! Check the two server windows for status." -ForegroundColor Green
Write-Host ""
