"""
Identifier Agent - Handles event identification tasks
"""

from langgraph.graph import END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command

from . import prompts as pt
from . import utils
from .models import IdentifierResponseFormatter, IdentifierTask


def identifier_node(coordinator, state):
    """Identifier agent node - handles event identification tasks"""
    communication = state.get('communication')
    system_prompt = pt.WORKER_SYSTEM_PROMPT
    prompt_template = ChatPromptTemplate([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # If handed over from planner
    if communication is not None:
        detected_events = state.get('detected_events')
        instruction_from_planner: IdentifierTask = communication.get('message')
        
        # Calculate values for template placeholders
        current_result_display = detected_events if detected_events else "None"
        total_events_count = len(detected_events) if detected_events else 0
        
        # Extract task_id
        task_id = instruction_from_planner.get('task_id')
        # Extract events to identify
        if instruction_from_planner.get('events_name'):
            events_to_identify = ', '.join(instruction_from_planner['events_name'])
        else:
            events_to_identify = "None"
        
        # Get patterns from the project's event patterns
        patterns = []
        if coordinator.event_patterns and instruction_from_planner.get('events_name'):
            for event_name in instruction_from_planner['events_name']:
                if event_name in coordinator.event_patterns:
                    patterns.append(f"**{event_name}**: {coordinator.event_patterns[event_name]}")
        patterns_text = "\n".join(patterns) if patterns else "No specific patterns provided"

        if instruction_from_planner.get('instructions') and instruction_from_planner.get('potential_windows'):
            instructions = instruction_from_planner['instructions']
            potential_windows = instruction_from_planner['potential_windows']
        else:
            instructions = "No specific instructions"
        message = pt.WORKER_INIT_MESSAGE.format(
            patterns=patterns_text,
            statistics=coordinator.stat,
            current_result_display=current_result_display,
            total_events_count=total_events_count,
            task_id=task_id,
            events_to_identify=events_to_identify,
            instructions=instructions,
            potential_windows=potential_windows
        )
        init_plot = coordinator.plot_viewer_identifier.plot_all()
        init_plot_message = utils.process_tool_message(init_plot, 'plot_all()')
        messages = [HumanMessage(message)] + init_plot_message
        print('------- RECEIVED BY IDENTIFIER ---------')
        print(message)
    else:
        # if not handed over from planner
        messages = state.get('identifier_messages')
        
    chain = prompt_template | coordinator.llm_identifier
    response, token_usage = coordinator._invoke_llm(messages, chain)
    token_usage = state.get('token_usage') + token_usage
    
    # Send LLM interaction to frontend immediately
    coordinator._send_llm_interaction_sync('Identifier', messages, response, token_usage)
    
    print('------ IDENTIFIER -------')
    print(f'TOKEN USAGE: {token_usage}')
    response: IdentifierResponseFormatter = response['parsed']
    print(response.raw_message)
    
    tool_match = hasattr(response, 'tool_call') and response.tool_call is not None
    if tool_match:
        print(f'tool_call: {response.tool_call}')
        return Command(update={
            'identifier_messages': messages+[AIMessage(content=response.raw_message, tool_call=response.tool_call)],
            'communication': None,
            'current_agent': 'identifier',
            'token_usage': token_usage
        })
    
    ## if IDENTIFIER_RESULT in response
    result_match = hasattr(response, 'task_result') and response.task_result is not None
    if result_match:
        task_result = response.task_result
        print(f"result: {task_result}")
        print(f'----- POST-PROCESSING IDENTIFIER RESULTS ------')
        
        # Post-process the results: update detected_events and plan
        detected_events = state.get('detected_events', [])
        current_plan = state.get('plan', [])
        
        # Add new events to detected_events if task completed successfully
        if task_result.status and task_result.events_found:
            for event in task_result.events_found:
                detected_events.append(event.model_dump())
        
        # Mark the task as done in the plan
        task_id = task_result.task_id
        for plan_item in current_plan:
            if plan_item.get('task_id') == task_id:
                plan_item['is_done'] = True
                
                # Send task completion notification to frontend
                import asyncio
                asyncio.create_task(coordinator.send_notification('task_completed', {
                    'message': f'Task completed: {plan_item.get("task_description", task_id)}',
                    'task_id': task_id,
                    'plan': current_plan
                }))
                break
        else:
            print(f'Error: task {task_id} not found in plan')
            return Command(update={
                'identifier_messages': messages+[AIMessage(content=f"Error: task {task_id} not found in plan. Please revise your response to take an actionable step.")],
                'communication': None,
                'current_agent': 'identifier',
                'token_usage': token_usage
            })
        
        print(f'----- HANDOVER TO PLANNER ------')
        task_result_dict = response.task_result.model_dump()
        
        return Command(update={
            'identifier_messages': messages+[AIMessage(content=response.raw_message)],
            'communication': {'from': 'identification', 'to': 'planner', 'message': task_result_dict},
            'detected_events': detected_events,
            'plan': current_plan,
            'current_agent': 'identifier',
            'token_usage': token_usage
        })
    else:
        print(f'Error: no tool call or task result')
        return Command(update={
            'identifier_messages': messages+[AIMessage(content=response.raw_message+"\nNo tool call, task result was found in the identifier's response. The LLM must either call a tool, or return a task result.")],
            'communication': None,
            'current_agent': 'identifier',
            'token_usage': token_usage
        })


def identifier_tools_node(coordinator, state):
    """Handle tool calls for identifier agent"""
    identifier_messages = state.get('identifier_messages')
    last_message = identifier_messages[-1]
    tool_calls = last_message.tool_call
    if 'plot_window' in tool_calls:
        for m in state.get('identifier_messages'):
            if isinstance(m, HumanMessage) and hasattr(m, 'tool_call_function'):
                m.content = [i for i in m.content if i['type']=='text']
    try:
        tool_response = eval(f'coordinator.plot_viewer_identifier.{tool_calls}')
    except Exception as err:
        tool_response = {'desc': f'There is error calling the function: {tool_calls}. The type of err is {type(err).__name__}. The message of error is {err}. Please revise your tool calling string.'}
    messages_processed = utils.process_tool_message(tool_response, tool_calls)
    print('------ IDENTIFIER TOOL -------')
    print(messages_processed[0].content[0]['text'])
    return Command(update={
        "identifier_messages": state.get('identifier_messages') + messages_processed,
        "current_agent": "identifier"
    })


def route_identifier_messages(coordinator, state):
    """Route messages for identifier agent"""
    token_usage = state.get('token_usage')
    if token_usage > 2000000:
        return END
    
    last_message = state.get('identifier_messages')[-1]
    tool_match = hasattr(last_message, 'tool_call') and last_message.tool_call is not None
    if tool_match:
        return "tools_identifier"
    communication = state.get('communication')
    if communication is not None:
        to = communication.get('to')
        if to == 'planner':
            return 'planner'
        else:
            return "identifier"
    else:
        return "identifier"

