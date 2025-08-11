@echo off
REM Manual server control script for Windows

if "%1"=="start" (
    echo Starting office server...
    call "D:\PhatThinhVina\office_server_startup.bat"
    goto :eof
)

if "%1"=="stop" (
    echo Stopping office server...
    call "D:\PhatThinhVina\office_server_shutdown.bat"
    goto :eof
)

if "%1"=="restart" (
    echo Restarting office server...
    call "D:\PhatThinhVina\office_server_shutdown.bat"
    timeout /t 2 /nobreak >nul
    call "D:\PhatThinhVina\office_server_startup.bat"
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
        powershell "Get-Content '%TEMP%\office_server.log' ^| Select-Object -Last 20"
    ) else (
        echo No startup log found
    )
    echo.
    echo === Shutdown Log ===
    if exist "%TEMP%\office_server_shutdown.log" (
        powershell "Get-Content '%TEMP%\office_server_shutdown.log' ^| Select-Object -Last 20"
    ) else (
        echo No shutdown log found
    )
    goto :eof
)

if "%1"=="schedule" (
    echo Current office hours schedule:
    echo - Startup: Monday-Friday at 9:00 AM
    echo - Shutdown: Monday-Friday at 7:00 PM
    echo.
    echo To change schedule, run:
    echo   schtasks /change /tn "Office Server Startup" /st HH:MM
    echo   schtasks /change /tn "Office Server Shutdown" /st HH:MM
    goto :eof
)

echo Usage: %0 {start|stop|restart|status|logs|schedule}
echo.
echo Commands:
echo   start    - Start the office server manually
echo   stop     - Stop the office server manually
echo   restart  - Restart the office server
echo   status   - Check server status
echo   logs     - View server logs
echo   schedule - Show current office hours schedule
