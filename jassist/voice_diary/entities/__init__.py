"""
Entities Module

This module processes voice entries containing entity information.
"""

from .entities_processor import process_entity_entry

def insert_into_entities(text: str, db_id=None):
    """
    Process a voice entry for entities insertion.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    return process_entity_entry(text, db_id) 