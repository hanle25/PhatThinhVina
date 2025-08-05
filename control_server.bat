@echo off
REM Office Hours Server Control Script for Windows
REM Manual control script for starting, stopping, and managing the server

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%1"=="start" (
    echo Starting office server...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    )
    python start_server.py
    goto :eof
)

if "%1"=="stop" (
    echo Stopping office server...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    )
    python stop_server.py
    goto :eof
)

if "%1"=="restart" (
    echo Restarting office server...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    )
    python stop_server.py
    timeout /t 2 /nobreak >nul
    python start_server.py
    goto :eof
)

if "%1"=="status" (
    echo Checking server status...
    netstat -ano | findstr ":3000"
    if %errorlevel%==0 (
        echo Frontend server is running
    ) else (
        echo Frontend server is not running
    )
    netstat -ano | findstr ":5000"
    if %errorlevel%==0 (
        echo Backend server is running
    ) else (
        echo Backend server is not running
    )
    goto :eof
)

if "%1"=="logs" (
    echo Recent server logs:
    echo === Startup Log ===
    if exist "%TEMP%\office_server.log" (
        powershell "Get-Content '%TEMP%\office_server.log' | Select-Object -Last 20"
    ) else (
        echo No startup log found
    )
    echo.
    echo === Shutdown Log ===
    if exist "%TEMP%\office_server_shutdown.log" (
        powershell "Get-Content '%TEMP%\office_server_shutdown.log' | Select-Object -Last 20"
    ) else (
        echo No shutdown log found
    )
    goto :eof
)

echo Usage: %0 {start^|stop^|restart^|status^|logs}
echo.
echo Commands:
echo   start   - Start the office server manually
echo   stop    - Stop the office server manually
echo   restart - Restart the office server
echo   status  - Check if servers are running
echo   logs    - Show recent server logs 