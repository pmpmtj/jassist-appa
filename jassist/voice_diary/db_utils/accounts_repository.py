"""
Database repository for accounts entries.
"""

from datetime import datetime
from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from typing import Optional, Dict, List, Any

logger = setup_logger("accounts_repository", module="db_utils")

@db_connection_handler
def save_accounts_entry(conn, entry_type, amount, currency="EUR", note=None, date=None, source_transcription_id=None, created_at=None):
    """
    Save an accounts entry to the database
    
    Args:
        entry_type (str): Type of entry ('income' or 'expense')
        amount (float): Monetary amount
        currency (str, optional): Currency code (default: EUR)
        note (str, optional): Note/description
        date (str, optional): Date in ISO format
        source_transcription_id (int, optional): ID of source transcription
        created_at (datetime, optional): Custom timestamp for when the entry was created
        
    Returns:
        int: ID of the inserted record or None if error
    """
    cur = conn.cursor()
    
    # Convert date string to datetime if provided
    date_obj = None
    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            logger.warning(f"Invalid date format: {date}, using current timestamp")
    
    # Build columns and values lists based on which parameters are provided
    columns = ["entry_type", "amount", "currency"]
    values = [entry_type, amount, currency]
    
    # Add optional parameters that are not None
    if note is not None:
        columns.append("note")
        values.append(note)
    
    if date_obj is not None:
        columns.append("date")
        values.append(date_obj)
    elif date is None:
        # If date is None, we need to explicitly add it and set to CURRENT_TIMESTAMP
        columns.append("date")
        values.append(datetime.now())
    
    if source_transcription_id is not None:
        columns.append("source_transcription_id")
        values.append(source_transcription_id)
    
    if created_at is not None:
        columns.append("created_at")
        values.append(created_at)
    
    # Build the SQL query dynamically
    placeholders = ", ".join(["%s"] * len(values))
    column_str = ", ".join(columns)
    
    query = f"""
    INSERT INTO accounts 
    ({column_str})
    VALUES ({placeholders})
    RETURNING id
    """
    
    # Execute the query
    cur.execute(query, values)
    
    entry_id = cur.fetchone()[0]
    
    conn.commit()
    logger.info(f"Saved accounts entry with ID: {entry_id}")
    return entry_id

@db_connection_handler
def get_accounts_entry(conn, entry_id):
    """
    Retrieve an accounts entry by ID
    
    Args:
        entry_id (int): The ID of the accounts entry
        
    Returns:
        dict: The accounts entry or None if not found
    """
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, entry_type, amount, currency, note, date, source_transcription_id, created_at
    FROM accounts
    WHERE id = %s
    """, (entry_id,))
    
    result = cur.fetchone()
    
    if result:
        return {
            "id": result[0],
            "entry_type": result[1],
            "amount": float(result[2]),
            "currency": result[3],
            "note": result[4],
            "date": result[5],
            "source_transcription_id": result[6],
            "created_at": result[7]
        }
    return None

@db_connection_handler
def get_accounts_by_date_range(conn, start_date, end_date):
    """
    Retrieve accounts entries within a date range
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        
    Returns:
        list: List of account entries
    """
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, entry_type, amount, currency, note, date, source_transcription_id, created_at
    FROM accounts
    WHERE date BETWEEN %s AND %s
    ORDER BY date DESC
    """, (start_date, end_date))
    
    results = cur.fetchall()
    entries = []
    
    for result in results:
        entries.append({
            "id": result[0],
            "entry_type": result[1],
            "amount": float(result[2]),
            "currency": result[3],
            "note": result[4],
            "date": result[5],
            "source_transcription_id": result[6],
            "created_at": result[7]
        })
    
    return entries

@db_connection_handler
def get_total_by_type(conn, entry_type, start_date=None, end_date=None):
    """
    Get total sum of income or expenses, optionally within a date range
    
    Args:
        entry_type (str): 'income' or 'expense'
        start_date (str, optional): Start date in ISO format
        end_date (str, optional): End date in ISO format
        
    Returns:
        dict: Dictionary with totals by currency
    """
    cur = conn.cursor()
    
    query = """
    SELECT currency, SUM(amount) as total
    FROM accounts
    WHERE entry_type = %s
    """
    params = [entry_type]
    
    if start_date:
        query += " AND date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= %s"
        params.append(end_date)
    
    query += " GROUP BY currency"
    
    cur.execute(query, params)
    
    results = cur.fetchall()
    totals = {}
    
    for currency, total in results:
        totals[currency] = float(total)
    
    return totals 