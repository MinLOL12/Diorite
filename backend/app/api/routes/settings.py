from fastapi import APIRouter
from ...services.settings_service import SettingsService
from ...models.schemas import Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])
service = SettingsService()

@router.get("")
def get_settings():
    s = service.get_settings()
    return s.model_dump()

@router.put("")
def update_settings(settings: Settings):
    saved = service.save_settings(settings)
    return saved.model_dump()

@router.patch("")
def patch_settings(updates: dict):
    saved = service.update_settings(updates)
    return saved.model_dump()
