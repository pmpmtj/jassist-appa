"""
Calendar processor module.

This module processes calendar entries and inserts them into 
the database and Google Calendar.
"""

from typing import Dict, Any, Optional, Tuple
from .llm.openai_client import process_with_openai_assistant
from .utils.json_extractor import extract_json_from_text
from .db.calendar_db import save_calendar_event
from .google_calendar import insert_event_into_google_calendar
from .utils.config_manager import load_calendar_config
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("calendar_processor", module="calendar")

def process_calendar_entry(text: str, db_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a voice entry for a calendar event.
    
    Args:
        text: The voice entry text
        db_id: Optional ID of the database record this is associated with
        
    Returns:
        Tuple containing (success status, event data)
    """
    try:
        logger.info("Processing calendar entry")
        
        # Process with OpenAI to extract calendar event data
        response = process_with_openai_assistant(text)
        
        # Extract JSON from response
        event_data = extract_json_from_text(response)
        if not event_data:
            logger.error("Failed to extract JSON from LLM response")
            return False, None
        
        # Save to database
        event_id = save_calendar_event(
            summary=event_data.get("summary"),
            start_datetime=event_data.get("start", {}).get("dateTime"),
            end_datetime=event_data.get("end", {}).get("dateTime"),
            location=event_data.get("location"),
            description=event_data.get("description"),
            start_timezone=event_data.get("start", {}).get("timeZone"),
            end_timezone=event_data.get("end", {}).get("timeZone"),
            attendees=event_data.get("attendees"),
            recurrence=event_data.get("recurrence"),
            reminders=event_data.get("reminders"),
            visibility=event_data.get("visibility"),
            color_id=event_data.get("colorId"),
            transparency=event_data.get("transparency"),
            status=event_data.get("status")
        )
        
        if not event_id:
            logger.error("Failed to save event to database")
            return False, event_data
        
        # Insert into Google Calendar
        link = insert_event_into_google_calendar(event_data)
        if link:
            logger.info(f"Google Calendar event created at: {link}")
            event_data["google_calendar_link"] = link
        else:
            logger.warning("Google Calendar event creation failed")
        
        return True, event_data
        
    except Exception as e:
        logger.exception(f"Error during calendar processing: {e}")
        return False, None 