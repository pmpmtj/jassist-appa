# Calendar Processing Flow

This document provides a detailed explanation of the calendar processing system in the jassist application. The process involves extracting calendar events from transcribed voice notes, parsing them with an AI assistant, saving them to a database, and optionally adding them to Google Calendar.

## Module Structure

The calendar functionality is organized in the following modules:

```
jassist/voice_diary/
├── calendar/
│   ├── __init__.py               # Package initialization and main entry point
│   ├── calendar_processor.py     # Core event processing logic
│   ├── google_calendar.py        # Google Calendar API integration
│   ├── llm_parser.py             # Re-exports the calendar insertion function
│   ├── config/
│   │   ├── calendar_config.json  # Calendar configuration
│   │   ├── openai_config.json    # OpenAI API configuration
│   │   └── prompts.yaml          # Prompt templates for AI processing
│   ├── credentials/              # Storage for Google API credentials
│   ├── db/
│   │   └── calendar_db.py        # Database operations for calendar events
│   ├── llm/
│   │   └── openai_client.py      # OpenAI API integration
│   └── utils/
│       ├── config_manager.py     # Configuration loading utilities
│       └── json_extractor.py     # JSON extraction from AI responses
└── route_transcription/
    └── route_transcription.py    # Routes transcriptions to modules
```

## Configuration

The calendar processing system is configuration-driven using multiple JSON and YAML files.

### Calendar Configuration (`calendar_config.json`)

```json
{
    "paths": {
        "json_output_directory": "output/calendar_events",
        "credentials_directory": "credentials"
    },
    "google_calendar": {
        "use_google_calendar": true,
        "calendar_id": "primary"
    },
    "date_format": "%Y-%m-%d",
    "timezone": "Europe/Lisbon",
    "default_event_duration_minutes": 60,
    "allow_summary_overwrite": true
} 
```

### OpenAI Configuration (`openai_config.json`)

```json
{
  "openai_config": {
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 1500,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "save_usage_stats": true,
    "thread_id": "thread_XH4Z5cakEgVLYyizhlZfDyjU",
    "thread_created_at": "2025-04-15T19:52:18.749568",
    "thread_retention_days": 30,
    "tools": [],
    "assistant_id": "asst_nu1Jbg9SAVGaahPoLZiNClAs"
  }
}
```

### Prompt Templates (`prompts.yaml`)

The prompts.yaml file contains structured templates that guide the AI in extracting calendar information from natural language text. These templates include:

- Instructions for the AI assistant
- Parse entry prompts with formatting requirements
- Example inputs and outputs
- Edge case handling instructions

## Calendar Processing Flow

### Entry Point

The calendar processing is initiated from `route_transcription.py`, which routes transcriptions classified as calendar entries to the calendar module:

```python
def route_transcription(
    text: str,
    file_path: Path,
    tag: str,
    duration: Optional[float] = None,
    model_used: Optional[str] = None
) -> Dict[str, Any]:
    # ... other code ...
    
    if tag and tag.lower() == "calendar":
        calendar_success = insert_into_calendar(text, db_id)
        calendar_processed = True
        result["calendar_processing"] = "success" if calendar_success else "failed"
        
    # ... other code ...
```

The main entry point in the calendar module is the `insert_into_calendar` function defined in `__init__.py`:

```python
def insert_into_calendar(text: str, db_id: int = None) -> bool:
    """
    Process a voice entry for calendar insertion.
    
    This is the main entry point for the calendar module, 
    designed to be called from the route_transcription module.
    
    Args:
        text: The voice entry text
        db_id: Optional database ID of the transcription
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Get logger instance
    logger = setup_logger("calendar", module="calendar")
    
    # Process the entry
    success, _ = process_calendar_entry(text, db_id)
    return success
```

### Calendar Processing

The `calendar_processor.py` module handles the core processing:

1. Sends the text to the OpenAI assistant
2. Extracts structured JSON from the response
3. Saves the event to the database
4. Inserts the event into Google Calendar
5. Returns the success status and event data

