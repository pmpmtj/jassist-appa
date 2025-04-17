"""
Database operations for to-do entries.

This module handles database operations specific to to-do entries.
"""

from typing import Optional
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("todo_db", module="todo")

def save_todo_entry(
    task: str,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "pending",
    source_transcription_id: Optional[int] = None
) -> Optional[int]:
    """
    Save a to-do entry to the database.
    
    Args:
        task: The to-do task description
        due_date: Optional due date in ISO format
        priority: Optional priority level (high, medium, low)
        status: Status of the task (default: pending)
        source_transcription_id: Optional ID of source transcription
        
    Returns:
        int: ID of the saved entry, or None if save failed
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_todo_entry as db_save_todo_entry
        
        # Call the database function
        entry_id = db_save_todo_entry(
            task=task,
            due_date=due_date,
            priority=priority,
            status=status,
            source_transcription_id=source_transcription_id
        )
        
        if entry_id:
            logger.info(f"Successfully saved to-do entry with ID: {entry_id}")
            
            # If we have a source transcription, mark it as processed
            if source_transcription_id:
                from jassist.voice_diary.db_utils.db_manager import mark_transcription_processed
                mark_transcription_processed(
                    transcription_id=source_transcription_id,
                    destination_table="to_do",
                    destination_id=entry_id
                )
        else:
            logger.error("Failed to save to-do entry to database")
            
        return entry_id
        
    except Exception as e:
        logger.exception(f"Error saving to-do entry to database: {e}")
        return None 