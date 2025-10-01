"""File-related API routes"""

import json
import logging
from typing import Annotated

import simplejson
from bson.json_util import dumps
from fastapi import APIRouter, Form, UploadFile

from app.api.dependencies import FileServiceDep, LabelServiceDep
from app.models.schemas import FileDescriptionUpdate, ReparseFilesRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["files"])


@router.post("/files")
async def upload_files(
    data: Annotated[str, Form()],
    user: Annotated[str, Form()],
    files: list[UploadFile],
    service: FileServiceDep,
):
    """Upload files to a folder"""
    folder_id = data
    user_name = user
    await service.upload_files(folder_id, files, user_name)
    return "done"


@router.get("/files")
async def get_files(filesId: str, service: FileServiceDep):
    """Get multiple files by IDs"""
    file_ids = json.loads(filesId)
    files = service.get_files(file_ids)
    return dumps(files)


@router.get("/files/{file_id}")
async def get_file(file_id: str, service: FileServiceDep):
    """Get file by ID with data"""
    result = service.get_file(file_id)
    # Return as JSON with file info and data separately
    response = {"fileInfo": dumps(result["fileInfo"]), "data": simplejson.dumps(result["data"])}
    return simplejson.dumps(response)


@router.delete("/files")
async def delete_file(file: str, service: FileServiceDep):
    """Delete a file"""
    file_data = json.loads(file)
    file_id = file_data["_id"]["$oid"]
    service.delete_file(file_id)
    return "done"


@router.put("/descriptions")
async def update_description(request: FileDescriptionUpdate, service: FileServiceDep):
    """Update file description"""
    service.update_description(request.file_id, request.description)
    return "done"


@router.put("/reparsingFiles")
async def reparse_files(request: ReparseFilesRequest, service: FileServiceDep):
    """Mark files for reparsing"""
    service.reparse_files(request.folderId)
    return "done"


@router.get("/files_data/{folder_id}")
async def get_files_data(folder_id: str, service: FileServiceDep):
    """Get all file data for a folder"""
    data = service.get_files_data(folder_id)
    return dumps(data)


@router.get("/files_event/{folder_id}")
async def get_files_events(folder_id: str, service: FileServiceDep):
    """Get all events for files in a folder"""
    events = service.get_files_events(folder_id)
    return dumps(events)


@router.post("/event")
async def add_event(
    data: Annotated[str, Form()],
    user: Annotated[str, Form()],
    file: UploadFile,
    service: LabelServiceDep,
):
    """Add an event to a label"""
    label_id = data
    user_name = user

    event_info = await file.read()
    event_info = json.loads(event_info)

    service.add_events_to_label(label_id, event_info, user_name)
    return "done"


@router.post("/events")
async def add_events(
    data: Annotated[str, Form()],
    user: Annotated[str, Form()],
    file: UploadFile,
    service: LabelServiceDep,
):
    """Add events to multiple files in a folder"""
    folder_id = data
    user_name = user

    event_info_list = await file.read()
    event_info_list = json.loads(event_info_list)

    service.add_events_batch(folder_id, event_info_list, user_name)
    return "done"

