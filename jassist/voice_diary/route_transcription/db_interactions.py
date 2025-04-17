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
    
    Handles multiple formats:
    1. text: "some text content"  (with quotes)
    2. text: some text content    (without quotes)
    
    followed by:
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
        # First try the format with quotes
        text_match = re.search(r'text:\s*"([^"]*)"', block)
        # If not found, try without quotes (more flexible)
        if not text_match:
            text_match = re.search(r'text:\s*(.+?)(?:\n|$)', block)
        
        tag_match = re.search(r'tag:\s*(\w+(?:\s+\w+)*)', block)
        
        if text_match and tag_match:
            text_content = text_match.group(1).strip()
            tag_value = tag_match.group(1).strip().lower()
            
            # If we matched a multi-line text without quotes, handle it properly
            if not re.search(r'text:\s*"', block) and '\n' in block:
                # Extract everything between 'text:' and 'tag:'
                full_block = block
                text_start = re.search(r'text:\s*', full_block)
                tag_start = re.search(r'tag:\s*', full_block)
                
                if text_start and tag_start:
                    text_start_pos = text_start.end()
                    tag_start_pos = tag_start.start()
                    if tag_start_pos > text_start_pos:  # Ensure tag comes after text
                        text_content = full_block[text_start_pos:tag_start_pos].strip()
            
            entries.append({
                'text': text_content,
                'tag': tag_value
            })
            
        # If we couldn't match with the regex, try a line-by-line approach
        elif "text:" in block and "tag:" in block:
            lines = block.strip().split('\n')
            text_content = ""
            tag_value = ""
            
            # Find the tag line (usually shorter and comes after text)
            tag_line_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("tag:"):
                    tag_line_idx = i
                    tag_value = line.strip()[4:].strip().lower()
                    break
            
            # If we found the tag line, everything before it (after text:) is the text content
            if tag_line_idx > 0:
                for i, line in enumerate(lines):
                    if i < tag_line_idx and line.strip().startswith("text:"):
                        # Remove the "text:" prefix
                        text_part = line.strip()[5:].strip()
                        # Remove quotes if present
                        if text_part.startswith('"') and text_part.endswith('"'):
                            text_part = text_part[1:-1]
                        text_content = text_part
                        break
                
                # Get any lines between "text:" and "tag:" for multi-line text
                if text_content and tag_line_idx > 1:
                    for i in range(1, tag_line_idx):
                        if not lines[i].strip().startswith("text:"):
                            text_content += " " + lines[i].strip()
            
            if text_content and tag_value:
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
    This function now simply saves the provided text and tag as is, without
    attempting to parse or process multiple entries (that's handled by the caller).

    Args:
        text: The transcription text
        file_path: Path to the original audio file
        duration: Optional duration of the audio
        model_used: Optional transcription model used
        tag: Optional classification tag

    Returns:
        The ID of the saved record if successful, None otherwise
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
        
        # Save the entry directly, without further parsing
        record_id = save_transcription(
            content=text,
            filename=file_path.name,
            audio_path=str(file_path),
            duration_seconds=duration,
            metadata=metadata,
            tag=tag
        )

        if record_id:
            logger.info(f"Transcription saved with ID: {record_id}")
            return record_id
        else:
            logger.error("Failed to save transcription to database.")
            return None

    except Exception as e:
        logger.error(f"Exception during DB save: {e}")
        return None 