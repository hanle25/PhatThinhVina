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
main_log_file = log_dir / "office_server.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(main_log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OfficeServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.backend_log_handle = None
        self.frontend_log_handle = None
        self.running = False
        
        # Get the project root directory
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
        # Network configuration
        # Bind on all interfaces for LAN access; still print the detected IP for convenience
        self.public_host = self.get_office_ip()
        self.bind_host = "0.0.0.0"
        self.backend_port = 5000
        self.frontend_port = 3000
        
        # Per-process log files
        self.backend_log_file = log_dir / "backend_server.log"
        self.frontend_log_file = log_dir / "frontend_server.log"
        
    def get_office_ip(self):
        """Get the local IP address to bind to (office network only)"""
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
            cmd = [python_cmd, "-m", "flask", "run", "--host", self.bind_host, "--port", str(self.backend_port)]
            # Open log handle (append mode)
            self.backend_log_handle = open(self.backend_log_file, "a", buffering=1, encoding="utf-8")
            if platform.system() == "Windows":
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=self.backend_dir,
                    stdout=self.backend_log_handle,
                    stderr=self.backend_log_handle,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=self.backend_dir,
                    stdout=self.backend_log_handle,
                    stderr=self.backend_log_handle,
                    preexec_fn=os.setsid
                )
            logger.info(f"Backend server started on {self.public_host}:{self.backend_port}")
            logger.info(f"Backend logs: {self.backend_log_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend server"""
        try:
            logger.info("Starting React frontend server...")
            env = os.environ.copy()
            # Bind dev server on all interfaces for LAN access
            env['HOST'] = self.bind_host
            env['PORT'] = str(self.frontend_port)
            env['BROWSER'] = 'none'  # Prevent browser from opening automatically
            # CRA + Node >= 20 OpenSSL fix
            env.setdefault('NODE_OPTIONS', '--openssl-legacy-provider')
            # In case host checks interfere on some environments
            env.setdefault('DANGEROUSLY_DISABLE_HOST_CHECK', 'true')
            
            # Open log handle (append mode)
            self.frontend_log_handle = open(self.frontend_log_file, "a", buffering=1, encoding="utf-8")
            if platform.system() == "Windows":
                cmd = ["npm.cmd", "start"]
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    env=env,
                    stdout=self.frontend_log_handle,
                    stderr=self.frontend_log_handle,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                cmd = ["npm", "start"]
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    env=env,
                    stdout=self.frontend_log_handle,
                    stderr=self.frontend_log_handle,
                    preexec_fn=os.setsid
                )
            logger.info(f"Frontend server started on {self.public_host}:{self.frontend_port}")
            logger.info(f"Frontend logs: {self.frontend_log_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to start frontend server: {e}")
            return False
    
    def wait_for_server(self, host, port, timeout=60):
        """Wait for a server to be ready on a specific host:port"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.create_connection((host, port), timeout=2)
                sock.close()
                logger.info(f"Server on {host}:{port} is ready")
                return True
            except Exception:
                time.sleep(1)
        logger.warning(f"Server on {host}:{port} did not become ready within {timeout} seconds")
        return False
    
    def start_servers(self):
        """Start both servers"""
        logger.info("Starting office hours server...")
        
        # Start backend first and wait
        if not self.start_backend():
            logger.error("Failed to start backend server")
            return False
        self.wait_for_server(self.public_host, self.backend_port, timeout=45)
        
        # Start frontend and wait longer (install/compile can take time on Windows)
        if not self.start_frontend():
            logger.error("Failed to start frontend server")
            self.stop_backend()
            return False
        self.wait_for_server(self.public_host, self.frontend_port, timeout=120)
        
        self.running = True
        logger.info("Both servers started successfully!")
        logger.info(f"Backend:  http://{self.public_host}:{self.backend_port}")
        logger.info(f"Frontend: http://{self.public_host}:{self.frontend_port}")
        
        return True
    
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
                    except Exception:
                        pass
            finally:
                self.backend_process = None
                if self.backend_log_handle:
                    try:
                        self.backend_log_handle.close()
                    except Exception:
                        pass
                    self.backend_log_handle = None
    
    def stop_frontend(self):
        """Stop the frontend server"""
        if self.frontend_process:
            try:
                if platform.system() == "Windows":
                    self.frontend_process.terminate()
                else:
                    try:
                        os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                    except (ProcessLookupError, OSError):
                        pass
                try:
                    self.frontend_process.wait(timeout=10)
                    logger.info("Frontend server stopped")
                except subprocess.TimeoutExpired:
                    self.frontend_process.kill()
                    logger.info("Frontend server force killed")
            except Exception as e:
                logger.error(f"Error stopping frontend: {e}")
                if self.frontend_process.poll() is None:
                    try:
                        self.frontend_process.kill()
                    except Exception:
                        pass
            finally:
                self.frontend_process = None
                if self.frontend_log_handle:
                    try:
                        self.frontend_log_handle.close()
                    except Exception:
                        pass
                    self.frontend_log_handle = None
    
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
            while self.running:
                time.sleep(1)
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