"""
Database Manager Module

This module serves as a facade for the database components.
It provides a centralized interface to the database operations.
"""

from jassist.voice_diary.db_utils.db_connection import (
    initialize_db, 
    close_all_connections
)
from jassist.voice_diary.db_utils.db_schema import create_tables
from jassist.voice_diary.db_utils.transcription_repository import (
    save_transcription,
    get_transcription,
    get_latest_transcriptions,
    get_transcriptions_by_date_range
)
from jassist.voice_diary.db_utils.summary_repository import (
    save_day_summary,
    get_day_summaries_by_date_range,
    get_latest_day_summaries,
    check_summary_exists
)
from jassist.voice_diary.db_utils.calendar_repository import (
    save_calendar_event,
    get_events_by_date_range,
    get_upcoming_events,
    get_calendar_events_by_config_interval,
    update_calendar_event,
    delete_calendar_event
)
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("db_manager", module="db_utils")

# Re-export initialize_db to maintain backward compatibility
__all__ = [
    # Connection management
    'initialize_db',
    'close_all_connections',
    'create_tables',
    
    # Transcription operations
    'save_transcription',
    'get_transcription',
    'get_latest_transcriptions',
    'get_transcriptions_by_date_range',
    
    # Summary operations
    'save_day_summary',
    'get_day_summaries_by_date_range',
    'get_latest_day_summaries',
    'check_summary_exists',
    
    # Calendar operations
    'save_calendar_event',
    'get_events_by_date_range',
    'get_upcoming_events',
    'get_calendar_events_by_config_interval',
    'update_calendar_event',
    'delete_calendar_event'
]
