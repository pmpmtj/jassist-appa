import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("db_config", module="db_utils")

# Load .env from config/
env_path = Path(__file__).parents[1] / "config" / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded .env from {env_path}")
else:
    logger.warning(f".env file not found at expected location: {env_path}")

def get_db_url():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment. Make sure .env file exists and contains DATABASE_URL.")
        # No fallback to config file anymore
        return None
    logger.debug(f"Using DB URL: {db_url}")
    logger.info("Using DB URL (connection string available)")
    return db_url
