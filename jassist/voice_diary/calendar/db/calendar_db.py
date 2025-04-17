"""
Database operations for calendar events.

This module handles database operations specific to calendar events.
"""

import json
from typing import Dict, Any, Optional, List
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("calendar_db", module="calendar")

def save_calendar_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    start_timezone: Optional[str] = None,
    end_timezone: Optional[str] = None,
    attendees: Optional[List[Dict[str, Any]]] = None,
    recurrence: Optional[List[str]] = None,
    reminders: Optional[Dict[str, Any]] = None,
    visibility: Optional[str] = None,
    color_id: Optional[str] = None,
    transparency: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[int]:
    """
    Save a calendar event to the database.
    
    Args:
        summary: Event title/summary
        start_datetime: Start date and time in ISO format
        end_datetime: End date and time in ISO format
        location: Event location
        description: Event description
        start_timezone: Timezone for start time
        end_timezone: Timezone for end time
        attendees: List of attendees
        recurrence: Recurrence rules
        reminders: Reminder configuration
        visibility: Event visibility
        color_id: Event color
        transparency: Whether event blocks time
        status: Event status
        
    Returns:
        int: ID of the saved event, or None if save failed
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_calendar_event as db_save_calendar_event
        
        # Note: JSON conversion is now handled inside db_manager.save_calendar_event
        
        # Call the database function - notice we don't pass a connection parameter
        event_id = db_save_calendar_event(
            summary=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=location,
            description=description,
            start_timezone=start_timezone,
            end_timezone=end_timezone,
            attendees=attendees,
            recurrence=recurrence,
            reminders=reminders,
            visibility=visibility,
            color_id=color_id,
            transparency=transparency,
            status=status
        )
        
        if event_id:
            logger.info(f"Successfully saved calendar event with ID: {event_id}")
        else:
            logger.error("Failed to save calendar event to database")
            
        return event_id
        
    except Exception as e:
        logger.exception(f"Error saving calendar event to database: {e}")
        return None

def get_upcoming_events(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get upcoming calendar events.
    
    Args:
        limit: Maximum number of events to retrieve
        
    Returns:
        List of calendar events
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import get_upcoming_events as db_get_upcoming_events
        
        # Call the function without a connection parameter
        events = db_get_upcoming_events(limit=limit)
        return events
    except Exception as e:
        logger.exception(f"Error getting upcoming events: {e}")
        return []

def get_events_by_date_range(start_date: str, end_date: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get calendar events within a date range.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        limit: Maximum number of events to retrieve
        
    Returns:
        List of calendar events
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import get_events_by_date_range as db_get_events_by_date_range
        
        # Call the function without a connection parameter
        events = db_get_events_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return events
    except Exception as e:
        logger.exception(f"Error getting events by date range: {e}")
        return [] 