"""
Auto-Detection Conversation Routes
Manages auto-detection workflow progress and results
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from bson.objectid import ObjectId
from bson.json_util import dumps

from database import get_db

router = APIRouter(prefix="/conversations/detection", tags=["detection-conversations"])


@router.get("/{file_id}")
async def get_detection_conversation(file_id: str):
    """
    Get auto-detection conversation for a file
    
    Returns detection progress/history or creates new empty conversation
    """
    db = get_db()
    conversation = db['auto_detection_conversations'].find_one({'fileId': file_id})
    
    if not conversation:
        # Create new conversation
        conversation = {
            'fileId': file_id,
            'messages': [],
            'status': 'idle',  # idle, running, completed, failed
            'createdAt': datetime.now(tz=timezone.utc).isoformat(),
            'updatedAt': datetime.now(tz=timezone.utc).isoformat()
        }
        result = db['auto_detection_conversations'].insert_one(conversation)
        conversation['_id'] = result.inserted_id
    
    return dumps(conversation)


@router.delete("/{file_id}")
async def clear_detection_conversation(file_id: str):
    """
    Delete auto-detection conversation and remove reference from file
    """
    db = get_db()
    
    # Delete the conversation document
    result = db['auto_detection_conversations'].delete_one({'fileId': file_id})
    
    # Remove conversation ID from file
    from bson import ObjectId
    db['files'].update_one(
        {'_id': ObjectId(file_id)},
        {'$unset': {'autoDetectionConversationId': ''}}
    )
    
    if result.deleted_count == 0:
        return {'status': 'not_found', 'message': 'No conversation found for this file'}
    
    return {'status': 'deleted', 'fileId': file_id}


@router.get("/{file_id}/latest")
async def get_latest_detection_run(file_id: str):
    """
    Get the latest completed detection run
    
    Returns the most recent successful detection with results
    """
    db = get_db()
    conversation = db['auto_detection_conversations'].find_one({'fileId': file_id})
    
    if not conversation:
        return {'status': 'not_found', 'message': 'No detection history for this file'}
    
    # Find last completed message
    messages = conversation.get('messages', [])
    latest_result = None
    
    for message in reversed(messages):
        if message.get('type') == 'result' and message.get('status') == 'completed':
            latest_result = message
            break
    
    if not latest_result:
        return {'status': 'no_results', 'message': 'No completed detection runs found'}
    
    return {
        'status': 'found',
        'result': latest_result,
        'totalRuns': len([m for m in messages if m.get('type') == 'result'])
    }


@router.get("/{file_id}/history")
async def get_detection_history(file_id: str):
    """
    Get all detection runs history
    
    Returns summary of all detection attempts
    """
    db = get_db()
    conversation = db['auto_detection_conversations'].find_one({'fileId': file_id})
    
    if not conversation:
        return {'runs': [], 'total': 0}
    
    messages = conversation.get('messages', [])
    
    # Extract all result messages
    results = [m for m in messages if m.get('type') == 'result']
    
    return {
        'runs': results,
        'total': len(results),
        'currentStatus': conversation.get('status', 'idle')
    }

