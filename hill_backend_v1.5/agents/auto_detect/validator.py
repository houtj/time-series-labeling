"""
Validator Agent - Handles event validation tasks
"""

from langgraph.graph import END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command

from . import prompts as pt
from . import utils
from .models import ValidatorResponseFormatter, ValidatorTask


def validator_node(coordinator, state):
    """Validator agent node - handles event validation tasks"""
    system_prompt = pt.VALIDATOR_SYSTEM_PROMPT
    prompt_template = ChatPromptTemplate([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])
    communication = state.get('communication')
    
    # Initialize variables that might be used in error handling
    messages = state.get('validator_messages', [])
    token_usage = state.get('token_usage', 0)
    
    # If handed over from planner
    if communication is not None:
        detected_events = state.get('detected_events')
        instruction_from_planner: ValidatorTask = communication.get('message')
        
        # Extract task_id
        task_id = instruction_from_planner.get('task_id')
        
        # Extract events to verify by event_ids and get their full details
        event_ids_to_verify = instruction_from_planner.get('events_to_verify', [])
        events_to_verify_details = []
        
        for event_id in event_ids_to_verify:
            for event in detected_events:
                if event.get('event_id') == event_id:
                    events_to_verify_details.append(event)
                    break
            else:
                print(f'Error: event {event_id} not found in detected_events')
                return Command(update={
                    'validator_messages': messages+[AIMessage(content=f"Error: event {event_id} not found in detected_events. Please revise your response to take an actionable step.")],
                    'communication': None,
                    'current_agent': 'validator',
                    'token_usage': token_usage
                })
        
        events_to_validate_display = f"{len(events_to_verify_details)} events: {', '.join([e.get('event_name', 'unknown') for e in events_to_verify_details])}"
        
        # Get patterns for events to validate based on their event names
        event_names = list(set([event.get('event_name') for event in events_to_verify_details if event.get('event_name')]))
        patterns = []
        if coordinator.event_patterns:
            for event_name in event_names:
                if event_name in coordinator.event_patterns:
                    patterns.append(f"**{event_name}**: {coordinator.event_patterns[event_name]}")
        patterns_text = "\n".join(patterns) if patterns else "No specific patterns provided"
        
        if instruction_from_planner.get('instructions') and instruction_from_planner.get('potential_windows'):
            instructions = instruction_from_planner['instructions']
            potential_windows = instruction_from_planner['potential_windows']
        else:
            instructions = "No specific instructions"
            potential_windows = "None"
        
        # Create validation criteria based on event patterns
        validation_criteria = """
        1. Sequential Rules: Check temporal ordering of events
        2. Occurrence Constraints: Verify single vs. multiple occurrence rules
        3. Context Dependencies: Ensure events occur within required contexts
        4. Pattern Completeness: Confirm full visual patterns are observed
        """
        
        message = pt.VALIDATOR_INIT_MESSAGE.format(
            patterns=patterns_text,
            statistics=coordinator.stat,
            validation_criteria=validation_criteria,
            task_id=task_id,
            events_to_validate=events_to_validate_display,
            events_details=events_to_verify_details,
            instructions=instructions,
            potential_windows=potential_windows
        )
        init_plot = coordinator.plot_viewer_validator.plot_all()
        init_plot_message = utils.process_tool_message(init_plot, 'plot_all()')
        messages = [HumanMessage(message)] + init_plot_message
        print('------- RECEIVED BY VALIDATOR ---------')
        print(message)
    # else: messages is already initialized from state.get('validator_messages', [])
        
    chain = prompt_template | coordinator.llm_validator
    response, token_usage = coordinator._invoke_llm(messages, chain)
    token_usage = state.get('token_usage') + token_usage
    
    # Send LLM interaction to frontend immediately
    coordinator._send_llm_interaction_sync('Validator', messages, response, token_usage)
    
    print('------ VALIDATOR -------')
    print(f'TOKEN USAGE: {token_usage}')
    response: ValidatorResponseFormatter = response['parsed']
    print(response.raw_message)
    
    tool_match = hasattr(response, 'tool_call') and response.tool_call is not None
    if tool_match:
        print(f'tool_call: {response.tool_call}')
        return Command(update={
            'validator_messages': messages+[AIMessage(content=response.raw_message, tool_call=response.tool_call)],
            'communication': None,
            'current_agent': 'validator',
            'token_usage': token_usage
        })
    
    ## if VALIDATOR_RESULT in response
    result_match = hasattr(response, 'task_result') and response.task_result is not None
    if result_match:
        task_result = response.task_result
        print(f"validation result: {task_result}")
        print(f'----- POST-PROCESSING VALIDATOR RESULTS ------')
        
        # Post-process the results: apply validation changes to detected_events and mark task as done
        detected_events = state.get('detected_events', [])
        current_plan = state.get('plan', [])
        
        # Apply validation changes if task completed successfully
        if task_result.status and task_result.validation_results:
            for validation in task_result.validation_results:
                event_id = validation.event_id
                remove = validation.remove
                
                # Find the event in detected_events
                event_found = False
                for event in detected_events:
                    if event.get('event_id') == event_id:
                        event_found = True
                        # Update event properties regardless of remove decision
                        event['need_verification'] = False
                        event['verification_result'] = 'remove' if remove else 'keep'
                        break
                
                if not event_found:
                    print(f'Warning: event {event_id} not found in detected_events')
                    return Command(update={
                        'validator_messages': messages+[AIMessage(content=f"Error: event {event_id} not found in detected_events. Please revise your response to take an actionable step.")],
                        'communication': None,
                        'current_agent': 'validator',
                        'token_usage': token_usage
                    })
                
        
        # Mark the task as done in the plan
        task_id = task_result.task_id
        for plan_item in current_plan:
            if plan_item.get('task_id') == task_id:
                plan_item['is_done'] = True
                break
        else:
            print(f'Error: task {task_id} not found in plan')
            return Command(update={
                'validator_messages': messages+[AIMessage(content=f"Error: task {task_id} not found in plan. Please revise your response to take an actionable step.")],
                'communication': None,
                'current_agent': 'validator',
                'token_usage': token_usage
            })
        
        print(f'----- HANDOVER TO PLANNER ------')
        task_result_dict = response.task_result.model_dump()
        task_result_dict['from'] = 'validator'
        
        return Command(update={
            'validator_messages': messages+[AIMessage(content=response.raw_message)],
            'communication': {'from': 'verification', 'to': 'planner', 'message': task_result_dict},
            'detected_events': detected_events,
            'plan': current_plan,
            'current_agent': 'validator',
            'token_usage': token_usage
        })
    else:
        print(f'Error: no tool call or task result')
        return Command(update={
            'validator_messages': messages+[AIMessage(content=response.raw_message+"\nNo tool call, task result was found in the validator's response. The LLM must either call a tool, or return a task result.")],
            'communication': None,
            'current_agent': 'validator',
            'token_usage': token_usage
        })


