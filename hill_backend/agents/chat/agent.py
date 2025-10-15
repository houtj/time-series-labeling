import os
import json
from datetime import datetime, timezone
from typing import Optional, Type
from pydantic import BaseModel, Field
from bson.objectid import ObjectId
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI configuration
azure_chat_model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1"),
    api_version=os.getenv("API_VERSION", "2024-02-01"),
    api_key=os.getenv("API_KEY"),
    azure_endpoint=os.getenv("API_ENDPOINT"),
    temperature=0.7,
)

# Global variables to store context for tools
current_file_id = None
current_user_name = "AI Assistant"  # Default to "AI Assistant"


def set_current_user(user_name: str):
    """Set the current user name for labeling"""
    global current_user_name
    current_user_name = user_name or "AI Assistant"

# Store pending notifications to be sent by the websocket handler
pending_notifications: dict[str, list[dict]] = {}

def queue_websocket_notification(file_id: str, message: dict):
    """Queue a WebSocket notification to be sent by the main WebSocket handler"""
    if file_id:
        if file_id not in pending_notifications:
            pending_notifications[file_id] = []
        pending_notifications[file_id].append(message)
        print(f"Queued notification for file {file_id}: {message['type']}")

# Pydantic models for tool inputs
class AddEventInput(BaseModel):
    class_name: str = Field(description="The name of the event class (must match existing project classes)")
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

    def _run(self, class_name: str, start: float, end: float, description: str = "created with chat") -> str:
        try:
            if not current_file_id:
                return "Error: No file context available"
            
            # Import here to avoid circular imports
            from database import get_db
            db = get_db()
                
            # Get file info and associated project
            file_info = db['files'].find_one({'_id': ObjectId(current_file_id)})
            if not file_info:
                return "Error: File not found"
                
            # Get folder and project info to validate class
            folder_info = db['folders'].find_one({'fileList': current_file_id})
            if not folder_info:
                return "Error: Folder not found"
                
            project_info = db['projects'].find_one({'_id': ObjectId(folder_info['project']['id'])})
            if not project_info:
                return "Error: Project not found"
                
            # Validate class name exists in project
            valid_classes = [cls['name'] for cls in project_info['classes']]
            if class_name not in valid_classes:
                return f"Error: Class '{class_name}' not found. Available classes: {', '.join(valid_classes)}"
                
            # Get class info
            class_info = next((cls for cls in project_info['classes'] if cls['name'] == class_name), None)
            
            # Get current label
            label_info = db['labels'].find_one({'_id': ObjectId(file_info['label'])})
            if not label_info:
                return "Error: Label not found"
                
            # Create new event
            labeler_name = current_user_name or 'AI Assistant'
            print(f"Creating event with labeler: {labeler_name}")
            new_event = {
                'className': class_name,
                'color': class_info['color'],
                'description': description,
                'labeler': labeler_name,
                'lastUpdate': datetime.now(tz=timezone.utc).isoformat(),
                'start': start,
                'end': end,
                'hide': False
            }
            
            # Add event to label
            if 'events' not in label_info:
                label_info['events'] = []
            label_info['events'].append(new_event)
            
            # Update database
            db['labels'].update_one(
                {'_id': ObjectId(file_info['label'])},
                {'$set': {'events': label_info['events']}}
            )
            
            # Update file event count
            events = label_info['events']
            if len(events) == 0:
                new_nb_events = '0'
            else:
                labelers = list(set([e['labeler'] for e in events]))
                new_nb_events = ''
                for labeler in labelers:
                    events_labeler = [e for e in events if e['labeler'] == labeler]
                    new_nb_events += f'{len(events_labeler)} by {labeler};'
                new_nb_events = new_nb_events.rstrip(';')
                
            last_modifier = current_user_name or 'AI Assistant'
            print(f"Updating file with lastModifier: {last_modifier}")
            db['files'].update_one(
                {'_id': ObjectId(current_file_id)},
                {'$set': {
                    'nbEvent': new_nb_events,
                    'lastModifier': last_modifier,
                    'lastUpdate': datetime.now(tz=timezone.utc).isoformat()
                }}
            )
            
            # Queue WebSocket notification to frontend
            queue_websocket_notification(current_file_id, {
                'type': 'event_added',
                'data': {
                    'event': new_event,
                    'message': f'Successfully added {class_name} event from {start} to {end}'
                }
            })
            
            return f"Successfully added {class_name} event from {start} to {end}"
            
        except Exception as e:
            return f"Error adding event: {str(e)}"

