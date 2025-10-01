from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PlanItem(BaseModel):
    task_id: str = Field(description="unique identifier for the subtask")
    task_description: str = Field(description="concise description of what the subtask is about")
    task_type: str = Field(description="type of the subtask: identification or verification")
    is_done: bool = Field(description="True if the subtask is completed, False otherwise")

class IdentifierTask(BaseModel):
    task_id: str = Field(description="Unique identifier for the subtask")
    task_type: str = Field(description="type of the subtask: identification")
    instructions: List[str] = Field(description="Clear and actionable hints for this event. CRITICAL: Do NOT include any specific window ranges, index numbers, or time ranges in these instructions. Window ranges are provided separately in the 'potential_windows' field and will be processed before being sent to the agent. Only include pattern descriptions, visual characteristics, and identification guidance.")
    events_name: List[str] = Field(description="The names of the potential events to identify in the window.")
    potential_windows: List[List[int]] = Field(description="Potential windows to look into for the events. Each window should be a list of exactly two integers: [start_index, end_index].")

class ValidatorTask(BaseModel):
    task_id: str = Field(description="Unique identifier for the subtask")
    task_type: str = Field(description="type of the subtask: verification")
    instructions: List[str] = Field(description="Clear and actionable hints for validation.")
    events_to_verify: List[str] = Field(description="List of event_ids that need to be verified.")
    potential_windows: List[List[int]] = Field(description="Potential windows to focus on during validation. Each window should be a list of exactly two integers: [start_index, end_index].")

class EventItem(BaseModel):
    event_name: str = Field(description="name of the event identified.")
    start: int = Field(description="index of the starting point of the event")
    end: int = Field(description="Index of the ending point of the event")


class AdditionalInfo(BaseModel):
    """Container for planner's additional information - only one field should be populated at a time."""
    plan: Optional[List[PlanItem]] = Field(description="The ENTIRE plan made by the PLANNER agent. Only provide this when the entire plan is made, reviewed or updated.")
    identifier_task: Optional[IdentifierTask] = Field(description="The task assigned to identifier agent. Only provide this when assigning identification task.")
    validator_task: Optional[ValidatorTask] = Field(description="The task assigned to validator agent. Only provide this when assigning validation task.")
    final_result: Optional[List[EventItem]] = Field(description="Final output of detected. Only provide this field when returning the completed event detection result. IMPORTANT: You must detect ALL the events before returning this result. Do NOT return partial results.")

class PlannerResponseFormatter(BaseModel):
    """Always use this tool to structure your response."""
    raw_message: str = Field(description='The raw message given by llm.')
    tool_call: Optional[str] = Field(description='Python code string to call one of the tools. The code string will be executed directly with `eval()`. Only add this when tool calling is necessary.')
    additional_info: Optional[AdditionalInfo] = Field(description="Additional information for the planner. Only populate one field at a time to avoid returning all information simultaneously.")


# to_worker: Optional[bool] = Field(description="True if ready to assign the task to the worker agent (worker_task should not be None). False otherwise.")

class StatusEnum(Enum):
    completed = "completed"
    failed = "failed"

class EventFoundItem(BaseModel):
    event_id: str = Field(description="Unique identifier for this event (e.g., event_name_startindex_endindex)")
    event_name: str = Field(description="Name of the event in lowercase. The event should satisfy the visual pattern.")
    start_index: int = Field(description="Starting index of the event")
    end_index: int = Field(description="Ending index of the event")
    visual_pattern: str = Field(description="consise description of visual pattern")
    need_verification: bool = Field(description="True if the event needs verification for the interdependencies, False otherwise")
    verification_guidance: str = Field(description="If the event needs verification, provide a guidance for the planner agent. Specify after idenfitying which interdependent events, the verification should be performed.")
    verification_result: str = Field(description="The result of verification if the event needs verification. If the event has not been verified, return 'not verified'. If the event is verified, return 'keep' or 'remove'.")

class IdentifierTaskResult(BaseModel):
    task_id: str = Field(description="The unique id of the task received from the planner agent.")
    status: bool = Field(description="True if the task is completed, False otherwise")
    events_found: List[EventFoundItem] = Field(description="The events founded by the WORKER agent")
    recommendations: str = Field(description="suggestions for the planner agent")

class IdentifierResponseFormatter(BaseModel):
    """Always use this tool to structure your response."""
    raw_message: str = Field(description='The raw message given by llm.')
    tool_call: Optional[str] = Field(description='Python code string to call one of the tools. The code string will be executed directly with `eval()`. Only add this when tool calling is necessary.')
    task_result: Optional[IdentifierTaskResult] = Field(description="The result of event identification task. Only add this at the last step of the task as a summary of the events identified.")


# to_planner: Optional[bool] = Field(description="True if ready to send the result to the planner agent (task_result should not be None). False otherwise")

class ValidationResult(BaseModel):
    event_id: str = Field(description="Unique identifier of the event being validated")
    remove: bool = Field(description="True if the event should be removed, False otherwise")

class ValidatorTaskResult(BaseModel):
    task_id: str = Field(description="The unique id of the validation task received from the planner agent.")
    status: bool = Field(description="True if the validation task is completed, False otherwise")
    validation_results: List[ValidationResult] = Field(description="The validation results for each event examined")
    recommendations: str = Field(description="Suggestions for the planner agent")

class ValidatorResponseFormatter(BaseModel):
    """Always use this tool to structure your response."""
    raw_message: str = Field(description='The raw message given by llm.')
    tool_call: Optional[str] = Field(description='Python code string to call one of the tools. The code string will be executed directly with `eval()`. Only add this when tool calling is necessary.')
    task_result: Optional[ValidatorTaskResult] = Field(description="The result of validation task. Only add this at the last step of the task as a summary of the validation results.")

