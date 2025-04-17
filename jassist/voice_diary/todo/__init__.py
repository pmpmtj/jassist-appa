"""
Todo package for jassist.

This package provides functionality for processing to-do entries.
"""

from pathlib import Path
import sys

# Ensure the package directory is in the path
PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.append(str(PACKAGE_DIR.parent))

# Export the main functions
from .todo_processor import process_todo_entry
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

def insert_into_todo(text: str, db_id: int = None) -> bool:
    """
    Process a voice entry for to-do insertion.
    
    This is the main entry point for the to-do module, 
    designed to be called from the route_transcription module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Get logger instance
    logger = setup_logger("todo", module="todo")
    
    # Process the entry
    success, _ = process_todo_entry(text, db_id)
    return success

# Initialize logging when the package is imported
logger = setup_logger("todo_init", module="todo") 