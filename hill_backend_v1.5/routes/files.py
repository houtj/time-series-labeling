"""File Routes"""
from fastapi import APIRouter, UploadFile, Form
from typing import Annotated
from bson.objectid import ObjectId
from bson.json_util import dumps
from datetime import datetime, timezone
from pathlib import Path
import simplejson as json
import shutil

from database import get_db, get_data_folder_path
from models import UpdateDescriptionRequest, ReparsingFilesRequest, DownloadJsonFilesRequest
from config import settings

router = APIRouter(prefix="/files", tags=["files"])


@router.post("")
async def upload_files(data: Annotated[str, Form()], user: Annotated[str, Form()], files: list[UploadFile]):
    """Upload files to folder"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    folderId = data
    userName = user
    
    for file in files:
        # Add new label
        labelInfo = {
            'events': [],
            'guidelines': [],
        }
        result = db['labels'].insert_one(labelInfo)
        newLabelId = result.inserted_id
        
        # Add new file
        fileInfo = {
            'name': file.filename,
            'parsing': 'uploading',
            'nbEvent': 'unlabeled',
            'description': '',
            'rawPath': '',
            'jsonPath': '',
            'lastModifier': userName,
            'lastUpdate': datetime.now(tz=timezone.utc),
            'label': str(newLabelId),
        }
        result = db['files'].insert_one(fileInfo)
        newFileId = result.inserted_id
        
        # Save file with fileID
        Path(f'{data_folder_path}/{folderId}/{str(newFileId)}').mkdir(exist_ok=True, parents=True)
        with open(f'{data_folder_path}/{folderId}/{str(newFileId)}/{file.filename}', 'wb') as f:
            content = file.file.read()
            f.write(content)
        
        # Update file 
        fileInfo['rawPath'] = f'{folderId}/{str(newFileId)}/{file.filename}'
        fileInfo['parsing'] = 'parsing start'
        db['files'].update_one({'_id': newFileId}, {'$set': fileInfo})
        db['folders'].update_one(
            {'_id': ObjectId(folderId)}, 
            {'$push': {'fileList': str(newFileId)}, '$inc': {'nbTotalFiles': 1}}
        )
    
    return 'done'


@router.get("")
async def get_files(filesId: str):
    """Get multiple files"""
    db = get_db()
    filesId = json.loads(filesId)
    result = db['files'].find({'_id': {'$in': [ObjectId(f) for f in filesId]}})
    return dumps(result)


@router.get("/{file_id}")
async def get_file(file_id: str):
    """Get single file with data"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    result = db['files'].find_one({'_id': ObjectId(file_id)})
    json_path = result['jsonPath']
    file_path = f'{data_folder_path}/{json_path}'
    
    with open(file_path, 'r') as f:
        json_string = f.read()
    
    response = {'fileInfo': dumps(result), 'data': json_string}
    return json.dumps(response)


@router.delete("")
async def delete_file(file: str):
    """Delete a file"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    file = json.loads(file)
    label_id = file['label']
    
    # Delete label
    db['labels'].delete_one({'_id': ObjectId(label_id)})
    
    # Update folder
    if file['nbEvent'] == 'unlabeled':
        update_dict = {
            '$pull': {'fileList': file['_id']['$oid']}, 
            '$inc': {'nbTotalFiles': -1}
        }
    else:
        update_dict = {
            '$pull': {'fileList': file['_id']['$oid']}, 
            '$inc': {'nbTotalFiles': -1, 'nbLabeledFiles': -1}
        }
    
    result = db['folders'].find_one({'fileList': file['_id']['$oid']})
    folder_id = str(result['_id'])
    db['folders'].update_many({'fileList': file['_id']['$oid']}, update_dict)
    
    # Delete file document
    db['files'].delete_one({'_id': ObjectId(file['_id']['$oid'])})
    
    # Delete file directory
    file_path = Path(data_folder_path) / folder_id / file['_id']['$oid']
    if file_path.exists():
        shutil.rmtree(file_path, ignore_errors=True)
    
    return 'done'


@router.put("/descriptions")
async def update_file_description(request: UpdateDescriptionRequest):
    """Update file description"""
    db = get_db()
    db['files'].update_one(
        {'_id': ObjectId(request.file_id)}, 
        {'$set': {'description': request.description}}
    )
    return 'done'


@router.put("/reparse")
async def reparse_files(request: ReparsingFilesRequest):
    """Trigger reparsing of files"""
    db = get_db()
    result = db['folders'].find_one({'_id': ObjectId(request.folderId)})
    files_id = result['fileList']
    db['files'].update_many(
        {'_id': {'$in': [ObjectId(id) for id in files_id]}}, 
        {'$set': {'parsing': 'parsing start'}}
    )
    return 'done'


@router.get("/data/{folder_id}")
async def get_files_data(folder_id: str):
    """Get all file data in folder"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_id = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_id]}})
    
    json_path = []
    file_names = []
    for file in result:
        if file['parsing'] == 'parsed':
            json_path.append(file['jsonPath'])
            file_names.append(file['name'])
    
    response = []
    for idx, path in enumerate(json_path):
        local_json_path = f'{data_folder_path}/{path}'
        with open(local_json_path, 'r') as f:
            data = json.load(f)
        response.append({'file_name': file_names[idx], 'data': data})
    
    return dumps(response)


@router.get("/events/{folder_id}")
async def get_files_events(folder_id: str):
    """Get all file events in folder"""
    db = get_db()
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_id = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_id]}})
    
    labels_id = []
    file_names = []
    for file in result:
        if file['parsing'] == 'parsed':
            labels_id.append(file['label'])
            file_names.append(file['name'])
    
    result = db['labels'].find({'_id': {'$in': [ObjectId(id) for id in labels_id]}})
    response = []
    for idx, label in enumerate(result):
        response.append({'file_name': file_names[idx], 'events': label['events']})
    
    return dumps(response)


@router.post("/jsonfiles")
async def download_project_files(request: DownloadJsonFilesRequest):
    """Bulk download all files in project (password protected)"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    project_id = request.projectId
    passwd = request.passwd
    
    if passwd != settings.DOWNLOAD_PASSWORD:
        return {'error': 'incorrect password'}
    
    data_folder_path = Path(data_folder_path)
    file_ids = [f.name for f in (data_folder_path / project_id).iterdir()]
    json_response = {}
    
    for file_id in file_ids:
        file_db = db['files'].find_one({'_id': ObjectId(file_id)})
        if file_db is not None and 'jsonPath' in file_db:
            filename = file_db['name']
            json_path = file_db['jsonPath']
            with open(data_folder_path / json_path) as f:
                data = json.load(f)
        else:
            data = 'none'
        
        if 'label' in file_db:
            label = db['labels'].find_one({'_id': ObjectId(file_db['label'])})
            if label is not None:
                label = json.loads(dumps(label))
            else:
                label = 'none'
        else:
            label = 'none'
        
        json_response[file_id] = {'name': filename, 'data': data, 'label': dumps(label)}
    
    return json_response

