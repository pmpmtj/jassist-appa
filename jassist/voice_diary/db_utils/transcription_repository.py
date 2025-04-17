import json
from psycopg2.extras import RealDictCursor
from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("transcription_repository", module="db_utils")

@db_connection_handler
def save_transcription(conn, content, filename=None, audio_path=None, model_type=None,
                      duration_seconds=None, metadata=None, tag=None):
    """
    Save a transcription to the database

    Args:
        content (str): The transcription content
        filename (str, optional): Associated filename
        audio_path (str, optional): Path to the audio file
        model_type (str, optional): The model used for transcription
        duration_seconds (float, optional): Duration of the audio
        metadata (dict, optional): Additional metadata
        tag (str, optional): Tag for categorization

    Returns:
        int: ID of the inserted record or None if error
    """
    try:
        cur = conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None

        cur.execute("""
        INSERT INTO transcriptions 
        (content, filename, audio_path, duration_seconds, metadata, tag)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (content, filename, audio_path, duration_seconds, metadata_json, tag))

        transcription_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Transcription saved with ID: {transcription_id}")
        return transcription_id
    except Exception as e:
        conn.rollback()
        logger.error("Failed to save transcription.")
        logger.error(str(e))
        return None

@db_connection_handler
def get_transcription(conn, transcription_id):
    """
    Retrieve a transcription by ID

    Args:
        transcription_id (int): ID of the transcription to retrieve

    Returns:
        dict: Transcription record or None if not found
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
    SELECT * FROM transcriptions WHERE id = %s
    """, (transcription_id,))
    return cur.fetchone()

@db_connection_handler
def get_latest_transcriptions(conn, limit=10):
    """
    Retrieve the latest transcriptions

    Args:
        limit (int, optional): Maximum number of records to return

    Returns:
        list: List of transcription records
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
    SELECT * FROM transcriptions ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    return cur.fetchall()

@db_connection_handler
def get_transcriptions_by_date_range(conn, start_date, end_date):
    """
    Retrieve transcriptions within a date range

    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format

    Returns:
        list: List of transcription records
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
    SELECT * FROM transcriptions
    WHERE created_at BETWEEN %s AND %s
    ORDER BY created_at DESC
    """, (start_date, end_date))
    return cur.fetchall()

@db_connection_handler
def mark_transcription_processed(conn, transcription_id, destination_table, destination_id):
    """
    Mark a transcription as processed and record where it was processed

    Args:
        transcription_id (int): ID of the transcription
        destination_table (str): Name of the destination table (e.g., "diary", "to_do", "calendar_events")
        destination_id (int): ID of the record in the destination table

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cur = conn.cursor()

        cur.execute("""
        UPDATE transcriptions
        SET is_processed = TRUE, 
            destination_table = %s, 
            destination_id = %s
        WHERE id = %s
        """, (destination_table, destination_id, transcription_id))

        affected_rows = cur.rowcount
        conn.commit()
        
        if affected_rows > 0:
            logger.info(f"Transcription {transcription_id} marked as processed to {destination_table}/{destination_id}")
            return True
        else:
            logger.warning(f"No transcription found with ID {transcription_id}")
            return False
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to mark transcription {transcription_id} as processed.")
        logger.error(str(e))
        return False
