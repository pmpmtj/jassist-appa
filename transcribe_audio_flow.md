# Audio Transcription Process Flow

This document provides a detailed explanation of the audio transcription process in the jassist application. The process involves several modules working together to transcribe audio files, classify the content, and route the transcriptions to the appropriate handling modules.

## Module Structure

The audio transcription functionality is organized in the following modules:

```
jassist/voice_diary/
├── config/
│   └── .env                     # Environment variables for API keys
├── downloaded/                  # Audio files download directory
├── transcriptions/              # Transcribed text output directory
├── logger_utils/                # Logging utilities 
├── transcribe/
│   ├── __init__.py
│   ├── config/
│   │   └── config_transcribe.json  # Transcription configuration
│   ├── config_loader.py         # Loads configuration from JSON and environment
│   ├── transcribe_cli.py        # Main CLI entry point
│   ├── transcriber.py           # Core transcription logic
│   ├── model_handler.py         # OpenAI client and model selection
│   ├── file_processor.py        # Audio file detection and processing
│   ├── classifier.py            # Content classification using LLM
│   ├── check_db.py              # Database validation
│   └── path_check.py            # Path validation utilities
└── route_transcription/
    ├── __init__.py
    ├── route_transcription.py   # Routes transcriptions to modules
    └── db_interactions.py       # Database storage utilities
```

## Configuration

The transcription process is configuration-driven using a JSON file. The configuration includes:

- Model selection and settings
- Language and prompt for transcription
- Output directories and file naming
- Cost management settings
- Batch processing options

Example configuration (`config_transcribe.json`):
```json
{
  "output_file": "diary_transcription.txt",
  "paths": {
    "output_dir": "../transcriptions"
  },
  "models": {
    "whisper-1": {
      "enabled": true,
      "description": "Original Whisper model, good general-purpose speech to text",
      "prompt": "Transcribe the given audio.",
      "response_format": "json",
      "supports_language_parameter": true
    }
  },
  "default_model": "whisper-1",
  "settings": {
    "language": "en",
    "prompt": "Transcribe the given audio.",
    "response_format": "json"
  },
  "cost_management": {
    "max_audio_duration_seconds": 300,
    "warn_on_large_files": true
  },
  "transcription": {
    "batch_processing": true,
    "individual_files": true,
    "batch_output_file": "batch_transcription.txt"
  }
}
```

## Transcription Process Flow

### Entry Point

The transcription process is initiated from `transcribe_cli.py`, which:
1. Sets up logging for the CLI process
2. Loads environment variables and configuration
3. Initializes the OpenAI client
4. Resolves absolute file paths
5. Processes audio files
6. Routes transcriptions to appropriate modules
7. Cleans up temporary files

```python
def main():
    logger.info("Starting transcription CLI...")

    # Step 1: Load config and env
    load_environment()
    config = load_config()

    # Step 2: Initialize OpenAI
    client = get_openai_client()
    if not client:
        logger.error("Cannot proceed without OpenAI client.")
        return

    # Step 3: Resolve paths with absolute paths
    script_dir = Path(__file__).resolve().parent
    voice_diary_dir = script_dir.parent
    
    # Hardcoded downloads directory path (design decision)
    downloads_dir_config = "downloaded"
    logger.info(f"Using hardcoded downloads directory: {downloads_dir_config}")
    
    # Get output directory from transcribe config's paths section
    output_dir_config = config.get("paths", {}).get("output_dir", "transcriptions")
    
    # Create absolute paths - handle both relative and absolute paths
    downloads_dir = Path(downloads_dir_config)
    if not downloads_dir.is_absolute():
        if "../" in downloads_dir_config:
            downloads_dir = (voice_diary_dir / downloads_dir_config).resolve()
        else:
            downloads_dir = voice_diary_dir / downloads_dir_config
    
    output_dir = Path(output_dir_config)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir_config
    
    # Step 4: Process files and route transcriptions
    # (continues...)
```

### Configuration Loading

The `config_loader.py` module handles loading configuration and environment variables:

1. Defines default paths for configuration
2. Loads or creates configuration file
3. Provides utilities for type conversion
4. Loads environment variables for API keys

```python
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
```

### Audio File Processing

The `file_processor.py` module provides utilities for locating and processing audio files:

1. Finds audio files in the downloads directory
2. Sorts files chronologically
3. Calculates audio duration using ffprobe
4. Provides fallback duration estimation based on file size

