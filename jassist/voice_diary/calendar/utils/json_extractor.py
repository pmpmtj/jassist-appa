"""
JSON extraction utilities for calendar processing.

This module extracts structured JSON data from text responses.
"""

import json
import re
import logging
from typing import Dict, Any, Optional

from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("json_extractor", module="calendar")

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from text, handling different formats.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        Dict: The extracted JSON object, or None if extraction failed
    """
    if not text:
        logger.error("No text provided for JSON extraction")
        return None
        
    try:
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract code blocks with ```json syntax
        json_block_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        for match in json_block_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Try to find anything between curly braces
        curly_match = re.search(r'({[\s\S]*})', text)
        if curly_match:
            try:
                return json.loads(curly_match.group(1))
            except json.JSONDecodeError:
                pass

        logger.error("Failed to extract valid JSON from text")
        return None
        
    except Exception as e:
        logger.error(f"Error during JSON extraction: {e}")
        return None 