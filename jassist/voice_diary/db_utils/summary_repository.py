from psycopg2.extras import RealDictCursor
from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("summary_repository", module="db_utils")

@db_connection_handler
def save_day_summary(conn, content, start_date=None, end_date=None, filename=None):
    """
    Save a day summary to the database
    
    Args:
        content (str): The summary content
        start_date (str, optional): Start date of the summary range in ISO format
        end_date (str, optional): End date of the summary range in ISO format
        filename (str, optional): Associated filename
        
    Returns:
        int: ID of the inserted record or None if error
    """
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO vday_summaries 
    (content, summary_date, filename, date_range_start, date_range_end)
    VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
    RETURNING id
    """, (content, filename, start_date, end_date))

    summary_id = cur.fetchone()[0]
    conn.commit()
    logger.info(f"Saved day summary ID: {summary_id}")
    return summary_id

@db_connection_handler
def get_day_summaries_by_date_range(conn, start_date, end_date, limit=10):
    """
    Retrieve day summaries within a date range
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of day summary records
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
    SELECT * FROM vday_summaries
    WHERE summary_date BETWEEN %s AND %s
    ORDER BY summary_date DESC
    LIMIT %s
    """, (start_date, end_date, limit))
    return cur.fetchall()

@db_connection_handler
def get_latest_day_summaries(conn, limit=5):
    """
    Retrieve the latest day summaries
    
    Args:
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of day summary records
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
    SELECT * FROM vday_summaries
    ORDER BY summary_date DESC
    LIMIT %s
    """, (limit,))
    return cur.fetchall()

@db_connection_handler
def check_summary_exists(conn, start_date, end_date):
    """
    Check if a summary exists for a specific date range
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        
    Returns:
        bool: True if a summary exists, False otherwise
    """
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) FROM vday_summaries
    WHERE date_range_start = %s AND date_range_end = %s
    """, (start_date, end_date))
    return cur.fetchone()[0] > 0 