```python
def get_audio_files(directory: Union[str, Path]) -> List[Path]:
    """
    Locate all audio files in a directory and sort them chronologically.
    """
    # Define common audio file extensions
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.mp4', '.aiff', '.opus'}
    
    directory = Path(directory)
    if not directory.exists():
        logger.error(f"Audio directory does not exist: {directory}")
        return []

    # Filter for only audio files using the extensions
    files = [f for f in directory.glob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
    if not files:
        logger.warning(f"No audio files found in {directory}.")
        return []

    def extract_timestamp(path: Path):
        match = re.search(r"(\d{8}_\d{6})", path.name)
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
            except ValueError:
                pass
        return datetime.datetime.fromtimestamp(path.stat().st_ctime)

    sorted_files = sorted(files, key=extract_timestamp)
    logger.info(f"{len(sorted_files)} audio files sorted by timestamp.")
    return sorted_files
```

### OpenAI Client Initialization

The `model_handler.py` module handles creating the OpenAI client and selecting the transcription model:

1. Loads API key from environment variables
2. Creates the OpenAI client
3. Selects an appropriate transcription model based on configuration
4. Provides fallbacks when configuration is incomplete

```python
def get_openai_client() -> Optional["OpenAI"]:
    """
    Create and return an OpenAI client using API key from environment.
    """
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI Python library is not installed. Install with `pip install openai`.")
        return None

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY in environment.")
        return None

    try:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client successfully initialized.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None

def get_transcription_model(config: Dict[str, Any]) -> str:
    """
    Choose which transcription model to use based on the config.
    """
    models = config.get("models", {})
    default_model = config.get("default_model", "whisper-1")

    logger.info("Selecting transcription model from config...")
    enabled_models = [name for name, opts in models.items() if opts.get("enabled", False)]

    if not enabled_models:
        logger.warning("No models enabled. Falling back to default.")
        return default_model

    if default_model in enabled_models:
        logger.info(f"Using default model: {default_model}")
        return default_model

    logger.info(f"Default model not enabled. Using first enabled model: {enabled_models[0]}")
    return enabled_models[0]
```

### Audio Transcription

The `transcriber.py` module handles the core transcription process:

1. Takes an audio file and configuration
2. Sets up appropriate model parameters
3. Sends the file to OpenAI's API for transcription
4. Measures performance and speed
5. Returns structured transcription results

```python
def transcribe_file(
    client: Any,
    file_path: Union[str, Path],
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Transcribe a single audio file using OpenAI and return the full response JSON.
    """
    file_path = Path(file_path)
    if not client:
        logger.error("No OpenAI client provided.")
        return None

    logger.info(f"Beginning transcription for: {file_path.name}")
    duration = calculate_duration(file_path)
    logger.info(f"Estimated duration: {duration:.2f} seconds")

    max_duration = config.get("cost_management", {}).get("max_audio_duration_seconds", 300)
    if duration and duration > max_duration:
        logger.warning(f"Audio exceeds max allowed ({max_duration}s). Proceeding with caution...")

    model_name = get_transcription_model(config)
    model_config = config["models"].get(model_name, {})
    settings = config.get("settings", {})

    language = settings.get("language")
    prompt = model_config.get("prompt") or settings.get("prompt")
    response_format = settings.get("response_format", "verbose_json")

    logger.info(f"Using model: {model_name}")
    if prompt:
        logger.info(f"Using prompt: {prompt}")

    try:
        start_time = time.time()
        with open(file_path, "rb") as audio_file:
            params = {
                "model": model_name,
                "file": audio_file,
                "response_format": response_format
            }

            if prompt:
                params["prompt"] = prompt
            if model_config.get("supports_language_parameter", True) and language:
                params["language"] = language

            response = client.audio.transcriptions.create(**params)

        end_time = time.time()
        speed = duration / (end_time - start_time) if duration else 0
        logger.info(f"Transcription done in {end_time - start_time:.2f}s ({speed:.2f}x real-time)")

        # Return raw dict
        if hasattr(response, 'model_dump'):
            return response.model_dump()
        return response

    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        return None
```

### Content Classification

The `classifier.py` module handles classifying the content of the transcription using an LLM:

1. Takes a transcription text or dictionary
2. Creates a prompt that asks to classify into specific categories (diary, calendar, to-do, accounts)
3. Sends the prompt to a more capable model (GPT-4) for content classification
4. Handles multiple contexts within a single transcription
5. Returns structured classification results

