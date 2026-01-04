@echo off
echo.
echo ============================================
echo    NeuroFlash - First Time Setup
echo ============================================
echo.

echo Installing Backend dependencies...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo Installing Frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo ============================================
echo    Setup Complete!
echo ============================================
echo.
echo To start the application, run:
echo    run.bat
echo.
pause
