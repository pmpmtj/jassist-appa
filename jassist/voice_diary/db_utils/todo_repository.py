"""
Database repository for to-do entries.
"""

from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from typing import Optional

logger = setup_logger("todo_repository", module="db_utils")

@db_connection_handler
def save_todo_entry(conn, task, due_date=None, priority=None, status="pending", source_transcription_id=None):
    """
    Save a to-do entry to the database
    
    Args:
        task (str): The to-do task description
        due_date (str, optional): Due date in ISO format
        priority (str, optional): Priority level (high, medium, low)
        status (str, optional): Task status (default: pending)
        source_transcription_id (int, optional): ID of source transcription
        
    Returns:
        int: ID of the inserted record or None if error
    """
    cur = conn.cursor()
    
    # Insert to-do entry
    cur.execute("""
    INSERT INTO to_do 
    (task, due_date, priority, status, source_transcription_id)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """, (task, due_date, priority, status, source_transcription_id))
    
    entry_id = cur.fetchone()[0]
    
    conn.commit()
    logger.info(f"Saved to-do entry with ID: {entry_id}")
    return entry_id

@db_connection_handler
def get_todo_entry(conn, entry_id):
    """
    Retrieve a to-do entry by ID
    
    Args:
        entry_id (int): The ID of the to-do entry
        
    Returns:
        dict: The to-do entry or None if not found
    """
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, task, due_date, priority, status, source_transcription_id
    FROM to_do
    WHERE id = %s
    """, (entry_id,))
    
    result = cur.fetchone()
    
    if result:
        return {
            "id": result[0],
            "task": result[1],
            "due_date": result[2],
            "priority": result[3],
            "status": result[4],
            "source_transcription_id": result[5]
        }
    return None

@db_connection_handler
def update_todo_status(conn, entry_id, status):
    """
    Update the status of a to-do entry
    
    Args:
        entry_id (int): The ID of the to-do entry
        status (str): The new status
        
    Returns:
        bool: Success status
    """
    cur = conn.cursor()
    
    cur.execute("""
    UPDATE to_do
    SET status = %s
    WHERE id = %s
    """, (status, entry_id))
    
    affected_rows = cur.rowcount
    
    conn.commit()
    
    if affected_rows > 0:
        logger.info(f"Updated to-do entry {entry_id} status to {status}")
        return True
    else:
        logger.warning(f"No to-do entry found with ID {entry_id}")
        return False 