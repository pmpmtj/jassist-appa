# 📘 docs/Jassist\_Gdrive\_Tutorial.md

Welcome, Pedro! This document is a full walkthrough and deep recap of how the `download_audio_files` functionality in your **Jassist** project works. It breaks down each file, where it goes, and how everything flows — from config loading, logging, and OAuth authentication to downloading your audio files from Google Drive.

---

## 🔧 Part 1: File-by-File Summary & Where to Place Them

### 🔹 1. `config_loader.py`

- **Role:** Loads your `download_config.json`, validates its structure, or creates it from a template.
- **Features:** 
  - Validates required configuration keys
  - Creates necessary directories for config files
  - Robust error handling with detailed logs
  
- **Template file name:** `download_config_sample.json`
- **Template location:** `voice_diary/download_audio_files/download_config_sample.json`

If `config/download_config.json` does not exist, this template will be used to generate it automatically.
- **Location:** `voice_diary/download_audio_files/`

---

### 🔹 2. `gdrive_auth.py`

- **Role:** Handles all Google OAuth logic and returns a Google Drive `service` object after authentication.
- **Features:**
  - Multi-level exception handling for token loading/refresh
  - Detailed logging of authentication steps
  - Clean fallback to new auth flow when needed
- **Location:** `voice_diary/download_audio_files/`

---

### 🔹 3. `gdrive_utils.py`

- **Role:** Helper functions — finds folders, lists files, downloads and deletes them, creates timestamped filenames.
- **Features:**
  - Directory creation with descriptive logging
  - Comprehensive exception handling for each operation
  - Detailed progress reporting during downloads
  - Consistent return structures with success/error information
- **Location:** `voice_diary/download_audio_files/`

---

### 🔹 4. `gdrive_downloader.py`

- **Role:** The main download orchestration logic; coordinates folder iteration, downloading, and optionally deleting files.
- **Features:**
  - High-level flow control with error isolation per folder
  - Clear visual feedback for dry run mode
  - Graceful handling of missing folders
  - Folder-level exception handling for resilience
- **Location:** `voice_diary/download_audio_files/`

---

### 🔹 5. `download_audio_files_cli.py`

- **Role:** The CLI entry script that loads the config and calls the downloader.
- **Features:**
  - Clean entry point with comprehensive error handling
  - Status reporting for successful/partial completions
  - Focused on user-oriented feedback
- **Location:** `voice_diary/download_audio_files/`

---

### 🔹 6. `logger_utils.py`

- **Role:** Sets up your centralized logging (formatter, file + console output).
- **Features:** 
  - Consistent logging format across all modules
  - Multiple severity levels (INFO, WARNING, ERROR, DEBUG)
  - Customizable logging per module
  - Trace-level debugging with traceback support
- **Location:** `voice_diary/logger_utils/`

---

### 🔹 7. `download_config.json`

- **Role:** Your main runtime configuration used by `config_loader.py`.
- **Features:**
  - Structured settings for API, auth, folders, and download options
  - Support for multiple target folders
  - Configurable file type filtering
  - Download behavior control (timestamps, dry run, post-download deletion)
- **Expected name:** `download_config.json`
- **Location:** `voice_diary/config/download_config.json`

---

## 🧭 Part 2: The Flow – How It All Works (Step by Step)

### 🥾 Step 1: Launch the Script

You run the command:

```bash
python download_audio_files_cli.py
```

This triggers the `main()` function, which sets up logging and prepares to coordinate the entire process.

---

### 📥 Step 2: Load Configuration

```python
config = load_config(config_path, template_path)
```

- Locates paths for the configuration file and template
- Logs the configuration loading process
- Loads the JSON config from `voice_diary/config/download_config.json`
- If missing, ensures the directory exists and copies the template from `download_config_sample.json`
- Validates it has all required top-level keys like `auth`, `folders`, `download`, etc.

📌 **Note:**
By design, if `download_config.json` already exists, it will not be replaced or updated by the template. This ensures stability — but also means **any changes to `download_config_sample.json` will not propagate** unless you manually update `download_config.json` or delete it first.