```python
def classify_text(client: OpenAI, transcription: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Classify the purpose of the transcribed text as 'diary', 'calendar', 'to do', or 'accounts'.
    If the text contains multiple contexts, it will be separated into different entries with appropriate tags.
    """
    try:
        logger.info("Sending transcription to LLM for classification...")
        
        # Handle dictionary transcription result
        if isinstance(transcription, dict):
            text = transcription.get("text", "")
        else:
            text = transcription

        prompt = (
            "Read the following entry and separate into different contexts if applicable. "
            "Classify each context into one of these categories: 'diary', 'calendar', 'to do', or 'accounts'.\n\n"
            "For each context, respond in this exact format:\n"
            'text: "the extracted text content"\n'
            "tag: the appropriate category\n\n"
            "If there are multiple contexts, separate them with a blank line.\n\n"
            f'Input: "{text.strip()}"'
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a text context separator and classifier. You extract different contexts from user input and classify each one appropriately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        tag = response.choices[0].message.content.strip()
        logger.info(f"Received tag: {tag}")
        return tag

    except Exception as e:
        logger.error("Failed to classify text.", exc_info=True)
        return None
```

### Transcription Routing

The `route_transcription.py` module handles routing transcriptions to the appropriate modules:

1. Takes transcription text, classification tag, and metadata
2. Saves the transcription to the database
3. Parses complex LLM classification responses that may contain multiple entries
4. Routes calendar entries to the calendar module
5. Returns structured results with processing status for each entry

```python
def route_transcription(
    text: str,
    file_path: Path,
    tag: str,
    duration: Optional[float] = None,
    model_used: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route a transcription to the appropriate module based on its tag.
    """
    db_id = save_to_database(
        text=text,
        file_path=file_path,
        duration=duration,
        model_used=model_used,
        tag=tag
    )

    result = {
        "status": "failed" if db_id is None else "success",
        "db_id": db_id,
        "tag": tag,
        "additional_processing": False,
        "entries_processed": 1
    }

    if db_id is None:
        return result

    entries = []
    calendar_processed = False

    if tag and ("text:" in tag and "tag:" in tag):
        entries = parse_llm_response(tag)
        if entries:
            result["entries_processed"] = len(entries)

    if entries:
        for entry in entries:
            entry_text = entry['text']
            entry_tag = entry['tag']

            if entry_tag == "calendar":
                calendar_success = insert_into_calendar(entry_text, db_id)
                calendar_processed = True
                if "calendar_entries" not in result:
                    result["calendar_entries"] = []
                result["calendar_entries"].append({
                    "text": entry_text,
                    "processing": "success" if calendar_success else "failed"
                })
    else:
        if tag and tag.lower() == "calendar":
            calendar_success = insert_into_calendar(text, db_id)
            calendar_processed = True
            result["calendar_processing"] = "success" if calendar_success else "failed"

    result["additional_processing"] = calendar_processed

    return result
```

## Complete Workflow

The complete transcription process follows these steps:

1. **Initialization**:
   - Load environment variables and configuration
   - Initialize the OpenAI client
   - Verify paths and database connections

2. **File Processing**:
   - Locate audio files in the downloads directory
   - Sort files chronologically
   - Calculate duration of each file for cost management

3. **Transcription**:
   - Select appropriate transcription model
   - Send audio to OpenAI's API for transcription
   - Handle response and measure performance

4. **Classification**:
   - Send transcription text to classifier
   - Determine content type and separate multi-purpose entries
   - Structure classification response for routing

5. **Routing**:
   - Save transcription to database
   - Process multi-context entries if present
   - Route to specialized modules based on classification:
     - Calendar entries to calendar module
     - Diary entries to diary storage
     - To-do entries to task manager
     - Account entries to financial tracking

6. **Cleanup**:
   - Save transcription text files
   - Record processing results
   - Clean the downloads directory after successful processing

## Error Handling and Logging

The transcription process includes comprehensive error handling at every step:

1. **Configuration Errors**:
   - Missing configuration files trigger creation of default configuration
   - Invalid configuration values fall back to defaults
   - Missing environment variables are clearly logged

2. **File Processing Errors**:
   - Missing directories are reported clearly
   - File access issues are caught and logged
   - Duration calculation errors use fallback estimation

3. **API Errors**:
   - Authentication failures are logged with helpful messages
   - API timeout and rate limit handling
   - Response validation with clear error messages

4. **Routing Errors**:
   - Database connection issues are properly handled
   - Failed entries are logged with specific reasons
   - Individual entry failures don't stop the entire process

## Summary

The audio transcription process is a sophisticated workflow that:

1. Processes downloaded audio files
2. Transcribes them using OpenAI's Whisper API
3. Classifies the content using GPT-4
4. Routes to specialized modules based on content type
5. Stores results in a database for future reference

The system is designed with modularity, error handling, and configuration flexibility in mind. Each component handles its specific responsibility and communicates through well-defined interfaces.
