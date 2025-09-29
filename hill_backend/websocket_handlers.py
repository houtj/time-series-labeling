from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from database import get_conversation, clear_conversation, update_conversation_history
from chatbot import generate_ai_response, pending_notifications
import json

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}

# Store active auto-detection WebSocket connections
auto_detection_connections: dict[str, WebSocket] = {}

async def handle_chat_websocket(websocket: WebSocket, file_id: str):
    """Handle WebSocket chat endpoint"""
    await websocket.accept()
    active_connections[file_id] = websocket
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()
            
            # Handle cancellation requests
            if data.get('type') == 'cancel_request':
                print(f"Received cancellation request for file {file_id}")
                # Send acknowledgment of cancellation
                await websocket.send_json({
                    'type': 'request_cancelled',
                    'message': 'Request has been cancelled'
                })
                continue
            
            user_message = data.get('message', '')
            
            if not user_message.strip():
                continue
            
            # Get existing conversation
            conversation_json = get_conversation(file_id)
            conversation = json.loads(conversation_json)
            
            # Add user message to history
            user_msg = {
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now(tz=timezone.utc).isoformat()
            }
            
            conversation['history'].append(user_msg)
            
            # Update database
            update_conversation_history(file_id, conversation['history'])
            
            # Send acknowledgment
            await websocket.send_json({
                'type': 'user_message_received',
                'message': user_msg
            })
            
            # Generate AI response
            ai_response = await generate_ai_response(conversation['history'], file_id)
            
            # Add AI response to history
            ai_msg = {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(tz=timezone.utc).isoformat()
            }
            
            conversation['history'].append(ai_msg)
            
            # Update database
            update_conversation_history(file_id, conversation['history'])
            
            # Send AI response
            await websocket.send_json({
                'type': 'ai_response',
                'message': ai_msg
            })
            
            # Send any queued notifications from tools
            if file_id in pending_notifications:
                for notification in pending_notifications[file_id]:
                    await websocket.send_json(notification)
                    print(f"Sent notification: {notification['type']}")
                # Clear the notifications for this file
                del pending_notifications[file_id]
            
    except WebSocketDisconnect:
        if file_id in active_connections:
            del active_connections[file_id]
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': f'An error occurred: {str(e)}'
        })

async def handle_auto_detection_websocket(websocket: WebSocket, file_id: str):
    """Handle WebSocket auto-detection endpoint"""
    await websocket.accept()
    auto_detection_connections[file_id] = websocket
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()
            
            # Handle different auto-detection commands
            command = data.get('command', '')
            
            if command == 'start_auto_detection':
                await start_auto_detection_process(websocket, file_id)
            elif command == 'cancel_auto_detection':
                await websocket.send_json({
                    'type': 'auto_detect_cancelled',
                    'data': {
                        'message': 'Auto-detection has been cancelled'
                    }
                })
            else:
                await websocket.send_json({
                    'type': 'error',
                    'data': {
                        'message': f'Unknown command: {command}'
                    }
                })
            
    except WebSocketDisconnect:
        if file_id in auto_detection_connections:
            del auto_detection_connections[file_id]
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'data': {
                'message': f'An error occurred: {str(e)}'
            }
        })

async def start_auto_detection_process(websocket: WebSocket, file_id: str):
    """Start the auto-detection process"""
    try:
        # Import the auto-detection logic
        from auto_detection import run_auto_detection
        
        # Define notification callback for auto-detection
        async def auto_detection_callback(file_id: str, message: dict):
            if file_id in auto_detection_connections:
                await auto_detection_connections[file_id].send_json(message)
        
        # Send start notification
        await websocket.send_json({
            'type': 'auto_detect_started',
            'data': {
                'message': 'Starting automatic event detection...'
            }
        })
        
        # Run the detection
        result = await run_auto_detection(file_id, "Auto-detection requested", auto_detection_callback)
        
        # Send final result
        if result['success']:
            await websocket.send_json({
                'type': 'auto_detect_completed',
                'data': {
                    'message': f'Auto-detection completed! Found {result["events_detected"]} events.',
                    'events_detected': result['events_detected'],
                    'analysis_summary': result['analysis_summary']
                }
            })
        else:
            await websocket.send_json({
                'type': 'auto_detect_error',
                'data': {
                    'message': f'Auto-detection failed: {result["error"]}'
                }
            })
            
    except Exception as e:
        await websocket.send_json({
            'type': 'auto_detect_error',
            'data': {
                'message': f'Auto-detection failed: {str(e)}'
            }
        })
