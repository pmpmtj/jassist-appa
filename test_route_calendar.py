"""
Test script for the route_transcription function with calendar data.
"""
import logging
from pathlib import Path
import json

from jassist.voice_diary.route_transcription.route_transcription import route_transcription, parse_complex_llm_response
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

# Setup logging
logger = setup_logger("test_route_calendar")

def main():
    print("Testing route_transcription with calendar functionality...")
    
    # Test case 1: Simple calendar entry
    test_text_1 = ("Schedule a meeting with John tomorrow at 3pm for project discussion. "
                  "Set a reminder 30 minutes before the meeting.")
    
    # Test case 2: More detailed calendar entry
    test_text_2 = ("Add to my calendar: Product demo with client on Friday at 10am. "
                  "It will last for 1 hour. Location is in the conference room. "
                  "Send invites to team@example.com.")
    
    # Create a mock file path
    file_path = Path("test_audio.wav")
    
    # Test the complex LLM response parser directly first
    print("\n---------- Testing Complex LLM Response Parser ----------")
    complex_llm_sample = """
    text: "Schedule a team meeting for tomorrow at 2pm."
    tag: calendar
    
    text: "Remind me to call John about the proposal."
    tag: reminder
    
    text: "Book a flight to New York for next Monday."
    tag: calendar
    """
    
    parsed_entries = parse_complex_llm_response(complex_llm_sample)
    print(f"Parsed {len(parsed_entries)} entries from complex LLM response:")
    for i, entry in enumerate(parsed_entries):
        print(f"Entry {i+1}:")
        print(f"  Text: {entry['text']}")
        print(f"  Tag: {entry['tag']}")
    
    # Better test case for multiple entries
    print("\n---------- Test Case 3: Multiple Calendar Entries (Improved) ----------")
    
    # Create a cleaner complex LLM response with multiple entries
    improved_complex_tag = """
text: "Schedule a team meeting for tomorrow at 2pm."
tag: calendar

text: "Remind me to call John about the proposal."
tag: reminder

text: "Book a flight to New York for next Monday."
tag: calendar
"""
    
    result_3 = route_transcription(
        text="This is a combined transcription with multiple entries.",
        file_path=file_path,
        tag=improved_complex_tag,
        duration=60.0,
        model_used="test"
    )
    
    print("Result:")
    print(json.dumps(result_3, indent=2))
    
    # Test with simple calendar entry
    print("\n---------- Test Case 1: Simple Calendar Entry ----------")
    result_1 = route_transcription(
        text=test_text_1,
        file_path=file_path,
        tag="calendar",
        duration=30.0,
        model_used="test"
    )
    
    print("Result:")
    print(json.dumps(result_1, indent=2))
    
    # Test with more detailed calendar entry
    print("\n---------- Test Case 2: Detailed Calendar Entry ----------")
    result_2 = route_transcription(
        text=test_text_2,
        file_path=file_path,
        tag="calendar",
        duration=45.0,
        model_used="test"
    )
    
    print("Result:")
    print(json.dumps(result_2, indent=2))
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 