def validator_tools_node(coordinator, state):
    """Handle tool calls for validator agent"""
    validator_messages = state.get('validator_messages')
    last_message = validator_messages[-1]
    tool_calls = last_message.tool_call
    if 'plot_window' in tool_calls:
        for m in state.get('validator_messages'):
            if isinstance(m, HumanMessage) and hasattr(m, 'tool_call_function'):
                m.content = [i for i in m.content if i['type']=='text']
    try:
        tool_response = eval(f'coordinator.plot_viewer_validator.{tool_calls}')
    except Exception as err:
        tool_response = {'desc': f'There is error calling the function: {tool_calls}. The type of err is {type(err).__name__}. The message of error is {err}. Please revise your tool calling string.'}
    messages_processed = utils.process_tool_message(tool_response, tool_calls)
    print('------ VALIDATOR TOOL -------')
    print(messages_processed[0].content[0]['text'])
    return Command(update={
        "validator_messages": state.get('validator_messages') + messages_processed,
        "current_agent": "validator"
    })


def route_validator_messages(coordinator, state):
    """Route messages for validator agent"""
    token_usage = state.get('token_usage')
    if token_usage > 2000000:
        return END
    communication = state.get('communication')
    last_message = state.get('validator_messages')[-1]
    tool_match = hasattr(last_message, 'tool_call') and last_message.tool_call is not None
    if tool_match:
        return "tools_validator"
    if communication is not None:
        to = communication.get('to')
        if to == 'planner':
            return 'planner'
        else:
            return "validator"
    else:
        return "validator"

