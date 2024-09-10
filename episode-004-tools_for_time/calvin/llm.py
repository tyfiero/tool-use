import datetime
import anthropic
from cal import calendar_manager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

client = anthropic.Anthropic()
console = Console()
tool_list =  [
    {
                "name": "create_event",
                "description": "Creates a new calendar event. This tool should be used when the user wants to add a new event to their calendar. It requires a summary (title), start time, and end time. Location and description are optional. The start_time and end_time should be provided in the format YYYY-MM-DD HH:MM. The tool will create the event in the user's primary calendar and return a confirmation message with the event details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Event title"},
                        "start_time": {"type": "string", "description": "Start time in format YYYY-MM-DD HH:MM"},
                        "end_time": {"type": "string", "description": "End time in format YYYY-MM-DD HH:MM"},
                        "location": {"type": "string", "description": "Event location"},
                        "description": {"type": "string", "description": "Event description"}
                    },
                    "required": ["summary", "start_time", "end_time"]
                }
            },
            {
                "name": "edit_event",
                "description": "Edits an existing calendar event. This tool should be used when the user wants to modify details of an event already in their calendar. It requires the event_id of the event to be edited. The user can update the summary (title), location, or description. The tool will only change the fields provided and leave others unchanged. It will return a confirmation message with the updated event details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event to edit"},
                        "summary": {"type": "string", "description": "New event title"},
                        "location": {"type": "string", "description": "New event location"},
                        "description": {"type": "string", "description": "New event description"}
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "search_events",
                "description": "Searches for calendar events based on a query. This tool should be used when the user wants to find events in their calendar matching certain criteria. It requires a search query and optionally allows specifying the maximum number of results to return. The tool will search event titles, descriptions, and locations for matches to the query. It returns a list of matching events with their IDs and titles.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "delete_event",
                "description": "Deletes a calendar event. This tool should be used when the user wants to remove an event from their calendar. It requires the event_id of the event to be deleted. The tool will permanently remove the specified event from the user's calendar and return a confirmation message. Use this tool with caution as the deletion cannot be undone.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event to delete"}
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "create_multiple_events",
                "description": "Creates multiple calendar events at once. This tool should be used when the user wants to add several events to their calendar in one go. It requires a list of events, where each event has a summary (title), start time, and end time. Location and description are optional for each event. The start_time and end_time should be provided in the format YYYY-MM-DD HH:MM for each event. The tool will create all events in the user's primary calendar and return a confirmation message with details of all created events.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string", "description": "Event title"},
                                    "start_time": {"type": "string", "description": "Start time in format YYYY-MM-DD HH:MM"},
                                    "end_time": {"type": "string", "description": "End time in format YYYY-MM-DD HH:MM"},
                                    "location": {"type": "string", "description": "Event location"},
                                    "description": {"type": "string", "description": "Event description"}
                                },
                                "required": ["summary", "start_time", "end_time"]
                            }
                        }
                    },
                    "required": ["events"]
                }
            },
            {
                "name": "delete_multiple_events",
                "description": "Deletes multiple calendar events at once. This tool should be used when the user wants to remove several events from their calendar in one go. It requires a list of event_ids to be deleted. The tool will permanently remove the specified events from the user's calendar and return a confirmation message. Use this tool with caution as the deletions cannot be undone.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of IDs of the events to delete"
                        }
                    },
                    "required": ["event_ids"]
                }
            },
            {
                "name": "get_free_time",
                "description": "Retrieves free time slots for a given date range. This tool should be used when the user wants to know their available time slots within a specific period. It requires a start date and an end date. Optionally, the user can specify the start and end times for each day. The tool will return a consolidated list of free time slots for each day in the given range.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date in format YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "End date in format YYYY-MM-DD"},
                        "day_start": {"type": "string", "description": "Optional. Start time of day in format HH:MM (24-hour)"},
                        "day_end": {"type": "string", "description": "Optional. End time of day in format HH:MM (24-hour)"}
                    },
                    "required": ["start_date", "end_date"]
                }
            }
]
def llm(conversation_history):
    now = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    system_message = f"You are a helpful calendar assistant. You can use these tools to manage the user's calendar: {', '.join([tool['name'] for tool in tool_list])}. If a user doesn't give you enough information, like a start time or end time, you are allowed to make assumptions, and fill in the blanks however you see fit. The user generally does NOT want to be asked for follow up questions, unless absolutely necessary. You can now create and delete multiple events at once using the create_multiple_events and delete_multiple_events tools. Today's date is: {now}."

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=system_message,
            tools=tool_list,
            messages=conversation_history
        )
        
        if response.stop_reason == "tool_use":
            for content in response.content:
                if content.type == "text":
                    md = Markdown(content.text)
                    console.print(Panel(md, title="[bold cyan]AI Assistant[/bold cyan]", border_style="cyan", box=box.ROUNDED))
                    console.print()
                if content.type == "tool_use":
                    tool_name = content.name
                    tool_input = content.input
                    tool_use_id = content.id
                    
                    intermediate_result = f"Using tool: {tool_name}\nInput: {tool_input}"
                    md = Markdown(intermediate_result)
                    console.print(Panel(md, title="[bold magenta]Tool Use[/bold magenta]", border_style="magenta", box=box.ROUNDED))
                    console.print()
                    
                    result = execute_tool(tool_name, tool_input)
                    
                    md = Markdown(result)
                    console.print(Panel(md, title="[bold green]Tool Result[/bold green]", border_style="green", box=box.ROUNDED))
                    console.print()
                    
                    conversation_history.append({"role": "assistant", "content": response.content})
                    conversation_history.append({"role": "user", "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        }
                    ]})
            
            # Continue the loop to allow for more tool calls
            continue
        else:
            # If no more tool calls are needed, break the loop
            break
    
    return response.content[0].text if response.content else "I apologize, but I couldn't generate a response."

def execute_tool(tool_name, tool_input):
    if tool_name == "create_event":
        return calendar_manager.create_event(**tool_input)
    elif tool_name == "edit_event":
        return calendar_manager.edit_event(**tool_input)
    elif tool_name == "search_events":
        return calendar_manager.search_events(**tool_input)
    elif tool_name == "delete_event":
        return calendar_manager.delete_event(**tool_input)
    elif tool_name == "create_multiple_events":
        return calendar_manager.create_multiple_events(**tool_input)
    elif tool_name == "delete_multiple_events":
        return calendar_manager.delete_multiple_events(**tool_input)
    elif tool_name == "get_free_time":
        return calendar_manager.get_free_time(**tool_input)
    else:
        return f"Error: Unknown tool '{tool_name}'"