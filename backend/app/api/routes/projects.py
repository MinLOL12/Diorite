from fastapi import APIRouter, HTTPException
from ...services.project_service import ProjectService
from ...models.schemas import ProjectCreateRequest

router = APIRouter(prefix="/api/projects", tags=["projects"])
service = ProjectService()

@router.get("")
def list_projects():
    projects = service.list_projects()
    return [p.model_dump(mode='json') for p in projects]

@router.post("")
def create_project(req: ProjectCreateRequest):
    try:
        proj = service.create_project(
            name=req.name,
            loader=req.loader.value,
            mc_version=req.mc_version,
            mod_id=req.mod_id,
            package=req.package,
            template_id=req.template_id
        )
        return proj.model_dump(mode='json')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
def get_project(project_id: str):
    proj = service.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return proj.model_dump(mode='json')

@router.delete("/{project_id}")
def delete_project(project_id: str):
    try:
        service.delete_project(project_id)
        return {"deleted": project_id}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/stats")
def get_stats(project_id: str):
    try:
        stats = service.get_project_stats(project_id)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
