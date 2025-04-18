# config_loader.py
import json
from pathlib import Path
from jassist.voice_diary.download_audio_files.gdrive_utils import ensure_directory_exists
from jassist.voice_diary.logger_utils.logger_utils import setup_logger, ENCODING

logger = setup_logger("config_loader", module="download_audio_files")

def load_config(config_path: Path, template_path: Path = None) -> dict:
    def validate_config(config: dict) -> dict:
        required_keys = ["api", "auth", "folders", "audio_file_types", "download"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        
        return config

    # Ensure the directory exists for all cases
    ensure_directory_exists(config_path.parent, description="config directory")
    
    if config_path.exists():
        with open(config_path, "r", encoding=ENCODING) as f:
            config = json.load(f)
            return validate_config(config)
    elif template_path and template_path.exists():
        with open(template_path, "r", encoding=ENCODING) as src:
            data = json.load(src)
        # Create the config file
        with open(config_path, "w", encoding=ENCODING) as dst:
            json.dump(data, dst, indent=4, sort_keys=True)
        logger.info(f"Created config from template at: {config_path}")
        return validate_config(data)
    else:
        raise FileNotFoundError("No config file or template available.")
