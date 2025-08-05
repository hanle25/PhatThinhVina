#!/usr/bin/env python3
"""
Office Hours Server Startup Script
Cross-platform script to start both Flask backend and React frontend servers
with network restrictions to only allow access from the office network.
"""

import subprocess
import sys
import os
import time
import signal
import logging
import platform
from pathlib import Path
import socket
import threading

# Configure logging
log_dir = Path("/tmp") if platform.system() != "Windows" else Path(os.environ.get("TEMP", "C:/temp"))
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "office_server.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OfficeServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
        # Get the project root directory
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
        # Network configuration - restrict to office network
        self.host = self.get_office_ip()
        self.backend_port = 5000
        self.frontend_port = 3000
        
    def get_office_ip(self):
        """Get the local IP address to bind to (office network only)"""
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"Binding to local IP: {local_ip}")
            return local_ip
        except Exception as e:
            logger.warning(f"Could not determine local IP, using localhost: {e}")
            return "127.0.0.1"
    
    def get_python_cmd(self):
        """Get the appropriate Python command for the platform"""
        # Try virtual environment first
        if platform.system() == "Windows":
            venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        else:
            venv_python = self.project_root / ".venv" / "bin" / "python"
        
        if venv_python.exists():
            return str(venv_python)
        
        # Fallback to system Python
        return sys.executable
    
    def start_backend(self):
        """Start the Flask backend server"""
        try:
            logger.info("Starting Flask backend server...")
            
            python_cmd = self.get_python_cmd()
            
            # Platform-specific command
            if platform.system() == "Windows":
                # Windows: use python -m flask
                cmd = [python_cmd, "-m", "flask", "run", "--host", self.host, "--port", str(self.backend_port)]
                # Use CREATE_NEW_PROCESS_GROUP on Windows
                self.backend_process = subprocess.Popen(
                    cmd, 
                    cwd=self.backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix-like systems
                cmd = [python_cmd, "-m", "flask", "run", "--host", self.host, "--port", str(self.backend_port)]
                self.backend_process = subprocess.Popen(
                    cmd, 
                    cwd=self.backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            logger.info(f"Backend server started on {self.host}:{self.backend_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend server"""
        try:
            logger.info("Starting React frontend server...")
            
            # Set environment variables
            env = os.environ.copy()
            env['HOST'] = self.host
            env['PORT'] = str(self.frontend_port)
            
            # Platform-specific npm command
            if platform.system() == "Windows":
                cmd = ["npm.cmd", "start"]
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                cmd = ["npm", "start"]
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            logger.info(f"Frontend server started on {self.host}:{self.frontend_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frontend server: {e}")
            return False
    
    def start_servers(self):
        """Start both servers"""
        logger.info("Starting office hours server...")
        
        # Start backend first
        if not self.start_backend():
            logger.error("Failed to start backend server")
            return False
        
        # Wait a moment for backend to initialize
        time.sleep(3)
        
        # Start frontend
        if not self.start_frontend():
            logger.error("Failed to start frontend server")
            self.stop_backend()
            return False
        
        self.running = True
        logger.info("Both servers started successfully!")
        logger.info(f"Backend: http://{self.host}:{self.backend_port}")
        logger.info(f"Frontend: http://{self.host}:{self.frontend_port}")
        
        return True
    
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            try:
                if platform.system() == "Windows":
                    self.backend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                
                self.backend_process.wait(timeout=10)
                logger.info("Backend server stopped")
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
                if self.backend_process.poll() is None:
                    self.backend_process.kill()
            finally:
                self.backend_process = None
    
    def stop_frontend(self):
        """Stop the frontend server"""
        if self.frontend_process:
            try:
                if platform.system() == "Windows":
                    self.frontend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                
                self.frontend_process.wait(timeout=10)
                logger.info("Frontend server stopped")
            except Exception as e:
                logger.error(f"Error stopping frontend: {e}")
                if self.frontend_process.poll() is None:
                    self.frontend_process.kill()
            finally:
                self.frontend_process = None
    
    def stop_servers(self):
        """Stop both servers"""
        logger.info("Stopping office hours server...")
        self.running = False
        
        self.stop_frontend()
        self.stop_backend()
        
        logger.info("All servers stopped")
    
    def run(self):
        """Main run loop"""
        try:
            if not self.start_servers():
                return False
            
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend server crashed")
                    break
                
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("Frontend server crashed")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop_servers()
        
        return True

def main():
    server = OfficeServer()
    success = server.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 