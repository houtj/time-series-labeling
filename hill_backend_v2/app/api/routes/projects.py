"""Project-related API routes"""

import json
import logging

from bson.json_util import dumps
from fastapi import APIRouter

from app.api.dependencies import ProjectServiceDep
from app.models.schemas import (
    ProjectCreate,
    ProjectDescriptionsUpdate,
    ClassCreate,
    ClassUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("")
async def create_project(request: ProjectCreate, service: ProjectServiceDep):
    """Create a new project"""
    project = service.create_project(request.projectName, request.userId)
    return dumps(project)


@router.get("")
async def get_projects(projects: str, service: ProjectServiceDep):
    """Get multiple projects by IDs"""
    project_ids = json.loads(projects)
    projects = service.get_projects(project_ids)
    return dumps(projects)


@router.post("/classes")
async def add_class(request: ClassCreate, service: ProjectServiceDep):
    """Add a new class to a project"""
    class_data = {
        "name": request.newClassName,
        "color": request.newClassColor,
        "description": request.description,
    }
    service.add_class(request.projectId, class_data)
    return "done"


@router.put("/classes")
async def update_class(request: ClassUpdate, service: ProjectServiceDep):
    """Update a class in a project"""
    new_class_data = {
        "name": request.newClassName,
        "color": request.newClassColor,
        "description": request.description,
    }
    service.update_class(request.projectId, request.updatingClassName, new_class_data)
    return "done"


@router.put("/descriptions")
async def update_descriptions(request: ProjectDescriptionsUpdate, service: ProjectServiceDep):
    """Update project and class descriptions"""
    service.update_descriptions(
        request.projectId, request.generalDescription, request.classDescriptions
    )
    return "done"

