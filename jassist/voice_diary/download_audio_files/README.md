# Download Audio Files Module Documentation

## Overview
The `download_audio_files` module is designed to download audio files from Google Drive. It handles authentication, folder navigation, file filtering, and download management with configurable options.

## Scripts and Components

### config_loader.py
- **Primary Role**: Loads configuration settings from JSON files.
- **Key Function**: `load_config(config_path, template_path)`
  - **Parameters**: 
    - `config_path`: Path to the configuration file
    - `template_path`: Path to a template configuration file (optional)
  - **Returns**: A dictionary containing configuration settings
  - **Behavior**: 
    - If the config file exists, loads and validates it
    - If not, creates a new config file from the template if available
    - Validates that required keys exist in the configuration

### gdrive_auth.py
- **Primary Role**: Handles authentication with Google Drive API.
- **Key Function**: `authenticate_google_drive(config)`
  - **Parameters**: 
    - `config`: Dictionary containing authentication settings
  - **Returns**: A Google Drive service object if successful, None otherwise
  - **Behavior**:
    - Attempts to use an existing token from a pickle file
    - Refreshes the token if expired
    - Initiates a new OAuth flow if no valid token exists
    - Creates and returns a Google Drive API service

### gdrive_utils.py
- **Primary Role**: Provides utility functions for Google Drive operations.
- **Key Functions**:
  - `ensure_directory_exists(dir_path, description)`
    - **Parameters**: Path to create, description string
    - **Returns**: Nothing (not fruitful)
    - **Behavior**: Creates directory if it doesn't exist
  
  - `find_folder_by_name(service, folder_name)`
    - **Parameters**: Drive service, folder name to find
    - **Returns**: Folder ID if found, None otherwise
    - **Behavior**: Searches Google Drive for a folder with the given name
  
  - `list_files_in_folder(service, folder_id)`
    - **Parameters**: Drive service, folder ID
    - **Returns**: List of file objects (excluding subfolders)
    - **Behavior**: Lists all files in the specified folder
  
  - `download_file(service, file_id, file_path)`
    - **Parameters**: Drive service, file ID, local path to save
    - **Returns**: Dictionary with success status and path or error
    - **Behavior**: Downloads a file from Google Drive to local storage
  
  - `delete_file(service, file_id, file_name)`
    - **Parameters**: Drive service, file ID, optional file name for logging
    - **Returns**: Boolean indicating success
    - **Behavior**: Deletes a file from Google Drive
  
  - `generate_filename_with_timestamp(filename, timestamp_format)`
    - **Parameters**: Original filename, format for timestamp
    - **Returns**: New filename with timestamp prefixed
    - **Behavior**: Creates a timestamped version of the filename

### gdrive_downloader.py
- **Primary Role**: Primary module that coordinates the download process.
- **Key Functions**:
  - `run_download(config)`
    - **Parameters**: Configuration dictionary 
    - **Returns**: Boolean indicating overall success
    - **Behavior**: 
      - Authenticates with Google Drive
      - Processes each target folder
      - Handles dry-run mode if configured
  
  - `process_folder(service, folder_id, folder_name, config, dry_run)`
    - **Parameters**: Drive service, folder ID, folder name, config, dry run flag
    - **Returns**: Nothing (not fruitful)
    - **Behavior**:
      - Queries files in the specified folder
      - Filters for audio files based on extensions in config
      - Downloads each file
      - Optionally adds timestamps to filenames
      - Optionally deletes files after downloading

### download_audio_files_cli.py
- **Primary Role**: Command-line interface entry point.
- **Key Function**: `main()`
  - **Parameters**: None
  - **Returns**: Nothing (not fruitful)
  - **Behavior**:
    - Loads configuration (using template if needed)
    - Calls run_download() to start the process
    - Handles and logs exceptions

### download_config_sample.json
- **Primary Role**: Template for configuration settings.
- **Content**: JSON structure with settings for:
  - API scopes
  - Authentication details
  - Target folders to download from
  - Supported audio file types
  - Download options (timestamps, dry-run mode, delete after download)

## Execution Flow
The process follows this flow:
1. CLI script (`download_audio_files_cli.py`) is executed
2. Configuration is loaded via `config_loader.py`
3. `run_download()` authenticates with Google Drive using `gdrive_auth.py`
4. For each target folder specified in config:
   - Find the folder ID using `find_folder_by_name()`
   - List audio files in the folder using `list_files_in_folder()`
   - For each audio file:
     - Generate a filename (with timestamp if configured)
     - Download the file using `download_file()`
     - Optionally delete the source file using `delete_file()`

The scripts make extensive use of logging throughout the process using a custom logger setup from `jassist.voice_diary.logger_utils.logger_utils`. 