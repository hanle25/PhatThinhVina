@echo off
REM Office Hours Server Shutdown Script for Windows
REM This script stops the office server automatically

echo Stopping Office Hours Server...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Stop the server
python stop_server.py

echo Server shutdown complete. 