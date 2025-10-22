"""
Planner Agent - Handles planning and coordination logic
"""

from langgraph.graph import END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command
import json

from . import prompts as pt
from . import utils
from .models import PlannerResponseFormatter, IdentifierTaskResult, ValidatorTaskResult, IdentifierTask, ValidatorTask


def planner_node(coordinator, state):
    """Planner agent node - handles planning and result processing from other agents"""
    communication = state.get('communication')
    system_prompt = pt.PLANNER_SYSTEM_PROMPT
    prompt_template = ChatPromptTemplate([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])
    current_messages = state.get("planner_messages")
    
    ## if the agent is switched from worker to planner
    if communication is not None:
        detected_events = state.get('detected_events')
        current_plan = state.get('plan')
        message_from_agent = state.get('communication')
        
        ### add last communication to message.
        if message_from_agent.get('from') == 'identification':
            identifier_result: IdentifierTaskResult = communication.get('message')
            task_id = identifier_result.get('task_id')
            events_count = len(identifier_result.get('events_found', []))
            
            message = f"""The identifier completed task {task_id}. Added {events_count} new events. 
            The current detected events are: {detected_events}. 
            Current plan status: {current_plan}
            If all the tasks are done, return the final result. Otherwise, you need to provide instruction to the identifier or validator for the next step.
            If needed, you can make adjustments to the plan by adding/modifying/removing unfinished tasks."""
            messages = current_messages + [HumanMessage(message)]
            print('-------- RECEIVED BY PLANNER --------')
            print(message)
            
        elif message_from_agent.get('from') == 'verification':
            validator_result: ValidatorTaskResult = communication.get('message')
            task_id = validator_result.get('task_id')
            
            message = f"""The validator completed task {task_id}. Applied validation changes. 
            The current detected events are: {detected_events}. 
            Current plan status: {current_plan}
            If all the tasks are done, return the final result. Otherwise, you need to provide instruction to the identifier or validator for the next step.
            If needed, you can make adjustments to the plan by adding/modifying/removing unfinished tasks."""
            messages = current_messages + [HumanMessage(message)]
            print('-------- RECEIVED BY PLANNER --------')
            print(message)
    else:
        messages = current_messages
    chain = prompt_template | coordinator.llm_planner
    response, token_usage = coordinator._invoke_llm(messages, chain)
    token_usage = state.get('token_usage') + token_usage
    
    # Send LLM interaction to frontend immediately
    coordinator._send_llm_interaction_sync('Planner', messages, response, token_usage)
    
    print('------ PLANNER -------')
    print(f'TOKEN USAGE: {token_usage}')
    response: PlannerResponseFormatter = response['parsed']
    print(response.raw_message)
    
    tool_match = hasattr(response, 'tool_call') and response.tool_call is not None
    if tool_match:
        print(f'tool_call: {response.tool_call}')
        return Command(update={
            'planner_messages': messages+[AIMessage(content=response.raw_message, tool_call=response.tool_call)],
            'communication': None,
            'current_agent': 'planner',
            'token_usage': token_usage
        })
    
    additional_info_match = hasattr(response, 'additional_info') and response.additional_info is not None
    if additional_info_match:
        additional_info = response.additional_info
        
        # Handle final result
        if additional_info.final_result is not None:
            # Perform final validation checks
            plan = state.get('plan', [])
            detected_events = state.get('detected_events', [])
            
            # Check 1: All tasks completed
            incomplete_tasks = [p for p in plan if not p.get('is_done', False)]
            if incomplete_tasks:
                return Command(update={
                    'planner_messages': messages+[AIMessage(content=f"Error: Cannot finalize results. Incomplete tasks remain: {incomplete_tasks}. Please complete all tasks first.")],
                    'communication': None,
                    'current_agent': 'planner',
                    'token_usage': token_usage
                })
            
            # Check 2: All events have need_verification=False
            events_needing_verification = [e for e in detected_events if e.get('need_verification', True)]
            if events_needing_verification:
                return Command(update={
                    'planner_messages': messages+[AIMessage(content=f"Error: Cannot finalize results. Some events still need verification: {[e.get('event_id', 'unknown') for e in events_needing_verification]}. Please validate all events first.")],
                    'communication': None,
                    'current_agent': 'planner',
                    'token_usage': token_usage
                })
            
            final_result = [r.model_dump() for r in additional_info.final_result]
            print(f'detected events: {detected_events}')
            print(f'final result: {final_result}')
            return Command(update={
                'planner_messages': messages+[AIMessage(content=response.raw_message, final_result=final_result)],
                'communication': None,
                'current_agent': 'planner',
                'token_usage': token_usage
            })
        
        # Handle plan updates
        elif additional_info.plan is not None:
            plan = [r.model_dump() for r in additional_info.plan]
            print(f'plan updated: {plan}')
            
            # Send plan update notification to frontend
            import asyncio
            asyncio.create_task(coordinator.send_notification('plan_updated', {
                'message': 'Planner has created/updated the plan',
                'plan': plan
            }))
            
            return Command(update={
                'planner_messages': messages+[AIMessage(content=response.raw_message), AIMessage(content=f"The plan is updated. The current plan is: {plan}. Please assign the task to the identifier or validator agent.")],
                'plan': plan,
                'communication': None,
                'current_agent': 'planner',
                'token_usage': token_usage
            })
        
        # Handle identifier task assignment
        elif additional_info.identifier_task is not None:
            task = additional_info.identifier_task.model_dump()
            if task.get('potential_windows'):
                task['potential_windows'] = [[w[0]-(w[1]-w[0])//2, w[1]+(w[1]-w[0])//2] for w in task['potential_windows']]
            
            # Check if the task's id is in the plan
            task_id = task.get('task_id')
            plan_task_ids = [p.get('task_id') for p in state.get('plan', []) if 'task_id' in p]
            if task_id not in plan_task_ids:
                print(f"Error: task_id '{task_id}' not found in plan")
                return Command(update={
                    'planner_messages': messages+[AIMessage(content=f"Warning: The assigned task (id: {task_id}) is not present in the plan. Please ensure every assigned task is included in the plan before handing over to the agent.")],
                    'communication': None,
                    'current_agent': 'planner',
                    'token_usage': token_usage
                })
            
            print(f'identifier task assigned: {task}')
            return Command(update={
                'planner_messages': messages+[AIMessage(content=response.raw_message)],
                'communication': {'from': 'planner','to': 'identification' ,'message': task},
                'current_agent': 'planner',
                'token_usage': token_usage
            })

        # Handle validator task assignment
        elif additional_info.validator_task is not None:
            task = additional_info.validator_task.model_dump()
            if task.get('potential_windows'):
                task['potential_windows'] = [[w[0]-(w[1]-w[0])//2, w[1]+(w[1]-w[0])//2] for w in task['potential_windows']]
            
            # Check if the task's id is in the plan
            task_id = task.get('task_id')
            plan_task_ids = [p.get('task_id') for p in state.get('plan', []) if 'task_id' in p]
            if task_id not in plan_task_ids:
                print(f"Error: task_id '{task_id}' not found in plan")
                return Command(update={
                    'planner_messages': messages+[AIMessage(content=f"Warning: The assigned task (id: {task_id}) is not present in the plan. Please ensure every assigned task is included in the plan before handing over to the agent.")],
                    'communication': None,
                    'current_agent': 'planner',
                    'token_usage': token_usage
                })
            
            print(f'validator task assigned: {task}')
            return Command(update={
                'planner_messages': messages+[AIMessage(content=response.raw_message)],
                'communication': {'from': 'planner','to': 'verification' ,'message': task},
                'current_agent': 'planner',
                'token_usage': token_usage
            })
    
    # No additional_info provided
    else:
        print(f'Error: no additional_info provided')
        return Command(update={
            'planner_messages': messages+[AIMessage(content=response.raw_message+"\nNo tool call or additional_info was found in the planner's response. The LLM must either call a tool or provide additional_info with plan/identifier_task/validator_task/final_result. Please revise your response to take an actionable step.")],
            'communication': None,
            'current_agent': 'planner',
            'token_usage': token_usage
        })


def planner_tools_node(coordinator, state):
    """Handle tool calls for planner agent"""
    planner_messages = state.get('planner_messages')
    last_message = planner_messages[-1]
    tool_calls = last_message.tool_call
    try:
        tool_response = eval(f'coordinator.plot_viewer_planner.{tool_calls}')
    except Exception as err:
        tool_response = {'desc': f'There is error calling the function: {tool_calls}. The type of err is {type(err).__name__}. The message of error is {err}. Please revise your tool calling string.'}
    messages_processed = utils.process_tool_message(tool_response, tool_calls)
    print('------ PLANNER TOOL -------')
    print(messages_processed[0].content[0]['text'])
    return Command(update={
        "planner_messages": state.get('planner_messages') + messages_processed,
        "current_agent": "planner"
    })


def route_planner_messages(coordinator, state):
    """Route messages for planner agent"""
    token_usage = state.get('token_usage')
    if token_usage > 500000:
        return END
    last_message = state.get('planner_messages')[-1]
    tool_match = hasattr(last_message, 'tool_call') and last_message.tool_call is not None
    if tool_match:
        return "tools_planner"
    final_match = (
        hasattr(last_message, 'final_result') 
        and last_message.final_result is not None 
    )
    if final_match:
        # Instead of writing to file, store result in coordinator for WebSocket notification
        coordinator.final_result = last_message.final_result
        return END
    if state.get('communication') is not None:
        # Determine which worker to route to based on task type
        communication = state.get('communication')
        to = communication.get('to')
        if to == 'verification':
            return "validator"
        else:
            return "identifier"
    else:
        return "planner"

