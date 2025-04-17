"""
Configuration management for OpenAI assistants.

This module provides functions for loading and managing assistant configurations.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from .exceptions import ConfigError

logger = setup_logger("config_manager", module="api_assistants_cliente")

def get_script_dir() -> Path:
    """
    Get the directory of the current script, handling both frozen and regular execution.
    
    Returns:
        Path: Path to the script directory
    """
    # Use the module directory instead of __file__ to avoid issues with frozen executables
    return Path(__file__).resolve().parent


def get_config_base_dir() -> Path:
    """
    Get the base configuration directory.
    
    Returns:
        Path: Path to the base config directory
    """
    voice_diary_dir = get_script_dir().parent
    return voice_diary_dir / "config"


def get_assistant_config_dir() -> Path:
    """
    Get the assistant configuration directory.
    
    Returns:
        Path: Path to the assistant config directory
    """
    config_dir = get_config_base_dir() / "assistants"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_module_dir(module_name: str) -> Path:
    """
    Get the directory for a specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Path: Path to the module directory
        
    Raises:
        ConfigError: If the module directory doesn't exist
    """
    # Get the voice_diary directory
    voice_diary_dir = get_script_dir().parent
    
    # Check if the module directory exists
    module_dir = voice_diary_dir / module_name
    if not module_dir.exists() or not module_dir.is_dir():
        raise ConfigError(f"Module directory not found: {module_dir}")
        
    return module_dir


def load_json_config(filepath: Path) -> Dict[str, Any]:
    """
    Load a JSON configuration file.
    
    Args:
        filepath: Path to the configuration file
        
    Returns:
        Dict: Configuration dictionary
        
    Raises:
        ConfigError: If the file doesn't exist or has parsing errors
    """
    # Check if file exists
    if not filepath.exists():
        raise ConfigError(f"Config file not found: {filepath}")
    
    # Load the file
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing JSON in {filepath}: {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)
    except Exception as e:
        error_msg = f"Error loading config file {filepath}: {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)


def load_yaml_config(filepath: Path) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        filepath: Path to the configuration file
        
    Returns:
        Dict: Configuration dictionary
        
    Raises:
        ConfigError: If the file doesn't exist or has parsing errors
    """
    # Check if file exists
    if not filepath.exists():
        raise ConfigError(f"Config file not found: {filepath}")
    
    # Load the file
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_msg = f"Error parsing YAML in {filepath}: {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)
    except Exception as e:
        error_msg = f"Error loading config file {filepath}: {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)


def save_json_config(config: Dict[str, Any], filepath: Path) -> bool:
    """
    Save a configuration to a JSON file.
    
    Args:
        config: Configuration dictionary to save
        filepath: Path to save the configuration file
        
    Returns:
        bool: Success status
    """
    # Create the directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        error_msg = f"Error saving config to {filepath}: {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)


