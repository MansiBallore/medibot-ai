@echo off
REM ════════════════════════════════════════════════════════════
REM MediBot AI — Windows Quick Start Script
REM Usage: start.bat
REM ════════════════════════════════════════════════════════════

echo.
echo  ███╗   ███╗███████╗██████╗ ██╗██████╗  ██████╗ ████████╗    █████╗ ██╗
echo  ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██╔═══██╗╚══██╔══╝   ██╔══██╗██║
echo  ██╔████╔██║█████╗  ██║  ██║██║██████╔╝██║   ██║   ██║      ███████║██║
echo  ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██╗██║   ██║   ██║      ██╔══██║██║
echo  ██║ ╚═╝ ██║███████╗██████╔╝██║██████╔╝╚██████╔╝   ██║      ██║  ██║██║
echo  ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═════╝  ╚═════╝    ╚═╝      ╚═╝  ╚═╝╚═╝
echo.
echo  Advanced Generative AI Healthcare Assistant v2.0
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Check .env
if not exist ".env" (
    echo [WARNING] .env not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Edit .env and add your AI API key, then re-run.
    echo    Get a FREE Gemini key: https://aistudio.google.com/app/apikey
    pause
    exit /b 0
)
echo [OK] .env found

REM Create venv if needed
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate
call venv\Scripts\activate.bat

REM Install deps
echo Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo [OK] Dependencies installed

REM Create dirs
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "data\vectorstore" mkdir data\vectorstore
if not exist "data\medical_docs" mkdir data\medical_docs

REM Launch
echo.
echo  Starting MediBot AI...
echo  Local:    http://localhost:8000
echo  API Docs: http://localhost:8000/api/docs
echo.

set PYTHONPATH=.
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0

pause
