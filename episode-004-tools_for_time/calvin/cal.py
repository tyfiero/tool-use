from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from datetime import datetime, timedelta 
import pytz

console = Console()

TIME_ZONE = "America/Los_Angeles"  

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    # return the service object
    service = build('calendar', 'v3', credentials=creds)
    return service
class CalendarManager:
    def __init__(self, service):
        self.service = service
        self.TIME_ZONE = "America/Los_Angeles" 
    def create_event(self, summary, start_time, end_time, location=None, description=None):
        start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M") 
        end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M") 

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': self.TIME_ZONE,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': self.TIME_ZONE,
            },
        }

        if location:
            event['location'] = location
        if description:
            event['description'] = description

        event = self.service.events().insert(calendarId='primary', body=event).execute()
        
        table = Table(title="Event Created", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Summary", event.get("summary"))
        table.add_row("Start", event["start"]["dateTime"])
        table.add_row("End", event["end"]["dateTime"])
        if location:
            table.add_row("Location", location)
        if description:
            table.add_row("Description", description)
        table.add_row("Link", event.get("htmlLink"))
        
        console.print(table)
        
        return f'Event created: {event.get("summary")} starting at {event["start"]["dateTime"]}. Link: {event.get("htmlLink")}'

    def edit_event(self, event_id, summary=None, location=None, description=None):
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()

        if summary:
            event['summary'] = summary
        if location:
            event['location'] = location
        if description:
            event['description'] = description

        updated_event = self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        
        table = Table(title="Event Updated", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Summary", updated_event.get("summary"))
        table.add_row("Start", updated_event["start"]["dateTime"])
        table.add_row("End", updated_event["end"]["dateTime"])
        if location:
            table.add_row("Location", updated_event.get("location"))
        if description:
            table.add_row("Description", updated_event.get("description"))
        table.add_row("Link", updated_event.get("htmlLink"))
        
        console.print(table)
        
        return f'Event updated: {updated_event["htmlLink"]}'

    def search_events(self, query, max_results=10):
        time_min = datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(calendarId='primary', timeMin=time_min,
                                            maxResults=max_results, singleEvents=True,
                                            orderBy='startTime', q=query).execute()
        events = events_result.get('items', [])

        if not events:
            console.print(Panel("No upcoming events found.", title="Search Results", border_style="yellow"))
            return 'No upcoming events found.'
        
        table = Table(title=f"Search Results for '{query}'", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Start Time", style="green")
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            table.add_row(event['id'], event['summary'], start)
        
        console.print(table)
        
        return [{'id': event['id'], 'name': event['summary']} for event in events]

    def delete_event(self, event_id):
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        console.print(Panel(f"Event with ID {event_id} has been deleted.", title="Event Deleted", border_style="red"))
        return 'Event deleted'

    def create_multiple_events(self, events):
        created_events = []
        for event_data in events:
            result = self.create_event(**event_data)
            created_events.append(result)
        
        
        for event in created_events:
            parts = event.split(". Link: ")
            if len(parts) == 2:
                summary_and_start, link = parts
                summary, start_time = summary_and_start.split(" starting at ")
                summary = summary.split(": ")[1] 
        return f"{len(created_events)} events created successfully."

    def delete_multiple_events(self, event_ids):
        deleted_events = []
        failed_deletions = []

        for event_id in event_ids:
            try:
                self.service.events().delete(calendarId='primary', eventId=event_id).execute()
                deleted_events.append(event_id)
            except Exception as e:
                failed_deletions.append((event_id, str(e)))

        table = Table(title="Multiple Events Deleted", box=box.ROUNDED)
        table.add_column("Status", style="cyan")
        table.add_column("Event ID", style="magenta")
        table.add_column("Result", style="green")

        for event_id in deleted_events:
            table.add_row("Deleted", event_id, "Success")

        for event_id, error in failed_deletions:
            table.add_row("Failed", event_id, error)

        console.print(table)

        success_count = len(deleted_events)
        fail_count = len(failed_deletions)
        return f"{success_count} events deleted successfully. {fail_count} deletions failed."

    def get_free_time(self, start_date, end_date, day_start='08:00', day_end='22:00'):
        # Convert start_date and end_date to datetime objects
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get the timezone
        timezone = pytz.timezone(self.TIME_ZONE)
        
        free_time = {}

        while start <= end:
            date_str = start.strftime('%Y-%m-%d')
            day_start_time = timezone.localize(datetime.strptime(f"{date_str} {day_start}", '%Y-%m-%d %H:%M'))
            day_end_time = timezone.localize(datetime.strptime(f"{date_str} {day_end}", '%Y-%m-%d %H:%M'))

            # Get events for the day
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=day_start_time.isoformat(),
                timeMax=day_end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            # Initialize free time slots
            free_slots = [(day_start_time, day_end_time)]

            # Adjust free time based on events
            for event in events:
                event_start = self._parse_datetime(event['start'].get('dateTime', event['start'].get('date')))
                event_end = self._parse_datetime(event['end'].get('dateTime', event['end'].get('date')))
                
                new_free_slots = []
                for slot_start, slot_end in free_slots:
                    if event_start <= slot_start and event_end >= slot_end:
                        continue
                    elif event_start > slot_start and event_end < slot_end:
                        new_free_slots.append((slot_start, event_start))
                        new_free_slots.append((event_end, slot_end))
                    elif event_start <= slot_start < event_end:
                        new_free_slots.append((event_end, slot_end))
                    elif event_start < slot_end <= event_end:
                        new_free_slots.append((slot_start, event_start))
                    else:
                        new_free_slots.append((slot_start, slot_end))
                free_slots = new_free_slots

            # Consolidate free time slots
            if free_slots:
                free_time[date_str] = self._consolidate_slots(free_slots)

            start += timedelta(days=1)

        return self._format_free_time(free_time)

    def _consolidate_slots(self, slots):
        consolidated = []
        for slot in sorted(slots):
            if not consolidated or slot[0] - consolidated[-1][1] > timedelta(minutes=30):
                consolidated.append(slot)
            else:
                consolidated[-1] = (consolidated[-1][0], max(consolidated[-1][1], slot[1]))
        return consolidated

    def _format_free_time(self, free_time):
        formatted = []
        for date, slots in free_time.items():
            slot_strs = [f"{slot[0].strftime('%I:%M %p')} to {slot[1].strftime('%I:%M %p')}" for slot in slots]
            formatted.append(f"{date}: {' and '.join(slot_strs)}")
        return '\n'.join(formatted)

    def _parse_datetime(self, dt_string):
        dt = datetime.fromisoformat(dt_string.rstrip('Z'))
        if dt.tzinfo is None:
            return pytz.timezone(self.TIME_ZONE).localize(dt)
        return dt.astimezone(pytz.timezone(self.TIME_ZONE))

# This function creates and returns the CalendarManager instance
def get_calendar_manager():
    service = authenticate()
    return CalendarManager(service)

calendar_manager = get_calendar_manager()
