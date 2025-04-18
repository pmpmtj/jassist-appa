import logging
import datetime
from pathlib import Path
import json

from jassist.voice_diary.transcribe.config_loader import load_config, load_environment
from jassist.voice_diary.transcribe.model_handler import get_openai_client
from jassist.voice_diary.transcribe.file_processor import get_audio_files, calculate_duration
from jassist.voice_diary.transcribe.transcriber import transcribe_file
from jassist.voice_diary.classification.classification_processor import classify_text
from jassist.voice_diary.route_transcription.route_transcription import route_transcription
from jassist.voice_diary.utils.file_tools import clean_directory
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.db_utils.db_manager import initialize_db, save_transcription

logger = setup_logger("transcribe_cli", module="transcribe")

def save_to_text_file(transcription: str, output_dir: Path, prefix: str):
    """Save transcription text to a file with timestamp in the filename."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{prefix}.txt"
        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        logger.info(f"Saved transcription to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save transcription to file: {e}")
        return False

def main():
    logger.info("Starting transcription CLI...")

    # Step 1: Load config and env
    load_environment()
    config = load_config()

    # Step 2: Initialize OpenAI
    client = get_openai_client()
    if not client:
        logger.error("Cannot proceed without OpenAI client.")
        return

    # Step 3: Initialize database
    if not initialize_db():
        logger.error("Database initialization failed.")
        return

    # Step 4: Resolve paths with absolute paths
    script_dir = Path(__file__).resolve().parent
    voice_diary_dir = script_dir.parent
    
    # Hardcoded downloads directory path (design decision)
    # No longer read from config file
    downloads_dir_config = "downloaded"
    logger.info(f"Using hardcoded downloads directory: {downloads_dir_config}")
    
    # Get output directory from transcribe config's paths section
    output_dir_config = config.get("paths", {}).get("output_dir", "transcriptions")
    
    # Create absolute paths - handle both relative and absolute paths in an OS-agnostic way
    downloads_dir = Path(downloads_dir_config)
    if not downloads_dir.is_absolute():
        # If path is relative with "../" notation, resolve correctly
        if "../" in downloads_dir_config:
            # Use Path's resolve mechanism to correctly handle parent directory references
            downloads_dir = (voice_diary_dir / downloads_dir_config).resolve()
        else:
            downloads_dir = voice_diary_dir / downloads_dir_config
    
    output_dir = Path(output_dir_config)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir_config
    
    logger.info(f"Using downloads directory: {downloads_dir}")
    logger.info(f"Using output directory: {output_dir}")

    # Verify the downloads directory exists
    if not downloads_dir.exists():
        logger.error(f"Downloads directory not found: {downloads_dir}. Cannot proceed.")
        return

    # Step 5: Get files
    files = get_audio_files(downloads_dir)
    if not files:
        logger.warning("No audio files found.")
        return

    successful = 0
    failed = 0

    # Step 6: Process each file
    for file_path in files:
        try:
            logger.info(f"Processing file: {file_path.name}")
            duration = calculate_duration(file_path)
            if duration is None:
                logger.warning(f"Could not determine duration for {file_path.name}, using default of 0.0")
                duration = 0.0
                
            transcription = transcribe_file(client, file_path, config)

            if not transcription:
                logger.error(f"Failed to transcribe file: {file_path.name}")
                failed += 1
                continue

            # Get the text from the transcription
            transcription_text = transcription.get("text", "") if isinstance(transcription, dict) else transcription
            
            # STEP 1: SAVE RAW TRANSCRIPTION TO DATABASE IMMEDIATELY
            try:
                metadata = {
                    "model_used": config.get("default_model"),
                    "transcribed_at": datetime.datetime.now().isoformat(),
                    "raw": True  # Mark this as a raw transcription
                }
                
                raw_db_id = save_transcription(
                    content=transcription_text,
                    filename=file_path.name,
                    audio_path=str(file_path),
                    duration_seconds=duration,
                    metadata=metadata,
                    tag="raw_transcription"  # Special tag for raw transcriptions
                )
                
                if raw_db_id:
                    logger.info(f"Raw transcription saved to database with ID: {raw_db_id}")
                else:
                    logger.error("Failed to save raw transcription to database.")
            except Exception as e:
                logger.error(f"Error saving raw transcription to database: {e}")
                # Continue processing even if database save fails
            
            # STEP 2: SAVE TO TEXT FILE
            if not save_to_text_file(transcription_text, output_dir, file_path.stem):
                logger.warning(f"Continuing processing despite file save error for {file_path.name}")
            
            # Add pause after saving raw data but before classification
            #print(f"\nRaw transcription saved to database with ID: {raw_db_id}")
            #print(f"Content: {transcription_text[:150]}{'...' if len(transcription_text) > 150 else ''}")
            #input("Press Enter to continue with classification and routing...")
            
            # Now continue with classification and routing
            try:
                tag = classify_text(transcription)
                logger.info(f"Classification result: {tag}")
            except Exception as e:
                logger.error(f"Classification failed: {e}")
                tag = "unclassified"  # Default classification on error
            
            try:
                # Route transcription to appropriate handlers
                result = route_transcription(
                    text=transcription_text,
                    file_path=file_path,
                    tag=tag,
                    duration=duration,
                    model_used=config.get("default_model")
                )
                
                if result["status"] == "success":
                    logger.info(f"Transcription processed successfully with ID: {result['db_id']}")
                    if result.get("additional_processing"):
                        logger.info(f"Additional processing performed for tag: {tag}")
                    successful += 1
                else:
                    logger.error(f"Failed to process transcription: {result.get('message', 'Unknown error')}")
                    failed += 1
            except Exception as e:
                logger.error(f"Error during transcription routing: {e}")
                failed += 1
        except Exception as e:
            logger.error(f"Unhandled error processing file {file_path.name}: {e}")
            failed += 1

    # Step 7: Summary
    total = successful + failed
    logger.info(f"Completed {total} file(s): {successful} succeeded, {failed} failed.")
    
    # Step 8: Clean the downloads directory after processing
    if total > 0:  # Only clean if files were processed
        try:
            logger.info("Cleaning downloads directory...")
            clean_result = clean_directory(downloads_dir)
            if clean_result["status"] == "success":
                logger.info(f"{clean_result.get('files_deleted', 0)} files deleted from downloads directory.")
            else:
                logger.error(f"Failed to clean downloads directory: {clean_result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error during directory cleanup: {e}")

if __name__ == "__main__":
    main()
