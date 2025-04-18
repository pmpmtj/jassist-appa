"""
Utility to check database transcription records.
"""

from jassist.voice_diary.db_utils.db_manager import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("check_db", module="transcribe")

@db_connection_handler
def check_recent_transcriptions(conn, limit=5):
    """
    Check the most recent transcription records in the database.
    
    Args:
        conn: Database connection
        limit: Maximum number of records to retrieve
        
    Returns:
        list: List of recent transcription records
    """
    cur = conn.cursor()
    
    # Query the database to check transcriptions
    cur.execute("""
    SELECT id, filename, tag, created_at 
    FROM transcriptions 
    ORDER BY id DESC
    LIMIT %s
    """, (limit,))
    
    rows = cur.fetchall()
    
    if not rows:
        logger.info("No transcription records found in the database.")
        return []
        
    logger.info(f"Found {len(rows)} transcription records")
    return rows

def format_transcription_records(records):
    """
    Format transcription records for display.
    
    Args:
        records: List of transcription records
        
    Returns:
        str: Formatted string for display
    """
    if not records:
        return "No records found in the database."
        
    output = f"\nFound {len(records)} transcription records:\n"
    output += "-" * 50 + "\n"
    
    for row in records:
        id, filename, tag, created_at = row
        output += f"ID: {id}\n"
        output += f"Filename: {filename}\n"
        output += f"Tag: {tag}\n"
        output += f"Created at: {created_at}\n"
        output += "-" * 50 + "\n"
    
    return output

def display_recent_transcriptions(limit=5):
    """
    Display the most recent transcription records.
    
    Args:
        limit: Maximum number of records to display
    """
    try:
        records = check_recent_transcriptions(limit=limit)
        print(format_transcription_records(records))
    except Exception as e:
        logger.error(f"Error checking transcriptions: {e}")
        print(f"Error: {e}") 