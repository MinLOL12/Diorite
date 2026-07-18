from fastapi import APIRouter, HTTPException
from ...services.process_manager import process_manager

router = APIRouter(prefix="/api", tags=["processes"])

@router.get("/processes")
def list_processes():
    return process_manager.list_processes()

@router.get("/projects/{project_id}/process/status")
def get_process_status(project_id: str):
    running = process_manager.is_running(project_id)
    procs = [p for p in process_manager.list_processes() if p["projectId"] == project_id]
    return {"projectId": project_id, "running": running, "processes": procs}

@router.post("/projects/{project_id}/process/stop")
async def stop_process(project_id: str):
    result = await process_manager.stop_process(project_id)
    if not result.get("success"):
        if "No process running" in result.get("message", ""):
            raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@router.post("/projects/{project_id}/process/restart")
async def restart_process(project_id: str):
    await process_manager.stop_process(project_id)
    result = await process_manager.launch_process(project_id, ["runClient"])
    return result
