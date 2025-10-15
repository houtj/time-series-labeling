"""User Routes"""
from fastapi import APIRouter
from bson.objectid import ObjectId
from bson.json_util import dumps
from datetime import datetime, timezone

from database import get_db
from models import (
    UpdateUserSharedFolderRequest,
    UpdateUserShareProjectRequest,
    UpdateUserRecentFilesRequest
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/info")
async def get_user_info():
    """Get or create default user"""
    db = get_db()
    userInfo = db['users'].find_one({'mail': 'default@default.com'})
    
    if userInfo is None:
        userInfo = {
            'name': 'default',
            'mail': 'default@default.com',
            'activeSince': datetime.now(tz=timezone.utc),
            'projectList': [],
            'folderList': [],
            'assistantList': [],
            'contributionHistory': [],
            'recent': [],
            'message': [],
            'badge': 'Iron',
            'rank': 100
        }
        result = db['users'].insert_one(userInfo)
        userInfo['_id'] = result.inserted_id
    
    return dumps(userInfo)


@router.get("")
async def get_users():
    """Get all users"""
    db = get_db()
    usersList = dumps(list(db['users'].find({})))
    return usersList


@router.put("/shared-folders")
async def share_folder_with_user(request: UpdateUserSharedFolderRequest):
    """Share folder with user"""
    db = get_db()
    folder = request.folder
    user = request.user
    userName = request.userName
    message = request.message
    
    user_folder = user['folderList']
    if folder['_id']['$oid'] not in user_folder:
        db['users'].update_one(
            {'_id': ObjectId(user['_id']['$oid'])}, 
            {'$push': {
                'folderList': folder['_id']['$oid'], 
                'message': {
                    'folder': folder['_id']['$oid'],
                    'displayText': f'From {userName}: Folder {folder["name"]} is shared to you. {message}'
                }
            }}
        )
    
    project_id = folder['project']['id']
    if project_id not in user['projectList']:
        db['users'].update_one(
            {'_id': ObjectId(user['_id']['$oid'])}, 
            {'$push': {'projectList': project_id}}
        )
    
    return 'done'


@router.put("/shared-files")
async def share_files_with_user(request: UpdateUserSharedFolderRequest):
    """Share files with user (same as folder sharing)"""
    db = get_db()
    folder = request.folder
    user = request.user
    userName = request.userName
    message = request.message
    
    user_folder = user['folderList']
    if folder['_id']['$oid'] not in user_folder:
        db['users'].update_one(
            {'_id': ObjectId(user['_id']['$oid'])}, 
            {'$push': {
                'folderList': folder['_id']['$oid'], 
                'message': {
                    'folder': folder['_id']['$oid'],
                    'displayText': f'From {userName}: Folder {folder["name"]} is shared to you. {message}'
                }
            }}
        )
    
    project_id = folder['project']['id']
    if project_id not in user['projectList']:
        db['users'].update_one(
            {'_id': ObjectId(user['_id']['$oid'])}, 
            {'$push': {'projectList': project_id}}
        )
    
    return 'done'


@router.put("/shared-projects")
async def share_project_with_user(request: UpdateUserShareProjectRequest):
    """Share project with user"""
    db = get_db()
    project = request.project
    user = request.user
    userName = request.userName
    message = request.message
    
    user_project = user['projectList']
    if project['_id']['$oid'] not in user_project:
        db['users'].update_one(
            {'_id': ObjectId(user['_id']['$oid'])}, 
            {'$push': {
                'projectList': project['_id']['$oid'], 
                'message': {
                    'project': project['_id']['$oid'],
                    'displayText': f'From {userName}: Project {project["projectName"]} is shared to you. {message}'
                }
            }}
        )
    
    return 'done'


@router.put("/recent-files")
async def update_recent_files(request: UpdateUserRecentFilesRequest):
    """Update user's recent files"""
    db = get_db()
    result = db['users'].find_one({'_id': ObjectId(request.userInfo['_id']['$oid'])})
    recent_files = result['recent']
    
    # Check if already exists
    if request.folderId in [r['folder'] for r in recent_files] and request.fileId in [r['file'] for r in recent_files]:
        return 'done'
    
    # Add and keep last 5
    recent_files.append({
        'folder': request.folderId, 
        'file': request.fileId, 
        'displayText': request.folderName + ' - ' + request.fileName
    })
    recent_files = recent_files[-5:]
    
    db['users'].update_one(
        {'_id': ObjectId(request.userInfo['_id']['$oid'])}, 
        {'$set': {'recent': recent_files}}
    )
    
    return 'done'

