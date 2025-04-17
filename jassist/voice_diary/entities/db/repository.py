"""
Entities repository for database operations.
"""

from typing import Optional, Dict, Any

from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("repository", module="entities")

@db_connection_handler
def save_entity(
    conn, 
    name: str,
    type: str = "",
    context: str = "",
    relevance_score: float = 0.5,
    source_transcription_id: Optional[int] = None
) -> Optional[int]:
    """
    Save an entity to the database.
    
    Args:
        conn: Database connection
        name: Name of the entity
        type: Type of entity (person, organization, location, etc.)
        context: Contextual information about the entity
        relevance_score: Score indicating the relevance (0.0-1.0)
        source_transcription_id: ID of the source transcription
        
    Returns:
        int: ID of the inserted entity or None if operation failed
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities 
            (name, type, context, relevance_score, source_transcription_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, type, context, relevance_score, source_transcription_id)
        )
        entity_id = cursor.fetchone()[0]
        conn.commit()
        
        # If we have a source transcription ID, update it to mark as processed
        if source_transcription_id:
            cursor.execute(
                """
                UPDATE transcriptions 
                SET is_processed = TRUE, 
                    destination_table = 'entities', 
                    destination_id = %s
                WHERE id = %s
                """,
                (entity_id, source_transcription_id)
            )
            conn.commit()
            
        logger.info(f"Saved entity with ID: {entity_id}")
        return entity_id
    except Exception as e:
        logger.error(f"Error saving entity: {e}")
        conn.rollback()
        return None 