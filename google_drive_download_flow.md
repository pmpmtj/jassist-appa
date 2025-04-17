# Google Drive Download Flow

This document provides a detailed explanation of the Google Drive file download process in the jassist application. The process involves several modules working together to authenticate with Google Drive, locate target folders, download files, and optionally delete them after downloading.

## Module Structure

The Google Drive download functionality is organized in the following modules:

```
jassist/voice_diary/
├── config/
│   └── download_config.json    # Production configuration
├── credentials/                # Storage for Google API credentials
├── logger_utils/               # Logging utilities 
├── downloaded/                 # Default download location
└── download_audio_files/
    ├── __init__.py
    ├── config_loader.py        # Loads configuration from JSON
    ├── download_config_sample.json  # Sample configuration template
    ├── download_audio_files_cli.py  # CLI entry point
    ├── gdrive_auth.py          # Google Drive authentication
    ├── gdrive_downloader.py    # Main download orchestration
    └── gdrive_utils.py         # Utility functions for Drive operations
```

## Configuration

The download process is configuration-driven using a JSON file. The configuration includes:

- API scopes and authentication settings
- Target folders to download from
- Supported audio file types
- Download options (timestamps, dry run, delete after download)

Example configuration (`download_config_sample.json`):
```json
{
    "version": "1.0.0",
    "api": {
      "scopes": ["https://www.googleapis.com/auth/drive"]
    },
    "auth": {
      "credentials_file": "gdrive_credentials.json",
      "token_file": "gdrive_token.pickle",
      "credentials_path": "jassist/voice_diary/credentials"
    },
    "folders": {
      "target_folders": ["root"]  
    },
    "audio_file_types": {
      "include": [".mp3", ".wav", ".m4a"]
    },
    "download": {
      "add_timestamps": true,
      "timestamp_format": "%Y%m%d_%H%M%S_%f",
      "dry_run": false,
      "delete_after_download": false
    }
}
```

## Download Process Flow

### Entry Point

The download process is initiated from `download_audio_files_cli.py`, which:
1. Sets up logging for the CLI process
2. Locates the config and template paths
3. Loads the configuration
4. Calls the main download function
5. Handles and logs any errors that occur

```python
def main():
    try:
        # Paths to config and template
        config_path = Path(__file__).parents[2] / "voice_diary" / "config" / "download_config.json"
        template_path = Path(__file__).parent / "download_config_sample.json"

        logger.info(f"Loading configuration from {config_path}")
        config = load_config(config_path, template_path)

        logger.info("Starting download process...")
        success = run_download(config)

        if success:
            logger.info("Download process completed successfully.")
        else:
            logger.warning("Download process finished with warnings or partial failure.")
    except Exception as e:
        logger.exception(f"Fatal error in CLI: {e}")
```

### Configuration Loading

The `config_loader.py` module handles loading and validating the configuration:

```python
def load_config(config_path: Path, template_path: Path = None) -> dict:
    def validate_config(config: dict) -> dict:
        required_keys = ["version", "api", "auth", "folders", "audio_file_types", "download"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        return config

    if config_path.exists():
        with open(config_path, "r", encoding=ENCODING) as f:
            config = json.load(f)
            return validate_config(config)
    elif template_path and template_path.exists():
        with open(template_path, "r", encoding=ENCODING) as src:
            data = json.load(src)
        # Ensure the directory exists before creating the config file
        ensure_directory_exists(config_path.parent, description="config directory")
        with open(config_path, "w", encoding=ENCODING) as dst:
            json.dump(data, dst, indent=4, sort_keys=True)
        logger.info(f"Created config from template at: {config_path}")
        return validate_config(data)
    else:
        raise FileNotFoundError("No config file or template available.")
```

### Authentication

The `gdrive_auth.py` module handles Google Drive authentication with enhanced error handling:

1. Checks for existing token and tries to load credentials
2. Refreshes token if expired
3. Performs new OAuth flow if needed
4. Builds and returns the Drive service
5. Properly handles and logs exceptions at each step

```python
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
```

### Main Download Process

The `gdrive_downloader.py` module orchestrates the download process with robust error handling:

1. Authenticates with Google Drive
2. For each target folder:
   - Finds the folder by name
   - If folder found, processes the files in that folder
   - Handles folder-specific errors gracefully
3. Provides clear visual feedback for dry run mode
4. Logs success/failure status

```python
def run_download(config: dict) -> bool:
    try:
        service = authenticate_google_drive(config)
        if not service:
            logger.error("Google Drive authentication failed.")
            return False

        target_folders = config['folders'].get('target_folders', ['root'])
        dry_run = config.get('download', {}).get('dry_run', False)

        if dry_run:
            logger.info("Running in DRY RUN mode")
            print("\n=== DRY RUN MODE - NO FILES WILL BE DOWNLOADED OR DELETED ===\n")

        for folder_name in target_folders:
            try:
                folder_id = 'root' if folder_name.lower() == 'root' else find_folder_by_name(service, folder_name)
                if not folder_id:
                    logger.warning(f"Folder '{folder_name}' not found. Skipping.")
                    continue

                logger.info(f"Processing folder: {folder_name} (ID: {folder_id})")
                process_folder(service, folder_id, folder_name, config, dry_run=dry_run)
            except Exception as e:
                logger.error(f"Error processing folder '{folder_name}': {e}")
                logger.debug(traceback.format_exc())

        logger.info("Google Drive download process completed.")
        return True

    except Exception as e:
        logger.error(f"Unexpected error in run_download: {e}")
        logger.debug(traceback.format_exc())
        return False
```

