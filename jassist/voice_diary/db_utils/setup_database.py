#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from pathlib import Path
from jassist.voice_diary.db_utils.db_connection import initialize_db
from jassist.voice_diary.db_utils.db_schema import create_tables
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("setup_database", module="db_utils")

def main():
    parser = argparse.ArgumentParser(description='Set up the PostgreSQL database')
    args = parser.parse_args()

    logs_dir = Path(__file__).parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logs_dir / "setup_database.log")
        ]
    )
    logger = logging.getLogger(__name__)

    env_path = Path(__file__).parents[1] / "config" / ".env"
    if not env_path.exists():
        logger.warning(f".env file not found at expected location: {env_path}")
        response = input("Continue without .env? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    logger.info("Initializing database...")
    if initialize_db():
        logger.info("Creating database tables...")
        if create_tables():
            logger.info("Database setup completed successfully.")
        else:
            logger.error("Table creation failed.")
            sys.exit(1)
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
