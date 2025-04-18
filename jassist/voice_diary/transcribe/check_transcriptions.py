"""
Command-line utility to check recent transcriptions in the database.
"""

from jassist.voice_diary.transcribe.db import display_recent_transcriptions

def main():
    """
    Command-line entry point to check recent transcriptions.
    """
    print("Checking recent transcriptions...")
    display_recent_transcriptions(limit=5)

if __name__ == "__main__":
    main() 