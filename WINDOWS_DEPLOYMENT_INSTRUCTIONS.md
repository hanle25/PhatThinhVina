# Windows Deployment Instructions

## 🎯 **Your Setup is Ready for Windows!**

The Python scripts have been tested and are working correctly. Here's exactly what you need to do on your Windows company machine.

## 📁 **Files to Copy to Windows Machine**

Copy these files to your Windows company machine:

### **Core Scripts**
- `start_server.py` ✅ (Tested and working)
- `stop_server.py` ✅ (Tested and working)
- `setup_windows_automation.bat`
- `office_server_startup.bat`
- `office_server_shutdown.bat`

### **Documentation**
- `WINDOWS_DEPLOYMENT_GUIDE.md`
- `WINDOWS_QUICK_REFERENCE.txt`

### **Your Application**
- `backend/` folder (your Flask backend)
- `frontend/` folder (your React frontend)

## 🚀 **Step-by-Step Windows Setup**

### **Step 1: Prepare Windows Machine**
1. **Install Python 3.7+** on Windows
2. **Install Node.js and npm** on Windows
3. **Copy all files** to a folder on the Windows machine

### **Step 2: Open Command Prompt as Administrator**
```cmd
# Right-click on Command Prompt → "Run as administrator"
# Navigate to your project directory
cd C:\path\to\your\project
```

### **Step 3: Run the Setup Script**
```cmd
# This will install dependencies and create Task Scheduler tasks
setup_windows_automation.bat
```

### **Step 4: Test the Setup**
```cmd
# Test manual startup
control_server.bat start

# Check server status
control_server.bat status

# View server logs
control_server.bat logs

# Show office hours schedule
control_server.bat schedule
```

## ⏰ **Office Hours: 9 AM - 7 PM**

Your server will automatically:
- **Start** at 9:00 AM on weekdays
- **Stop** at 7:00 PM on weekdays
- **Remain off** on weekends

## 🌐 **Access Information**

Once running, your application will be accessible at:
- **Frontend**: `http://[COMPANY_MACHINE_IP]:3000`
- **Backend API**: `http://[COMPANY_MACHINE_IP]:5000`

To find your company machine IP:
```cmd
ipconfig | findstr "IPv4"
```

## 🔧 **Daily Commands on Windows**

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

## 🛠️ **Troubleshooting on Windows**

### **If `control_server.bat start` gives an error:**

1. **Check if Python is installed:**
   ```cmd
   python --version
   ```

2. **Check if Node.js is installed:**
   ```cmd
   node --version
   npm --version
   ```

3. **Install dependencies:**
   ```cmd
   cd backend && pip install -r requirements.txt
   cd frontend && npm install
   ```

4. **Check if ports are available:**
   ```cmd
   netstat -ano | findstr ":3000"
   netstat -ano | findstr ":5000"
   ```

5. **Run as Administrator:**
   - Right-click Command Prompt → "Run as administrator"

### **If automation doesn't work:**

1. **Check Task Scheduler:**
   ```cmd
   schtasks /query /tn "Office Server Startup"
   schtasks /query /tn "Office Server Shutdown"
   ```

2. **Run tasks manually:**
   ```cmd
   schtasks /run /tn "Office Server Startup"
   ```

## 🔒 **Firewall Configuration (Optional)**

If you need to configure Windows Firewall:

```cmd
# Allow incoming connections (run as Administrator)
netsh advfirewall firewall add rule name="Office Server Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Office Server Backend" dir=in action=allow protocol=TCP localport=5000
```

## 📞 **Support**

If you encounter issues:
1. Check the log files in `%TEMP%\office_server.log`
2. Run `control_server.bat status` to check server state
3. Verify all dependencies are installed
4. Ensure you're running as Administrator
5. Check if ports 3000 and 5000 are available

## ✅ **What's Been Tested**

- ✅ Python scripts work correctly
- ✅ Server startup and shutdown work
- ✅ Network binding works
- ✅ Process management works
- ✅ Logging works

## 🎉 **You're Ready for Windows Deployment!**

The setup has been tested and is ready for your Windows company machine. Just follow the steps above and you'll have your office hours server running automatically from 9 AM to 7 PM! 