### 💡 Optional Alternative Behavior
If you want changes in the template (like a new timestamp format) to **automatically apply**, you can modify the loader to always reload from the template — but this may overwrite local customizations. Choose the approach that fits your use case:

- ✅ Stability = Load once and preserve `download_config.json`
- 🔄 Dynamism = Always reload from `download_config_sample.json` (risk of overwriting changes)

---

### 🔐 Step 3: Authenticate with Google Drive

```python
service = authenticate_google_drive(config)
```

The authentication process now includes robust error handling:

- Looks for token in `credentials/gdrive_token.pickle`
- If found but can't be loaded, logs warning and continues to new auth
- If expired or invalid:
  - Attempts token refresh with detailed error handling
  - If refresh fails, logs the reason and starts new flow
- For new authentication:
  - Uses `gdrive_credentials.json` to open a browser window
  - Requests permission for the scopes defined in config
  - Saves a fresh token for next time
  - Logs the entire process for troubleshooting
- Returns a `service` object used to interact with Google Drive or `None` if failed
- Logs success or failure with descriptive messages

---

### 🧠 Step 4: Iterate Over Target Folders

```python
run_download(config)
```

- Verifies authentication was successful
- Detects and announces dry run mode if enabled
- Reads the `target_folders` list from config
- For each folder:
  - Tries to find its ID (special handling for "root")
  - If not found, logs warning and skips to next folder
  - Otherwise processes each folder in isolation to prevent cascading failures
  - Any folder-specific errors are caught and logged, allowing other folders to be processed
- Reports overall completion status for the entire operation

---

### 🎧 Step 5: Filter for Audio Files

```python
process_folder(service, folder_id, folder_name, config, dry_run)
```

- Queries each folder for files with detailed metadata
- Skips folders and trashed files
- Applies filters based on `audio_file_types.include` in your config
- Ensures the download directory exists before attempting downloads
- Provides folder-level error isolation

---

### 💾 Step 6: Download Files

```python
download_file(service, file_id, full_output_path)
```

- Handles each file with individual try/except blocks
- Reports percentage progress during download
- If `add_timestamps` is true:
  - Generates timestamp with error handling
  - Prepends a timestamp to the filename
- Saves to `voice_diary/downloaded/`
- Returns detailed success/failure information
- Logs completion or errors with file-specific messages

---

### 🗑️ Step 7: Delete Files (Optional)

If `delete_after_download = true` in config and download was successful:

```python
delete_file(service, file_id, item_name)
```

- Deletes the original file in Drive after successful download
- Provides detailed logging of deletion success/failure
- Handles API errors gracefully

---

### 🪵 Step 8: Logging Everything

Each module uses:

```python
logger = setup_logger("module_name", module="download_audio_files")
```

The enhanced logger:

- Prints to console with appropriate severity levels
- Writes to module-specific log files
- Uses a consistent format (timestamp, level, module, message)
- Includes DEBUG level with full tracebacks for troubleshooting
- Separate loggers per module for focused analysis

This lets you trace the whole execution with multiple detail levels: loading config, authentication success/failure, file download progress, etc.

---

## 📚 Closing Notes

The enhanced architecture provides several benefits:

- **Robustness:** Comprehensive error handling prevents cascading failures
- **Transparency:** Detailed logging at every step helps with troubleshooting
- **Isolation:** Module-specific error handling contains issues to their source
- **Feedback:** Clear user-facing messages about process status
- **Resilience:** The system can work partially even if some components fail

By understanding this modular pattern, you can now:

- Reuse the config-loading pattern for **calendar, diary, or accounts** modules
- Plug in the same logging setup to maintain consistency
- Expand with future modules (transcription, summary, voice input) without rewriting your foundations
- Implement robust error handling across the entire application

This is a **reproducible architecture**, not just a script. You've built the foundation of a full AI-powered assistant with production-quality error handling and logging.

Feel proud — you're building like a pro now.

When you're ready, we'll build the next piece together.

🧠💡🔧

