from fastapi import APIRouter, HTTPException, Query
from ...services.file_service import FileService
from ...models.schemas import FileSaveRequest, FileCreateRequest, FileRenameRequest

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])
service = FileService()

@router.get("/tree")
def get_tree(project_id: str):
    try:
        tree = service.get_tree(project_id)
        return tree.model_dump(mode='json')
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def list_files(project_id: str, path: str = Query(default="")):
    try:
        return service.list_files(project_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/content")
def read_file(project_id: str, path: str = Query(...)):
    try:
        data = service.read_file(project_id, path)
        service.touch_recent(project_id, path)
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
def save_file(project_id: str, req: FileSaveRequest):
    try:
        result = service.write_file(project_id, req.path, req.content)
        service.touch_recent(project_id, req.path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
def create_file(project_id: str, req: FileCreateRequest):
    try:
        result = service.create_file_or_dir(project_id, req.path, req.is_directory, req.content or "")
        return result
    except FileExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename")
def rename(project_id: str, req: FileRenameRequest):
    try:
        return service.rename(project_id, req.old_path, req.new_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("")
def delete_file(project_id: str, path: str = Query(...)):
    try:
        return service.delete(project_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/recent")
def get_recent(project_id: str):
    try:
        return {"recent": service.get_recent(project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
