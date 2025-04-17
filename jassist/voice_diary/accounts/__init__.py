"""
Accounts package for jassist.

This package provides functionality for processing financial account entries.
"""

from pathlib import Path
import sys

# Ensure the package directory is in the path
PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.append(str(PACKAGE_DIR.parent))

# Export the main functions
from .accounts_processor import process_accounts_entry
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

def insert_into_accounts(text: str, db_id: int = None) -> bool:
    """
    Process a voice entry for accounts insertion.
    
    This is the main entry point for the accounts module, 
    designed to be called from the route_transcription module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Get logger instance
    logger = setup_logger("accounts", module="accounts")
    
    # Process the entry
    success, _ = process_accounts_entry(text, db_id)
    return success

# Initialize logging when the package is imported
logger = setup_logger("accounts_init", module="accounts")
