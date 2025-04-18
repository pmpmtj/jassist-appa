"""
OpenAI client for entities processing.

This module handles interactions with the OpenAI API via the centralized adapter.
"""


from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("openai_client", module="entities")

def process_with_openai_assistant(entry_content: str) -> str:
    """
    Process an classification entry using OpenAI's assistant API.
    
    Args:
        entry_content: The classification entry text to process
        
    Returns:
        str: The assistant's response (JSON formatted)
    """
    # Use the centralized assistant client through the entities adapter
    response = process_with_entities_assistant(entry_content)
    
    if not response:
        raise ValueError("No assistant response found")
    
    return response 