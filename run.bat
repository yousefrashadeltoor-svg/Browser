@echo off
REM JO Browser — Quick Launch (Windows)
REM Run this after running install.bat

call venv\Scripts\activate.bat 2>nul || (
    echo Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)
python main.py
