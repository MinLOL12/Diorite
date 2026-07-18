from fastapi import APIRouter, HTTPException
from ...services.template_service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["templates"])
service = TemplateService()

@router.get("")
def list_templates():
    return service.list_templates()

@router.get("/{template_id}")
def get_template(template_id: str):
    tmpl = service.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return tmpl
