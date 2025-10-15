"""
Agent Coordinator - Manages interaction between Planner and Worker agents
Orchestrates the multi-agent workflow for time-series event identification
"""

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage
from langchain_openai import AzureChatOpenAI
from pathlib import Path
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import asyncio
from dotenv import load_dotenv

from .models import PlannerResponseFormatter, StatusEnum, IdentifierResponseFormatter, ValidatorResponseFormatter

from . import tools
from . import prompts as pt
from langgraph.types import Command
from . import utils
import openai
import pickle
# Removed sleep import - using asyncio.sleep instead
import json

# Import agent functions
from .planner import planner_node, planner_tools_node, route_planner_messages
from .identifier import identifier_node, identifier_tools_node, route_identifier_messages
from .validator import validator_node, validator_tools_node, route_validator_messages

class State(TypedDict):
    planner_messages: List[AnyMessage]
    identifier_messages: List[AnyMessage]
    validator_messages: List[AnyMessage]
    plan: List[Dict] # {task_id, task_description, task_type, is_done}
    communication: dict # {from, to, message}
    detected_events: List[Dict] # [{event_name, start_idx, end_idx,]
    token_usage: int
    current_agent: str # Current running agent: "planner", "identifier", "validator"

load_dotenv()

class Config:
    API_VERSION = os.getenv('API_VERSION')
    API_KEY = os.getenv('API_KEY')
    API_ENDPOINT = os.getenv('API_ENDPOINT')

