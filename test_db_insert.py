from jassist.voice_diary.db_utils.transcription_repository import save_transcription
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("test_db_insert")

def test_insert():
    """Test inserting a basic transcription into the database"""
    try:
        # Simple test data
        test_content = "This is a test transcription for database insertion."
        test_filename = "test_audio.wav"
        
        # Try to save to the database
        transcription_id = save_transcription(
            content=test_content,
            filename=test_filename,
            audio_path="C:/test/test_audio.wav",
            duration_seconds=3.5,
            metadata={"test": True, "purpose": "debugging"},
            tag="test_transcription"
        )
        
        if transcription_id:
            print(f"SUCCESS: Transcription saved with ID: {transcription_id}")
            return True
        else:
            print("FAILED: Could not save transcription")
            return False
            
    except Exception as e:
        logger.error(f"Exception during test: {e}")
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing database insertion...")
    result = test_insert()
    print(f"Test result: {'Passed' if result else 'Failed'}") 