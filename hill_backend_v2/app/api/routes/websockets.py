"""WebSocket-related API routes"""

import json
import logging
from datetime import datetime, timezone

from bson.json_util import dumps
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import get_sync_database
from app.repositories.conversation import ConversationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websockets"])

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}
auto_detection_connections: dict[str, WebSocket] = {}


@router.get("/conversations/{file_id}")
async def get_conversation(file_id: str):
    """Get conversation history for a file"""
    db = get_sync_database()
    repo = ConversationRepository(db)

    conversation = repo.find_by_file_id(file_id)
    if conversation:
        return dumps(conversation)
    else:
        # Create new conversation if none exists
        new_id = repo.create_for_file(file_id)
        new_conversation = repo.find_by_id(new_id)
        return dumps(new_conversation)


@router.delete("/conversations/{file_id}")
async def clear_conversation(file_id: str):
    """Clear conversation history for a file"""
    db = get_sync_database()
    repo = ConversationRepository(db)
    repo.clear_history(file_id)
    return "done"


@router.websocket("/ws/chat/{file_id}")
async def websocket_chat(websocket: WebSocket, file_id: str):
    """WebSocket endpoint for chat functionality"""
    await websocket.accept()
    active_connections[file_id] = websocket

    try:
        # Import here to avoid circular dependencies
        from app.services.chatbot import handle_chat_message

        while True:
            # Receive message from frontend
            data = await websocket.receive_json()

            # Handle cancellation requests
            if data.get("type") == "cancel_request":
                logger.info(f"Received cancellation request for file {file_id}")
                await websocket.send_json(
                    {"type": "request_cancelled", "message": "Request has been cancelled"}
                )
                continue

            user_message = data.get("message", "")

            if not user_message.strip():
                continue

            # Handle the chat message
            await handle_chat_message(websocket, file_id, user_message)

    except WebSocketDisconnect:
        if file_id in active_connections:
            del active_connections[file_id]
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": f"An error occurred: {str(e)}"})


@router.websocket("/ws/auto-detection/{file_id}")
async def websocket_auto_detection(websocket: WebSocket, file_id: str):
    """WebSocket endpoint for auto-detection functionality"""
    await websocket.accept()
    auto_detection_connections[file_id] = websocket

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()

            # Handle different auto-detection commands
            command = data.get("command", "")

            if command == "start_auto_detection":
                # Import here to avoid circular dependencies
                try:
                    from app.services.auto_detection import start_auto_detection_process

                    await start_auto_detection_process(websocket, file_id)
                except ImportError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": {"message": "Auto-detection module not available"},
                        }
                    )
            elif command == "cancel_auto_detection":
                await websocket.send_json(
                    {
                        "type": "auto_detect_cancelled",
                        "data": {"message": "Auto-detection has been cancelled"},
                    }
                )
            else:
                await websocket.send_json(
                    {"type": "error", "data": {"message": f"Unknown command: {command}"}}
                )

    except WebSocketDisconnect:
        if file_id in auto_detection_connections:
            del auto_detection_connections[file_id]
    except Exception as e:
        logger.error(f"WebSocket auto-detection error: {e}")
        await websocket.send_json(
            {"type": "error", "data": {"message": f"An error occurred: {str(e)}"}}
        )

