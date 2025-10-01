"""Chatbot service - AI chat functionality with tools"""

import json
import logging
from datetime import datetime, timezone
from typing import Type

from bson import ObjectId
from bson.json_util import dumps
from fastapi import WebSocket
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.database import get_sync_database
from app.repositories.conversation import ConversationRepository

logger = logging.getLogger(__name__)
settings = get_settings()

# Azure OpenAI configuration
azure_chat_model = AzureChatOpenAI(
    azure_deployment=settings.azure_openai_deployment_name,
    api_version=settings.azure_openai_api_version,
    api_key=settings.azure_openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    temperature=settings.azure_openai_temperature,
)

# Global variables to store context for tools
current_file_id = None
current_user_name = None

# Store pending notifications to be sent by the websocket handler
pending_notifications: dict[str, list[dict]] = {}


def queue_websocket_notification(file_id: str, message: dict):
    """Queue a WebSocket notification to be sent by the main WebSocket handler"""
    if file_id:
        if file_id not in pending_notifications:
            pending_notifications[file_id] = []
        pending_notifications[file_id].append(message)
        logger.debug(f"Queued notification for file {file_id}: {message['type']}")


# Pydantic models for tool inputs
class AddEventInput(BaseModel):
    class_name: str = Field(
        description="The name of the event class (must match existing project classes)"
    )
    start: float = Field(description="Start time/position of the event")
    end: float = Field(description="End time/position of the event")
    description: str = Field(default="created with chat", description="Description of the event")


class AddGuidelineInput(BaseModel):
    channel_name: str = Field(description="The name of the data channel/variable")
    value: float = Field(description="The Y-axis value for the guideline")
    description: str = Field(default="created with chat", description="Description of the guideline")


class AddEventTool(BaseTool):
    name: str = "add_event"
    description: str = "Add an event/label to the current file's timeline"
    args_schema: Type[BaseModel] = AddEventInput

    def _run(
        self, class_name: str, start: float, end: float, description: str = "created with chat"
    ) -> str:
        try:
            if not current_file_id:
                return "Error: No file context available"

            db = get_sync_database()

            # Get file info and associated project
            file_info = db["files"].find_one({"_id": ObjectId(current_file_id)})
            if not file_info:
                return "Error: File not found"

            # Get folder and project info to validate class
            folder_info = db["folders"].find_one({"fileList": current_file_id})
            if not folder_info:
                return "Error: Folder not found"

            project_info = db["projects"].find_one({"_id": ObjectId(folder_info["project"]["id"])})
            if not project_info:
                return "Error: Project not found"

            # Validate class name exists in project
            valid_classes = [cls["name"] for cls in project_info["classes"]]
            if class_name not in valid_classes:
                return f"Error: Class '{class_name}' not found. Available classes: {', '.join(valid_classes)}"

            # Get class info
            class_info = next(
                (cls for cls in project_info["classes"] if cls["name"] == class_name), None
            )

            # Get current label
            label_info = db["labels"].find_one({"_id": ObjectId(file_info["label"])})
            if not label_info:
                return "Error: Label not found"

            # Create new event
            new_event = {
                "className": class_name,
                "color": class_info["color"],
                "description": description,
                "labeler": current_user_name or "AI Assistant",
                "start": start,
                "end": end,
                "hide": False,
            }

            # Add event to label
            if "events" not in label_info:
                label_info["events"] = []
            label_info["events"].append(new_event)

            # Update database
            db["labels"].update_one(
                {"_id": ObjectId(file_info["label"])}, {"$set": {"events": label_info["events"]}}
            )

            # Update file event count
            events = label_info["events"]
            new_nb_events = _calculate_event_count(events)

            db["files"].update_one(
                {"_id": ObjectId(current_file_id)},
                {
                    "$set": {
                        "nbEvent": new_nb_events,
                        "lastModifier": current_user_name or "AI Assistant",
                        "lastUpdate": datetime.now(tz=timezone.utc),
                    }
                },
            )

            # Queue WebSocket notification to frontend
            queue_websocket_notification(
                current_file_id,
                {
                    "type": "event_added",
                    "data": {
                        "event": new_event,
                        "message": f"Successfully added {class_name} event from {start} to {end}",
                    },
                },
            )

            return f"Successfully added {class_name} event from {start} to {end}"

        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return f"Error adding event: {str(e)}"


class AddGuidelineTool(BaseTool):
    name: str = "add_guideline"
    description: str = "Add a horizontal guideline to the current file's chart"
    args_schema: Type[BaseModel] = AddGuidelineInput

    def _run(
        self, channel_name: str, value: float, description: str = "created with chat"
    ) -> str:
        try:
            if not current_file_id:
                return "Error: No file context available"

            db = get_sync_database()

            # Get file info
            file_info = db["files"].find_one({"_id": ObjectId(current_file_id)})
            if not file_info:
                return "Error: File not found"

            # Get current label
            label_info = db["labels"].find_one({"_id": ObjectId(file_info["label"])})
            if not label_info:
                return "Error: Label not found"

            # Create new guideline
            new_guideline = {
                "yaxis": "y",
                "y": value,
                "channelName": channel_name,
                "color": "#FF6B6B",
                "hide": False,
            }

            # Add guideline to label
            if "guidelines" not in label_info:
                label_info["guidelines"] = []
            label_info["guidelines"].append(new_guideline)

            # Update database
            db["labels"].update_one(
                {"_id": ObjectId(file_info["label"])},
                {"$set": {"guidelines": label_info["guidelines"]}},
            )

            # Queue WebSocket notification to frontend
            queue_websocket_notification(
                current_file_id,
                {
                    "type": "guideline_added",
                    "data": {
                        "guideline": new_guideline,
                        "message": f"Successfully added guideline for {channel_name} at value {value}",
                    },
                },
            )

            return f"Successfully added guideline for {channel_name} at value {value}"

        except Exception as e:
            logger.error(f"Error adding guideline: {e}")
            return f"Error adding guideline: {str(e)}"


