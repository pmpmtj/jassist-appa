"""
Database operations for diary entries.

This module handles database operations specific to diary entries.
"""

from typing import Optional, List
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("diary_db", module="diary")

def save_diary_entry(
    content: str,
    mood: Optional[str] = None,
    tags: Optional[List[str]] = None,
    source_transcription_id: Optional[int] = None
) -> Optional[int]:
    """
    Save a diary entry to the database.
    
    Args:
        content: The diary entry content
        mood: Optional mood descriptor for the entry
        tags: Optional list of tags for the entry
        source_transcription_id: Optional ID of source transcription
        
    Returns:
        int: ID of the saved entry, or None if save failed
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_diary_entry as db_save_diary_entry
        
        # Call the database function
        entry_id = db_save_diary_entry(
            content=content,
            mood=mood,
            tags=tags,
            source_transcription_id=source_transcription_id
        )
        
        if entry_id:
            logger.info(f"Successfully saved diary entry with ID: {entry_id}")
            
            # If we have a source transcription, mark it as processed
            if source_transcription_id:
                from jassist.voice_diary.db_utils.db_manager import mark_transcription_processed
                mark_transcription_processed(
                    transcription_id=source_transcription_id,
                    destination_table="diary",
                    destination_id=entry_id
                )
        else:
            logger.error("Failed to save diary entry to database")
            
        return entry_id
        
    except Exception as e:
        logger.exception(f"Error saving diary entry to database: {e}")
        return None 