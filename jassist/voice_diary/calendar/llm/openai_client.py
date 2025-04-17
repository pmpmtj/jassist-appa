"""
OpenAI client for calendar processing.

This module handles interactions with the OpenAI API.
"""

import os
from datetime import datetime
from jassist.voice_diary.api_assistants_cliente.adapters.calendar_adapter import process_with_calendar_assistant
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("openai_client", module="calendar")

def process_with_openai_assistant(entry_content: str) -> str:
    """
    Process a calendar entry using OpenAI's assistant API.
    
    Args:
        entry_content: The calendar entry text to process
        
    Returns:
        str: The assistant's response
    """
    # Use the centralized assistant client through the calendar adapter
    response = process_with_calendar_assistant(entry_content)
    
    if not response:
        raise ValueError("No assistant response found")
    
    return response 