class AddGuidelineTool(BaseTool):
    name: str = "add_guideline"
    description: str = "Add a horizontal guideline to the current file's chart"
    args_schema: Type[BaseModel] = AddGuidelineInput

    def _run(self, channel_name: str, value: float, description: str = "created with chat") -> str:
        try:
            if not current_file_id:
                return "Error: No file context available"
            
            # Import here to avoid circular imports
            from database import get_db
            db = get_db()
                
            # Get file info
            file_info = db['files'].find_one({'_id': ObjectId(current_file_id)})
            if not file_info:
                return "Error: File not found"
                
            # Get current label
            label_info = db['labels'].find_one({'_id': ObjectId(file_info['label'])})
            if not label_info:
                return "Error: Label not found"
                
            # Create new guideline
            new_guideline = {
                'yaxis': 'y',  # Default to primary y-axis
                'y': value,
                'channelName': channel_name,
                'color': '#FF6B6B',  # Default color
                'hide': False
            }
            
            # Add guideline to label
            if 'guidelines' not in label_info:
                label_info['guidelines'] = []
            label_info['guidelines'].append(new_guideline)
            
            # Update database
            db['labels'].update_one(
                {'_id': ObjectId(file_info['label'])},
                {'$set': {'guidelines': label_info['guidelines']}}
            )
            
            # Queue WebSocket notification to frontend
            queue_websocket_notification(current_file_id, {
                'type': 'guideline_added',
                'data': {
                    'guideline': new_guideline,
                    'message': f'Successfully added guideline for {channel_name} at value {value}'
                }
            })
            
            return f"Successfully added guideline for {channel_name} at value {value}"
            
        except Exception as e:
            return f"Error adding guideline: {str(e)}"


async def get_project_context(file_id: str) -> str:
    """Get project context including classes and data channels for the current file"""
    try:
        from database import get_db, get_data_folder_path
        db = get_db()
        data_folder_path = get_data_folder_path()
        
        # Get file info
        file_info = db['files'].find_one({'_id': ObjectId(file_id)})
        if not file_info:
            return "File not found"
            
        # Get folder and project info
        folder_info = db['folders'].find_one({'fileList': file_id})
        if not folder_info:
            return "Folder not found"
            
        project_info = db['projects'].find_one({'_id': ObjectId(folder_info['project']['id'])})
        if not project_info:
            return "Project not found"
            
        # Build context
        context = f"""
Current Project: {project_info['projectName']}
Current File: {file_info['name']}

Available Event Classes:
"""
        for cls in project_info['classes']:
            context += f"- {cls['name']} (color: {cls['color']})"
            if cls.get('description'):
                context += f": {cls['description']}"
            context += "\n"
            
        # Get data channels from file data
        if file_info and file_info.get('jsonPath'):
            try:
                json_path = file_info['jsonPath']
                file_path = f'{data_folder_path}/{json_path}'
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                context += "\nAvailable Data Channels:\n"
                if isinstance(data, list):
                    for channel in data:
                        if isinstance(channel, dict) and 'name' in channel:
                            context += f"- {channel['name']}"
                            if channel.get('unit'):
                                context += f" ({channel['unit']})"
                            context += "\n"
                elif isinstance(data, dict):
                    # If data is a dict, try to extract channel names from keys
                    for key in data.keys():
                        context += f"- {key}\n"
            except Exception as e:
                context += f"\nNote: Could not load data channels ({str(e)})\n"
                
        return context
    except Exception as e:
        return f"Error getting context: {str(e)}"

async def generate_ai_response(messages: list[dict], file_id: str) -> str:
    """Generate AI response using Azure OpenAI via LangChain with tools"""
    global current_file_id, current_user_name
    
    try:
        # Debug: Print the messages structure
        print(f"DEBUG: messages type: {type(messages)}")
        print(f"DEBUG: messages content: {messages}")
        
        # Set global context for tools
        current_file_id = file_id
        # current_user_name is set by set_current_user() from WebSocket handler
        
        # Get project context
        project_context = await get_project_context(file_id)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a helpful AI assistant that helps users analyze time series data and labeling tasks. 

{project_context}

You have access to tools to add events and guidelines to the data. Use these tools when users ask to:
- Add events/labels to specific time ranges
- Add horizontal guidelines at specific values
- Mark or annotate data points

When using tools:
- For events: specify the class name, start time, end time
- For guidelines: specify the channel name and value
- Always confirm successful actions to the user

Be concise and helpful in your responses."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
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
            result = await agent_executor.ainvoke({
                "input": current_input,
                "chat_history": chat_history
            })
            
            if isinstance(result, dict) and "output" in result:
                return result["output"]
            else:
                return str(result)
                
        except Exception as agent_error:
            print(f"Agent execution error: {str(agent_error)}")
            # Fallback to simple response without tools
            simple_response = await azure_chat_model.ainvoke([
                SystemMessage(content=f"You are a helpful AI assistant for time series data analysis. {project_context}"),
                HumanMessage(content=current_input)
            ])
            return simple_response.content
        
    except Exception as e:
        print(f"General error in generate_ai_response: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"I apologize, but I encountered an error: {str(e)}"
