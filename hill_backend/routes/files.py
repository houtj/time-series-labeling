"""File Routes"""
from fastapi import APIRouter, UploadFile, Form, Query
from fastapi.responses import Response
from typing import Annotated, Optional
from bson.objectid import ObjectId
from bson.json_util import dumps
from datetime import datetime, timezone
from pathlib import Path
import simplejson as json
import shutil
import logging
import numpy as np

from database import get_db, get_data_folder_path
from models import UpdateDescriptionRequest, ReparsingFilesRequest, DownloadJsonFilesRequest
from config import settings
from redis_client import get_redis_client
from services import get_data_reader, ResamplerService

logger = logging.getLogger(__name__)

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
        fileInfo['parsing'] = 'queued'  # Changed from 'parsing start'
        db['files'].update_one({'_id': newFileId}, {'$set': fileInfo})
        db['folders'].update_one(
            {'_id': ObjectId(folderId)}, 
            {'$push': {'fileList': str(newFileId)}, '$inc': {'nbTotalFiles': 1}}
        )
        
        # Add to Redis queue for processing
        try:
            redis = get_redis_client()
            redis.add_file_to_queue(
                file_id=str(newFileId),
                metadata={'filename': file.filename, 'folder_id': folderId}
            )
            # Update status to queued
            db['files'].update_one({'_id': newFileId}, {'$set': {'parsing': 'queued'}})
            logger.info(f"File {newFileId} added to parsing queue")
        except Exception as e:
            logger.error(f"Failed to add file {newFileId} to Redis queue: {e}")
            # Fall back to old method if Redis fails
            db['files'].update_one({'_id': newFileId}, {'$set': {'parsing': 'parsing start'}})
    
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
    """Get single file with data.
    
    For large files (useBinaryFormat=True), returns overview data for initial display.
    For small files, returns full data.
    """
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    result = db['files'].find_one({'_id': ObjectId(file_id)})
    
    # Check if this is a large file using binary format
    use_binary = result.get('useBinaryFormat', False)
    
    if use_binary and result.get('overviewPath'):
        # Large file: return overview data for initial display
        overview_path = result['overviewPath']
        file_path = f'{data_folder_path}/{overview_path}'
        
        with open(file_path, 'r') as f:
            overview_content = json.load(f)
        
        # New format has { meta: {...}, data: [...] }
        # Extract just the data array for backward compatibility
        if isinstance(overview_content, dict) and 'data' in overview_content:
            json_string = json.dumps(overview_content['data'])
        else:
            # Old format - direct array
            json_string = json.dumps(overview_content)
        
        logger.info(f"Returning overview data for large file: {file_id}")
    else:
        # Small file or no overview: return full data
        json_path = result['jsonPath']
        file_path = f'{data_folder_path}/{json_path}'
        
        with open(file_path, 'r') as f:
            json_string = f.read()
    
    response = {'fileInfo': dumps(result), 'data': json_string}
    return json.dumps(response)


