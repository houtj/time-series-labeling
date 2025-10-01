"""User-related API routes"""

import logging

from bson.json_util import dumps
from fastapi import APIRouter

from app.api.dependencies import UserServiceDep
from app.models.schemas import (
    UserRecentFilesUpdate,
    UserSharedFolderUpdate,
    UserSharedProjectUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["users"])


@router.get("/userInfo")
async def get_user_info(service: UserServiceDep):
    """Get or create default user info"""
    user_info = service.get_or_create_default_user()
    return dumps(user_info)


@router.get("/users")
async def get_users(service: UserServiceDep):
    """Get all users"""
    users = service.get_all_users()
    return dumps(users)


@router.put("/userRecentFiles")
async def update_recent_files(request: UserRecentFilesUpdate, service: UserServiceDep):
    """Update user's recent files"""
    user_id = request.userInfo["_id"]["$oid"]
    service.update_recent_files(
        user_id, request.folderId, request.fileId, request.folderName, request.fileName
    )
    return "done"


@router.put("/usersSharedFolders")
async def share_folder(request: UserSharedFolderUpdate, service: UserServiceDep):
    """Share a folder with a user"""
    user_id = request.user["_id"]["$oid"]
    service.share_folder_with_user(user_id, request.folder, request.userName, request.message)
    return "done"


@router.put("/usersSharedFiles")
async def share_files(request: UserSharedFolderUpdate, service: UserServiceDep):
    """Share files with a user (same as sharing folder)"""
    user_id = request.user["_id"]["$oid"]
    service.share_folder_with_user(user_id, request.folder, request.userName, request.message)
    return "done"


@router.put("/usersSharedProjects")
async def share_project(request: UserSharedProjectUpdate, service: UserServiceDep):
    """Share a project with a user"""
    user_id = request.user["_id"]["$oid"]
    service.share_project_with_user(user_id, request.project, request.userName, request.message)
    return "done"

