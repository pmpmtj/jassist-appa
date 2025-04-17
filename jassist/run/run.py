#!/usr/bin/env python3
"""
Test script that sequentially runs voice diary processing steps:
1. Download audio files
2. Transcribe the downloaded files
"""
import sys
import logging
import argparse
from pathlib import Path
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("run", module="run")

def main():
    """
    Main function that sequentially runs voice diary modules
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run voice diary processing sequence")
    parser.add_argument("--reset-assistant", action="store_true", 
                        help="Reset the OpenAI assistants before running")
    parser.add_argument("--reset-module", 
                        help="Specify which module's assistants to reset (default: all)")
    args = parser.parse_args()
    
    # Reset assistant if requested
    if args.reset_assistant:
        try:
            # Use the new shared reset utility instead of local implementation
            from jassist.voice_diary.utils.reset_assistants_cli import reset_module_assistants, reset_all_assistants
            
            if args.reset_module:
                logger.info(f"Resetting assistants for module: {args.reset_module}")
                reset_module_assistants(args.reset_module)
            else:
                logger.info("Resetting all assistants")
                reset_all_assistants()
                
            logger.info("Assistant reset completed")
        except Exception as e:
            logger.warning(f"Failed to reset assistants: {e}")
    
    logger.info("Starting voice diary processing sequence")
    
    try:
        # Step 1: Run download_audio_files_cli
        logger.info("Step 1: Running download_audio_files_cli")
        from jassist.voice_diary.download_audio_files.download_audio_files_cli import main as download_main
        download_main()
        
        # Step 2: Run transcribe_cli
        logger.info("Step 2: Running transcribe_cli")
        from jassist.voice_diary.transcribe.transcribe_cli import main as transcribe_main
        transcribe_main()
        
        logger.info("Voice diary processing sequence completed successfully")
        return 0
    except Exception as e:
        logger.exception(f"Error in processing sequence: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 