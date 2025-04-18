#!/usr/bin/env python3
"""
Test script for the classification module.
"""
import sys
from pathlib import Path
from jassist.voice_diary.classification.classification_processor import classify_text
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("test_classification")

def main():
    """
    Test the classification module with some sample texts.
    """
    test_texts = [
        "I feel happy today because the weather is nice. I went for a walk in the park.",
        "Schedule a meeting with John tomorrow at 3PM to discuss the project.",
        "Reminder to buy milk, eggs, and bread from the grocery store.",
        "Pay $50 for the electricity bill by next Friday.",
        "John Smith's phone number is 555-123-4567 and his email is john@example.com.",
        "Microsoft is a technology company based in Redmond, Washington. Their website is microsoft.com."
    ]
    
    logger.info("Testing classification module...")
    
    for i, text in enumerate(test_texts):
        logger.info(f"\nTest {i+1}: {text}")
        result = classify_text(text)
        logger.info(f"Classification result: {result}")
    
    logger.info("Classification tests completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 