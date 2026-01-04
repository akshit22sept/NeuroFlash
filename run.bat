@echo off
cls
echo.
echo ============================================
echo    NeuroFlash - Starting Servers
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5005
echo.
echo Starting Backend...
start "NeuroFlash Backend" cmd /k "cd /d "%~dp0backend" && python server.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "NeuroFlash Frontend" cmd /k "cd /d "%~dp0frontend" && set PORT=5005 && npm start"

echo.
echo Servers are starting...
echo Browser will open at http://localhost:5005
echo.

timeout /t 8 /nobreak >nul
start http://localhost:5005

echo Done! Check the server windows for status.
