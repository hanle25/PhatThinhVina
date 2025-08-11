# Windows Troubleshooting Guide

## 🚨 **Common Issues and Solutions**

### **Issue 1: `control_server.bat start` gives an error**

**Symptoms:**
- Command prompt shows error messages
- Server doesn't start
- Ports are not accessible

**Solutions:**

#### **Step 1: Check Dependencies**
```cmd
# Check Python version
python --version

# Check Node.js version
node --version

# Check npm version
npm --version
```

#### **Step 2: Install Missing Dependencies**
```cmd
# Install Python packages
cd backend
pip install -r requirements.txt

# Install Node.js packages
cd frontend
npm install
```

#### **Step 3: Check Port Availability**
```cmd
# Check if ports are already in use
netstat -ano | findstr ":3000"
netstat -ano | findstr ":5000"

# If ports are in use, kill the processes
taskkill /PID [PID_NUMBER] /F
```

#### **Step 4: Run as Administrator**
- Right-click Command Prompt → "Run as administrator"
- Navigate to your project directory
- Try the command again

### **Issue 2: Frontend Server Crashes Immediately**

**Symptoms:**
- Backend starts successfully
- Frontend starts but crashes within seconds
- Error messages about React/Node.js

**Solutions:**

#### **Option A: Use Backend-Only Mode**
```cmd
# Start only the backend server
python start_backend_only.py

# Or use the batch file
start_backend_only.bat
```

#### **Option B: Fix Frontend Issues**
```cmd
# Navigate to frontend directory
cd frontend

# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rmdir /s node_modules
del package-lock.json
npm install

# Try starting again
npm start
```

#### **Option C: Check Frontend Dependencies**
```cmd
# Check if all required packages are installed
npm list

# Install missing packages
npm install react react-dom react-scripts
```

### **Issue 3: Automation Not Working**

**Symptoms:**
- Server doesn't start automatically at 9 AM
- Server doesn't stop automatically at 7 PM
- Task Scheduler shows errors

**Solutions:**

#### **Step 1: Check Task Scheduler**
```cmd
# Check if tasks exist
schtasks /query /tn "Office Server Startup"
schtasks /query /tn "Office Server Shutdown"

# Check task status
schtasks /query /tn "Office Server Startup" /fo table
schtasks /query /tn "Office Server Shutdown" /fo table
```

#### **Step 2: Run Tasks Manually**
```cmd
# Test startup task
schtasks /run /tn "Office Server Startup"

# Test shutdown task
schtasks /run /tn "Office Server Shutdown"
```

#### **Step 3: Recreate Tasks**
```cmd
# Delete existing tasks
schtasks /delete /tn "Office Server Startup" /f
schtasks /delete /tn "Office Server Shutdown" /f

# Run setup again
setup_windows_automation.bat
```

### **Issue 4: Network Access Problems**

**Symptoms:**
- Server starts but can't be accessed from other computers
- Firewall blocks connections
- "Connection refused" errors

**Solutions:**

#### **Step 1: Check Windows Firewall**
```cmd
# Allow incoming connections (run as Administrator)
netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000
```

#### **Step 2: Check Network Configuration**
```cmd
# Find your IP address
ipconfig | findstr "IPv4"

# Test connectivity
ping [YOUR_IP_ADDRESS]
```

#### **Step 3: Test from Another Computer**
```cmd
# From another computer in the office
curl http://[COMPANY_MACHINE_IP]:5000
curl http://[COMPANY_MACHINE_IP]:3000
```

### **Issue 5: Permission Errors**

**Symptoms:**
- "Access denied" messages
- Can't create log files
- Can't start services

**Solutions:**

#### **Step 1: Run as Administrator**
- Always run Command Prompt as Administrator
- Right-click Command Prompt → "Run as administrator"

#### **Step 2: Check File Permissions**
```cmd
# Check if you can write to temp directory
echo test > %TEMP%\test.txt
del %TEMP%\test.txt
```

#### **Step 3: Check Python Permissions**
```cmd
# Test Python installation
python -c "print('Python is working')"
```

### **Issue 6: Virtual Environment Problems**

**Symptoms:**
- "Module not found" errors
- Python can't find packages
- Virtual environment not activated

**Solutions:**

#### **Step 1: Create Virtual Environment**
```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate.bat

# Install packages
pip install -r backend\requirements.txt
pip install psutil
```

#### **Step 2: Check Virtual Environment**
```cmd
# Check if virtual environment is active
where python

# Should show: C:\path\to\your\project\.venv\Scripts\python.exe
```

### **Issue 7: Log File Issues**

**Symptoms:**
- No log files created
- Can't read log files
- Log files are empty

**Solutions:**

#### **Step 1: Check Log File Location**
```cmd
# Check temp directory
echo %TEMP%

# List log files
dir %TEMP%\office_server*.log
```

#### **Step 2: Create Log Directory**
```cmd
# Create log directory if it doesn't exist
mkdir %TEMP%\office_logs 2>nul

# Check permissions
echo test > %TEMP%\office_logs\test.log
del %TEMP%\office_logs\test.log
```

## 🔧 **Alternative Solutions**

### **Backend-Only Deployment**
If frontend continues to have issues, you can deploy just the backend:

```cmd
# Use backend-only script
python start_backend_only.py

# Or use the batch file
start_backend_only.bat
```

### **Manual Control**
If automation doesn't work, use manual control:

```cmd
# Start server manually
control_server.bat start

# Stop server manually
control_server.bat stop

# Check status
control_server.bat status
```

### **Production Frontend**
If development frontend has issues, build production version:

```cmd
# Navigate to frontend
cd frontend

# Build production version
npm run build

# Serve production build
npx serve -s build -l 3000
```

## 📞 **Getting Help**

### **Check Logs First**
```cmd
# View startup logs
control_server.bat logs

# View specific log files
type %TEMP%\office_server.log
type %TEMP%\office_server_shutdown.log
```

### **Common Error Messages**

| Error | Solution |
|-------|----------|
| "Module not found" | Install missing packages: `pip install [package_name]` |
| "Port already in use" | Kill process using port: `taskkill /PID [PID] /F` |
| "Access denied" | Run as Administrator |
| "Node.js not found" | Install Node.js from https://nodejs.org/ |
| "Python not found" | Install Python from https://python.org/ |

### **Emergency Commands**
```cmd
# Force stop all servers
taskkill /f /im python.exe
taskkill /f /im node.exe

# Restart Task Scheduler service
net stop Schedule
net start Schedule

# Check system resources
tasklist | findstr python
tasklist | findstr node
```

## ✅ **Success Indicators**

Your setup is working correctly when:
- ✅ `control_server.bat start` runs without errors
- ✅ `control_server.bat status` shows servers running
- ✅ You can access `http://[COMPANY_IP]:5000` from other computers
- ✅ Log files are created in `%TEMP%`
- ✅ Task Scheduler shows tasks as "Ready"
- ✅ Server starts automatically at 9 AM
- ✅ Server stops automatically at 7 PM 