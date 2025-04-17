# gdrive_auth.py
import pickle
import traceback
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("gdrive_auth", module="download_audio_files")

def authenticate_google_drive(config: dict):
    try:
        auth_cfg = config.get("auth", {})
        api_cfg = config.get("api", {})

        credentials_file = Path(auth_cfg.get("credentials_path", "credentials")) / auth_cfg.get("credentials_file", "gdrive_credentials.json")
        token_file = credentials_file.parent / auth_cfg.get("token_file", "gdrive_token.pickle")
        scopes = api_cfg.get("scopes", ["https://www.googleapis.com/auth/drive"])

        creds = None
        if token_file.exists():
            try:
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")
                logger.debug(traceback.format_exc())

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Token refreshed successfully.")
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                logger.debug(traceback.format_exc())
                creds = None

        if not creds:
            logger.info("Starting new OAuth flow.")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes=scopes)
            creds = flow.run_local_server(port=0)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("New credentials saved.")

        service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service created successfully.")
        return service

    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        logger.debug(traceback.format_exc())
        return None
