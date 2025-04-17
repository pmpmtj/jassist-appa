"""
Google Calendar integration module.

This module handles interactions with the Google Calendar API.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .utils.config_manager import load_calendar_config, get_script_dir
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("google_calendar", module="calendar")

# Define the scopes required for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials_path() -> Path:
    """
    Get path to Google API credentials.
    
    Returns:
        Path: Path to the credentials directory
    """
    config = load_calendar_config()
    
    # Get the current module's directory
    base_dir = Path(__file__).resolve().parent
    
    # Get credentials directory from config or use default
    credentials_dir = config.get('paths', {}).get('credentials_directory', 'credentials')
    credentials_path = base_dir / credentials_dir
    
    # Create directory if it doesn't exist
    if not credentials_path.exists():
        credentials_path.mkdir(parents=True, exist_ok=True)
    
    return credentials_path

def get_calendar_service():
    """
    Get an authenticated Google Calendar service.
    
    Returns:
        Resource: Google Calendar service
    """
    creds = None
    credentials_dir = get_credentials_path()
    token_path = credentials_dir / "token.json"
    credentials_path = credentials_dir / "credentials.json"

    # Check if token already exists
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Google API credentials not found at {credentials_path}. "
                    "Download credentials.json from the Google Developer Console "
                    "and place it in the credentials directory."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def insert_event_into_google_calendar(event_data: Dict[str, Any]) -> Optional[str]:
    """
    Insert an event into Google Calendar.
    
    Args:
        event_data: Dictionary containing event data
        
    Returns:
        str: URL to the created event, or None if creation failed
    """
    config = load_calendar_config()
    
    # Check if Google Calendar integration is enabled
    use_google_calendar = config.get('google_calendar', {}).get('use_google_calendar', True)
    if not use_google_calendar:
        logger.info("Google Calendar integration is disabled in config")
        return None
    
    calendar_id = config.get('google_calendar', {}).get('calendar_id', 'primary')
    
    try:
        service = get_calendar_service()
        event = service.events().insert(
            calendarId=calendar_id,
            body=event_data
        ).execute()

        logger.info(f"Event created: {event.get('htmlLink')}")
        return event.get("htmlLink")
        
    except HttpError as error:
        logger.error(f"An error occurred inserting event: {error}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error inserting event: {e}")
        return None 