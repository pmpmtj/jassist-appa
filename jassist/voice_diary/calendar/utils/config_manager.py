"""
Configuration management utilities for calendar processing

This module centralizes configuration loading from various sources.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("config_manager", module="calendar")

def get_script_dir() -> Path:
    """
    Get the directory of the current script, handling both frozen and regular execution.
    
    Returns:
        Path: Path to the script directory
    """
    # Handle both frozen (PyInstaller) and regular Python execution
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Normal Python execution
        return Path(__file__).resolve().parent

def get_config_dir() -> Path:
    """
    Get the configuration directory.
    
    Returns:
        Path: Path to the config directory
    """
    return get_script_dir().parent / "config"

def load_json_config(file_name: str) -> Dict[str, Any]:
    """
    Load a JSON configuration file.
    
    Args:
        file_name: Name of the configuration file
        
    Returns:
        Dict containing the configuration
    """
    try:
        config_path = get_config_dir() / file_name
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return {}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file {file_name}: {e}")
        return {}

def load_yaml_config(file_name: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        file_name: Name of the configuration file
        
    Returns:
        Dict containing the configuration
    """
    try:
        config_path = get_config_dir() / file_name
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return {}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config file {file_name}: {e}")
        return {}

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

def save_openai_config(config: Dict[str, Any]) -> bool:
    """
    Save the OpenAI configuration.
    
    Args:
        config: The configuration to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        config_path = get_config_dir() / "openai_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving OpenAI config: {e}")
        return False 