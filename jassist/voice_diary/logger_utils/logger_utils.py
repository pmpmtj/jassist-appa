import logging
import os
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler

ENCODING = "utf-8"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Path to the logger config
LOGGER_CONFIG_PATH = Path(__file__).parents[1] / "config" / "logger_config.json"
LOGGER_CONFIG_SAMPLE_PATH = Path(__file__).parent / "logger_config_sample.json"

# Base directory for logs - inside the module
MODULE_DIR = Path(__file__).parents[1]
LOGS_DIR = MODULE_DIR / "logs"

def ensure_logger_config():
    """
    Ensure logger configuration file exists by creating it from sample if needed.
    
    Returns:
        dict: The configuration if created, empty dict otherwise
    """
    if not LOGGER_CONFIG_PATH.exists() and LOGGER_CONFIG_SAMPLE_PATH.exists():
        try:
            # Create config directory if it doesn't exist
            LOGGER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy from sample
            with open(LOGGER_CONFIG_SAMPLE_PATH, "r", encoding=ENCODING) as src:
                data = json.load(src)
            
            with open(LOGGER_CONFIG_PATH, "w", encoding=ENCODING) as dst:
                json.dump(data, dst, indent=4, sort_keys=True)
                
            print(f"[Logger] Created config from template at: {LOGGER_CONFIG_PATH}")
            return data
        except Exception as e:
            print(f"[Logger] Failed to create config from sample: {e}")
            
    return {}

def load_logger_config():
    """Load logger configuration from JSON file if it exists."""
    # Try to ensure config exists first
    if not LOGGER_CONFIG_PATH.exists():
        config = ensure_logger_config()
        if config:
            return config
    
    if LOGGER_CONFIG_PATH.exists():
        try:
            with open(LOGGER_CONFIG_PATH, "r", encoding=ENCODING) as f:
                return json.load(f)
        except Exception as e:
            print(f"[Logger] Failed to load config: {e}")
    return {}

def ensure_log_directory(log_filename):
    """
    Ensure the directory for the log file exists.
    If log_filename is a relative path, it will be relative to the module's logs directory.
    """
    log_path = Path(log_filename)
    
    # If path is absolute, use it as is
    if log_path.is_absolute():
        log_dir = log_path.parent
    else:
        # If path contains subdirectories but is relative, append to LOGS_DIR
        if "/" in log_filename or "\\" in log_filename:
            log_path = LOGS_DIR / log_filename
            log_dir = log_path.parent
        else:
            # Simple filename, put in LOGS_DIR
            log_dir = LOGS_DIR
            log_path = log_dir / log_filename
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(log_dir, exist_ok=True)
        # Verify directory was created
        if not os.path.exists(log_dir):
            print(f"[Logger Error] Failed to create log directory: {log_dir}")
            # Try alternate method to create directory
            log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[Logger Error] Exception creating log directory: {e}")
        # Use a fallback directory if the logs directory creation fails
        fallback_dir = Path.home() / "voice_diary_logs"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        log_path = fallback_dir / os.path.basename(log_filename)
        print(f"[Logger Warning] Using fallback log location: {log_path}")
    
    return str(log_path)

def setup_logger(name="voice_diary", module=None):
    """
    Set up a logger with configuration from the config file.
    
    Args:
        name: The base name for the logger
        module: Optional module name to use module-specific config
        
    Returns:
        A configured logger instance
    """
    config = load_logger_config()
    logging_config = config.get("logging", {})
    
    # Get the logger instance
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if already configured
    if logger.hasHandlers():
        return logger
    
    # Determine if we should use module-specific configuration
    module_config = None
    if module and module in logging_config.get("modules", {}):
        module_config = logging_config["modules"][module]
    
    # Set up console handler
    console_config = logging_config.get("console", {})
    console_level = getattr(logging, console_config.get("level", DEFAULT_LOG_LEVEL).upper(), logging.INFO)
    console_format = console_config.get("format", DEFAULT_LOG_FORMAT)
    console_date_format = console_config.get("date_format", DEFAULT_DATE_FORMAT)
    
    console_formatter = logging.Formatter(
        fmt=console_format,
        datefmt=console_date_format
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Set up file handler with rotation
    file_config = logging_config.get("file", {})
    
    # Override with module-specific config if available
    if module_config:
        for key in ["level", "log_filename"]:
            if key in module_config:
                file_config[key] = module_config[key]
    
    file_level = getattr(logging, file_config.get("level", DEFAULT_LOG_LEVEL).upper(), logging.INFO)
    file_format = file_config.get("format", DEFAULT_LOG_FORMAT)
    file_date_format = file_config.get("date_format", DEFAULT_DATE_FORMAT)
    log_filename = file_config.get("log_filename", "voice_diary.log")
    max_bytes = file_config.get("max_size_bytes", 1048576)  # Default 1MB
    backup_count = file_config.get("backup_count", 5)
    encoding = file_config.get("encoding", ENCODING)
    
    # Ensure log directory exists and get absolute path
    log_path = ensure_log_directory(log_filename)
    
    file_formatter = logging.Formatter(
        fmt=file_format,
        datefmt=file_date_format
    )
    
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Set logger level to the most verbose of the handlers
    logger.setLevel(min(console_level, file_level))
    
    return logger
