"""Folder Routes"""
from fastapi import APIRouter
from bson.objectid import ObjectId
from bson.json_util import dumps
import simplejson as json
from pathlib import Path
import shutil

from database import get_db, get_data_folder_path
from models import NewFolderRequest

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("")
async def create_folder(folder: NewFolderRequest):
    """Create new folder"""
    db = get_db()
    
    # Add new folder
    newFolder = {
        'name': folder.newFolderName,
        'project': {
            'id': folder.project['id'],
            'name': folder.project['name'],
        },
        'template': {
            'id': folder.template['id'],
            'name': folder.template['name']
        },
        'fileList': [],
        'nbLabeledFiles': 0,
        'nbTotalFiles': 0,
    }
    result = db['folders'].insert_one(newFolder)
    newFolderId = result.inserted_id
    
    # Update user
    db['users'].update_one(
        {'_id': ObjectId(folder.userId)}, 
        {'$push': {'folderList': str(newFolderId)}}
    )
    
    return 'done'


@router.get("")
async def get_folders(folders: str):
    """Get multiple folders"""
    db = get_db()
    folders = json.loads(folders)
    result = db['folders'].find({'_id': {'$in': [ObjectId(f) for f in folders]}})
    return dumps(result)


@router.get("/{folder_id}")
async def get_folder(folder_id: str):
    """Get single folder"""
    db = get_db()
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    return dumps(result)


@router.delete("")
async def delete_folder(folder: str):
    """Delete folder and all files"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    folder = json.loads(folder)
    files_id = folder['fileList']
    folder_id = folder['_id']['$oid']
    
    # Delete labels
    files = db['files'].find({'_id': {'$in': [ObjectId(f) for f in files_id]}})
    labels = [file.get('label') for file in files if file.get('label')]
    if labels:
        db['labels'].delete_many({'_id': {'$in': [ObjectId(l) for l in labels]}})
    
    # Delete files
    db['files'].delete_many({'_id': {'$in': [ObjectId(f) for f in files_id]}})
    
    # Remove folder from users
    db['users'].update_many(
        {'folderList': folder_id}, 
        {'$pull': {'folderList': folder_id}}
    )
    
    # Delete folder document
    db['folders'].delete_one({'_id': ObjectId(folder_id)})
    
    # Delete folder directory
    folder_path = Path(data_folder_path) / folder_id
    if folder_path.exists():
        shutil.rmtree(folder_path, ignore_errors=True)
    
    return 'done'