### Folder Processing

The `process_folder` function in `gdrive_downloader.py`:

1. Queries files in the folder
2. Filters for audio files based on extensions
3. Creates the download directory (if not exists)
4. For each audio file:
   - Adds timestamp to filename if configured
   - Downloads the file 
   - Optionally deletes the source file
5. Logs progress and completion status

```python
def process_folder(service, folder_id, folder_name, config, dry_run=False):
    try:
        query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size, modifiedTime, fileExtension)",
            pageSize=1000
        ).execute()

        all_items = results.get('files', [])
        audio_extensions = config.get('audio_file_types', {}).get('include', [])
        audio_items = [item for item in all_items if any(item['name'].lower().endswith(ext) for ext in audio_extensions)]

        # Downloads directory is hardcoded
        downloads_dir = "downloaded"
        base_download_dir = (Path(__file__).parent.parent / downloads_dir).resolve()
        ensure_directory_exists(base_download_dir, "download directory")

        for item in audio_items:
            item_id = item['id']
            item_name = item['name']
            output_filename = item_name

            if config.get('download', {}).get('add_timestamps', False):
                timestamp_format = config.get('download', {}).get('timestamp_format', '%Y%m%d_%H%M%S_%f')
                output_filename = generate_filename_with_timestamp(item_name, timestamp_format)

            output_path = base_download_dir / output_filename

            if dry_run:
                logger.info(f"Would download: {item_name} -> {output_path}")
                continue

            result = download_file(service, item_id, str(output_path))
            if result['success'] and config.get('download', {}).get('delete_after_download', False):
                delete_file(service, item_id, item_name)

        logger.info(f"Finished processing folder: {folder_name}")

    except Exception as e:
        logger.error(f"Error in process_folder for '{folder_name}': {e}")
        logger.debug(traceback.format_exc())
```

### Utility Functions

The `gdrive_utils.py` module provides several helper functions:

#### Ensure Directory Exists
```python
def ensure_directory_exists(dir_path: Path, description="directory"):
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created {description} at: {dir_path}")
    except Exception as e:
        logger.error(f"Error ensuring {description}: {e}")
        logger.debug(traceback.format_exc())
```

#### Find Folder by Name
```python
def find_folder_by_name(service, folder_name):
    try:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        folders = results.get('files', [])
        if folders:
            folder_id = folders[0]['id']
            logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")
            return folder_id
        logger.warning(f"No folder named '{folder_name}' found.")
    except Exception as e:
        logger.error(f"Error finding folder '{folder_name}': {e}")
        logger.debug(traceback.format_exc())
    return None
```

#### List Files in Folder
```python
def list_files_in_folder(service, folder_id):
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
        files = results.get('files', [])
        return [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']
    except Exception as e:
        logger.error(f"Error listing files in folder '{folder_id}': {e}")
        logger.debug(traceback.format_exc())
        return []
```

#### File Download
```python
def download_file(service, file_id, file_path):
    try:
        request = service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}% complete.")
        logger.info(f"Download completed: {file_path}")
        return {"success": True, "path": str(file_path)}
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {e}")
        logger.debug(traceback.format_exc())
        return {"success": False, "error": str(e)}
```

#### File Deletion
```python
def delete_file(service, file_id, file_name=None):
    try:
        service.files().delete(fileId=file_id).execute()
        logger.info(f"Deleted file: {file_name or file_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete file {file_name or file_id}: {e}")
        logger.debug(traceback.format_exc())
        return False
```

#### Filename with Timestamp
```python
def generate_filename_with_timestamp(filename, timestamp_format="%Y%m%d_%H%M%S_%f"):
    try:
        timestamp = datetime.datetime.now().strftime(timestamp_format)
        return f"{timestamp}_{filename}"
    except Exception as e:
        logger.error(f"Error generating timestamped filename for {filename}: {e}")
        logger.debug(traceback.format_exc())
        return filename
```

## Summary

The Google Drive download process follows these steps:

1. **Configuration**: Load JSON configuration with API settings, target folders, etc.
2. **Authentication**: Use OAuth to authenticate with Google Drive
3. **Folder Discovery**: Find specified target folders
4. **File Listing**: List files in the target folders
5. **File Filtering**: Filter for supported audio file types
6. **Download**: Download each file to the specified directory
7. **Cleanup**: Optionally delete files after download

The process has been enhanced with:
- Comprehensive error handling at every step
- Detailed logging with different severity levels
- Clear feedback for dry run mode
- Graceful handling of missing folders/files
- Improved directory structure ensuring
- Centralized configuration validation 