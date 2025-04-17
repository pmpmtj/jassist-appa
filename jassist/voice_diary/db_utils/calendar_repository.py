import json
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("calendar_repository", module="db_utils")

@db_connection_handler
def save_calendar_event(conn, summary, start_datetime, end_datetime, location=None, description=None, 
                       start_timezone=None, end_timezone=None, attendees=None, recurrence=None, 
                       reminders=None, visibility=None, color_id=None, transparency=None, status=None):
    """
    Save a calendar event to the database
    
    Args:
        summary (str): Event summary/title
        start_datetime (str): Start date and time in ISO format
        end_datetime (str): End date and time in ISO format
        location (str, optional): Event location
        description (str, optional): Event description
        start_timezone (str, optional): Timezone for the start time
        end_timezone (str, optional): Timezone for the end time
        attendees (list, optional): List of attendees as dicts
        recurrence (list/str, optional): Recurrence rules 
        reminders (dict, optional): Reminder configuration
        visibility (str, optional): Event visibility
        color_id (str, optional): Color identifier
        transparency (str, optional): Whether event blocks time
        status (str, optional): Event status
        
    Returns:
        int: ID of the inserted record or None if error
    """
    # Convert complex objects to JSON strings
    if attendees and isinstance(attendees, list):
        attendees = json.dumps(attendees)
        
    if recurrence and isinstance(recurrence, list):
        recurrence = json.dumps(recurrence)
        
    if reminders and isinstance(reminders, dict):
        reminders = json.dumps(reminders)
    
    cur = conn.cursor()
    
    # Insert event
    cur.execute("""
    INSERT INTO calendar_events 
    (summary, location, description, start_dateTime, start_timeZone, 
    end_dateTime, end_timeZone, attendees, recurrence, reminders,
    visibility, colorId, transparency, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """, (summary, location, description, start_datetime, start_timezone, 
          end_datetime, end_timezone, attendees, recurrence, reminders,
          visibility, color_id, transparency, status))
    
    event_id = cur.fetchone()[0]
    
    conn.commit()
    logger.info(f"Saved calendar event with ID: {event_id}")
    return event_id


@db_connection_handler
def get_events_by_date_range(conn, start_date, end_date, limit=50):
    """
    Retrieve calendar events within a date range
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of calendar event records as dictionaries
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
    SELECT *
    FROM calendar_events
    WHERE start_dateTime >= %s AND start_dateTime <= %s
    ORDER BY start_dateTime ASC
    LIMIT %s
    """, (start_date, end_date, limit))
    
    results = cur.fetchall()
    return results

@db_connection_handler
def get_upcoming_events(conn, limit=10):
    """
    Retrieve upcoming calendar events
    
    Args:
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of calendar event records as dictionaries
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
    SELECT *
    FROM calendar_events
    WHERE start_dateTime >= CURRENT_TIMESTAMP
    ORDER BY start_dateTime ASC
    LIMIT %s
    """, (limit,))
    
    results = cur.fetchall()
    return results

@db_connection_handler
def get_calendar_events_by_config_interval(conn):
    """
    Retrieve calendar events from the database based on a default date interval
    
    Returns:
        list: List of calendar event records as dictionaries
    """
    try:
        # Use current date for default values
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Format dates for query
        start_date = yesterday.strftime("%Y-%m-%dT00:00:00")
        end_date = tomorrow.strftime("%Y-%m-%dT23:59:59")
        
        # Default query limit
        query_limit = 100
        
        # Query events within the date range
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # psycopg2 will handle the conversion of ISO strings to proper timestamp values
        cur.execute("""
        SELECT *
        FROM calendar_events
        WHERE start_dateTime >= %s AND start_dateTime <= %s
        ORDER BY start_dateTime ASC
        LIMIT %s
        """, (start_date, end_date, query_limit))
        
        results = cur.fetchall()
        
        logger.info(f"Retrieved {len(results)} calendar events between {start_date} and {end_date} (limit: {query_limit})")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving calendar events by default interval: {str(e)}")
        return []

@db_connection_handler
def update_calendar_event(conn, event_id, **kwargs):
    """
    Update a calendar event
    
    Args:
        event_id (int): ID of the event to update
        **kwargs: Fields to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Process complex objects
    if 'attendees' in kwargs and isinstance(kwargs['attendees'], list):
        kwargs['attendees'] = json.dumps(kwargs['attendees'])
        
    if 'recurrence' in kwargs and isinstance(kwargs['recurrence'], list):
        kwargs['recurrence'] = json.dumps(kwargs['recurrence'])
        
    if 'reminders' in kwargs and isinstance(kwargs['reminders'], dict):
        kwargs['reminders'] = json.dumps(kwargs['reminders'])
    
    # Build the update query dynamically based on provided fields
    fields = []
    values = []
    
    for key, value in kwargs.items():
        fields.append(f"{key} = %s")
        values.append(value)
        
    if not fields:
        logger.warning("No fields to update")
        return False
        
    values.append(event_id)  # For the WHERE clause
    
    query = f"""
    UPDATE calendar_events
    SET {", ".join(fields)}
    WHERE id = %s
    """
    
    cur = conn.cursor()
    cur.execute(query, values)
    
    rows_affected = cur.rowcount
    conn.commit()
    
    logger.info(f"Updated calendar event ID {event_id}, {rows_affected} rows affected")
    return rows_affected > 0

@db_connection_handler
def delete_calendar_event(conn, event_id):
    """
    Delete a calendar event
    
    Args:
        event_id (int): ID of the event to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    cur = conn.cursor()
    
    cur.execute("""
    DELETE FROM calendar_events
    WHERE id = %s
    """, (event_id,))
    
    rows_affected = cur.rowcount
    conn.commit()
    
    logger.info(f"Deleted calendar event ID {event_id}, {rows_affected} rows affected")
    return rows_affected > 0 