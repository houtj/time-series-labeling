"""
Auto-Detection WebSocket Handler
Handles WebSocket connections for auto-detection agent
"""
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from database import get_db
import json
import asyncio

# Store active auto-detection WebSocket connections
auto_detection_connections: dict[str, WebSocket] = {}
# Store running detection tasks for cancellation
auto_detection_tasks: dict[str, asyncio.Task] = {}


async def handle_websocket(websocket: WebSocket, file_id: str):
    """Handle auto-detection WebSocket connection"""
    await websocket.accept()
    auto_detection_connections[file_id] = websocket
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()
            command = data.get('command', '')
            
            if command == 'start_auto_detection':
                await start_auto_detection_process(websocket, file_id)
            elif command == 'cancel_auto_detection':
                # Cancel the running task if it exists
                if file_id in auto_detection_tasks:
                    task = auto_detection_tasks[file_id]
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass  # Expected when cancelling
                    del auto_detection_tasks[file_id]
                    
                    # Update database status
                    db = get_db()
                    db['auto_detection_conversations'].update_one(
                        {'fileId': file_id},
                        {
                            '$set': {
                                'status': 'cancelled',
                                'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                            }
                        }
                    )
                
                await websocket.send_json({
                    'type': 'detection_cancelled',
                    'data': {'message': 'Auto-detection has been cancelled'}
                })
            else:
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': f'Unknown command: {command}'}
                })
            
    except WebSocketDisconnect:
        # Cancel any running task when client disconnects
        if file_id in auto_detection_tasks:
            auto_detection_tasks[file_id].cancel()
            del auto_detection_tasks[file_id]
        if file_id in auto_detection_connections:
            del auto_detection_connections[file_id]
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'data': {'message': f'An error occurred: {str(e)}'}
        })


async def start_auto_detection_process(websocket: WebSocket, file_id: str):
    """Start the auto-detection process with conversation tracking"""
    
    # Cancel any existing task for this file
    if file_id in auto_detection_tasks:
        auto_detection_tasks[file_id].cancel()
        try:
            await auto_detection_tasks[file_id]
        except asyncio.CancelledError:
            pass
        del auto_detection_tasks[file_id]
    
    async def run_detection_task():
        """Wrapper for the detection task to handle cancellation"""
        try:
            from agents.auto_detect import run_auto_detection
            
            # Initialize conversation
            db = get_db()
            result = db['auto_detection_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$set': {
                        'fileId': file_id,
                        'messages': [],
                        'status': 'started',
                        'createdAt': datetime.now(tz=timezone.utc).isoformat(),
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
            
            # Get conversation ID and update file
            conversation = db['auto_detection_conversations'].find_one({'fileId': file_id})
            if conversation and '_id' in conversation:
                conversation_id = str(conversation['_id'])
                from bson import ObjectId
                db['files'].update_one(
                    {'_id': ObjectId(file_id)},
                    {'$set': {'autoDetectionConversationId': conversation_id}}
                )
            
            # Define callback to save messages and stream to WebSocket
            async def auto_detection_callback(file_id: str, message: dict):
                """Save message to DB and stream to WebSocket"""
                db = get_db()
                
                # Create conversation message
                conv_message = {
                    'type': message.get('type', 'progress'),
                    'status': message.get('data', {}).get('status', 'running'),
                    'message': message.get('data', {}).get('message', ''),
                    'timestamp': datetime.now(tz=timezone.utc).isoformat()
                }
                
                # Add extra fields if present
                if 'eventsDetected' in message.get('data', {}):
                    conv_message['eventsDetected'] = message['data']['eventsDetected']
                if 'summary' in message.get('data', {}):
                    conv_message['summary'] = message['data']['summary']
                if 'error' in message.get('data', {}):
                    conv_message['error'] = message['data']['error']
                
                # Database update operations
                update_ops = {
                    '$push': {'messages': conv_message},
                    '$set': {
                        'status': conv_message['status'],
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                }
                
                # Handle plan updates - save plan to database
                if message.get('type') == 'plan_updated' and 'plan' in message.get('data', {}):
                    update_ops['$set']['plan'] = message['data']['plan']
                
                # Save to database
                db['auto_detection_conversations'].update_one(
                    {'fileId': file_id},
                    update_ops
                )
                
                # Stream to WebSocket
                if file_id in auto_detection_connections:
                    await auto_detection_connections[file_id].send_json(message)
            
            # Run the detection
            result = await run_auto_detection(file_id, "Auto-detection requested", auto_detection_callback)
            
            # Mark as completed
            db['auto_detection_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$set': {
                        'status': 'completed' if result.get('success') else 'failed',
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                }
            )
            
        except asyncio.CancelledError:
            # Task was cancelled by user
            db = get_db()
            db['auto_detection_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$set': {
                        'status': 'cancelled',
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                }
            )
            # Re-raise to propagate cancellation
            raise
            
        except Exception as e:
            # Save error to conversation
            db = get_db()
            error_message = {
                'type': 'error',
                'status': 'failed',
                'message': f'Auto-detection failed: {str(e)}',
                'timestamp': datetime.now(tz=timezone.utc).isoformat(),
                'error': str(e)
            }
            
            db['auto_detection_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$push': {'messages': error_message},
                    '$set': {
                        'status': 'failed',
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                }
            )
            
            if file_id in auto_detection_connections:
                await auto_detection_connections[file_id].send_json({
                    'type': 'auto_detect_error',
                    'data': {'message': f'Auto-detection failed: {str(e)}'}
                })
        finally:
            # Clean up task reference
            if file_id in auto_detection_tasks:
                del auto_detection_tasks[file_id]
    
    # Create and store the task
    task = asyncio.create_task(run_detection_task())
    auto_detection_tasks[file_id] = task
    
    # Wait for task to complete (or be cancelled)
    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected when task is cancelled

