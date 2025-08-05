@echo off
REM Windows Office Hours Server Automation Setup
REM This script sets up automatic startup and shutdown using Windows Task Scheduler

echo Setting up Office Hours Server Automation for Windows...

REM Get the current directory
set SCRIPT_DIR=%~dp0
echo Project directory: %SCRIPT_DIR%

REM Install required Python packages
echo Installing required Python packages...
pip install psutil

REM Create startup task (Monday-Friday at 9:00 AM)
echo Creating startup task...
schtasks /create /tn "Office Server Startup" /tr "\"%SCRIPT_DIR%office_server_startup.bat\"" /sc daily /st 09:00 /f /ru SYSTEM

REM Create shutdown task (Monday-Friday at 7:00 PM)
echo Creating shutdown task...
schtasks /create /tn "Office Server Shutdown" /tr "\"%SCRIPT_DIR%office_server_shutdown.bat\"" /sc daily /st 19:00 /f /ru SYSTEM

REM Create a manual control script
echo Creating manual control script...
(
echo @echo off
echo REM Manual server control script for Windows
echo.
echo if "%%1"=="start" ^(
echo     echo Starting office server...
echo     call "%SCRIPT_DIR%office_server_startup.bat"
echo     goto :eof
echo ^)
echo.
echo if "%%1"=="stop" ^(
echo     echo Stopping office server...
echo     call "%SCRIPT_DIR%office_server_shutdown.bat"
echo     goto :eof
echo ^)
echo.
echo if "%%1"=="restart" ^(
echo     echo Restarting office server...
echo     call "%SCRIPT_DIR%office_server_shutdown.bat"
echo     timeout /t 2 /nobreak ^>nul
echo     call "%SCRIPT_DIR%office_server_startup.bat"
echo     goto :eof
echo ^)
echo.
echo if "%%1"=="status" ^(
echo     echo Checking server status...
echo     netstat -ano ^| findstr ":3000"
echo     if %%errorlevel%%==0 ^(
echo         echo Frontend server is running
echo     ^) else ^(
echo         echo Frontend server is not running
echo     ^)
echo     netstat -ano ^| findstr ":5000"
echo     if %%errorlevel%%==0 ^(
echo         echo Backend server is running
echo     ^) else ^(
echo         echo Backend server is not running
echo     ^)
echo     goto :eof
echo ^)
echo.
echo if "%%1"=="logs" ^(
echo     echo Recent server logs:
echo     echo === Startup Log ===
echo     if exist "%%TEMP%%\office_server.log" ^(
echo         powershell "Get-Content '%%TEMP%%\office_server.log' ^| Select-Object -Last 20"
echo     ^) else ^(
echo         echo No startup log found
echo     ^)
echo     echo.
echo     echo === Shutdown Log ===
echo     if exist "%%TEMP%%\office_server_shutdown.log" ^(
echo         powershell "Get-Content '%%TEMP%%\office_server_shutdown.log' ^| Select-Object -Last 20"
echo     ^) else ^(
echo         echo No shutdown log found
echo     ^)
echo     goto :eof
echo ^)
echo.
echo if "%%1"=="schedule" ^(
echo     echo Current office hours schedule:
echo     echo - Startup: Monday-Friday at 9:00 AM
echo     echo - Shutdown: Monday-Friday at 7:00 PM
echo     echo.
echo     echo To change schedule, run:
echo     echo   schtasks /change /tn "Office Server Startup" /st HH:MM
echo     echo   schtasks /change /tn "Office Server Shutdown" /st HH:MM
echo     goto :eof
echo ^)
echo.
echo echo Usage: %%0 {start^|stop^|restart^|status^|logs^|schedule}
echo echo.
echo echo Commands:
echo echo   start    - Start the office server manually
echo echo   stop     - Stop the office server manually
echo echo   restart  - Restart the office server
echo echo   status   - Check server status
echo echo   logs     - View server logs
echo echo   schedule - Show current office hours schedule
) > "%SCRIPT_DIR%control_server.bat"

echo.
echo ✅ Setup complete!
echo.
echo 📋 What was installed:
echo   • Automatic startup at 9:00 AM (Monday-Friday)
echo   • Automatic shutdown at 7:00 PM (Monday-Friday)
echo   • Manual control script: control_server.bat
echo.
echo 🔧 Manual controls:
echo   control_server.bat start    - Start server manually
echo   control_server.bat stop     - Stop server manually
echo   control_server.bat restart  - Restart server
echo   control_server.bat status   - Check server status
echo   control_server.bat logs     - View server logs
echo   control_server.bat schedule - Show office hours schedule
echo.
echo 🌐 Server will be accessible at:
echo   Frontend: http://[YOUR_OFFICE_IP]:3000
echo   Backend:  http://[YOUR_OFFICE_IP]:5000
echo.
echo 📝 To uninstall automation:
echo   schtasks /delete /tn "Office Server Startup" /f
echo   schtasks /delete /tn "Office Server Shutdown" /f
echo.
pause 