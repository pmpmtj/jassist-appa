"""
Accounts processor module.

This module processes financial entries and inserts them into the database.
"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .db.accounts_db import save_accounts_entry
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("accounts_processor", module="accounts")

def process_accounts_entry(text: str, db_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a voice entry for a financial transaction.
    
    Args:
        text: The voice entry text
        db_id: Optional ID of the database record this is associated with
        
    Returns:
        Tuple containing (success status, entry data)
    """
    try:
        logger.info("Processing accounts entry")
        
        # Extract entry type (income or expense)
        entry_type = detect_entry_type(text)
        logger.info(f"Detected entry type: {entry_type}")
        
        # Extract amount from text
        amount, currency = extract_amount_and_currency(text)
        if amount is None:
            logger.error("Could not extract amount from text")
            return False, None
        
        logger.info(f"Extracted amount: {amount} {currency}")
        
        # Extract date (default to current date if not found)
        transaction_date = extract_date(text)
        if transaction_date:
            date_str = transaction_date.isoformat()
            logger.info(f"Extracted date: {date_str}")
        else:
            date_str = None  # Use the database default (current timestamp)
        
        # Save to database
        entry_id = save_accounts_entry(
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            note=text,
            date=date_str,
            source_transcription_id=db_id
        )
        
        if not entry_id:
            logger.error("Failed to save accounts entry to database")
            return False, None
        
        logger.info(f"Accounts entry saved with ID: {entry_id}")
        
        # Return entry data
        entry_data = {
            "id": entry_id,
            "entry_type": entry_type,
            "amount": amount,
            "currency": currency,
            "note": text,
            "date": date_str
        }
        
        return True, entry_data
        
    except Exception as e:
        logger.exception(f"Error during accounts processing: {e}")
        return False, None

def detect_entry_type(text: str) -> str:
    """
    Determine if the entry is income or expense based on text content.
    
    Args:
        text: The entry text
        
    Returns:
        str: 'income' or 'expense'
    """
    # List of keywords that indicate income
    income_keywords = [
        "received", "earned", "income", "salary", "wage", "payment", "paid me",
        "deposit", "revenue", "profit", "bonus", "dividend", "interest",
        "refund", "reimbursement", "credit", "gain", "earning"
    ]
    
    # Check if any income keywords are in the text
    for keyword in income_keywords:
        if re.search(r'\b' + keyword + r'\b', text.lower()):
            return "income"
    
    # Default to expense if no income keywords found
    return "expense"

def extract_amount_and_currency(text: str) -> Tuple[Optional[float], str]:
    """
    Extract the monetary amount and currency from text.
    
    Args:
        text: The entry text
        
    Returns:
        Tuple of (amount as float or None if not found, currency code)
    """
    # Pattern for currency symbols and amounts: €50, 50€, $50, 50$, etc.
    currency_symbols = {
        '€': 'EUR',
        '$': 'USD',
        '£': 'GBP',
        '¥': 'JPY'
    }
    
    # Check for currency symbols
    for symbol, code in currency_symbols.items():
        # Pattern for symbol before number: €50, €50.25, €50,25
        pattern1 = rf'{re.escape(symbol)}\s*(\d+(?:[.,]\d+)?)'
        match = re.search(pattern1, text)
        if match:
            amount_str = match.group(1).replace(',', '.')
            return float(amount_str), code
            
        # Pattern for symbol after number: 50€, 50.25€, 50,25€
        pattern2 = r'(\d+(?:[.,]\d+)?)\s*' + re.escape(symbol)
        match = re.search(pattern2, text)
        if match:
            amount_str = match.group(1).replace(',', '.')
            return float(amount_str), code
    
    # Check for currency codes: 50 EUR, EUR 50, etc.
    currency_codes = ['EUR', 'USD', 'GBP', 'JPY', 'CHF']
    for code in currency_codes:
        # Pattern for code after number: 50 EUR
        pattern1 = rf'(\d+(?:[.,]\d+)?)\s*{code}'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '.')
            return float(amount_str), code
            
        # Pattern for code before number: EUR 50
        pattern2 = rf'{code}\s*(\d+(?:[.,]\d+)?)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '.')
            return float(amount_str), code
    
    # General number pattern if no currency indicator found
    pattern = r'(\d+(?:[.,]\d+)?)'
    match = re.search(pattern, text)
    if match:
        amount_str = match.group(1).replace(',', '.')
        return float(amount_str), 'EUR'  # Default to EUR
    
    return None, 'EUR'  # Default currency

def extract_date(text: str) -> Optional[datetime]:
    """
    Extract date from text, if present.
    
    Args:
        text: The entry text
        
    Returns:
        datetime object or None if not found
    """
    today = datetime.now().date()
    
    # Check for relative dates (today, yesterday, tomorrow)
    if re.search(r'\btoday\b', text.lower()):
        return datetime.combine(today, datetime.min.time())
    
    # Check for date patterns: MM/DD/YYYY, MM-DD-YYYY, etc.
    date_patterns = [
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})'     # YYYY/MM/DD
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            # Try different date formats
            try:
                if len(match.group(1)) == 4:  # YYYY/MM/DD
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                else:  # Assume MM/DD/YYYY for simplicity
                    month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if year < 100:
                        year += 2000  # Assume 21st century for 2-digit years
                
                return datetime(year, month, day)
            except ValueError:
                continue  # Try next pattern if date is invalid
    
    # No date found
    return None 