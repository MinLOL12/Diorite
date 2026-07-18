from fastapi import APIRouter, HTTPException
from ...services.build_service import BuildService
from ...models.schemas import BuildRequest, RunRequest

router = APIRouter(prefix="/api/projects/{project_id}", tags=["builds"])
build_service = BuildService()

@router.post("/build")
async def build_project(project_id: str, req: BuildRequest = None):
    tasks = req.tasks if req and req.tasks else ["build"]
    try:
        result = await build_service.build_project(project_id, tasks)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def run_project(project_id: str, req: RunRequest = None):
    tasks = req.tasks if req and req.tasks else ["runClient"]
    stop_existing = req.stop_existing if req else True
    try:
        result = await build_service.run_project(project_id, tasks, stop_existing)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/build/status")
async def build_status(project_id: str):
    try:
        status = await build_service.get_build_status(project_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
