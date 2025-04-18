"""Simple test runner for the download_audio_files tests."""
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import pytest
import pytest

if __name__ == "__main__":
    # Run the tests
    test_path = "tests/jassist/voice_diary/download_audio_files"
    pytest.main(["-v", test_path]) 