"""
Diary processor module.

This module processes diary entries and inserts them into the database.
"""

from typing import Dict, Any, Optional, Tuple
from .db.diary_db import save_diary_entry
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("diary_processor", module="diary")

def process_diary_entry(text: str, db_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a voice entry for a diary entry.
    
    Args:
        text: The voice entry text
        db_id: Optional ID of the database record this is associated with
        
    Returns:
        Tuple containing (success status, entry data)
    """
    try:
        logger.info("Processing diary entry")
        
        # For diary entries, we directly save the content without any additional processing
        # This can be enhanced later to extract mood or tags if needed
        
        # Save to database
        entry_id = save_diary_entry(
            content=text,
            source_transcription_id=db_id
        )
        
        if not entry_id:
            logger.error("Failed to save diary entry to database")
            return False, None
        
        logger.info(f"Diary entry saved with ID: {entry_id}")
        
        # Return simple entry data
        entry_data = {
            "id": entry_id,
            "content": text
        }
        
        return True, entry_data
        
    except Exception as e:
        logger.exception(f"Error during diary processing: {e}")
        return False, None 