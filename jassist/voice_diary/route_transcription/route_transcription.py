### route_transcription.py
# jassist/voice_diary/route_transcription/route_transcription.py

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from jassist.voice_diary.db_utils.db_manager import initialize_db
from jassist.voice_diary.calendar import insert_into_calendar
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.route_transcription.db_interactions import save_to_database, parse_llm_response

logger = setup_logger("route_transcription", module="route_transcription")

def route_transcription(
    text: str,
    file_path: Path,
    tag: str,
    duration: Optional[float] = None,
    model_used: Optional[str] = None,
    db_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Route a transcription to the appropriate module based on its tag.
    
    Args:
        text: The transcription text content
        file_path: Path to the original audio file
        tag: Classification tag for determining routing
        duration: Optional duration of the audio in seconds
        model_used: Optional name of the model used for transcription
        db_id: Optional database ID if the transcription is already saved
        
    Returns:
        Dict containing status information about the routing process
    """
    # Initialize result dictionary
    result = {
        "status": "failed",
        "db_id": db_id,
        "tag": tag,
        "additional_processing": False,
        "entries_processed": 0,
        "processed_entries": []
    }
    
    # If db_id is not provided, we need to save the transcription first
    if db_id is None:
        logger.info("No db_id provided, saving transcription to database")
        db_id = save_to_database(
            text=text,
            file_path=file_path,
            duration=duration,
            model_used=model_used,
            tag=tag
        )
        result["db_id"] = db_id
        
        if db_id is None:
            logger.error("Failed to save transcription to database")
            result["message"] = "Database save failed"
            return result
    
    logger.info(f"Routing transcription with tag: {tag} and db_id: {db_id}")
    
    # Check if the tag contains multiple entries (LLM response with text: and tag: format)
    entries = []
    if tag and isinstance(tag, str) and "text:" in tag and "tag:" in tag:
        logger.info("Detected complex LLM response with multiple entries")
        entries = parse_llm_response(tag)
        logger.info(f"Parsed {len(entries)} entries from LLM response")
        
        # If parsing failed or returned no entries, try a more direct approach
        if not entries:
            logger.info("Trying alternative parsing approach for complex LLM response")
            entries = parse_complex_llm_response(tag)
            logger.info(f"Alternative parser found {len(entries)} entries")
    
    # If we have parsed entries, process each one
    if entries:
        processed_count = 0
        success_count = 0
        
        for entry in entries:
            entry_text = entry['text']
            entry_tag = entry['tag']
            
            # Clean up tag if needed (remove extra whitespace and newlines)
            entry_tag = entry_tag.strip()
            
            logger.info(f"Processing entry {processed_count+1}/{len(entries)}: tag='{entry_tag}'")
            
            entry_result = process_entry_by_tag(entry_text, entry_tag, db_id)
            result["processed_entries"].append({
                "text": entry_text[:50] + "..." if len(entry_text) > 50 else entry_text,
                "tag": entry_tag,
                "success": entry_result
            })
            
            processed_count += 1
            if entry_result:
                success_count += 1
        
        # Update overall result
        result["entries_processed"] = processed_count
        result["success_count"] = success_count
        result["additional_processing"] = processed_count > 0
        result["status"] = "success" if success_count > 0 else "failed"
    else:
        # Process single entry
        success = process_entry_by_tag(text, tag, db_id)
        result["status"] = "success" if success else "failed"
        result["additional_processing"] = success
        result["entries_processed"] = 1
        result["success_count"] = 1 if success else 0
    
    return result

def parse_complex_llm_response(response: str) -> List[Dict[str, str]]:
    """
    Alternative parser for complex LLM responses.
    
    Args:
        response: The LLM response text with multiple entries
        
    Returns:
        List of dictionaries with text and tag
    """
    entries = []
    
    # Split by empty lines to separate entries
    blocks = response.split("\n\n")
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
            
        # Look for text: and tag: lines
        text_line = None
        tag_line = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("text:"):
                text_line = line
            elif line.startswith("tag:"):
                tag_line = line
        
        if text_line and tag_line:
            # Extract the text content (removing quotes if present)
            text_content = text_line[5:].strip()
            if text_content.startswith('"') and text_content.endswith('"'):
                text_content = text_content[1:-1]
                
            # Extract the tag
            tag_value = tag_line[4:].strip()
            
            entries.append({
                "text": text_content,
                "tag": tag_value
            })
    
    return entries

def process_entry_by_tag(text: str, tag: str, db_id: Optional[int] = None) -> bool:
    """
    Process a single entry based on its tag.
    
    Args:
        text: The text content to process
        tag: The tag determining how to process the content
        db_id: Optional database ID reference
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger.info(f"Processing entry with tag: {tag}")
    
    if tag.lower() == "calendar":
        return insert_into_calendar(text, db_id)
    else:
        # Other tags can be processed here as they are implemented
        logger.info(f"No specific processing implemented for tag: {tag}")
        return True  # Consider it processed successfully

def insert_into_calendar(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for calendar insertion.
    Re-exports the function from the calendar module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.calendar import insert_into_calendar as calendar_insert
    return calendar_insert(text, db_id)
