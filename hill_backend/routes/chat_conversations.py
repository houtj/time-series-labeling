"""
Chat Conversation Routes
Manages conversational UI interactions for file labeling
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from bson.objectid import ObjectId
from bson.json_util import dumps

from database import get_db

router = APIRouter(prefix="/conversations/chat", tags=["chat-conversations"])


@router.get("/{file_id}")
async def get_chat_conversation(file_id: str):
    """
    Get chat conversation for a file
    
    Returns conversation history or creates new empty conversation
    """
    db = get_db()
    conversation = db['chat_conversations'].find_one({'fileId': file_id})
    
    if not conversation:
        # Create new conversation
        conversation = {
            'fileId': file_id,
            'messages': [],
            'createdAt': datetime.now(tz=timezone.utc).isoformat(),
            'updatedAt': datetime.now(tz=timezone.utc).isoformat()
        }
        result = db['chat_conversations'].insert_one(conversation)
        conversation['_id'] = result.inserted_id
    
    return dumps(conversation)


@router.delete("/{file_id}")
async def clear_chat_conversation(file_id: str):
    """
    Clear chat conversation history
    
    Empties the message array but keeps the conversation document
    """
    db = get_db()
    result = db['chat_conversations'].update_one(
        {'fileId': file_id},
        {
            '$set': {
                'messages': [],
                'updatedAt': datetime.now(tz=timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        return {'status': 'not_found', 'message': 'No conversation found for this file'}
    
    return {'status': 'cleared', 'fileId': file_id}


@router.get("/{file_id}/messages/recent")
async def get_recent_chat_messages(file_id: str, limit: int = 50):
    """
    Get recent chat messages (for pagination)
    
    Returns last N messages
    """
    db = get_db()
    conversation = db['chat_conversations'].find_one({'fileId': file_id})
    
    if not conversation:
        return {'messages': [], 'total': 0}
    
    messages = conversation.get('messages', [])
    total = len(messages)
    recent = messages[-limit:] if len(messages) > limit else messages
    
    return {
        'messages': recent,
        'total': total,
        'returned': len(recent)
    }