def load_assistant_config(
    module_name: str, 
    assistant_name: Optional[str] = None,
    config_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Load configuration for a specific assistant or module.
    
    This function will look for configuration in the following order:
    1. The specified config_file if provided
    2. The assistant-specific config file if assistant_name is provided
    3. A module-specific config file in the module's own config directory
    
    Args:
        module_name: Name of the module (e.g., 'calendar')
        assistant_name: Optional specific assistant name
        config_file: Optional specific config file path
        
    Returns:
        Dict: Combined configuration dictionary
        
    Raises:
        ConfigError: If no configuration can be found
    """
    # If specific file provided, use it
    if config_file:
        config_path = Path(config_file) if isinstance(config_file, str) else config_file
        return load_json_config(config_path)
    
    # If assistant name provided, check for assistant-specific config
    if assistant_name:
        assistant_config_dir = get_assistant_config_dir()
        assistant_filename = f"{module_name}_{assistant_name.lower().replace(' ', '_')}.json"
        assistant_config_path = assistant_config_dir / assistant_filename
        
        if assistant_config_path.exists():
            logger.info(f"Loading assistant-specific config: {assistant_config_path}")
            return load_json_config(assistant_config_path)
    
    # Check module's own config directory
    try:
        module_dir = get_module_dir(module_name)
        module_config_path = module_dir / "config" / "openai_config.json"
        
        if module_config_path.exists():
            logger.info(f"Loading module config: {module_config_path}")
            config = load_json_config(module_config_path)
            
            # Handle nested 'openai_config' key if present
            if "openai_config" in config:
                return config["openai_config"]
            else:
                return config
    except ConfigError as e:
        logger.error(f"Error loading module config: {e}")
    
    # If we get here, no configuration was found
    raise ConfigError(f"No configuration found for module '{module_name}'" +
                     (f" with assistant '{assistant_name}'" if assistant_name else ""))


def get_module_config(module_name: str, config_filename: str) -> Dict[str, Any]:
    """
    Load a specific configuration file from a module's config directory.
    
    Args:
        module_name: Name of the module (e.g., 'contacts')
        config_filename: Name of the config file (e.g., 'contacts_assistant_config.json')
        
    Returns:
        Dict: Configuration dictionary
        
    Raises:
        ConfigError: If the file doesn't exist or has parsing errors
    """
    try:
        module_dir = get_module_dir(module_name)
        config_path = module_dir / "config" / config_filename
        
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
            
        logger.info(f"Loading module config: {config_path}")
        return load_json_config(config_path)
        
    except Exception as e:
        error_msg = f"Error loading module config '{config_filename}' for module '{module_name}': {e}"
        logger.error(error_msg)
        raise ConfigError(error_msg)


def load_prompt_templates(
    module_name: str,
    prompts_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Load prompt templates for a specific module.
    
    This function will look for prompt templates in the following order:
    1. The specified prompts_file if provided
    2. A module-specific prompts file in the module's own config directory (module/config/prompts.yaml)
    3. A module-specific prompts file in the central config directory (config/module/prompts.yaml)
    4. The general prompts.yaml file
    
    Args:
        module_name: Name of the module
        prompts_file: Optional specific prompts file
        
    Returns:
        Dict: Prompts dictionary
    """
    # Get the config dir
    base_config_dir = get_config_base_dir()
    
    # If prompts file provided, use it
    if prompts_file:
        prompts_path = Path(prompts_file) if isinstance(prompts_file, str) else prompts_file
        try:
            if prompts_path.suffix.lower() in ('.yaml', '.yml'):
                with open(prompts_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f).get('prompts', {})
            else:
                with open(prompts_path, "r", encoding="utf-8") as f:
                    return json.load(f).get('prompts', {})
        except Exception as e:
            logger.error(f"Error loading specific prompts file {prompts_path}: {e}")
            # Continue to try other sources
    
    # Try to load from the module's own config directory
    module_dir = get_module_dir(module_name)
    if module_dir:
        module_prompts_path = module_dir / "config" / "prompts.yaml"
        if module_prompts_path.exists():
            try:
                with open(module_prompts_path, "r", encoding="utf-8") as f:
                    prompts = yaml.safe_load(f).get('prompts', {})
                    if prompts:
                        logger.info(f"Loaded prompts from module directory: {module_prompts_path}")
                        return prompts
            except Exception as e:
                logger.warning(f"Error loading module prompts from {module_prompts_path}: {e}")
    
    # Try to load module-specific prompts.yaml from config directory
    try:
        # First try in a module-specific subdirectory
        module_prompts_path = base_config_dir / module_name / "prompts.yaml"
        if module_prompts_path.exists():
            with open(module_prompts_path, "r", encoding="utf-8") as f:
                prompts = yaml.safe_load(f).get('prompts', {})
                if prompts:
                    logger.info(f"Loaded prompts from module-specific subdirectory")
                    return prompts
    except Exception as e:
        logger.debug(f"No module prompts found in {module_prompts_path}: {e}")
    
    # Fall back to global prompts.yaml
    try:
        global_prompts_path = base_config_dir / "prompts.yaml"
        if global_prompts_path.exists():
            with open(global_prompts_path, "r", encoding="utf-8") as f:
                prompts = yaml.safe_load(f).get('prompts', {})
                if prompts:
                    logger.info(f"Loaded prompts from global file")
                    return prompts
    except Exception as e:
        logger.warning(f"Could not load global prompts: {e}")
    
    logger.warning(f"No prompt templates found for module {module_name}")
    return {} 