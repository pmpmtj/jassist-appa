"""
Test script for Google Calendar integration.
"""
import logging
import datetime
from pathlib import Path

from jassist.voice_diary.calendar.google_calendar import (
    get_calendar_service, 
    insert_event_into_google_calendar, 
    get_credentials_path
)

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def main():
    print("Testing Google Calendar integration...")
    
    # Check credentials path
    credentials_path = get_credentials_path()
    print(f"Credentials path: {credentials_path}")
    
    token_path = credentials_path / "token.json"
    cred_path = credentials_path / "credentials.json"
    
    print(f"Token file exists: {token_path.exists()}")
    print(f"Credentials file exists: {cred_path.exists()}")
    
    # Create a test event
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(hours=1)
    
    event = {
        'summary': 'Test Calendar Event',
        'location': 'Virtual Meeting',
        'description': 'This is a test event created by the test script.',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Lisbon',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Lisbon',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    try:
        # Get authenticated service
        print("\nAttempting to get calendar service...")
        service = get_calendar_service()
        print("Calendar service obtained successfully!")
        
        # Insert event
        print("\nAttempting to insert event...")
        event_link = insert_event_into_google_calendar(event)
        if event_link:
            print(f"Event created successfully: {event_link}")
        else:
            print("Failed to create event.")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 