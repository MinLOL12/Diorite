from fastapi import APIRouter, HTTPException
from ...services.cache_service import CacheService

router = APIRouter(prefix="/api/cache", tags=["cache"])
service = CacheService()

@router.get("/status")
def cache_status():
    try:
        return service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
def clear_cache(category: str = None, version: str = None):
    try:
        if not category:
            service.clear_all()
            return {"cleared": "all"}
        else:
            service.clear_category(category, version)
            return {"cleared": category, "version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ensure")
def ensure_cache(category: str, version: str):
    try:
        result = service.ensure_cached(category, version)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