@router.get("/{file_id}/viewport")
async def get_viewport(
    file_id: str,
    x_min: float = Query(..., description="Start of range (in x-axis units)"),
    x_max: float = Query(..., description="End of range (in x-axis units)"),
    max_points: int = Query(default=20000, description="Target points per channel"),
):
    """Get viewport data for a specific range.
    
    Returns binary data optimized for the requested viewport.
    Used for progressive loading when user zooms/pans on large files.
    
    Response Headers:
        X-Total-Points: Original points in requested range
        X-Returned-Points: Points after resampling
        X-Full-Resolution: "true" if no resampling was applied
        X-Num-Columns: Number of columns (1 + num_channels)
        X-X-Min: Actual range start
        X-X-Max: Actual range end
        X-Channel-Names: Comma-separated channel names
    
    Response Body:
        Binary ArrayBuffer containing float64 values.
        Layout: [x_values][ch1_values][ch2_values]...
        Each array has length = X-Returned-Points
    """
    try:
        db = get_db()
        data_folder_path = get_data_folder_path()
        
        result = db['files'].find_one({'_id': ObjectId(file_id)})
        
        if not result:
            return Response(
                content=b"File not found",
                status_code=404,
                media_type="text/plain"
            )
        
        use_binary = result.get('useBinaryFormat', False)
        
        if not use_binary:
            # Small file: load from JSON and return all data in range
            json_path = result['jsonPath']
            file_path = f'{data_folder_path}/{json_path}'
            
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            
            # Convert to numpy arrays
            x_trace = next(d for d in json_data if d['x'])
            channels = [d for d in json_data if not d['x']]
            
            x_data = x_trace['data']
            x_is_time = isinstance(x_data[0], str) if x_data else False
            
            if x_is_time:
                x_numeric = np.arange(len(x_data), dtype=np.float64)
            else:
                x_numeric = np.array(x_data, dtype=np.float64)
            
            # Find range
            start_idx = int(np.searchsorted(x_numeric, x_min, side='left'))
            end_idx = int(np.searchsorted(x_numeric, x_max, side='right'))
            
            start_idx = max(0, start_idx)
            end_idx = min(len(x_numeric), end_idx)
            
            original_count = end_idx - start_idx
            
            # Handle empty range
            if original_count == 0:
                return Response(
                    content=np.array([], dtype=np.float64).tobytes(),
                    media_type="application/octet-stream",
                    headers={
                        "X-Total-Points": "0",
                        "X-Returned-Points": "0",
                        "X-Full-Resolution": "true",
                        "X-Num-Columns": str(1 + len(channels)),
                        "X-X-Min": str(x_min),
                        "X-X-Max": str(x_max),
                        "X-Channel-Names": ",".join(ch['name'] for ch in channels),
                    }
                )
            
            # Extract data
            x_slice = x_numeric[start_idx:end_idx]
            channel_slices = [
                np.array(ch['data'], dtype=np.float64)[start_idx:end_idx] 
                for ch in channels
            ]
            channel_names = [ch['name'] for ch in channels]
            
            # Resample if needed
            resampler = ResamplerService(max_points)
            x_out, channels_out, is_full = resampler.resample(x_slice, channel_slices)
            
            # Pack into binary
            # Layout: x, ch1, ch2, ... (each contiguous)
            result_data = np.concatenate([x_out] + channels_out)
            
            logger.debug(f"Viewport response: {len(x_out)} points, {len(channels_out)} channels, {result_data.nbytes} bytes")
            
            return Response(
                content=result_data.tobytes(),
                media_type="application/octet-stream",
                headers={
                    "X-Total-Points": str(original_count),
                    "X-Returned-Points": str(len(x_out)),
                    "X-Full-Resolution": str(is_full).lower(),
                    "X-Num-Columns": str(1 + len(channels_out)),
                    "X-X-Min": str(float(x_out[0]) if len(x_out) > 0 else x_min),
                    "X-X-Max": str(float(x_out[-1]) if len(x_out) > 0 else x_max),
                    "X-Channel-Names": ",".join(channel_names),
                }
            )
        
        # Large file: use memory-mapped reader
        binary_path = f'{data_folder_path}/{result["binaryPath"]}'
        meta_path = f'{data_folder_path}/{result["metaPath"]}'
        
        reader = get_data_reader(binary_path, meta_path)
        
        # Get slice from memory-mapped file
        data, original_count = reader.get_slice(x_min, x_max)
        
        if len(data) == 0:
            return Response(
                content=np.array([], dtype=np.float64).tobytes(),
                media_type="application/octet-stream",
                headers={
                    "X-Total-Points": "0",
                    "X-Returned-Points": "0",
                    "X-Full-Resolution": "true",
                    "X-Num-Columns": str(reader.num_columns),
                    "X-X-Min": str(x_min),
                    "X-X-Max": str(x_max),
                    "X-Channel-Names": ",".join(ch['name'] for ch in reader.channels),
                }
            )
        
        # Extract x and channels
        x = data[:, 0]
        channel_arrays = [data[:, i + 1] for i in range(len(reader.channels))]
        channel_names = [ch['name'] for ch in reader.channels]
        
        # Resample if needed
        resampler = ResamplerService(max_points)
        x_out, channels_out, is_full = resampler.resample(x, channel_arrays)
        
        # Pack into binary (row-major: concatenate arrays)
        result_data = np.concatenate([x_out] + channels_out)
        
        logger.debug(f"Viewport response (binary): {len(x_out)} points, {len(channels_out)} channels, {result_data.nbytes} bytes")
        
        return Response(
            content=result_data.tobytes(),
            media_type="application/octet-stream",
            headers={
                "X-Total-Points": str(original_count),
                "X-Returned-Points": str(len(x_out)),
                "X-Full-Resolution": str(is_full).lower(),
                "X-Num-Columns": str(1 + len(channels_out)),
                "X-X-Min": str(float(x_out[0])),
                "X-X-Max": str(float(x_out[-1])),
                "X-Channel-Names": ",".join(channel_names),
                "X-X-Type": reader.x_type,
                "X-X-Format": reader.x_format or "",
            }
        )
        
    except Exception as e:
        logger.error(f"Viewport error: {e}", exc_info=True)
        return Response(
            content=f"Viewport error: {str(e)}".encode(),
            status_code=500,
            media_type="text/plain"
        )


@router.delete("")
async def delete_file(file: str):
    """Delete a file"""
    db = get_db()
    data_folder_path = get_data_folder_path()
    
    file = json.loads(file)
    label_id = file['label']
    file_id = file['_id']['$oid']
    
    # Get folder info before deletion
    result = db['folders'].find_one({'fileList': file_id})
    folder_id = str(result['_id']) if result else None
    
    # Delete database records first (always succeeds)
    # Delete label
    db['labels'].delete_one({'_id': ObjectId(label_id)})
    
    # Update folder
    if file['nbEvent'] == 'unlabeled':
        update_dict = {
            '$pull': {'fileList': file_id}, 
            '$inc': {'nbTotalFiles': -1}
        }
    else:
        update_dict = {
            '$pull': {'fileList': file_id}, 
            '$inc': {'nbTotalFiles': -1, 'nbLabeledFiles': -1}
        }
    db['folders'].update_many({'fileList': file_id}, update_dict)
    
    # Delete file document
    db['files'].delete_one({'_id': ObjectId(file_id)})
    
    # Try to delete file directory (don't fail if directory doesn't exist)
    try:
        if folder_id:
            file_path = Path(data_folder_path) / folder_id / file_id
            if file_path.exists():
                shutil.rmtree(file_path, ignore_errors=True)
                logger.info(f"Deleted file directory: {file_path}")
            else:
                logger.warning(f"File directory not found (already deleted?): {file_path}")
    except Exception as e:
        # Log the error but don't fail the request
        logger.warning(f"Failed to delete file directory for {file_id}: {e}")
    
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
    
    # Update status to queued
    db['files'].update_many(
        {'_id': {'$in': [ObjectId(id) for id in files_id]}}, 
        {'$set': {'parsing': 'queued'}}
    )
    
    # Add all files to Redis queue
    try:
        redis = get_redis_client()
        for file_id in files_id:
            redis.add_file_to_queue(
                file_id=file_id,
                metadata={'reparse': True, 'folder_id': request.folderId}
            )
        logger.info(f"Added {len(files_id)} files to reparse queue")
    except Exception as e:
        logger.error(f"Failed to add files to Redis queue for reparsing: {e}")
        # Fall back to old method if Redis fails
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

