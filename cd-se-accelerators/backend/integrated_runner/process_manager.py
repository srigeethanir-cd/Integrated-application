"""Process Manager for asynchronously launching, monitoring, and managing integrated application processes."""

import os
import sys
import time
import subprocess
import threading
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .port_manager import find_free_port, is_port_in_use
from .runtime_store import save_runtime_info, load_runtime_info

logger = logging.getLogger(__name__)

# Global Singleton Instance
_RUNNER_INSTANCE: Optional['IntegratedProjectRunner'] = None

def get_runner() -> 'IntegratedProjectRunner':
    global _RUNNER_INSTANCE
    if _RUNNER_INSTANCE is None:
        _RUNNER_INSTANCE = IntegratedProjectRunner()
    return _RUNNER_INSTANCE


class IntegratedProjectRunner:
    def __init__(self):
        self.project_path: str = ""
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        
        self.frontend_port: int = 5175
        self.backend_port: int = 8010

        self.status_state: str = "idle"  # idle, starting, running, failed, stopped
        self.status_message: str = "Application is not running."
        self.error_detail: Optional[str] = None

        self.logs: List[str] = []
        self._log_lock = threading.Lock()
        self._start_time: Optional[str] = None

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        logger.info(entry)
        with self._log_lock:
            self.logs.append(entry)
            if len(self.logs) > 300:
                self.logs.pop(0)

    def get_logs(self, limit: int = 100) -> List[str]:
        with self._log_lock:
            return self.logs[-limit:]

    def is_healthy(self) -> bool:
        if self.status_state != "running":
            return False
        return self._check_backend_health() and self._check_frontend_health()

    def _check_backend_health(self) -> bool:
        url = f"http://127.0.0.1:{self.backend_port}/health"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _check_frontend_health(self) -> bool:
        url = f"http://127.0.0.1:{self.frontend_port}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status in (200, 304, 404)
        except Exception:
            return False

    def start_application(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        if project_path:
            self.project_path = os.path.abspath(project_path)
        elif not self.project_path:
            # Default to backend/integrated_project/TodoApp
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.project_path = os.path.join(backend_dir, "integrated_project", "TodoApp")

        # If already running and healthy, return status
        if self.status_state == "running" and self.is_healthy():
            self.log("Application is already running and healthy.")
            return self.get_runtime_status()

        # Stop existing processes if any
        self.stop_application()

        self.status_state = "starting"
        self.status_message = "Initializing integrated application launch..."
        self.error_detail = None
        self.logs.clear()
        self._start_time = datetime.now().isoformat()

        # Start launch sequence in a background thread to prevent blocking HTTP handler
        thread = threading.Thread(target=self._launch_sequence, daemon=True)
        thread.start()

        return self.get_runtime_status()

    def _launch_sequence(self):
        try:
            self.log(f"Starting Integrated Application from: {self.project_path}")
            if not os.path.exists(self.project_path):
                raise FileNotFoundError(f"Integrated project path '{self.project_path}' does not exist.")

            # Step 1: Allocate free ports
            self.backend_port = find_free_port(start_port=8010)
            self.frontend_port = find_free_port(start_port=5175)
            self.log(f"Allocated ports -> Frontend: {self.frontend_port}, Backend API: {self.backend_port}")

            # Step 2: Ensure node_modules / install dependencies if missing
            node_modules = os.path.join(self.project_path, "node_modules")
            if not os.path.exists(node_modules):
                self.log("Installing frontend npm dependencies (this may take a few seconds)...")
                npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
                res = subprocess.run(
                    [npm_cmd, "install"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if res.returncode != 0:
                    self.log(f"npm install warning: {res.stderr[:200]}")
                else:
                    self.log("npm dependencies verified successfully.")

            # Step 3: Launch FastAPI Backend Process
            self.log(f"Launching FastAPI backend on port {self.backend_port}...")
            backend_dir = os.path.join(self.project_path, "backend")
            env = os.environ.copy()
            env["PORT"] = str(self.backend_port)
            env["PYTHONPATH"] = backend_dir + os.pathsep + self.project_path + os.pathsep + env.get("PYTHONPATH", "")

            python_bin = sys.executable
            main_py = os.path.join(backend_dir, "main.py")

            self.backend_process = subprocess.Popen(
                [python_bin, main_py],
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            threading.Thread(target=self._read_output, args=(self.backend_process, "Backend"), daemon=True).start()

            # Wait for backend health check
            backend_ready = False
            for _ in range(25):
                time.sleep(0.5)
                if self._check_backend_health():
                    backend_ready = True
                    break
            
            if not backend_ready:
                self.log("Backend health check timed out, continuing startup...")

            self.log("Backend service operational.")

            # Step 4: Launch Vite Frontend Process
            self.log(f"Launching Vite React frontend on port {self.frontend_port}...")
            npm_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
            env["PORT"] = str(self.frontend_port)
            env["VITE_BACKEND_URL"] = f"http://localhost:{self.backend_port}"

            self.frontend_process = subprocess.Popen(
                [npm_cmd, "vite", "--port", str(self.frontend_port), "--host", "0.0.0.0"],
                cwd=self.project_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            threading.Thread(target=self._read_output, args=(self.frontend_process, "Frontend"), daemon=True).start()

            # Wait for frontend health check
            frontend_ready = False
            for _ in range(25):
                time.sleep(0.5)
                if self._check_frontend_health():
                    frontend_ready = True
                    break

            self.log("Frontend service operational.")

            # Step 5: Save runtime.json info
            runtime_data = {
                "status": "running",
                "frontend_url": f"http://localhost:{self.frontend_port}",
                "backend_url": f"http://localhost:{self.backend_port}",
                "frontend_port": self.frontend_port,
                "backend_port": self.backend_port,
                "backend_pid": self.backend_process.pid if self.backend_process else None,
                "frontend_pid": self.frontend_process.pid if self.frontend_process else None,
                "started_at": self._start_time
            }
            save_runtime_info(self.project_path, runtime_data)

            self.status_state = "running"
            self.status_message = "Integrated Application is ready and running."
            self.log("[SUCCESS] Application successfully launched and running!")

        except Exception as e:
            logger.exception("Failed to launch integrated application")
            self.status_state = "failed"
            self.status_message = "Startup failed"
            self.error_detail = str(e)
            self.log(f"❌ Error during launch: {e}")
            self.stop_application()

    def _read_output(self, process: subprocess.Popen, prefix: str):
        if not process.stdout:
            return
        for line in iter(process.stdout.readline, ''):
            if line:
                line_str = line.strip()
                if line_str:
                    self.log(f"[{prefix}] {line_str}")
        process.stdout.close()

    def stop_application(self) -> Dict[str, Any]:
        self.log("Stopping integrated application server processes...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=3)
            except Exception:
                try:
                    self.backend_process.kill()
                except Exception:
                    pass
            self.backend_process = None

        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=3)
            except Exception:
                try:
                    self.frontend_process.kill()
                except Exception:
                    pass
            self.frontend_process = None

        self.status_state = "stopped"
        self.status_message = "Application stopped."
        self.log("Application processes terminated cleanly.")
        return self.get_runtime_status()

    def get_runtime_status(self) -> Dict[str, Any]:
        frontend_url = f"http://localhost:{self.frontend_port}" if self.status_state == "running" else None
        backend_url = f"http://localhost:{self.backend_port}" if self.status_state == "running" else None

        return {
            "status": self.status_state,
            "message": self.status_message,
            "error_detail": self.error_detail,
            "frontend_url": frontend_url or f"http://localhost:{self.frontend_port}",
            "backend_url": backend_url or f"http://localhost:{self.backend_port}",
            "frontend_port": self.frontend_port,
            "backend_port": self.backend_port,
            "is_healthy": self.is_healthy() if self.status_state == "running" else False,
            "started_at": self._start_time,
            "logs_count": len(self.logs)
        }
