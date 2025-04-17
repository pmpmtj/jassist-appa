"""
Contacts repository for database operations.
"""

from typing import Optional, Dict, Any

from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("repository", module="contacts")

@db_connection_handler
def save_contact(
    conn, 
    first_name: str = "", 
    last_name: str = "", 
    phone: str = "",
    email: str = "", 
    note: str = "",
    source_transcription_id: Optional[int] = None
) -> Optional[int]:
    """
    Save a contact to the database.
    
    Args:
        conn: Database connection
        first_name: First name of the contact
        last_name: Last name of the contact
        phone: Phone number
        email: Email address
        note: Additional notes about the contact
        source_transcription_id: ID of the source transcription
        
    Returns:
        int: ID of the inserted contact or None if operation failed
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts 
            (first_name, last_name, phone, email, note, source_transcription_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (first_name, last_name, phone, email, note, source_transcription_id)
        )
        contact_id = cursor.fetchone()[0]
        conn.commit()
        
        # If we have a source transcription ID, update it to mark as processed
        if source_transcription_id:
            cursor.execute(
                """
                UPDATE transcriptions 
                SET is_processed = TRUE, 
                    destination_table = 'contacts', 
                    destination_id = %s
                WHERE id = %s
                """,
                (contact_id, source_transcription_id)
            )
            conn.commit()
            
        logger.info(f"Saved contact with ID: {contact_id}")
        return contact_id
    except Exception as e:
        logger.error(f"Error saving contact: {e}")
        conn.rollback()
        return None 