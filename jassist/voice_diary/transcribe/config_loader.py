import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

ENCODING = "utf-8"

logger = setup_logger("config_loader", module="transcribe")

# Define paths
MODULE_DIR = Path(__file__).parent
CONFIG_PATH = MODULE_DIR / "config" / "config_transcribe.json"
ENV_PATH = MODULE_DIR.parents[1] / "voice_diary" / "config" / ".env"  # voice_diary/config/.env

def convert_string_booleans(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert 'true'/'false' strings into Python booleans."""
    for key, value in config_dict.items():
        if isinstance(value, dict):
            convert_string_booleans(value)
        elif isinstance(value, str):
            if value.lower() == "true":
                config_dict[key] = True
            elif value.lower() == "false":
                config_dict[key] = False
    return config_dict

def create_sample_config(path: Path) -> Dict[str, Any]:
    """Create a sample config file with default values."""
    default_config = {
        "transcriptions_dir": "transcriptions",
        "output_file": "diary_transcription.txt",
        "paths": {
            "output_dir": "transcriptions"
        },
        "models": {
            "whisper-1": {
                "enabled": True,
                "description": "Original Whisper model, good general-purpose speech to text",
                "prompt": "Transcribe the given audio into English.",
                "supports_language_parameter": True
            }
        },
        "default_model": "whisper-1",
        "settings": {
            "language": "en",
            "prompt": "Transcribe the given audio into English.",
            "response_format": "json"
        },
        "cost_management": {
            "max_audio_duration_seconds": 300,
            "warn_on_large_files": True
        },
        "transcription": {
            "batch_processing": True,
            "individual_files": True,
            "batch_output_file": "batch_transcription.txt"
        }
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=ENCODING) as f:
        json.dump(default_config, f, indent=4)
    logger.info(f"Sample transcription config created at: {path}")
    return default_config

def load_config() -> Dict[str, Any]:
    """Load or create the transcription config."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding=ENCODING) as f:
                config = json.load(f)
            logger.info(f"Loaded transcription config from: {CONFIG_PATH}")
            return convert_string_booleans(config)
        except Exception as e:
            logger.warning(f"Failed to parse config: {e}")
    
    logger.warning("Transcription config not found. Creating sample.")
    return create_sample_config(CONFIG_PATH)

def load_environment():
    """Load .env file for API keys and database config."""
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
        logger.info(f"Environment variables loaded from: {ENV_PATH}")
    else:
        logger.warning(f".env file not found at expected location: {ENV_PATH}")