```python
def process_calendar_entry(text: str, db_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a voice entry for a calendar event.
    
    Args:
        text: The voice entry text
        db_id: Optional ID of the database record this is associated with
        
    Returns:
        Tuple containing (success status, event data)
    """
    try:
        logger.info("Processing calendar entry")
        
        # Process with OpenAI to extract calendar event data
        response = process_with_openai_assistant(text)
        
        # Extract JSON from response
        event_data = extract_json_from_text(response)
        if not event_data:
            logger.error("Failed to extract JSON from LLM response")
            return False, None
        
        # Save to database
        event_id = save_calendar_event(
            summary=event_data.get("summary"),
            start_datetime=event_data.get("start", {}).get("dateTime"),
            end_datetime=event_data.get("end", {}).get("dateTime"),
            location=event_data.get("location"),
            description=event_data.get("description"),
            start_timezone=event_data.get("start", {}).get("timeZone"),
            end_timezone=event_data.get("end", {}).get("timeZone"),
            attendees=event_data.get("attendees"),
            recurrence=event_data.get("recurrence"),
            reminders=event_data.get("reminders"),
            visibility=event_data.get("visibility"),
            color_id=event_data.get("colorId"),
            transparency=event_data.get("transparency"),
            status=event_data.get("status")
        )
        
        if not event_id:
            logger.error("Failed to save event to database")
            return False, event_data
        
        # Insert into Google Calendar
        link = insert_event_into_google_calendar(event_data)
        if link:
            logger.info(f"Google Calendar event created at: {link}")
            event_data["google_calendar_link"] = link
        else:
            logger.warning("Google Calendar event creation failed")
        
        return True, event_data
        
    except Exception as e:
        logger.exception(f"Error during calendar processing: {e}")
        return False, None
```

### OpenAI Assistant Processing

The `openai_client.py` module handles interactions with the OpenAI API:

1. Initializes the OpenAI client
2. Loads prompt templates and formats them
3. Uses the assistant API to extract calendar data
4. Returns the structured response

```python
def process_with_openai_assistant(entry_content: str) -> str:
    """
    Process a calendar entry using OpenAI's assistant API.
    
    Args:
        entry_content: The calendar entry text to process
        
    Returns:
        str: The assistant's response
    """
    # Get prompt template
    prompt_template = get_prompt_template("parse_entry_prompt")
    
    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Format prompt with all required parameters
    prompt = prompt_template.format(
        entry_content=entry_content,
        current_date=current_date,
        current_time=current_time
    )
    
    # Get OpenAI client
    client = get_openai_client()
    
    # Get assistant instructions from prompt templates
    try:
        instructions = get_prompt_template("assistant_instructions")
    except ValueError:
        instructions = "You are a calendar entry parser that extracts structured information from text."
    
    # Get OpenAI config for model and other settings
    openai_config = load_openai_config()
    config = openai_config.get('openai_config', {})
    model = config.get('model', 'gpt-4o')
    
    # Create assistant manager
    assistant_manager = get_assistant_manager(
        client=client,
        module_name="calendar",
        assistant_name="Calendar Entry Parser",
        model_name=model,
        instructions=instructions,
        tools=config.get('tools', [{"type": "file_search"}])
    )
    
    # Get or create a thread
    thread_id = assistant_manager.get_or_create_thread(
        thread_key="default",
        retention_days=config.get('thread_retention_days', 30)
    )
    
    # Run the assistant
    response = assistant_manager.run_assistant(
        thread_id=thread_id,
        prompt=prompt,
        max_retries=2
    )
    
    if not response:
        raise ValueError("No assistant response found")
    
    return response
```

### JSON Extraction

The `json_extractor.py` module extracts the structured JSON from the AI's response, handling multiple formats:

```python
def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from text, handling different formats.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        Dict: The extracted JSON object, or None if extraction failed
    """
    if not text:
        logger.error("No text provided for JSON extraction")
        return None
        
    try:
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract code blocks with ```json syntax
        json_block_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        for match in json_block_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Try to find anything between curly braces
        curly_match = re.search(r'({[\s\S]*})', text)
        if curly_match:
            try:
                return json.loads(curly_match.group(1))
            except json.JSONDecodeError:
                pass

        logger.error("Failed to extract valid JSON from text")
        return None
        
    except Exception as e:
        logger.error(f"Error during JSON extraction: {e}")
        return None
```

### Database Operations

The `calendar_db.py` module handles storing calendar events in the database:

```python
def save_calendar_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    start_timezone: Optional[str] = None,
    end_timezone: Optional[str] = None,
    attendees: Optional[List[Dict[str, Any]]] = None,
    recurrence: Optional[List[str]] = None,
    reminders: Optional[Dict[str, Any]] = None,
    visibility: Optional[str] = None,
    color_id: Optional[str] = None,
    transparency: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[int]:
    """
    Save a calendar event to the database.
    """
    try:
        # Import here to avoid circular imports
        from jassist.voice_diary.db_utils.db_manager import save_calendar_event as db_save_calendar_event
        
        # Call the database function
        event_id = db_save_calendar_event(
            summary=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=location,
            description=description,
            start_timezone=start_timezone,
            end_timezone=end_timezone,
            attendees=attendees,
            recurrence=recurrence,
            reminders=reminders,
            visibility=visibility,
            color_id=color_id,
            transparency=transparency,
            status=status
        )
        
        if event_id:
            logger.info(f"Successfully saved calendar event with ID: {event_id}")
        else:
            logger.error("Failed to save calendar event to database")
            
        return event_id
        
    except Exception as e:
        logger.exception(f"Error saving calendar event to database: {e}")
        return None
