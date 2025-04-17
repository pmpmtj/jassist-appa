import datetime
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from jassist.voice_diary.db_utils.db_manager import initialize_db, save_transcription
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("db_interactions", module="route_transcription")

def parse_llm_response(response: str) -> List[Dict[str, str]]:
    """
    Parse the LLM response that contains text and tags.
    
    Expected format:
    text: "some text content"
    tag: tag_name
    
    (possibly repeated for multiple entries)
    
    Args:
        response: The response from the LLM
        
    Returns:
        List of dictionaries with 'text' and 'tag' keys
    """
    entries = []
    
    # Split by blank lines to handle multiple entries
    blocks = [block.strip() for block in response.split("\n\n") if block.strip()]
    
    for block in blocks:
        # Extract text and tag using regex
        text_match = re.search(r'text:\s*"([^"]*)"', block)
        tag_match = re.search(r'tag:\s*(\w+(?:\s+\w+)*)', block)
        
        if text_match and tag_match:
            text_content = text_match.group(1).strip()
            tag_value = tag_match.group(1).strip().lower()
            
            entries.append({
                'text': text_content,
                'tag': tag_value
            })
    
    return entries

def save_to_database(
    text: str,
    file_path: Path,
    duration: Optional[float] = None,
    model_used: Optional[str] = None,
    tag: Optional[str] = None
) -> Optional[int]:
    """
    Save a transcription result to the database.
    Handles both single entries and multiple entries from the LLM.

    Args:
        text: The transcription text
        file_path: Path to the original audio file
        duration: Optional duration of the audio
        model_used: Optional transcription model used
        tag: Optional classification tag from LLM (may contain multiple entries)

    Returns:
        The ID of the last saved record if successful, None otherwise
    """
    if not initialize_db():
        logger.error("Database initialization failed.")
        return None

    try:
        logger.info(f"Saving transcription to database for: {file_path.name}")
        
        metadata = {
            "model_used": model_used,
            "transcribed_at": datetime.datetime.now().isoformat()
        }
        
        last_record_id = None
        
        # Check if the tag field actually contains an LLM response with multiple entries
        if tag and ("text:" in tag and "tag:" in tag):
            # Parse the LLM response into multiple entries
            entries = parse_llm_response(tag)
            
            if not entries:
                # Fallback: Save the whole thing as one entry
                logger.warning("Could not parse LLM response, saving as a single entry")
                # The save_transcription function now handles connections internally
                last_record_id = save_transcription(
                    content=text,
                    filename=file_path.name,
                    audio_path=str(file_path),
                    duration_seconds=duration,
                    metadata=metadata,
                    tag=tag
                )
            else:
                # Save each entry separately
                logger.info(f"Found {len(entries)} separate entries in LLM response")
                for entry in entries:
                    entry_text = entry['text']
                    entry_tag = entry['tag']
                    
                    logger.info(f"Saving entry with tag: {entry_tag}")
                    # The save_transcription function now handles connections internally
                    record_id = save_transcription(
                        content=entry_text,
                        filename=file_path.name,
                        audio_path=str(file_path),
                        duration_seconds=duration,
                        metadata=metadata,
                        tag=entry_tag
                    )
                    
                    if record_id:
                        last_record_id = record_id
                    else:
                        logger.error(f"Failed to save entry with tag '{entry_tag}'")
        else:
            # Standard single entry
            # The save_transcription function now handles connections internally
            last_record_id = save_transcription(
                content=text,
                filename=file_path.name,
                audio_path=str(file_path),
                duration_seconds=duration,
                metadata=metadata,
                tag=tag
            )

        if last_record_id:
            logger.info(f"Transcription saved with ID: {last_record_id}")
            return last_record_id
        else:
            logger.error("Failed to save transcription to database.")
            return None

    except Exception as e:
        logger.error(f"Exception during DB save: {e}")
        return None 