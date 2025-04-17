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
