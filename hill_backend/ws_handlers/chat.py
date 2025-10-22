"""
Chat WebSocket Handler
Handles WebSocket connections for chat assistant
"""
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from database import get_db
from agents.chat import generate_ai_response, pending_notifications, set_current_user
import json

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}

# Store user context for each file
user_contexts: dict[str, dict] = {}


async def handle_websocket(websocket: WebSocket, file_id: str):
    """Handle chat WebSocket connection"""
    await websocket.accept()
    active_connections[file_id] = websocket
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()
            
            # Handle set-context action
            if data.get('action') == 'set-context':
                context = data.get('context', {})
                user_contexts[file_id] = context
                # Set user name for the agent
                if 'userName' in context:
                    print(f"Setting current user to: {context['userName']}")
                    set_current_user(context['userName'])
                else:
                    print(f"No userName in context: {context}")
                continue
            
            # Handle cancellation
            if data.get('type') == 'cancel_request':
                await websocket.send_json({
                    'type': 'request_cancelled',
                    'message': 'Request has been cancelled'
                })
                continue
            
            user_message = data.get('message', '')
            if not user_message.strip():
                continue
            
            # Get existing conversation
            db = get_db()
            conversation = db['chat_conversations'].find_one({'fileId': file_id})
            
            if not conversation:
                conversation = {
                    'fileId': file_id,
                    'messages': [],
                    'createdAt': datetime.now(tz=timezone.utc).isoformat(),
                    'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                }
                result = db['chat_conversations'].insert_one(conversation)
                conversation_id = str(result.inserted_id)
                
                # Update file with conversation ID
                from bson import ObjectId
                db['files'].update_one(
                    {'_id': ObjectId(file_id)},
                    {'$set': {'chatConversationId': conversation_id}}
                )
            
            # Add user message
            user_msg = {
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now(tz=timezone.utc).isoformat()
            }
            conversation['messages'].append(user_msg)
            
            # Update database
            db['chat_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$push': {'messages': user_msg},
                    '$set': {'updatedAt': datetime.now(tz=timezone.utc).isoformat()}
                }
            )
            
            # Send acknowledgment
            await websocket.send_json({
                'type': 'user_message_received',
                'message': user_msg
            })
            
            # Generate AI response
            ai_response = await generate_ai_response(conversation['messages'], file_id)
            
            # Add AI response
            ai_msg = {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(tz=timezone.utc).isoformat()
            }
            conversation['messages'].append(ai_msg)
            
            # Update database
            db['chat_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$push': {'messages': ai_msg},
                    '$set': {'updatedAt': datetime.now(tz=timezone.utc).isoformat()}
                }
            )
            
            # Send AI response
            await websocket.send_json({
                'type': 'ai_response',
                'message': ai_msg
            })
            
            # Send any queued notifications from tools
            if file_id in pending_notifications:
                for notification in pending_notifications[file_id]:
                    await websocket.send_json(notification)
                del pending_notifications[file_id]
            
    except WebSocketDisconnect:
        if file_id in active_connections:
            del active_connections[file_id]
        if file_id in user_contexts:
            del user_contexts[file_id]
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': f'An error occurred: {str(e)}'
        })

