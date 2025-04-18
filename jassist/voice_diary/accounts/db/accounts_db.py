"""
Database operations for accounts entries.

This module handles database operations specific to accounts entries.
"""

from typing import Optional
from datetime import datetime
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("accounts_db", module="accounts")

def save_accounts_entry(
    entry_type: str,
    amount: float,
    currency: str = "EUR",
    note: Optional[str] = None,
    date: Optional[str] = None,
    source_transcription_id: Optional[int] = None,
    created_at: Optional[datetime] = None
) -> Optional[int]:
    """
    Save an accounts entry to the database.
    
    Args:
        entry_type: Type of entry ('income' or 'expense')
        amount: Monetary amount
        currency: Currency code (default: EUR)
        note: Optional note/description
        date: Optional date in ISO format
        source_transcription_id: Optional ID of source transcription
        created_at: Optional timestamp for when the entry was created
        
    Returns:
        int: ID of the saved entry, or None if save failed
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_accounts_entry as db_save_accounts_entry
        
        # Call the database function
        entry_id = db_save_accounts_entry(
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            note=note,
            date=date,
            source_transcription_id=source_transcription_id,
            created_at=created_at
        )
        
        if entry_id:
            logger.info(f"Successfully saved accounts entry with ID: {entry_id}")
            
            # If we have a source transcription, mark it as processed
            if source_transcription_id:
                from jassist.voice_diary.db_utils.db_manager import mark_transcription_processed
                mark_transcription_processed(
                    transcription_id=source_transcription_id,
                    destination_table="accounts",
                    destination_id=entry_id
                )
        else:
            logger.error("Failed to save accounts entry to database")
            
        return entry_id
        
    except Exception as e:
        logger.exception(f"Error saving accounts entry to database: {e}")
        return None 