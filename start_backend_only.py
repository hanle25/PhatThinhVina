#!/usr/bin/env python3
"""
Simple Backend Server Startup Script
This script starts only the Flask backend server for testing purposes.
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

# Configure logging
log_dir = Path("/tmp") if platform.system() != "Windows" else Path(os.environ.get("TEMP", "C:/temp"))
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "backend_server.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackendServer:
    def __init__(self):
        self.backend_process = None
        self.running = False
        
        # Get the project root directory
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        
        # Network configuration
        self.host = self.get_office_ip()
        self.backend_port = 5000
        
    def get_office_ip(self):
        """Get the local IP address to bind to"""
        try:
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
        if platform.system() == "Windows":
            venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        else:
            venv_python = self.project_root / ".venv" / "bin" / "python"
        
        if venv_python.exists():
            return str(venv_python)
        
        return sys.executable
    
    def start_backend(self):
        """Start the Flask backend server"""
        try:
            logger.info("Starting Flask backend server...")
            
            python_cmd = self.get_python_cmd()
            
            # Platform-specific command
            if platform.system() == "Windows":
                cmd = [python_cmd, "-m", "flask", "run", "--host", self.host, "--port", str(self.backend_port)]
                self.backend_process = subprocess.Popen(
                    cmd, 
                    cwd=self.backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                cmd = [python_cmd, "-m", "flask", "run", "--host", self.host, "--port", str(self.backend_port)]
                self.backend_process = subprocess.Popen(
                    cmd, 
                    cwd=self.backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            logger.info(f"Backend server started on {self.host}:{self.backend_port}")
            logger.info(f"Access URL: http://{self.host}:{self.backend_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            return False
    
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            try:
                if platform.system() == "Windows":
                    self.backend_process.terminate()
                else:
                    try:
                        os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                    except (ProcessLookupError, OSError):
                        pass
                
                try:
                    self.backend_process.wait(timeout=10)
                    logger.info("Backend server stopped")
                except subprocess.TimeoutExpired:
                    self.backend_process.kill()
                    logger.info("Backend server force killed")
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
                if self.backend_process.poll() is None:
                    try:
                        self.backend_process.kill()
                    except:
                        pass
            finally:
                self.backend_process = None
    
    def run(self):
        """Main run loop"""
        try:
            if not self.start_backend():
                return False
            
            self.running = True
            logger.info("Backend server is running. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
                
                # Check if process is still running
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend server crashed")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop_backend()
        
        return True

def main():
    server = BackendServer()
    success = server.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 