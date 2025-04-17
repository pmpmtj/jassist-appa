"""
OpenAI client for contacts processing.

This module handles interactions with the OpenAI API via the centralized adapter.
"""

from jassist.voice_diary.api_assistants_cliente.adapters.contacts_adapter import process_with_contacts_assistant
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("openai_client", module="contacts")

def process_with_openai_assistant(entry_content: str) -> str:
    """
    Process a contact entry using OpenAI's assistant API.
    
    Args:
        entry_content: The contact entry text to process
        
    Returns:
        str: The assistant's response (JSON formatted)
    """
    # Use the centralized assistant client through the contacts adapter
    response = process_with_contacts_assistant(entry_content)
    
    if not response:
        raise ValueError("No assistant response found")
    
    return response 