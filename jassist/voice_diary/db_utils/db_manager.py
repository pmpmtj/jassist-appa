"""
Database Manager Module

This module serves as a facade for the database components.
It provides a centralized interface to the database operations.
"""

from jassist.voice_diary.db_utils.db_connection import (
    initialize_db, 
    close_all_connections,
    db_connection_handler
)
from jassist.voice_diary.db_utils.db_schema import create_tables
from jassist.voice_diary.db_utils.transcription_repository import (
    save_transcription,
    get_transcription,
    get_latest_transcriptions,
    get_transcriptions_by_date_range,
    mark_transcription_processed
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
from jassist.voice_diary.db_utils.diary_repository import (
    save_diary_entry,
    get_diary_entry
)
from jassist.voice_diary.db_utils.todo_repository import (
    save_todo_entry,
    get_todo_entry,
    update_todo_status
)
from jassist.voice_diary.db_utils.accounts_repository import (
    save_accounts_entry,
    get_accounts_entry,
    get_accounts_by_date_range,
    get_total_by_type
)
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("db_manager", module="db_utils")

# Re-export initialize_db to maintain backward compatibility
__all__ = [
    # Connection management
    'initialize_db',
    'close_all_connections',
    'create_tables',
    'db_connection_handler',
    
    # Transcription operations
    'save_transcription',
    'get_transcription',
    'get_latest_transcriptions',
    'get_transcriptions_by_date_range',
    'mark_transcription_processed',
    
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
    'delete_calendar_event',
    
    # Diary operations
    'save_diary_entry',
    'get_diary_entry',
    
    # To-do operations
    'save_todo_entry',
    'get_todo_entry',
    'update_todo_status',
    
    # Accounts operations
    'save_accounts_entry',
    'get_accounts_entry',
    'get_accounts_by_date_range',
    'get_total_by_type'
]
