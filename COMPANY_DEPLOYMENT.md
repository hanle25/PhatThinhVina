# Company Machine Deployment Guide

This guide will help you deploy your React + Flask application on a company machine (Windows or Linux) with automatic office hours scheduling and network restrictions.

## 🎯 Overview

The setup includes:
- **Cross-platform compatibility** - Works on Windows and Linux
- **Network-restricted access** - Only accessible from office network
- **Automatic startup** - Starts at 8:00 AM on weekdays
- **Automatic shutdown** - Stops at 6:00 PM on weekdays
- **Manual controls** - Start/stop/restart as needed
- **Firewall protection** - Blocks external access

## 📋 Prerequisites

### Windows Requirements
- Windows 10/11 or Windows Server
- Python 3.7+
- Node.js and npm
- Administrator access (for Task Scheduler)

### Linux Requirements
- Ubuntu 18.04+, CentOS 7+, or similar
- Python 3.7+
- Node.js and npm
- sudo access (for systemd services)

## 🚀 Quick Setup

### For Windows Company Machines

1. **Run the Windows setup script:**
   ```cmd
   setup_windows_automation.bat
   ```

2. **Test the setup:**
   ```cmd
   control_server.bat start
   control_server.bat status
   ```

### For Linux Company Machines

1. **Run the Linux setup script:**
   ```bash
   chmod +x setup_linux_automation.sh
   sudo ./setup_linux_automation.sh
   ```

2. **Test the setup:**
   ```bash
   ./control_server.sh start
   ./control_server.sh status
   ```

## 🔧 Manual Controls

### Windows Controls
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
```

### Linux Controls
```bash
# Start server manually
./control_server.sh start

# Stop server manually  
./control_server.sh stop

# Restart server
./control_server.sh restart

# Check server status
./control_server.sh status

# View server logs
./control_server.sh logs

# Enable/disable automation
./control_server.sh enable-timer
./control_server.sh disable-timer
```

## ⏰ Automation Schedule

- **Startup**: Monday-Friday at 8:00 AM
- **Shutdown**: Monday-Friday at 6:00 PM
- **Weekends**: Server remains off

## 🌐 Access Information

Once running, your application will be accessible at:
- **Frontend**: `http://[COMPANY_MACHINE_IP]:3000`
- **Backend API**: `http://[COMPANY_MACHINE_IP]:5000`

### Find Company Machine IP Address

**Windows:**
```cmd
ipconfig | findstr "IPv4"
```

**Linux:**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

## 📁 File Structure

```
PhatThinhVina/
├── start_server.py                    # Cross-platform server startup
├── stop_server.py                     # Cross-platform server shutdown
├── setup_windows_automation.bat       # Windows automation setup
├── setup_linux_automation.sh          # Linux automation setup
├── office_server_startup.bat          # Windows startup script
├── office_server_shutdown.bat         # Windows shutdown script
├── control_server.bat                 # Windows manual control
├── control_server.sh                  # Linux manual control
├── office-server.service              # Linux systemd service
├── office-server.timer                # Linux systemd timer
├── backend/                           # Flask backend
├── frontend/                          # React frontend
└── COMPANY_DEPLOYMENT.md              # This guide
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

**Windows:**
- `%TEMP%\office_server.log` - Server startup logs
- `%TEMP%\office_server_shutdown.log` - Shutdown logs

**Linux:**
- `journalctl -u office-server.service` - System logs
- `/tmp/office_server.log` - Application logs

### Status Checking
```bash
# Windows
control_server.bat status

# Linux
./control_server.sh status
```

## 🛠️ Troubleshooting

### Server Won't Start

1. **Check if ports are already in use:**

   **Windows:**
   ```cmd
   netstat -ano | findstr ":3000"
   netstat -ano | findstr ":5000"
   ```

   **Linux:**
   ```bash
   lsof -i :3000
   lsof -i :5000
   ```

2. **Check logs:**
   ```bash
   # Windows
   control_server.bat logs
   
   # Linux
   ./control_server.sh logs
   ```

3. **Verify dependencies:**
   ```bash
   cd backend && pip install -r requirements.txt
   cd frontend && npm install
   ```

### Automation Not Working

**Windows:**
1. Check Task Scheduler:
   ```cmd
   schtasks /query /tn "Office Server Startup"
   schtasks /query /tn "Office Server Shutdown"
   ```

2. Run tasks manually:
   ```cmd
   schtasks /run /tn "Office Server Startup"
   ```

**Linux:**
1. Check systemd services:
   ```bash
   sudo systemctl status office-server.service
   sudo systemctl status office-server.timer
   ```

2. Enable and start services:
   ```bash
   sudo systemctl enable office-server.service
   sudo systemctl start office-server.service
   ```

### Network Access Issues

1. **Check firewall settings:**
   - Windows: Windows Firewall
   - Linux: iptables/ufw

2. **Verify network connectivity:**
   ```bash
   # Test from another machine in the office
   curl http://[COMPANY_MACHINE_IP]:3000
   curl http://[COMPANY_MACHINE_IP]:5000
   ```

## 🔄 Customization

### Change Office Hours

**Windows:**
Edit Task Scheduler tasks:
```cmd
schtasks /change /tn "Office Server Startup" /st 09:00
schtasks /change /tn "Office Server Shutdown" /st 17:00
```

**Linux:**
Edit the timer file:
```bash
sudo nano /etc/systemd/system/office-server.timer
# Change OnCalendar times
sudo systemctl daemon-reload
```

### Change Ports
If you need different ports:
1. Update `start_server.py` (lines with port numbers)
2. Update `stop_server.py` (port detection)
3. Update control scripts (status checking)

## 🗑️ Uninstallation

### Windows
```cmd
# Remove scheduled tasks
schtasks /delete /tn "Office Server Startup" /f
schtasks /delete /tn "Office Server Shutdown" /f

# Stop any running servers
control_server.bat stop
```

### Linux
```bash
# Disable and remove services
sudo systemctl disable office-server.service
sudo systemctl disable office-server.timer
sudo rm /etc/systemd/system/office-server.service
sudo rm /etc/systemd/system/office-server.timer
sudo systemctl daemon-reload

# Stop any running servers
./control_server.sh stop
```

## 🔧 Advanced Configuration

### Windows Firewall Configuration
```cmd
# Allow incoming connections on ports 3000 and 5000
netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000
```

### Linux Firewall Configuration
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 3000/tcp
sudo ufw allow 5000/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 📞 Support

If you encounter issues:
1. Check the log files
2. Run status commands to check server state
3. Verify network connectivity within your office
4. Ensure all dependencies are installed
5. Check system resources (CPU, memory, disk space)

## 🔄 Updates

To update the automation after code changes:
1. Stop the current server
2. Pull latest code changes
3. Restart the server
4. The automation will continue to work with the updated code

## 🚨 Important Notes

1. **Administrator Access**: Setup requires administrator/sudo privileges
2. **Network Security**: Ensure your IT department approves the network configuration
3. **Backup**: Keep backups of your configuration files
4. **Monitoring**: Regularly check logs for any issues
5. **Updates**: Keep the system and dependencies updated 