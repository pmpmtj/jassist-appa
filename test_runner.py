"""Simple test runner for the voice_diary tests."""
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import pytest
import pytest

if __name__ == "__main__":
    # Define test paths
    test_paths = [
        "tests/jassist/voice_diary/download_audio_files",
        "tests/jassist/voice_diary/transcribe"
    ]
    
    # Run each test suite sequentially
    for test_path in test_paths:
        print(f"\n{'=' * 80}")
        print(f"Running tests in {test_path}")
        print(f"{'=' * 80}\n")
        pytest.main(["-v", test_path]) 