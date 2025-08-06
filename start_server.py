#!/usr/bin/env python3
"""
Patched Office Hours Server Startup Script
- Redirects backend/frontend stdout/stderr to a log file (no PIPE blocking)
- Uses detached process flags on Windows
- Optional production frontend mode (build + serve) when env USE_PROD_FRONTEND=1
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

# Setup logging file location
IS_WINDOWS = platform.system() == "Windows"
TEMP_DIR = Path(os.environ.get("TEMP", "C:/temp")) if IS_WINDOWS else Path("/tmp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = TEMP_DIR / "office_server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

class OfficeServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False

        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"

        self.host = self.get_office_ip()
        self.backend_port = int(os.environ.get("BACKEND_PORT", 5000))
        self.frontend_port = int(os.environ.get("FRONTEND_PORT", 3000))

        # Toggle production frontend (build + serve) with env var
        self.use_prod_frontend = os.environ.get("USE_PROD_FRONTEND", "0") in ("1", "true", "True")

    def get_office_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            logger.info(f"Binding to local IP: {ip}")
            return ip
        except Exception as e:
            logger.warning(f"Could not determine local IP, falling back to 127.0.0.1: {e}")
            return "127.0.0.1"

    def get_python_cmd(self):
        # Prefer virtualenv python if present
        if IS_WINDOWS:
            venv_py = self.project_root / ".venv" / "Scripts" / "python.exe"
        else:
            venv_py = self.project_root / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)
        return sys.executable

    def open_log_handles(self):
        # Open shared append handles (line-buffered if possible)
        # buffering=1 gives line-buffering for text mode
        f_out = open(LOG_FILE, "a", buffering=1, encoding="utf-8")
        f_err = open(LOG_FILE, "a", buffering=1, encoding="utf-8")
        return f_out, f_err

    def start_backend(self):
        logger.info("Starting Flask backend server...")
        python_cmd = self.get_python_cmd()
        env = os.environ.copy()
        
        # Đặt biến môi trường để flask biết app và host, port
        env["FLASK_APP"] = "app.py"  # sửa thành tên file Flask app chính của bạn nếu khác
        env["FLASK_RUN_HOST"] = self.host
        env["FLASK_RUN_PORT"] = str(self.backend_port)

        cmd = [python_cmd, "-m", "flask", "run", "--host", self.host, "--port", str(self.backend_port)]

        out, err = self.open_log_handles()
        try:
            if IS_WINDOWS:
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=str(self.backend_dir),
                    env=env,
                    stdout=out,
                    stderr=err,
                    creationflags=creationflags,
                )
            else:
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=str(self.backend_dir),
                    env=env,
                    stdout=out,
                    stderr=err,
                    preexec_fn=os.setsid,
                )
            logger.info(f"Backend server started on {self.host}:{self.backend_port}")
            return True
        except Exception as e:
            logger.exception(f"Failed to start backend: {e}")
            return False


    def build_frontend(self):
        """Run npm install and npm run build (blocking)"""
        logger.info("Running frontend build (npm install && npm run build)...")
        env = os.environ.copy()
        try:
            # npm install
            cmd_install = ["npm", "install"] if not IS_WINDOWS else ["npm.cmd", "install"]
            subprocess.check_call(cmd_install, cwd=str(self.frontend_dir), env=env)
            # npm run build
            cmd_build = ["npm", "run", "build"] if not IS_WINDOWS else ["npm.cmd", "run", "build"]
            subprocess.check_call(cmd_build, cwd=str(self.frontend_dir), env=env)
            logger.info("Frontend build completed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.exception(f"Frontend build failed: {e}")
            return False

    def start_frontend(self):
        logger.info("Starting React frontend server...")
        env = os.environ.copy()
        env["HOST"] = self.host
        env["PORT"] = str(self.frontend_port)

        out, err = self.open_log_handles()

        try:
            if self.use_prod_frontend:
                # Production mode: serve the build folder using npx serve -s build -l <port>
                # Ensure build exists (if not, build it)
                build_dir = self.frontend_dir / "build"
                if not build_dir.exists():
                    ok = self.build_frontend()
                    if not ok:
                        logger.error("Frontend build failed, cannot start production frontend")
                        return False

                if IS_WINDOWS:
                    cmd = ["npx.cmd", "serve", "-s", "build", "-l", str(self.frontend_port)]
                    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                    self.frontend_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.frontend_dir),
                        env=env,
                        stdout=out,
                        stderr=err,
                        creationflags=creationflags,
                    )
                else:
                    cmd = ["npx", "serve", "-s", "build", "-l", str(self.frontend_port)]
                    self.frontend_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.frontend_dir),
                        env=env,
                        stdout=out,
                        stderr=err,
                        preexec_fn=os.setsid,
                    )

            else:
                # Dev mode: run npm start (dev server)
                if IS_WINDOWS:
                    cmd = ["npm.cmd", "start"]
                    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                    self.frontend_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.frontend_dir),
                        env=env,
                        stdout=out,
                        stderr=err,
                        creationflags=creationflags,
                    )
                else:
                    cmd = ["npm", "start"]
                    self.frontend_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.frontend_dir),
                        env=env,
                        stdout=out,
                        stderr=err,
                        preexec_fn=os.setsid,
                    )

            logger.info(f"Frontend server started on {self.host}:{self.frontend_port} (prod={self.use_prod_frontend})")
            return True
        except Exception as e:
            logger.exception(f"Failed to start frontend: {e}")
            return False

    def stop_backend(self):
        if self.backend_process:
            try:
                logger.info("Stopping backend server...")
                if IS_WINDOWS:
                    self.backend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                self.backend_process.wait(timeout=10)
                logger.info("Backend server stopped")
            except Exception as e:
                logger.exception(f"Error stopping backend: {e}")
                try:
                    self.backend_process.kill()
                except Exception:
                    pass
            finally:
                self.backend_process = None

    def stop_frontend(self):
        if self.frontend_process:
            try:
                logger.info("Stopping frontend server...")
                if IS_WINDOWS:
                    self.frontend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                self.frontend_process.wait(timeout=10)
                logger.info("Frontend server stopped")
            except Exception as e:
                logger.exception(f"Error stopping frontend: {e}")
                try:
                    self.frontend_process.kill()
                except Exception:
                    pass
            finally:
                self.frontend_process = None

    def start_servers(self):
        logger.info("Starting office hours server...")
        if not self.start_backend():
            logger.error("Failed to start backend")
            return False

        time.sleep(2)  # give backend a moment
        if not self.start_frontend():
            logger.error("Failed to start frontend, shutting backend down")
            self.stop_backend()
            return False

        self.running = True
        logger.info("Both servers started successfully!")
        logger.info(f"Backend: http://{self.host}:{self.backend_port}")
        logger.info(f"Frontend: http://{self.host}:{self.frontend_port}")
        return True

    def stop_servers(self):
        logger.info("Stopping office hours server...")
        self.running = False
        self.stop_frontend()
        self.stop_backend()
        logger.info("All servers stopped")

    def run(self):
        try:
            ok = self.start_servers()
            if not ok:
                return False

            # main loop
            while self.running:
                time.sleep(1)
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend server crashed")
                    break
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("Frontend server crashed")
                    break

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
        finally:
            self.stop_servers()
        return True

def main():
    server = OfficeServer()
    success = server.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()