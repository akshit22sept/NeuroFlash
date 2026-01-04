@echo off
setlocal enabledelayedexpansion

cls
echo.
echo ============================================
echo    NeuroFlash - Development Server
echo ============================================
echo.

:: Check Python
echo [Step 1/4] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo Found: !PYTHON_VER!
echo.

:: Check Node.js
echo [Step 2/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 16+ from https://nodejs.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
echo Found: Node !NODE_VER!
echo.

:: Setup Backend
echo [Step 3/4] Setting up Backend...
cd /d "%~dp0backend"

if not exist "uploads" mkdir uploads
if not exist "results" mkdir results

echo Installing Python requirements (may take 2-3 minutes on first run)...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo WARNING: Some Python packages may have failed to install
    echo Backend may not work properly
    echo.
)
echo Backend setup complete!
echo.

:: Setup Frontend
echo [Step 4/4] Setting up Frontend...
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing Node.js dependencies (may take 5-10 minutes on first run)...
    echo This only happens once!
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Frontend dependencies failed to install
        cd /d "%~dp0"
        pause
        exit /b 1
    )
) else (
    echo Frontend dependencies already installed
)
echo Frontend setup complete!
echo.

:: Start servers
cd /d "%~dp0"
echo ============================================
echo   Starting Servers...
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5005
echo.
echo Two windows will open - do NOT close them!
echo.
echo Starting Backend...
start "NeuroFlash Backend - Do NOT Close" cmd /k "cd /d "%~dp0backend" && python server.py"

:: Wait for backend to start
timeout /t 5 /nobreak >nul

echo Starting Frontend...
start "NeuroFlash Frontend - Do NOT Close" cmd /k "cd /d "%~dp0frontend" && set PORT=5005 && npm start"

echo.
echo ============================================
echo   Servers Starting!
echo ============================================
echo.
echo Your browser will open automatically in a few seconds.
echo.
echo To stop: Close both server windows
echo.
echo This window can be closed safely.
echo ============================================
echo.

:: Wait a bit then try to open browser
timeout /t 10 /nobreak >nul
start http://localhost:5005

echo.
echo Done! Check the two server windows for status.
echo.