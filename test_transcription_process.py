"""
Test script for the transcription and routing process.
"""
import logging
from pathlib import Path

from jassist.voice_diary.route_transcription.route_transcription import route_transcription

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    print("Testing transcription and routing process...")
    
    # Path to the test file
    test_file_path = Path("jassist/voice_diary/downloaded/calendar_test.txt")
    
    if not test_file_path.exists():
        print(f"Error: Test file not found at {test_file_path}")
        return
    
    # Read the test file
    with open(test_file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"Text from file: {text}")
    
    # Route the transcription with a calendar tag
    result = route_transcription(
        text=text,
        file_path=test_file_path,
        tag="calendar",
        duration=30.0,
        model_used="gpt-4"
    )
    
    print("\nRouting result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 