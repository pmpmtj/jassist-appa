"""
Database operations for transcriptions.

This module handles database operations specific to transcriptions.
"""

import datetime
import logging
from typing import Optional

from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("transcribe_db", module="transcribe")

def initialize_transcription_db() -> bool:
    """
    Initialize the database for transcription operations.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import initialize_db, create_tables
        import psycopg2.errors
        
        # Initialize the database connection
        if not initialize_db():
            logger.error("Database connection initialization failed")
            return False
            
        # Create tables
        logger.info("Creating database tables...")
        try:
            create_tables()
            logger.info("Database tables created successfully")
        except Exception as e:
            # If we get a DuplicateObject error, the tables/triggers already exist, which is fine
            if isinstance(e, psycopg2.errors.DuplicateObject):
                logger.info("Tables already exist, continuing with existing schema")
            else:
                logger.error(f"Database tables creation failed: {e}")
                return False
            
        logger.info("Database initialized successfully with all required tables")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def save_raw_transcription(
    content: str,
    filename: str,
    audio_path: str,
    duration_seconds: Optional[float] = None,
    model_used: Optional[str] = None
) -> Optional[int]:
    """
    Save a raw transcription to the database.
    
    Args:
        content: The transcription text content
        filename: Name of the transcribed audio file
        audio_path: Path to the audio file
        duration_seconds: Optional duration of the audio in seconds
        model_used: Optional name of the model used for transcription
        
    Returns:
        int: ID of the saved transcription, or None if save failed
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_transcription
        
        metadata = {
            "model_used": model_used,
            "transcribed_at": datetime.datetime.now().isoformat(),
            "raw": True  # Mark this as a raw transcription
        }
        
        # Save the transcription with a raw_transcription tag
        transcription_id = save_transcription(
            content=content,
            filename=filename,
            audio_path=audio_path,
            duration_seconds=duration_seconds,
            metadata=metadata,
            tag="raw_transcription"  # Special tag for raw transcriptions
        )
        
        if transcription_id:
            logger.info(f"Raw transcription saved to database with ID: {transcription_id}")
        else:
            logger.error("Failed to save raw transcription to database")
            
        return transcription_id
        
    except Exception as e:
        logger.error(f"Error saving raw transcription to database: {e}")
        return None 