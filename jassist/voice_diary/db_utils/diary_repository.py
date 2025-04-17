"""
Database repository for diary entries.
"""

from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from typing import Optional, List

logger = setup_logger("diary_repository", module="db_utils")

@db_connection_handler
def save_diary_entry(conn, content, mood=None, tags=None, source_transcription_id=None):
    """
    Save a diary entry to the database
    
    Args:
        content (str): The diary entry content
        mood (str, optional): The mood of the entry
        tags (list, optional): List of tags for the entry
        source_transcription_id (int, optional): ID of source transcription
        
    Returns:
        int: ID of the inserted record or None if error
    """
    cur = conn.cursor()
    
    # Insert diary entry
    cur.execute("""
    INSERT INTO diary 
    (content, mood, tags, source_transcription_id)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """, (content, mood, tags, source_transcription_id))
    
    entry_id = cur.fetchone()[0]
    
    conn.commit()
    logger.info(f"Saved diary entry with ID: {entry_id}")
    return entry_id

@db_connection_handler
def get_diary_entry(conn, entry_id):
    """
    Retrieve a diary entry by ID
    
    Args:
        entry_id (int): The ID of the diary entry
        
    Returns:
        dict: The diary entry or None if not found
    """
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, content, entry_date, mood, tags, source_transcription_id
    FROM diary
    WHERE id = %s
    """, (entry_id,))
    
    result = cur.fetchone()
    
    if result:
        return {
            "id": result[0],
            "content": result[1],
            "entry_date": result[2],
            "mood": result[3],
            "tags": result[4],
            "source_transcription_id": result[5]
        }
    return None 