```

### Google Calendar Integration

The `google_calendar.py` module handles the Google Calendar API integration:

1. Sets up authentication with OAuth
2. Manages credentials and token handling
3. Creates events in Google Calendar
4. Returns the link to the created event

```python
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
```

Authentication with Google Calendar:

```python
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
```

### Configuration Management

The `config_manager.py` module centralizes configuration loading from various sources:

```python
def load_calendar_config() -> Dict[str, Any]:
    """
    Load the calendar configuration.
    
    Returns:
        Dict containing the calendar configuration
    """
    return load_json_config("calendar_config.json")

def load_openai_config() -> Dict[str, Any]:
    """
    Load the OpenAI API configuration.
    
    Returns:
        Dict containing the OpenAI configuration
    """
    return load_json_config("openai_config.json")

def load_prompts() -> Dict[str, Any]:
    """
    Load the prompt templates.
    
    Returns:
        Dict containing the prompts configuration
    """
    config = load_yaml_config("prompts.yaml")
    return config.get('prompts', {})
```

## Complete Workflow

The complete calendar processing flow follows these steps:

1. **Entry Routing**:
   - The transcribed text is classified as a calendar entry 
   - The `route_transcription` module routes it to the calendar module
   - The `insert_into_calendar` function is called with the text and database ID

2. **Natural Language Processing**:
   - The text is sent to the OpenAI assistant
   - The assistant parses the text to extract structured calendar data
   - Prompt templates guide the assistant in extracting the correct information
   - The assistant formats the data as a Google Calendar compatible JSON object

3. **JSON Extraction**:
   - The assistant's response is processed to extract the structured JSON
   - Multiple extraction strategies are attempted for robustness
   - The JSON is validated to ensure it contains the required fields

4. **Database Storage**:
   - The extracted event data is saved to the database
   - A unique event ID is generated for the entry
   - Relationships to the original transcription are maintained

5. **Google Calendar Integration**:
   - If enabled, the event is also inserted into Google Calendar
   - OAuth authentication is handled automatically
   - The Google Calendar event link is stored with the event

6. **Response Handling**:
   - Success or failure status is returned to the calling module
   - Detailed error information is logged for debugging
   - The event data is returned for further processing if needed

## AI Processing Details

The calendar processing relies heavily on AI to extract structured information from natural language. The assistant needs to:

1. Understand date and time references (both absolute and relative)
2. Extract event duration when specified
3. Identify location information
4. Determine attendees when mentioned
5. Handle recurring event patterns
6. Extract reminders and other calendar-specific metadata

The AI assistant converts natural language like:

> "Schedule a meeting with John next Tuesday at 2 PM about the project proposal. It should last for an hour and remind me 30 minutes before."

Into structured data:

```json
{
  "summary": "Meeting with John about the project proposal",
  "start": {
    "dateTime": "2024-04-23T14:00:00",
    "timeZone": "Europe/Lisbon"
  },
  "end": {
    "dateTime": "2024-04-23T15:00:00",
    "timeZone": "Europe/Lisbon"
  },
  "attendees": [
    {
      "email": "",
      "displayName": "John"
    }
  ],
  "reminders": {
    "useDefault": false,
    "overrides": [
      {
        "method": "popup",
        "minutes": 30
      }
    ]
  }
}
```

## Error Handling and Logging

The calendar processing flow includes comprehensive error handling:

1. **AI Processing Errors**:
   - Network or API issues when calling OpenAI
   - Invalid or incomplete responses from the assistant
   - Prompt template loading failures

2. **JSON Extraction Errors**:
   - Malformed JSON in the assistant's response
   - Missing required fields in the extracted data
   - Type conversion errors

3. **Database Errors**:
   - Connection issues with the database
   - Schema or constraint violations
   - Transaction failures

4. **Google Calendar Errors**:
   - Authentication failures
   - API rate limiting or quota issues
   - Invalid event data format

All errors are logged with appropriate context for debugging, and the system is designed to fail gracefully without crashing.

## Summary

The calendar processing system is a sophisticated workflow that:

1. Takes natural language descriptions of calendar events
2. Uses AI to extract structured data
3. Stores the events in a database
4. Optionally adds them to Google Calendar

The system is designed with modularity, error handling, and configuration flexibility in mind. Each component handles its specific responsibility and communicates through well-defined interfaces.

This calendar integration enables the user to add events to their calendar simply by speaking, without requiring specific formatted commands or user interface interactions.
