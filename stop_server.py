#!/usr/bin/env python3
"""
Office Hours Server Shutdown Script
Cross-platform script to gracefully stop both Flask backend and React frontend servers.
"""

import subprocess
import sys
import os
import time
import signal
import logging
import platform
import psutil
from pathlib import Path

# Configure logging
log_dir = Path("/tmp") if platform.system() != "Windows" else Path(os.environ.get("TEMP", "C:/temp"))
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "office_server_shutdown.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_and_kill_processes():
    """Find and kill Flask and React development servers"""
    killed_processes = []
    
    try:
        # Find Flask processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Kill Flask development server
                if 'flask' in cmdline.lower() and 'run' in cmdline.lower():
                    logger.info(f"Killing Flask process (PID: {proc.info['pid']})")
                    proc.terminate()
                    killed_processes.append(proc.info['pid'])
                
                # Kill React development server
                elif 'react-scripts' in cmdline.lower() and 'start' in cmdline.lower():
                    logger.info(f"Killing React process (PID: {proc.info['pid']})")
                    proc.terminate()
                    killed_processes.append(proc.info['pid'])
                
                # Kill Node.js processes on ports 3000 and 5000
                elif proc.info['name'] == 'node' and any(port in cmdline for port in ['3000', '5000']):
                    logger.info(f"Killing Node.js process on development port (PID: {proc.info['pid']})")
                    proc.terminate()
                    killed_processes.append(proc.info['pid'])
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Wait for processes to terminate gracefully
        if killed_processes:
            logger.info("Waiting for processes to terminate gracefully...")
            time.sleep(5)
            
            # Force kill if still running
            for proc in psutil.process_iter(['pid']):
                try:
                    if proc.info['pid'] in killed_processes and proc.is_running():
                        logger.info(f"Force killing process (PID: {proc.info['pid']})")
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        logger.info("All development servers stopped")
        return True
        
    except Exception as e:
        logger.error(f"Error stopping processes: {e}")
        return False

def kill_by_port():
    """Kill processes by port number"""
    try:
        if platform.system() == "Windows":
            # Windows: use netstat and taskkill
            # Kill processes on port 3000 (React)
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ':3000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        logger.info(f"Killing process on port 3000 (PID: {pid})")
                        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
            
            # Kill processes on port 5000 (Flask)
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ':5000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        logger.info(f"Killing process on port 5000 (PID: {pid})")
                        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
        else:
            # Unix-like systems: use lsof
            # Kill processes on port 3000 (React)
            result = subprocess.run(['lsof', '-ti:3000'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Killing process on port 3000 (PID: {pid})")
                        subprocess.run(['kill', '-TERM', pid])
            
            # Kill processes on port 5000 (Flask)
            result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Killing process on port 5000 (PID: {pid})")
                        subprocess.run(['kill', '-TERM', pid])
            
            time.sleep(3)
            
            # Force kill if still running
            result = subprocess.run(['lsof', '-ti:3000'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Force killing process on port 3000 (PID: {pid})")
                        subprocess.run(['kill', '-KILL', pid])
            
            result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Force killing process on port 5000 (PID: {pid})")
                        subprocess.run(['kill', '-KILL', pid])
                    
    except Exception as e:
        logger.error(f"Error killing processes by port: {e}")

def main():
    logger.info("Starting server shutdown process...")
    
    # Try to stop processes gracefully
    success = find_and_kill_processes()
    
    # Fallback: kill by port
    if not success:
        logger.info("Falling back to port-based process killing...")
        kill_by_port()
    
    logger.info("Server shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 