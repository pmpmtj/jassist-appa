"""
Test script for the transcription routing functionality.
"""

import logging
from pathlib import Path
from jassist.voice_diary.route_transcription.route_transcription import route_transcription
from jassist.voice_diary.db_utils.db_manager import initialize_db

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multiple_entries():
    """Test processing multiple entries in one transcription."""
    
    # Initialize database
    if not initialize_db():
        logger.error("Failed to initialize database.")
        return
        
    # Sample transcription with multiple entries
    text = "This is a test transcription with multiple entries."
    tag = '''
    text: "This is a diary entry for testing."
    tag: diary

    text: "Remember to fix the bugs by tomorrow."
    tag: to_do

    text: "Meeting with development team at 3pm tomorrow."
    tag: calendar
    '''
    
    # Call route_transcription
    result = route_transcription(
        text=text,
        file_path=Path("test_audio.m4a"),
        tag=tag,
        duration=10.0,
        model_used="test_model"
    )
    
    # Print result
    logger.info(f"Test result: {result}")
    logger.info(f"Status: {result['status']}")
    logger.info(f"Entries processed: {result['entries_processed']}")
    logger.info(f"Success count: {result['success_count']}")
    
    for idx, entry in enumerate(result.get('processed_entries', [])):
        logger.info(f"Entry {idx+1}: {entry['tag']} - Success: {entry['success']}")

if __name__ == "__main__":
    logger.info("Starting transcription routing test...")
    test_multiple_entries()
    logger.info("Test completed.") 