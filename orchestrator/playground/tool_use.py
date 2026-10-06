import json
import anthropic

from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# tool definitions
tools = [
    {
        "name": "create_calendar_event",
        "description": "create calendar event with attendees and optional recurrence",
        "input_schema": {
            "type": "object",
            "properties": {
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "string", "format": "email",
                    }
                },
                "recurrence": {
                    "type": "object",
                    "properties": {
                        "frequency": {"enum": ["daily", "weekly", "monthly"]},
                        "count": {"type": "integer", "minimum": 1},
                    }
                },
                "title": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
            },
            "required": ["title", "start", "end"],
        },
    },
    {
        "name": "list_calendar_events",
        "description": "list all calendar events on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
            },
            "required": ["date"],
        }
    }
]

# run the tool
def run_tool(name, tool_input):
    if name == "create_calendar_event":
        print(f"{name} called with: {tool_input}")
        return {"event_id": "event_1", "status": "created", "title": tool_input["title"] }
    if name == "list_calendar_events":
        print(f"{name} called with: {tool_input}")
        return { "events": [
                { "title": "Existing Meeting", "start": "08:00", "end": "09:00" },
                {"title": "Existing Meeting", "start": "10:00", "end": "11:00"},
                {"title": "Existing Meeting", "start": "12:00", "end": "13:00"},
            ]
        }
    return {"error": f"unknown tool: {name}"}

# keep full conversation history
messages = [
    {
        "role": "user",
        "content": "Check what I have on Monday, March 30, 2026, "
                   "then schedule a one-hour planning session that day "
                   "that avoids any conflicts."
    }
]

# call claude
response = client.messages.create(
    model = "claude-sonnet-haiku",
    max_tokens=1024,
    tools = tools,
    tool_choice={"type": "auto", "disabled_parallel_tool_use": True},
    messages=messages,
)

# loop while stop_reason is tool_use
while response.stop_reason == "tool_use":
    # single tool use
    '''
    print(" --- tool use ---")
    tool_use = next(block for block in response.content if block.type == "tool_use")
    result = run_tool(tool_use.name, tool_use.input)

    # append the result messages
    messages.append({"role": "assistant", "content": response.content})
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result),
                }
            ]
        }
    )

    response = client.messages.create(
        model="claude-sonnet-haiku",
        max_tokens=1024,
        tools=tools,
        tool_choice={"type": "auto", "disabled_parallel_tool_use": True},
        messages=messages,
    )
    '''

    # multiple tool use
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = run_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                }
            )

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})

    response = client.messages.create(
        model="claude-sonnet-haiku",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

final_text = next(block for block in response.content if block.type == "text")
print(final_text.text)