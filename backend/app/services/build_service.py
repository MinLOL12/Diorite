import asyncio
from pathlib import Path
from typing import Dict, Optional, List
from ..core.gradle_runner import GradleRunner
from ..core.config import get_projects_dir
from .cache_service import CacheService
from ..core.websocket_manager import manager

class BuildService:
    def __init__(self):
        self.projects_root = get_projects_dir()
        self.cache_service = CacheService()
        # Track active builds per project to prevent parallel builds
        self.active_builds: Dict[str, bool] = {}

    async def build_project(self, project_id: str, tasks: List[str] = None) -> dict:
        if tasks is None:
            tasks = ["build"]

        if self.active_builds.get(project_id):
            return {"success": False, "message": "Build already in progress"}

        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        self.active_builds[project_id] = True

        runner = GradleRunner(project_path)
        logs = []
        success = False
        exit_code = -1

        # Notify start via websocket
        await manager.broadcast(f"build:{project_id}", {"type": "build_start", "tasks": tasks, "projectId": project_id})

        try:
            async for entry in runner.run_task(tasks):
                logs.append(entry)
                # Stream to websocket
                await manager.broadcast(f"build:{project_id}", entry)
                await manager.broadcast(f"logs:{project_id}", entry)
                # Also global logs
                await manager.broadcast(f"global", {"projectId": project_id, **entry})

                if entry.get("type") == "done":
                    success = entry.get("success", False)
                    exit_code = entry.get("exit_code", 0)

        except Exception as e:
            await manager.broadcast(f"build:{project_id}", {"type": "error", "line": str(e), "is_error": True})
            success = False
        finally:
            self.active_builds[project_id] = False
            await manager.broadcast(f"build:{project_id}", {"type": "build_end", "success": success, "exit_code": exit_code})

        # Save last build log
        try:
            log_dir = project_path / ".diorite"
            log_dir.mkdir(exist_ok=True)
            (log_dir / "last_build.log").write_text("\n".join([l.get("line", "") or l.get("clean", "") for l in logs if "line" in l or "clean" in l]))
        except:
            pass

        return {"success": success, "exit_code": exit_code, "tasks": tasks, "logs": logs[-100:]}

    async def run_project(self, project_id: str, tasks: List[str] = None, stop_existing: bool = True) -> dict:
        if tasks is None:
            tasks = ["runClient"]

        # For runClient, we want to delegate to process manager after build check
        # But if tasks include runClient, we treat it as build+run combined
        # First build if needed (quick check)
        # Actually for Minecraft mods, runClient itself builds

        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        # Optionally stop existing
        if stop_existing:
            from .process_manager import process_manager
            await process_manager.stop_process(project_id)

        # Then run build+launch stream
        # For now, we just run the gradle tasks (which includes launching MC)
        # In process_manager, runClient will launch subprocess and track

        from .process_manager import process_manager
        result = await process_manager.launch_process(project_id, tasks)

        return result

    def is_building(self, project_id: str) -> bool:
        return self.active_builds.get(project_id, False)

    async def get_build_status(self, project_id: str) -> dict:
        return {
            "projectId": project_id,
            "building": self.is_building(project_id),
        }
