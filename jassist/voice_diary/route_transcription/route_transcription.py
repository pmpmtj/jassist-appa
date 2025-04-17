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
    
    # Flag to track if we're dealing with a multi-entry response
    is_multi_entry = False
    
    # Check upfront if text or tag contains multiple entries
    contains_multiple_entries = (
        (tag and isinstance(tag, str) and "text:" in tag and "tag:" in tag) or
        (text and isinstance(text, str) and "text:" in text and "tag:" in text)
    )
    
    # Parse entries before saving, so we can use them later
    entries_from_input = []
    multi_entry_source = None
    
    # First check the tag field for multiple entries
    if tag and isinstance(tag, str) and "text:" in tag and "tag:" in tag:
        entries_from_input = parse_llm_response(tag)
        multi_entry_source = "tag"
        logger.info(f"Found {len(entries_from_input)} entries in tag field before saving")
    
    # If no entries found in tag field, check the text field
    if not entries_from_input and text and isinstance(text, str) and "text:" in text and "tag:" in text:
        entries_from_input = parse_llm_response(text)
        multi_entry_source = "text"
        logger.info(f"Found {len(entries_from_input)} entries in text field before saving")
    
    # If db_id is not provided, we need to save the transcription first
    saved_entries_ids = []
    if db_id is None:
        logger.info("No db_id provided, saving transcription to database")
        
        # If we have entries from input, save each one separately
        if entries_from_input:
            logger.info(f"Saving {len(entries_from_input)} separate entries")
            for idx, entry in enumerate(entries_from_input):
                entry_text = entry['text']
                entry_tag = entry['tag']
                
                # Save the entry to the database
                entry_id = save_to_database(
                    text=entry_text,
                    file_path=file_path,
                    duration=duration,
                    model_used=model_used,
                    tag=entry_tag
                )
                
                if entry_id:
                    saved_entries_ids.append(entry_id)
                    logger.info(f"Saved entry {idx+1}/{len(entries_from_input)} with ID: {entry_id}")
                else:
                    logger.error(f"Failed to save entry {idx+1}/{len(entries_from_input)}")
            
            # Use the first entry's ID as the main db_id for the result
            if saved_entries_ids:
                db_id = saved_entries_ids[0]
                result["db_id"] = db_id
                logger.info(f"Using first entry ID as main ID: {db_id}")
        else:
            # Save as a single transcription
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
    
    # If we already parsed entries from the input, use those
    entries = entries_from_input
    
    # If we didn't already parse entries (and haven't saved multiple entries), try parsing now
    if not entries and not saved_entries_ids:
        # First, check the tag field for multiple entries
        if tag and isinstance(tag, str) and "text:" in tag and "tag:" in tag:
            logger.info("Detected complex LLM response in tag field with multiple entries")
            entries = parse_llm_response(tag)
            logger.info(f"Parsed {len(entries)} entries from tag field LLM response")
            
            # If parsing failed or returned no entries, try a more direct approach
            if not entries:
                logger.info("Trying alternative parsing approach for complex LLM response in tag field")
                entries = parse_complex_llm_response(tag)
                logger.info(f"Alternative parser found {len(entries)} entries from tag field")
        
        # If no entries found in tag field, check the text field
        if not entries and text and isinstance(text, str) and "text:" in text and "tag:" in text:
            logger.info("Detected complex LLM response in text field with multiple entries")
            entries = parse_llm_response(text)
            logger.info(f"Parsed {len(entries)} entries from text field LLM response")
            
            # If parsing failed or returned no entries, try a more direct approach
            if not entries:
                logger.info("Trying alternative parsing approach for complex LLM response in text field")
                entries = parse_complex_llm_response(text)
                logger.info(f"Alternative parser found {len(entries)} entries from text field")
    
    # If we have saved multiple entries individually, process each saved entry
    if saved_entries_ids:
        logger.info(f"Processing {len(saved_entries_ids)} previously saved entries")
        is_multi_entry = True
        processed_count = 0
        success_count = 0
        
        for idx, entry_id in enumerate(saved_entries_ids):
            if idx < len(entries_from_input):
                entry = entries_from_input[idx]
                entry_text = entry['text']
                entry_tag = entry['tag']
                
                logger.info(f"Processing saved entry {idx+1}/{len(saved_entries_ids)}: tag='{entry_tag}', id={entry_id}")
                
                # Process the entry using its own ID
                entry_result = process_entry_by_tag(entry_text, entry_tag, entry_id)
                result["processed_entries"].append({
                    "id": entry_id,
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
    
    # If we have parsed entries (and didn't process saved entries), process them now
    elif entries:
        is_multi_entry = True
        processed_count = 0
        success_count = 0
        
        for entry in entries:
            entry_text = entry['text']
            entry_tag = entry['tag']
            
            # Clean up tag if needed (remove extra whitespace and newlines)
            entry_tag = entry_tag.strip()
            
            logger.info(f"Processing entry {processed_count+1}/{len(entries)}: tag='{entry_tag}'")
            
            # Process the entry using the original db_id for all entries
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
    
    # Additional logging for debugging
    if is_multi_entry:
        logger.info(f"Processed {result['success_count']}/{result['entries_processed']} entries successfully")
    else:
        success_str = "successful" if result["status"] == "success" else "failed"
        logger.info(f"Processed single entry with tag '{tag}': {success_str}")
    
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
    
    # Convert the tag to lowercase for case-insensitive comparison
    tag_lower = tag.lower()
    
    if tag_lower == "calendar":
        return insert_into_calendar(text, db_id)
    elif tag_lower == "diary":
        return insert_into_diary(text, db_id)
    elif tag_lower == "to_do" or tag_lower == "todo":
        return insert_into_todo(text, db_id)
    elif tag_lower == "accounts" or tag_lower == "account":
        return insert_into_accounts(text, db_id)
    elif tag_lower == "contacts" or tag_lower == "contact":
        return insert_into_contacts(text, db_id)
    elif tag_lower == "entities" or tag_lower == "entity":
        return insert_into_entities(text, db_id)
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

def insert_into_diary(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for diary insertion.
    Re-exports the function from the diary module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.diary import insert_into_diary as diary_insert
    return diary_insert(text, db_id)

def insert_into_todo(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for to-do insertion.
    Re-exports the function from the todo module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.todo import insert_into_todo as todo_insert
    return todo_insert(text, db_id)

def insert_into_accounts(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for accounts insertion.
    Re-exports the function from the accounts module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.accounts import insert_into_accounts as accounts_insert
    return accounts_insert(text, db_id)

def insert_into_contacts(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for contacts insertion.
    Re-exports the function from the contacts module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.contacts import insert_into_contacts as contacts_insert
    return contacts_insert(text, db_id)

def insert_into_entities(text: str, db_id: Optional[int] = None) -> bool:
    """
    Process a voice entry for entities insertion.
    Re-exports the function from the entities module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    from jassist.voice_diary.entities import insert_into_entities as entities_insert
    return entities_insert(text, db_id)
