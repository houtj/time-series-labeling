"""Label and Event Routes"""
from fastapi import APIRouter, UploadFile, Form
from typing import Annotated
from bson.objectid import ObjectId
from bson.json_util import dumps
from datetime import datetime, timezone
import simplejson as json

from database import get_db
from models import UpdateLabelRequest, NewClassRequest, UpdateClassRequest

router = APIRouter(prefix="/labels", tags=["labels"])


def calculate_event_display(events: list[dict]) -> str:
    """Helper: Calculate event count display like '3 by Alice; 2 by Bob'"""
    if len(events) == 0:
        return '0'
    
    labelers = list(set([e['labeler'] for e in events]))
    parts = []
    for labeler in labelers:
        count = len([e for e in events if e['labeler'] == labeler])
        parts.append(f'{count} by {labeler}')
    
    return ';'.join(parts)


@router.get("/{label_id}")
async def get_label(label_id: str):
    """Get label by ID"""
    db = get_db()
    result = db['labels'].find_one({'_id': ObjectId(label_id)})
    return dumps(result)


@router.put("")
async def update_label(request: UpdateLabelRequest):
    """Update label"""
    db = get_db()
    label_info = request.label
    label_id = label_info['_id']['$oid']
    del label_info['_id']
    
    db['labels'].update_one({'_id': ObjectId(label_id)}, {'$set': label_info})
    
    file = db['files'].find_one({'label': label_id})
    previous_nbEvents = file['nbEvent']
    new_nbEvents = calculate_event_display(label_info['events'])
    
    db['files'].update_one(
        {'label': label_id}, 
        {'$set': {
            'nbEvent': new_nbEvents, 
            'lastModifier': request.user, 
            'lastUpdate': datetime.now(tz=timezone.utc)
        }}
    )
    
    if previous_nbEvents == 'unlabeled':
        db['folders'].update_one(
            {'fileList': str(file['_id'])}, 
            {'$inc': {'nbLabeledFiles': 1}}
        )
    
    return 'done'


@router.post("/event")
async def add_event(data: Annotated[str, Form()], user: Annotated[str, Form()], file: UploadFile):
    """Add single event (can include both events and guidelines)"""
    db = get_db()
    import_data = file.file.read()
    import_data = json.loads(import_data)
    label_id = data
    user_name = user
    
    # Handle both old format (just array of events) and new format (object with events and guidelines)
    update_dict = {}
    events_list = []
    if isinstance(import_data, list):
        # Old format: just events array
        update_dict['events'] = import_data
        events_list = import_data
    elif isinstance(import_data, dict):
        # New format: object with events and/or guidelines
        if 'events' in import_data:
            update_dict['events'] = import_data['events']
            events_list = import_data['events']
        if 'guidelines' in import_data:
            update_dict['guidelines'] = import_data['guidelines']
    
    if update_dict:
        db['labels'].update_one({'_id': ObjectId(label_id)}, {'$set': update_dict})
    
    file_doc = db['files'].find_one({'label': label_id})
    previous_nbEvents = file_doc['nbEvent']
    new_nbEvents = calculate_event_display(events_list)
    
    db['files'].update_one(
        {'label': label_id}, 
        {'$set': {
            'nbEvent': new_nbEvents, 
            'lastModifier': user_name, 
            'lastUpdate': datetime.now(tz=timezone.utc)
        }}
    )
    
    if previous_nbEvents == 'unlabeled':
        db['folders'].update_one(
            {'fileList': str(file_doc['_id'])}, 
            {'$inc': {'nbLabeledFiles': 1}}
        )
    
    return 'done'


@router.post("/events")
async def add_events_bulk(data: Annotated[str, Form()], user: Annotated[str, Form()], file: UploadFile):
    """Add multiple events"""
    db = get_db()
    event_info_list = file.file.read()
    event_info_list = json.loads(event_info_list)
    folder_id = data
    
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_list = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_list]}})
    
    file_name_dict = {}
    for file_doc in result:
        file_name_dict[file_doc['name']] = file_doc['label']
    
    for event in event_info_list:
        if event['file_name'] in file_name_dict:
            label_id = file_name_dict[event['file_name']]
            db['labels'].update_one(
                {'_id': ObjectId(label_id)}, 
                {'$set': {'events': event['events']}}
            )
            
            file_doc = db['files'].find_one({'label': label_id})
            previous_nbEvents = file_doc['nbEvent']
            new_nbEvents = calculate_event_display(event['events'])
            
            db['files'].update_one(
                {'label': label_id}, 
                {'$set': {
                    'nbEvent': new_nbEvents, 
                    'lastModifier': user, 
                    'lastUpdate': datetime.now(tz=timezone.utc)
                }}
            )
            
            if previous_nbEvents == 'unlabeled':
                db['folders'].update_one(
                    {'fileList': str(file_doc['_id'])}, 
                    {'$inc': {'nbLabeledFiles': 1}}
                )
    
    return 'done'


@router.post("/classes")
async def add_class(class_: NewClassRequest):
    """Add new class to project"""
    db = get_db()
    db['projects'].update_one(
        {'_id': ObjectId(class_.projectId)}, 
        {'$push': {
            'classes': {
                'name': class_.newClassName, 
                'color': class_.newClassColor, 
                'description': class_.description
            }
        }}
    )
    return 'done'


@router.put("/classes")
async def update_class(newClass: UpdateClassRequest):
    """Update existing class"""
    db = get_db()
    db['projects'].update_one(
        {'_id': ObjectId(newClass.projectId), 'classes.name': newClass.updatingClassName}, 
        {'$set': {
            'classes.$': {
                'name': newClass.newClassName, 
                'color': newClass.newClassColor, 
                'description': newClass.description
            }
        }}
    )
    return 'done'

