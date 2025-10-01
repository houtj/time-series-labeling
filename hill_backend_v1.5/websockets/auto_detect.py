"""
Auto-Detection WebSocket Handler
Handles WebSocket connections for auto-detection agent
"""
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from database import get_db
import json

# Store active auto-detection WebSocket connections
auto_detection_connections: dict[str, WebSocket] = {}


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
                await websocket.send_json({
                    'type': 'auto_detect_cancelled',
                    'data': {'message': 'Auto-detection has been cancelled'}
                })
            else:
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': f'Unknown command: {command}'}
                })
            
    except WebSocketDisconnect:
        if file_id in auto_detection_connections:
            del auto_detection_connections[file_id]
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'data': {'message': f'An error occurred: {str(e)}'}
        })


async def start_auto_detection_process(websocket: WebSocket, file_id: str):
    """Start the auto-detection process with conversation tracking"""
    try:
        from agents.auto_detect import run_auto_detection
        
        # Initialize conversation
        db = get_db()
        db['auto_detection_conversations'].update_one(
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
            
            # Save to database
            db['auto_detection_conversations'].update_one(
                {'fileId': file_id},
                {
                    '$push': {'messages': conv_message},
                    '$set': {
                        'status': conv_message['status'],
                        'updatedAt': datetime.now(tz=timezone.utc).isoformat()
                    }
                }
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
        
        await websocket.send_json({
            'type': 'auto_detect_error',
            'data': {'message': f'Auto-detection failed: {str(e)}'}
        })

