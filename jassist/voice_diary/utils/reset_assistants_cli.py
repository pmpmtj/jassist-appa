#!/usr/bin/env python3
"""
Reset OpenAI assistants CLI utility.

This script provides a command-line interface to reset OpenAI assistants
used across different jassist modules.
"""
import argparse
import logging
import json
import os
import glob
from pathlib import Path
from typing import List, Optional
from openai import OpenAI
from .openai_assistant_manager import OpenAIAssistantManager
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.utils.path_utils import resolve_path

logger = setup_logger("reset_assistants_cli", module="utils")

def get_available_modules() -> List[str]:
    """
    Get a list of all modules that have assistant configurations.
    
    Returns:
        List[str]: List of module names
    """
    # Find the voice_diary root directory
    script_dir = Path(__file__).resolve().parent.parent
    config_dir = resolve_path("config/assistants", script_dir)
    
    # Make sure the directory exists
    if not config_dir.exists():
        return []
    
    # Find all assistant config files
    config_files = glob.glob(str(config_dir / "*_assistants.json"))
    
    # Extract module names from filenames
    modules = []
    for file_path in config_files:
        filename = os.path.basename(file_path)
        if filename.endswith("_assistants.json"):
            module_name = filename[:-16]  # Remove "_assistants.json"
            modules.append(module_name)
    
    return modules

def reset_module_assistants(module_name: str, openai_api_key: Optional[str] = None) -> bool:
    """
    Reset all assistants for a specific module.
    
    Args:
        module_name: Name of the module to reset
        openai_api_key: OpenAI API key (optional if set in env)
        
    Returns:
        bool: True if reset was successful
    """
    # Get API key from environment if not provided
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key provided and none found in environment")
        return False
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Find the config file
    script_dir = Path(__file__).resolve().parent.parent
    config_dir = resolve_path("config/assistants", script_dir)
    config_file = resolve_path(f"{module_name}_assistants.json", config_dir)
    
    if not config_file.exists():
        logger.error(f"No assistant config found for module '{module_name}'")
        return False
    
    # Load the config to find all assistants
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return False
    
    # Find all assistant IDs in the config
    assistant_keys = [k for k in config.keys() if k.startswith("assistant_id_")]
    if not assistant_keys:
        logger.info(f"No assistants found in config for module '{module_name}'")
        return True
    
    # Create a temporary assistant manager to handle deletion
    assistant_manager = OpenAIAssistantManager(
        client=client,
        config_path=config_file,
        assistant_name="Temporary",  # Not used for deletion
        model_name="gpt-4o"  # Not used for deletion
    )
    
    # For each assistant key, try to delete from OpenAI and then from config
    for key in assistant_keys:
        try:
            assistant_id = config[key]
            logger.info(f"Deleting assistant '{key}' with ID: {assistant_id}")
            
            # Try to delete from OpenAI
            try:
                client.beta.assistants.delete(assistant_id)
                logger.info(f"Successfully deleted assistant from OpenAI: {assistant_id}")
            except Exception as e:
                logger.warning(f"Failed to delete assistant from OpenAI (may already be deleted): {e}")
            
            # Remove from config
            del config[key]
        except Exception as e:
            logger.error(f"Error processing assistant key '{key}': {e}")
    
    # Save the updated config
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated config file: {config_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving updated config: {e}")
        return False

def reset_all_assistants(openai_api_key: Optional[str] = None) -> bool:
    """
    Reset all assistants across all modules.
    
    Args:
        openai_api_key: OpenAI API key (optional if set in env)
        
    Returns:
        bool: True if all resets were successful
    """
    modules = get_available_modules()
    if not modules:
        logger.info("No modules with assistant configurations found")
        return True
    
    success = True
    for module in modules:
        logger.info(f"Resetting assistants for module: {module}")
        module_success = reset_module_assistants(module, openai_api_key)
        if not module_success:
            logger.warning(f"Failed to reset assistants for module: {module}")
            success = False
    
    return success

def main():
    """CLI entry point for resetting assistants."""
    parser = argparse.ArgumentParser(description="Reset OpenAI assistants")
    parser.add_argument(
        "--module", 
        help="Specific module to reset (if not specified, all modules will be reset)"
    )
    parser.add_argument(
        "--api-key", 
        help="OpenAI API key (can also be set via OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="List available modules and exit"
    )
    
    args = parser.parse_args()
    
    # List modules if requested
    if args.list_modules:
        modules = get_available_modules()
        if modules:
            print("Available modules:")
            for module in modules:
                print(f"  - {module}")
        else:
            print("No modules with assistant configurations found")
        return 0
    
    # Reset based on the module argument
    if args.module:
        logger.info(f"Resetting assistants for module: {args.module}")
        success = reset_module_assistants(args.module, args.api_key)
    else:
        logger.info("Resetting assistants for all modules")
        success = reset_all_assistants(args.api_key)
    
    if success:
        logger.info("Reset complete")
        return 0
    else:
        logger.error("Reset failed")
        return 1

if __name__ == "__main__":
    main() 