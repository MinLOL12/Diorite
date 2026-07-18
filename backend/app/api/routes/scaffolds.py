from fastapi import APIRouter, HTTPException
from ...services.scaffold_service import ScaffoldService
from ...models.schemas import (
    ScaffoldBlockRequest, ScaffoldItemRequest, ScaffoldEntityRequest,
    ScaffoldScreenRequest, ScaffoldRecipeRequest, ScaffoldComponentRequest
)

router = APIRouter(prefix="/api/projects/{project_id}/scaffold", tags=["scaffold"])
service = ScaffoldService()

@router.post("/block")
def scaffold_block(project_id: str, req: ScaffoldBlockRequest):
    try:
        return service.create_block(project_id, req.name, req.material, req.creative_tab)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/item")
def scaffold_item(project_id: str, req: ScaffoldItemRequest):
    try:
        return service.create_item(project_id, req.name, req.stack_size, req.creative_tab)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entity")
def scaffold_entity(project_id: str, req: ScaffoldEntityRequest):
    try:
        return service.create_entity(project_id, req.name, req.category, req.width, req.height)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screen")
def scaffold_screen(project_id: str, req: ScaffoldScreenRequest):
    try:
        return service.create_screen(project_id, req.name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recipe")
def scaffold_recipe(project_id: str, req: ScaffoldRecipeRequest):
    try:
        return service.create_recipe(project_id, req.name, req.type)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/component")
def scaffold_component(project_id: str, req: ScaffoldComponentRequest):
    try:
        return service.create_data_component(project_id, req.name, req.type)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
