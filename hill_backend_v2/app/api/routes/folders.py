"""Folder-related API routes"""

import json
import logging

from bson.json_util import dumps
from fastapi import APIRouter

from app.api.dependencies import FolderServiceDep
from app.models.schemas import FolderCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("")
async def create_folder(request: FolderCreate, service: FolderServiceDep):
    """Create a new folder"""
    result = service.create_folder(
        request.newFolderName,
        {"id": request.project.id, "name": request.project.name},
        {"id": request.template.id, "name": request.template.name},
        request.userId,
    )
    return "done"


@router.get("")
async def get_folders(folders: str, service: FolderServiceDep):
    """Get multiple folders by IDs"""
    folder_ids = json.loads(folders)
    folders = service.get_folders(folder_ids)
    return dumps(folders)


@router.get("/{folder_id}")
async def get_folder(folder_id: str, service: FolderServiceDep):
    """Get folder by ID"""
    folder = service.get_folder(folder_id)
    return dumps(folder)


@router.delete("")
async def delete_folder(folder: str, service: FolderServiceDep):
    """Delete a folder"""
    folder_data = json.loads(folder)
    folder_id = folder_data["_id"]["$oid"]
    service.delete_folder(folder_id)
    return "done"

