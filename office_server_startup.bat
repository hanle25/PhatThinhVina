@echo off
REM Office Hours Server Startup Script for Windows
REM This script starts the office server automatically

echo Starting Office Hours Server...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Start the server
python start_server.py

echo Server startup complete.
pause 