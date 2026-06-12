@echo off
REM JO Browser — Windows Install Script
REM Run this once to set up the environment

echo ==========================================
echo  JO Browser — Setup
echo ==========================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download Python from https://python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Done!
echo.
echo To run JO Browser:
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
echo To build .exe:
echo   pip install pyinstaller
echo   pyinstaller build.spec
echo.
pause