class AgentCoordinator:
    def __init__(self, df, file_id: str, project_info=None, event_patterns=None, notification_callback=None):
        self.df = df
        self.file_id = file_id
        self.project_info = project_info
        self.event_patterns = event_patterns or {}
        self.notification_callback = notification_callback
        self.final_result = None
        
        # Initialize components
        self._read_file()
        self._init_tools()
        self._init_llm()
    
    def _read_file(self):
        self.stat = tools.get_basic_statistics(self.df)

    def _init_llm(self):
        config = Config()
        
        llm_planner = AzureChatOpenAI(
            azure_deployment="gpt-4.1",
            api_version=config.API_VERSION,
            api_key=config.API_KEY,
            azure_endpoint=config.API_ENDPOINT,
            temperature=0,
        )
        llm_identifier = AzureChatOpenAI(
            azure_deployment="gpt-4.1",
            api_version=config.API_VERSION,
            api_key=config.API_KEY,
            azure_endpoint=config.API_ENDPOINT,
            temperature=0,
        )
        llm_validator = AzureChatOpenAI(
            azure_deployment="gpt-4.1",
            api_version=config.API_VERSION,
            api_key=config.API_KEY,
            azure_endpoint=config.API_ENDPOINT,
            temperature=0,
        )
        self.llm_planner = llm_planner.with_structured_output(PlannerResponseFormatter, include_raw=True)
        self.llm_identifier = llm_identifier.with_structured_output(IdentifierResponseFormatter, include_raw=True)
        self.llm_validator = llm_validator.with_structured_output(ValidatorResponseFormatter, include_raw=True)
    
    def _init_tools(self):
        self.plot_viewer_planner = tools.PlotViewer(self.df, self._create_view_sync_callback('Planner'))
        self.plot_viewer_identifier = tools.PlotViewer(self.df, self._create_view_sync_callback('Identifier'))
        self.plot_viewer_validator = tools.PlotViewer(self.df, self._create_view_sync_callback('Validator'))

    def _invoke_llm(self, messages, chain):
        try:
            response = chain.invoke({"messages": messages})
        except openai.BadRequestError:
            if len(messages[-1].content)==2:
                messages[-1].content[0] = {"type":"text", "text": "The image is regarded illegal by GPT-4.1. Try another way to view the data."}
                messages[-1].content = [messages[-1].content[0]]
                response = chain.invoke({"messages": messages})
            else:
                raise RuntimeError("OpenAI BadRequestError encountered and could not recover by removing the image from the message.")
        token_usage = response['raw'].response_metadata['token_usage']['total_tokens']
        return response, token_usage

    def _send_llm_interaction_sync(self, agent_name: str, messages, response, token_usage):
        """Send LLM interaction details to frontend synchronously"""
        if not self.notification_callback:
            return
            
        # Format the last user message (sent to LLM)
        last_message = messages[-1] if messages else None
        sent_message = ""
        if last_message:
            if hasattr(last_message, 'content'):
                if isinstance(last_message.content, list):
                    # Handle multi-modal content (text + images)
                    text_parts = [item.get('text', '') for item in last_message.content if item.get('type') == 'text']
                    sent_message = '\n'.join(text_parts)
                else:
                    sent_message = str(last_message.content)
            else:
                sent_message = str(last_message)
        
        # Format the LLM response
        received_message = ""
        if response and 'parsed' in response:
            parsed_response = response['parsed']
            if hasattr(parsed_response, 'raw_message'):
                received_message = parsed_response.raw_message
            else:
                received_message = str(parsed_response)
        
        # Store the notification for immediate sending
        if not hasattr(self, 'pending_llm_notifications'):
            self.pending_llm_notifications = []
            
        notification_data = {
            'type': 'llm_interaction',
            'data': {
                'agent': agent_name,
                'sent_message': sent_message,
                'received_message': received_message,
                'token_usage': token_usage,
                'total_token_usage': getattr(self, 'total_token_usage', token_usage)
            }
        }
        
        self.pending_llm_notifications.append(notification_data)

    def _create_view_sync_callback(self, agent_name: str):
        """Create a callback function to sync plot view changes with frontend"""
        def sync_callback(start_idx: int, end_idx: int):
            if self.notification_callback:
                # Store the notification for sending in the next async iteration
                if not hasattr(self, 'pending_view_sync_notifications'):
                    self.pending_view_sync_notifications = []
                
                self.pending_view_sync_notifications.append({
                    'type': 'plot_view_sync',
                    'data': {
                        'agent': agent_name,
                        'start_idx': start_idx,
                        'end_idx': end_idx,
                        'timestamp': pd.Timestamp.now().isoformat()
                    }
                })
        return sync_callback

    # Agent node wrappers - pass coordinator to agent functions
    def planner_node(self, state: State):
        return planner_node(self, state)
    
    def identifier_node(self, state: State):
        return identifier_node(self, state)
    
    def validator_node(self, state: State):
        return validator_node(self, state)
    
    def planner_tools_node(self, state: State):
        return planner_tools_node(self, state)
    
    def identifier_tools_node(self, state: State):
        return identifier_tools_node(self, state)
    
    def validator_tools_node(self, state: State):
        return validator_tools_node(self, state)

    # Routing wrappers
    def _route_messages_planner(self, state: State):
        return route_planner_messages(self, state)
        
    def _route_messages_identifier(self, state: State):
        return route_identifier_messages(self, state)
            
    def _route_messages_validator(self, state: State):
        return route_validator_messages(self, state)

    def _build_workflow(self):
        workflow = StateGraph(State)

        workflow.add_node("planner", self.planner_node)
        workflow.add_node("identifier", self.identifier_node)
        workflow.add_node("validator", self.validator_node)
        workflow.add_node("tools_planner", self.planner_tools_node)
        workflow.add_node("tools_identifier", self.identifier_tools_node)
        workflow.add_node("tools_validator", self.validator_tools_node)

        workflow.set_entry_point('planner')
        workflow.add_conditional_edges(
            "planner",
            self._route_messages_planner
        )
        workflow.add_conditional_edges(
            "identifier",
            self._route_messages_identifier
        )
        workflow.add_conditional_edges(
            "validator",
            self._route_messages_validator
        )
        workflow.add_edge("tools_planner", "planner")
        workflow.add_edge("tools_identifier", "identifier")
        workflow.add_edge("tools_validator", "validator")
        
        return workflow.compile()
    
    async def send_notification(self, message_type: str, data: Dict):
        """Send notification via callback if available"""
        if self.notification_callback:
            await self.notification_callback(self.file_id, {
                'type': message_type,
                'data': data,
            })
    
    async def send_pending_llm_notifications(self):
        """Send any pending LLM interaction notifications"""
        if hasattr(self, 'pending_llm_notifications') and self.pending_llm_notifications:
            notifications_to_send = self.pending_llm_notifications.copy()
            self.pending_llm_notifications.clear()
            
            for notification in notifications_to_send:
                await self.send_notification(notification['type'], notification['data'])
                
    async def send_pending_view_sync_notifications(self):
        """Send any pending plot view sync notifications"""
        if hasattr(self, 'pending_view_sync_notifications') and self.pending_view_sync_notifications:
            notifications_to_send = self.pending_view_sync_notifications.copy()
            self.pending_view_sync_notifications.clear()
            
            for notification in notifications_to_send:
                await self.send_notification(notification['type'], notification['data'])
    
    async def run(self):
        """Run the event detection workflow"""
        print("Starting fresh event detection workflow...")
        
        await self.send_notification('detection_started', {
            'message': 'Starting multi-agent event detection...'
        })
        
        workflow = self._build_workflow()
        init_plot = self.plot_viewer_planner.plot_all()
        init_plot_message = utils.process_tool_message(init_plot, 'plot_all()')
        
        # Create event list from project classes
        events_list = []
        if self.project_info and 'classes' in self.project_info:
            events_list = [cls['name'] for cls in self.project_info['classes']]
        events_list_str = ', '.join(events_list) if events_list else "No events defined"
        
        # Extract general pattern description from project
        general_description = ""
        if self.project_info and 'general_pattern_description' in self.project_info:
            general_description = self.project_info['general_pattern_description']
        if not general_description:
            general_description = "No general project context provided."
        
        # Create patterns text from project classes
        patterns_text = ""
        if self.project_info and 'classes' in self.project_info:
            pattern_parts = []
            for cls in self.project_info['classes']:
                pattern_parts.append(f"**{cls['name']}**:")
                if cls.get('description'):
                    pattern_parts.append(f"  {cls['description']}")
                else:
                    pattern_parts.append(f"  No description provided")
                pattern_parts.append("")  # Empty line
            patterns_text = "\n".join(pattern_parts)
        
        init_message = pt.PLANNER_INIT_MESSAGE.format(
            general_description=general_description,
            patterns=patterns_text,
            statistics=self.stat,
            events_list=events_list_str,
        )
        print('-------- PLANNER INIT ---------')
        print(init_message)
        
        state: State = {
            'planner_messages': [HumanMessage(init_message)] + init_plot_message,
            'identifier_messages': [],
            'validator_messages': [],
            'communication': None,
            'plan': [],
            'detected_events': [],
            'token_usage': 0,
        }

        try:
            await self.send_notification('analysis_started', {
                'message': 'Multi-agent analysis started...'
            })
            
            for chunk in workflow.stream(state, {"recursion_limit": 10}, stream_mode='updates'):
                # Send any pending LLM notifications
                await self.send_pending_llm_notifications()
                
                # Send any pending view sync notifications
                await self.send_pending_view_sync_notifications()
                
                # Send periodic updates
                await self.send_notification('analysis_progress', {
                    'message': 'Analysis in progress...',
                    'token_usage': state.get('token_usage', 0)
                })
                await asyncio.sleep(0.1)  # Small delay for real-time updates
                
            # Send any remaining pending notifications
            await self.send_pending_llm_notifications()
            await self.send_pending_view_sync_notifications()
            
            # Check if we have final results
            if self.final_result:
                await self.send_notification('analysis_completed', {
                    'message': f'Multi-agent analysis completed. Found {len(self.final_result)} events.',
                    'events_found': len(self.final_result)
                })
                
                # Convert final results to database format and save
                await self._save_detected_events(self.final_result)
                
                await self.send_notification('detection_completed', {
                    'message': f'Auto-detection completed successfully! Detected and saved {len(self.final_result)} events.',
                    'total_events': len(self.final_result)
                })
                
                return {
                    'success': True,
                    'events_detected': len(self.final_result),
                    'final_result': self.final_result
                }
            else:
                await self.send_notification('detection_failed', {
                    'message': 'Auto-detection completed but no final results were produced.'
                })
                
                return {
                    'success': False,
                    'error': 'No final results produced'
                }
                
        except Exception as e:
            await self.send_notification('detection_failed', {
                'message': f'Auto-detection failed: {str(e)}'
            })
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _save_detected_events(self, detected_events: List[Dict]):
        """Save the detected events to the database"""
        try:
            from database import get_db
            from datetime import datetime, timezone
            from bson.objectid import ObjectId
            
            db = get_db()
            
            # Get current label info
            # First, find the file info to get the label ID
            file_info = db['files'].find_one({'_id': ObjectId(self.file_id)})
            if not file_info:
                raise ValueError("File not found")
                
            label_info = db['labels'].find_one({'_id': ObjectId(file_info['label'])})
            if not label_info:
                raise ValueError("Label not found")
            
            # Convert detected events to database format
            new_events = []
            for event in detected_events:
                # Map the event to the database format
                new_event = {
                    'className': event.get('event_name', 'Unknown'),
                    'color': self._get_class_color(event.get('event_name', 'Unknown')),
                    'description': f"Auto-detected: Multi-agent detection",
                    'labeler': 'AI Multi-Agent',
                    'start': int(event.get('start', 0)),
                    'end': int(event.get('end', 0)),
                    'hide': False,
                    'auto_detected': True
                }
                new_events.append(new_event)
            
            # Add events to existing events
            if 'events' not in label_info:
                label_info['events'] = []
            
            label_info['events'].extend(new_events)
            
            # Update database
            db['labels'].update_one(
                {'_id': ObjectId(file_info['label'])},
                {'$set': {'events': label_info['events']}}
            )
            
            # Update file metadata
            db['files'].update_one(
                {'_id': ObjectId(self.file_id)},
                {'$set': {
                    'lastModifier': 'AI Multi-Agent',
                    'lastUpdate': datetime.now(tz=timezone.utc)
                }}
            )
            
            await self.send_notification('events_saved', {
                'message': f'Successfully saved {len(new_events)} auto-detected events',
                'events_count': len(new_events)
            })
            
            return new_events
            
        except Exception as e:
            await self.send_notification('error', {
                'message': f'Failed to save events: {str(e)}'
            })
            raise
    
    def _get_class_color(self, class_name: str):
        """Get the color for a given class name"""
        if self.project_info and 'classes' in self.project_info:
            for cls in self.project_info['classes']:
                if cls['name'] == class_name:
                    return cls.get('color', '#FF6B6B')
        return '#FF6B6B'  # Default color


async def run_multi_agent_detection(file_id: str, df: pd.DataFrame, project_info=None, event_patterns=None, notification_callback=None):
    """Main entry point for running multi-agent auto-detection"""
    coordinator = AgentCoordinator(df, file_id, project_info, event_patterns, notification_callback)
    return await coordinator.run()

