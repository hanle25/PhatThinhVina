@echo off
REM Backend Server Startup Script for Windows
REM This script starts only the Flask backend server

echo Starting Backend Server...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Start the backend server
python start_backend_only.py

echo Backend server startup complete.
pause 