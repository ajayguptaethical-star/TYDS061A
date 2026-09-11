@echo off
title EduQuestion AI - Backend and Frontend
color 0A

echo =====================================================================
echo                Starting EduQuestion AI (FastAPI + UI)
echo =====================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

echo [2/3] Checking Virtual Environment (if present)...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Active virtual environment: venv
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Active virtual environment: .venv
)

echo [3/3] Launching FastAPI Server with Embedded UI...
echo.
echo =====================================================================
echo  - Frontend Web UI:      http://localhost:8000
echo  - Swagger API Docs:     http://localhost:8000/docs
echo  - ReDoc Documentation:  http://localhost:8000/redoc
echo  - Health Endpoint:      http://localhost:8000/health
echo =====================================================================
echo.
echo Opening browser in 3 seconds...
start "" timeout /t 3 /nobreak >nul & start http://localhost:8000

python run.py

pause
