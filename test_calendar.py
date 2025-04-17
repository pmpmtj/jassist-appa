"""
Simple test script for testing the calendar functionality.
"""
import logging
import datetime
from pathlib import Path

from jassist.voice_diary.calendar import insert_into_calendar
from jassist.voice_diary.calendar.llm_parser import insert_into_calendar as insert_from_parser
from jassist.voice_diary.calendar.google_calendar import get_credentials_path

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("Testing calendar functionality...")
    
    # Check credentials path
    credentials_path = get_credentials_path()
    print(f"Credentials path: {credentials_path}")
    
    token_path = credentials_path / "token.json"
    cred_path = credentials_path / "credentials.json"
    
    print(f"Token file exists: {token_path.exists()}")
    print(f"Credentials file exists: {cred_path.exists()}")
    
    # Test text for calendar entry
    test_text = ("Schedule a meeting with John tomorrow at 3pm for project discussion. "
                "Set a reminder 30 minutes before the meeting.")
    
    # Test the direct import from calendar package
    print("\nTesting direct import from calendar package...")
    result1 = insert_into_calendar(test_text)
    print(f"Result: {'Success' if result1 else 'Failed'}")
    
    # Test the import from llm_parser
    print("\nTesting import from llm_parser...")
    result2 = insert_from_parser(test_text)
    print(f"Result: {'Success' if result2 else 'Failed'}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 