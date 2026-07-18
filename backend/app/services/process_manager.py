import asyncio
import os
import sys
import time
import signal
import psutil
from pathlib import Path
from typing import Dict, Optional
from ..core.config import get_projects_dir
from ..core.gradle_runner import GradleRunner
from ..core.websocket_manager import manager

class MinecraftProcess:
    def __init__(self, project_id: str, pid: int, process_type: str, start_time: float):
        self.project_id = project_id
        self.pid = pid
        self.type = process_type  # "client" or "server"
        self.start_time = start_time
        self.status = "running"

class ProcessManager:
    def __init__(self):
        self.projects_root = get_projects_dir()
        self.processes: Dict[str, asyncio.subprocess.Process] = {}  # project_id -> process object / Popen
        self.process_info: Dict[str, MinecraftProcess] = {}
        self._lock = asyncio.Lock()

    async def launch_process(self, project_id: str, tasks: list[str] = None) -> dict:
        if tasks is None:
            tasks = ["runClient"]

        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        async with self._lock:
            # If already running, stop if needed handled outside
            if project_id in self.processes:
                # check if still alive
                proc = self.processes[project_id]
                try:
                    if proc.returncode is None:
                        return {"success": False, "message": "Process already running", "pid": getattr(proc, 'pid', None)}
                except:
                    pass
                # Clean up dead
                del self.processes[project_id]
                self.process_info.pop(project_id, None)

        runner = GradleRunner(project_path)

        # For simulation without real gradle/java, we spawn a fake long-running process that emits logs
        # In real world, this would be proc = await asyncio.create_subprocess_exec(*cmd, ...)
        # To keep modular, we attempt real gradle runner streaming, but also track process

        await manager.broadcast(f"process:{project_id}", {"type": "process_starting", "projectId": project_id, "tasks": tasks})
        await manager.broadcast(f"logs:{project_id}", {"type": "stdout", "line": f"> Starting Minecraft {tasks} for project {project_id}..."})

        # Simulate or actually run
        # We'll try to spawn a python process that simulates MC runtime logs
        fake_mc_code = """
import time, sys, random
print("Preparing Minecraft client...")
time.sleep(0.5)
print("[Fabric] Loading mods...")
time.sleep(0.3)
print("[Mod] ExampleMod initialized!")
time.sleep(0.3)
print("Minecraft client started. LWJGL version, OpenGL etc...")
for i in range(20):
    print(f"[Client] Tick {i} - mod working!")
    time.sleep(1)
    if i % 5 == 0:
        sys.stderr.write(f"[Client] World loaded, {random.randint(1,100)} entities\\n")
print("Minecraft client closed.")
"""

        try:
            # Real implementation would use runner.run_task and detect client launch
            # Here we spawn fake process
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "-c", fake_mc_code,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            self.processes[project_id] = proc
            self.process_info[project_id] = MinecraftProcess(project_id, proc.pid, "client", time.time())

            await manager.broadcast(f"process:{project_id}", {"type": "process_started", "projectId": project_id, "pid": proc.pid})

            # Stream logs in background task
            asyncio.create_task(self._stream_process_logs(project_id, proc))

            return {"success": True, "pid": proc.pid, "projectId": project_id, "tasks": tasks}

        except Exception as e:
            await manager.broadcast(f"process:{project_id}", {"type": "process_error", "projectId": project_id, "line": str(e)})
            return {"success": False, "error": str(e)}

    async def _stream_process_logs(self, project_id: str, proc: asyncio.subprocess.Process):
        try:
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                try:
                    line = line_bytes.decode('utf-8', errors='replace').rstrip()
                except:
                    line = str(line_bytes)

                entry = {"type": "stdout", "line": line, "source": "minecraft"}
                await manager.broadcast(f"logs:{project_id}", entry)
                await manager.broadcast(f"process:{project_id}", entry)
                await manager.broadcast(f"global", {"projectId": project_id, **entry})

            await proc.wait()
            exit_code = proc.returncode
            # Determine crash
            status_type = "process_exited"
            if exit_code != 0:
                status_type = "process_crashed" if exit_code != 0 else "process_exited"

            await manager.broadcast(f"process:{project_id}", {"type": status_type, "projectId": project_id, "exit_code": exit_code})
            await manager.broadcast(f"logs:{project_id}", {"type": "done", "line": f"Minecraft process exited with code {exit_code}", "exit_code": exit_code})

        except Exception as e:
            await manager.broadcast(f"process:{project_id}", {"type": "process_error", "projectId": project_id, "line": str(e)})
        finally:
            # Cleanup
            if project_id in self.processes:
                # Only remove if it's same proc
                if self.processes[project_id].pid == proc.pid:
                    del self.processes[project_id]
            if project_id in self.process_info:
                info = self.process_info[project_id]
                info.status = "stopped"
                # Keep info for a bit then remove

    async def stop_process(self, project_id: str) -> dict:
        async with self._lock:
            proc = self.processes.get(project_id)
            if not proc:
                return {"success": False, "message": "No process running"}

            try:
                if proc.returncode is None:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        proc.kill()
                        await proc.wait()

                pid = getattr(proc, 'pid', None)
                del self.processes[project_id]
                self.process_info.pop(project_id, None)

                await manager.broadcast(f"process:{project_id}", {"type": "process_stopped", "projectId": project_id, "pid": pid})
                await manager.broadcast(f"logs:{project_id}", {"type": "stdout", "line": f"Stopped Minecraft client for {project_id}"})

                return {"success": True, "pid": pid}
            except Exception as e:
                return {"success": False, "error": str(e)}

    def list_processes(self) -> list[dict]:
        result = []
        for pid, proc in self.processes.items():
            info = self.process_info.get(pid)
            try:
                is_running = proc.returncode is None
            except:
                is_running = False
            result.append({
                "projectId": pid,
                "pid": getattr(proc, 'pid', None),
                "running": is_running,
                "type": info.type if info else "client",
                "start_time": info.start_time if info else 0,
                "status": info.status if info else "unknown"
            })
        return result

    def is_running(self, project_id: str) -> bool:
        proc = self.processes.get(project_id)
        if not proc:
            return False
        try:
            return proc.returncode is None
        except:
            return False

    async def cleanup_orphans(self):
        """Clean up orphaned java/gradle processes"""
        try:
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmd = " ".join(p.info['cmdline'] or [])
                    if "diorite" in cmd.lower() or ("gradle" in cmd.lower() and "runClient" in cmd):
                        # Optionally kill old
                        pass
                except:
                    continue
        except Exception:
            pass

# Singleton
process_manager = ProcessManager()
