"""Template-related API routes"""

import logging
from typing import Annotated

from bson.json_util import dumps
from fastapi import APIRouter, Form, UploadFile

from app.api.dependencies import TemplateServiceDep, ExtractionServiceDep
from app.models.schemas import TemplateCreate, TemplateUpdate, TemplateClone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("")
async def create_template(request: TemplateCreate, service: TemplateServiceDep):
    """Create a new template"""
    template_id = service.create_template(
        request.templateName, request.projectId, request.fileType
    )
    return template_id


@router.get("/{template_id}")
async def get_template(template_id: str, service: TemplateServiceDep):
    """Get template by ID"""
    template = service.get_template(template_id)
    return dumps(template)


@router.put("")
async def update_template(request: TemplateUpdate, service: TemplateServiceDep):
    """Update a template"""
    template_data = request.request.copy()
    # Extract template ID from the nested structure
    if "_id" in template_data and "$oid" in template_data["_id"]:
        template_id = template_data["_id"]["$oid"]
        del template_data["_id"]
    else:
        # Fallback if structure is different
        template_id = str(template_data.get("_id", ""))
        if "_id" in template_data:
            del template_data["_id"]

    service.update_template(template_id, request.projectId, template_data)
    return "done"


@router.put("/clone")
async def clone_template(request: TemplateClone, service: TemplateServiceDep):
    """Clone an existing template"""
    new_template_id = service.clone_template(
        request.templateId, request.newTemplateName, request.projectId
    )
    return new_template_id


@router.post("/extract-columns")
async def extract_columns(
    file: UploadFile, templateId: Annotated[str, Form()], service: ExtractionServiceDep
):
    """Extract column information from an uploaded file"""
    result = await service.extract_columns(file, templateId)
    return result

