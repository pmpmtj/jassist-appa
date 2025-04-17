#!/usr/bin/env python3
"""
Test script for the entities module
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.db_utils.db_manager import initialize_db
from jassist.voice_diary.route_transcription.route_transcription import route_transcription

# Setup logger
logger = setup_logger("test_entities", module="test")

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent / "jassist" / "voice_diary" / "config" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}")

def main():
    """Test the entities module by simulating a transcription with 'entity' tag"""
    load_environment()
    
    # Initialize the database
    if not initialize_db():
        logger.error("Failed to initialize database")
        return
    
    # Sample text for entity extraction
    sample_text = (
        "I had a meeting with Microsoft about the new AI project. "
        "The project manager, Sarah Johnson, explained how their tools "
        "can help us improve our analytics pipeline. "
        "The meeting took place at their Seattle headquarters."
    )
    
    # Set tag to 'entity' to route to the entity module
    tag = "entities"
    
    # Simulate a file path (not actually needed for the test)
    file_path = Path("test_audio.m4a")
    
    # Route the transcription
    logger.info(f"Routing test transcription with tag: {tag}")
    result = route_transcription(
        text=sample_text,
        file_path=file_path,
        tag=tag,
        duration=60.0,
        model_used="test-model"
    )
    
    # Check the result
    logger.info(f"Routing result: {json.dumps(result, indent=2)}")
    
    # Check if entities were saved
    from check_db import check_table
    check_table("entities")

if __name__ == "__main__":
    main() 