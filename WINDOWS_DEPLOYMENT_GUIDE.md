# Windows Company Machine Deployment Guide

This guide will help you deploy your React + Flask application on a Windows company machine with automatic office hours scheduling (9 AM to 7 PM) and network restrictions.

## 🎯 Overview

The setup includes:
- **Automatic startup** - Starts at 9:00 AM on weekdays
- **Automatic shutdown** - Stops at 7:00 PM on weekdays
- **Network-restricted access** - Only accessible from office network
- **Manual controls** - Start/stop/restart as needed
- **Windows Task Scheduler** - Reliable automation

## 📋 Prerequisites

- Windows 10/11 or Windows Server
- Python 3.7+
- Node.js and npm
- Administrator access (for Task Scheduler)

## 🚀 Step-by-Step Setup

### Step 1: Prepare Your Files

1. **Copy your project to the company machine**
2. **Open Command Prompt as Administrator**
3. **Navigate to your project directory**

### Step 2: Run the Setup Script

```cmd
# Run the Windows setup script (as Administrator)
setup_windows_automation.bat
```

This will:
- Install required Python packages
- Create Task Scheduler tasks for 9 AM startup and 7 PM shutdown
- Create manual control scripts

### Step 3: Test the Setup

```cmd
# Test manual startup
control_server.bat start

# Check server status
control_server.bat status

# View server logs
control_server.bat logs
```

## 🔧 Manual Controls

### Basic Commands
```cmd
# Start server manually
control_server.bat start

# Stop server manually  
control_server.bat stop

# Restart server
control_server.bat restart

# Check server status
control_server.bat status

# View server logs
control_server.bat logs

# Show office hours schedule
control_server.bat schedule
```

### Advanced Commands
```cmd
# Check Task Scheduler status
schtasks /query /tn "Office Server Startup"
schtasks /query /tn "Office Server Shutdown"

# Run tasks manually
schtasks /run /tn "Office Server Startup"
schtasks /run /tn "Office Server Shutdown"
```

## ⏰ Office Hours Schedule

- **Startup**: Monday-Friday at 9:00 AM
- **Shutdown**: Monday-Friday at 7:00 PM
- **Weekends**: Server remains off

## 🌐 Access Information

Once running, your application will be accessible at:
- **Frontend**: `http://[COMPANY_MACHINE_IP]:3000`
- **Backend API**: `http://[COMPANY_MACHINE_IP]:5000`

### Find Company Machine IP Address
```cmd
ipconfig | findstr "IPv4"
```

## 📁 File Structure

```
YourProject/
├── start_server.py                    # Cross-platform server startup
├── stop_server.py                     # Cross-platform server shutdown
├── setup_windows_automation.bat       # Windows automation setup
├── office_server_startup.bat          # Windows startup script
├── office_server_shutdown.bat         # Windows shutdown script
├── control_server.bat                 # Windows manual control
├── backend/                           # Flask backend
├── frontend/                          # React frontend
└── WINDOWS_DEPLOYMENT_GUIDE.md        # This guide
```

## 🔒 Security Features

### Network Restrictions
- Server binds to local network interface only
- Only office network can access the application
- External access is blocked by default

### Process Management
- Graceful startup and shutdown
- Automatic process monitoring
- Crash detection and logging

## 📊 Monitoring

### Log Files
- `%TEMP%\office_server.log` - Server startup logs
- `%TEMP%\office_server_shutdown.log` - Shutdown logs

### Status Checking
```cmd
control_server.bat status
```

## 🛠️ Troubleshooting

### Server Won't Start

1. **Check if ports are already in use:**
   ```cmd
   netstat -ano | findstr ":3000"
   netstat -ano | findstr ":5000"
   ```

2. **Check logs:**
   ```cmd
   control_server.bat logs
   ```

3. **Verify dependencies:**
   ```cmd
   cd backend && pip install -r requirements.txt
   cd frontend && npm install
   ```

### Automation Not Working

1. **Check Task Scheduler:**
   ```cmd
   schtasks /query /tn "Office Server Startup"
   schtasks /query /tn "Office Server Shutdown"
   ```

2. **Run tasks manually:**
   ```cmd
   schtasks /run /tn "Office Server Startup"
   ```

3. **Check Task Scheduler service:**
   ```cmd
   sc query Schedule
   ```

### Network Access Issues

1. **Check Windows Firewall:**
   ```cmd
   # Allow incoming connections on ports 3000 and 5000
   netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000
   netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000
   ```

2. **Verify network connectivity:**
   ```cmd
   # Test from another machine in the office
   curl http://[COMPANY_MACHINE_IP]:3000
   curl http://[COMPANY_MACHINE_IP]:5000
   ```

## 🔄 Customization

### Change Office Hours

**Method 1: Using Command Line**
```cmd
# Change startup time to 8:30 AM
schtasks /change /tn "Office Server Startup" /st 08:30

# Change shutdown time to 6:30 PM
schtasks /change /tn "Office Server Shutdown" /st 18:30
```

**Method 2: Using Task Scheduler GUI**
1. Open "Task Scheduler" (taskschd.msc)
2. Find "Office Server Startup" and "Office Server Shutdown"
3. Right-click → Properties → Triggers
4. Edit the time settings

### Change Ports
If you need different ports:
1. Update `start_server.py` (lines with port numbers)
2. Update `stop_server.py` (port detection)
3. Update `control_server.bat` (status checking)
4. Update firewall rules

## 🗑️ Uninstallation

### Remove Automation
```cmd
# Remove scheduled tasks
schtasks /delete /tn "Office Server Startup" /f
schtasks /delete /tn "Office Server Shutdown" /f

# Stop any running servers
control_server.bat stop
```

### Remove Firewall Rules
```cmd
netsh advfirewall firewall delete rule name="Office Server Frontend"
netsh advfirewall firewall delete rule name="Office Server Backend"
```

## 🔧 Advanced Configuration

### Windows Firewall Configuration
```cmd
# Allow incoming connections on ports 3000 and 5000
netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000

# Allow only from office network (replace with your office network)
netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000 remoteip=192.168.1.0/24
netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000 remoteip=192.168.1.0/24
```

### PowerShell Script for Monitoring
```powershell
# Create a monitoring script
$logFile = "$env:TEMP\office_server.log"
Get-Content $logFile -Wait -Tail 10
```

## 📞 Support

If you encounter issues:
1. Check the log files in `%TEMP%`
2. Run `control_server.bat status` to check server state
3. Verify network connectivity within your office
4. Ensure all dependencies are installed
5. Check system resources (CPU, memory, disk space)

## 🔄 Updates

To update the automation after code changes:
1. Stop the current server: `control_server.bat stop`
2. Pull latest code changes
3. Restart the server: `control_server.bat start`
4. The automation will continue to work with the updated code

## 🚨 Important Notes

1. **Administrator Access**: Setup requires administrator privileges
2. **Network Security**: Ensure your IT department approves the network configuration
3. **Backup**: Keep backups of your configuration files
4. **Monitoring**: Regularly check logs for any issues
5. **Updates**: Keep the system and dependencies updated

## 📋 Quick Reference

### Daily Commands
```cmd
# Check if server is running
control_server.bat status

# View recent logs
control_server.bat logs

# Show office hours
control_server.bat schedule
```

### Emergency Commands
```cmd
# Force stop server
control_server.bat stop

# Force start server
control_server.bat start

# Restart server
control_server.bat restart
```

### Administrative Commands
```cmd
# Check Task Scheduler
schtasks /query /tn "Office Server*"

# Run tasks manually
schtasks /run /tn "Office Server Startup"
schtasks /run /tn "Office Server Shutdown"
``` 