def _calculate_event_count(events: list[dict]) -> str:
    """Calculate event count string by labeler"""
    if not events:
        return "0"

    labelers = list(set([e["labeler"] for e in events]))
    new_nb_events = ""
    for labeler in labelers:
        events_labeler = [e for e in events if e["labeler"] == labeler]
        new_nb_events += f'{len(events_labeler)} by {labeler};'

    return new_nb_events.rstrip(";")


async def get_project_context(file_id: str) -> str:
    """Get project context including classes and data channels for the current file"""
    try:
        db = get_sync_database()
        data_folder_path = settings.data_folder_path

        # Get file info
        file_info = db["files"].find_one({"_id": ObjectId(file_id)})
        if not file_info:
            return "File not found"

        # Get folder and project info
        folder_info = db["folders"].find_one({"fileList": file_id})
        if not folder_info:
            return "Folder not found"

        project_info = db["projects"].find_one({"_id": ObjectId(folder_info["project"]["id"])})
        if not project_info:
            return "Project not found"

        # Build context
        context = f"""
Current Project: {project_info['projectName']}
Current File: {file_info['name']}

Available Event Classes:
"""
        for cls in project_info["classes"]:
            context += f"- {cls['name']} (color: {cls['color']})"
            if cls.get("description"):
                context += f": {cls['description']}"
            context += "\n"

        # Get data channels from file data
        if file_info and file_info.get("jsonPath"):
            try:
                json_path = file_info["jsonPath"]
                file_path = f"{data_folder_path}/{json_path}"
                with open(file_path, "r") as f:
                    data = json.load(f)

                context += "\nAvailable Data Channels:\n"
                if isinstance(data, list):
                    for channel in data:
                        if isinstance(channel, dict) and "name" in channel:
                            context += f"- {channel['name']}"
                            if channel.get("unit"):
                                context += f" ({channel['unit']})"
                            context += "\n"
                elif isinstance(data, dict):
                    for key in data.keys():
                        context += f"- {key}\n"
            except Exception as e:
                context += f"\nNote: Could not load data channels ({str(e)})\n"

        return context
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return f"Error getting context: {str(e)}"


async def generate_ai_response(messages: list[dict], file_id: str) -> str:
    """Generate AI response using Azure OpenAI via LangChain with tools"""
    global current_file_id, current_user_name

    try:
        # Set global context for tools
        current_file_id = file_id
        current_user_name = "AI Assistant"

        # Get project context
        project_context = await get_project_context(file_id)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""You are a helpful AI assistant that helps users analyze time series data and labeling tasks. 

{project_context}

You have access to tools to add events and guidelines to the data. Use these tools when users ask to:
- Add events/labels to specific time ranges
- Add horizontal guidelines at specific values
- Mark or annotate data points

When using tools:
- For events: specify the class name, start time, end time
- For guidelines: specify the channel name and value
- Always confirm successful actions to the user

Be concise and helpful in your responses.""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create tools list
        tools = [AddEventTool(), AddGuidelineTool()]

        # Create agent
        agent = create_openai_tools_agent(azure_chat_model, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        # Format chat history (exclude the last message which is current input)
        chat_history = []
        if len(messages) > 1:
            for msg in messages[:-1]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))

        # Get current input
        current_input = ""
        if messages and len(messages) > 0:
            last_msg = messages[-1]
            if isinstance(last_msg, dict) and "content" in last_msg:
                current_input = last_msg["content"]
            else:
                current_input = str(last_msg)

        # Execute agent
        try:
            result = await agent_executor.ainvoke({"input": current_input, "chat_history": chat_history})

            if isinstance(result, dict) and "output" in result:
                return result["output"]
            else:
                return str(result)

        except Exception as agent_error:
            logger.error(f"Agent execution error: {agent_error}")
            # Fallback to simple response without tools
            simple_response = await azure_chat_model.ainvoke(
                [
                    SystemMessage(
                        content=f"You are a helpful AI assistant for time series data analysis. {project_context}"
                    ),
                    HumanMessage(content=current_input),
                ]
            )
            return simple_response.content

    except Exception as e:
        logger.error(f"General error in generate_ai_response: {e}")
        import traceback

        traceback.print_exc()
        return f"I apologize, but I encountered an error: {str(e)}"


async def handle_chat_message(websocket: WebSocket, file_id: str, user_message: str):
    """Handle a chat message from the websocket"""
    db = get_sync_database()
    repo = ConversationRepository(db)

    # Get existing conversation
    conversation = repo.find_by_file_id(file_id)
    if not conversation:
        repo.create_for_file(file_id)
        conversation = repo.find_by_file_id(file_id)

    # Add user message to history
    user_msg = {
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    history = conversation.get("history", [])
    history.append(user_msg)

    # Update database
    repo.update_history(file_id, history)

    # Send acknowledgment
    await websocket.send_json({"type": "user_message_received", "message": user_msg})

    # Generate AI response
    ai_response = await generate_ai_response(history, file_id)

    # Add AI response to history
    ai_msg = {
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    history.append(ai_msg)

    # Update database
    repo.update_history(file_id, history)

    # Send AI response
    await websocket.send_json({"type": "ai_response", "message": ai_msg})

    # Send any queued notifications from tools
    if file_id in pending_notifications:
        for notification in pending_notifications[file_id]:
            await websocket.send_json(notification)
            logger.info(f"Sent notification: {notification['type']}")
        # Clear the notifications for this file
        del pending_notifications[file_id]

