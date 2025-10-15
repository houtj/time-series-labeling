from langchain_core.messages import ToolMessage, HumanMessage
import json

def process_tool_message(tool_response: dict, tool_calls: str):
    if tool_response.get('fig'):
        desc = tool_response['desc']
        img = tool_response['fig']
        human_message = HumanMessage(content=[
            {'type': 'text', 'text': desc},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
            ], tool_call_function=tool_calls)
    else:
        desc = tool_response['desc']
        human_message = HumanMessage(content=[
            {'type': 'text', 'text': desc},
        ])
    return [human_message]

