"""
OpenAI Assistant Manager

A shared utility for managing OpenAI assistants across different modules.
Handles assistant creation, verification, and recovery from deleted assistants.
"""

import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Callable

from openai import OpenAI

from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("openai_assistant_manager", module="utils")

class OpenAIAssistantManager:
    """
    Manages OpenAI assistants across different modules.
    Handles creation, verification, and recovery for assistants.
    """
    
    def __init__(
        self, 
        client: OpenAI,
        config_path: Path,
        assistant_name: str,
        model_name: str = "gpt-4o",
        instructions: str = "",
        tools: List[Dict[str, Any]] = None
    ):
        """
        Initialize the assistant manager.
        
        Args:
            client: OpenAI client instance
            config_path: Path to the config file where assistant IDs are stored
            assistant_name: Name of the assistant
            model_name: OpenAI model to use
            instructions: Instructions for the assistant
            tools: List of tools for the assistant
        """
        self.client = client
        self.config_path = config_path
        self.assistant_name = assistant_name
        self.model_name = model_name
        self.instructions = instructions
        self.tools = tools or [{"type": "file_search"}]
        
        # Load config
        self.config = self._load_config()
        
        # Format the key for storing this specific assistant's ID
        self.assistant_key = f"assistant_id_{self.assistant_name.lower().replace(' ', '_')}"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from the file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {}
            
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _save_config(self) -> bool:
        """Save the configuration to the file."""
        try:
            # Ensure parent directories exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_or_create_assistant(self) -> Tuple[str, bool]:
        """
        Get an existing assistant or create a new one if needed.
        
        Returns:
            Tuple[str, bool]: (assistant_id, was_created)
                - assistant_id: ID of the assistant
                - was_created: True if a new assistant was created, False if using existing
        """
        # First check if we have an assistant ID for this specific assistant
        if self.assistant_key in self.config:
            assistant_id = self.config[self.assistant_key]
            
            # Verify the assistant exists
            try:
                assistant = self.client.beta.assistants.retrieve(assistant_id)
                logger.info(f"Using existing assistant: {assistant_id}")
                return assistant_id, False
            except Exception as e:
                logger.warning(f"Assistant no longer exists or error retrieving assistant: {e}")
                # Continue to creating a new assistant
        
        # Create a new assistant
        logger.info(f"Creating new assistant: {self.assistant_name}")
        try:
            assistant = self.client.beta.assistants.create(
                name=self.assistant_name,
                instructions=self.instructions,
                tools=self.tools,
                model=self.model_name
            )
            assistant_id = assistant.id
            
            # Save the new assistant ID
            self.config[self.assistant_key] = assistant_id
            self._save_config()
            
            logger.info(f"Created new assistant with ID: {assistant_id}")
            return assistant_id, True
        except Exception as e:
            logger.error(f"Failed to create new assistant: {e}")
            raise RuntimeError(f"Failed to create OpenAI assistant: {e}")
    
    def delete_assistant(self) -> bool:
        """
        Delete the assistant and remove it from the config.
        
        Returns:
            bool: True if deleted successfully
        """
        if self.assistant_key not in self.config:
            logger.info(f"No assistant ID found to delete for {self.assistant_name}")
            return True
        
        assistant_id = self.config[self.assistant_key]
        
        try:
            # Try to delete from OpenAI
            self.client.beta.assistants.delete(assistant_id)
            logger.info(f"Deleted assistant with ID: {assistant_id}")
        except Exception as e:
            logger.warning(f"Failed to delete assistant from OpenAI (may already be deleted): {e}")
        
        # Remove from config regardless of whether the API call succeeded
        del self.config[self.assistant_key]
        self._save_config()
        
        return True
    
    def get_or_create_thread(self, thread_key: str = "default", retention_days: int = 30) -> str:
        """
        Get an existing thread or create a new one if needed.
        
        Args:
            thread_key: Key to identify this specific thread in the config
            retention_days: Number of days to keep a thread before rotating
            
        Returns:
            str: Thread ID
        """
        # Format the key for storing this specific thread
        full_thread_key = f"thread_id_{self.assistant_name.lower().replace(' ', '_')}_{thread_key}"
        created_at_key = f"{full_thread_key}_created_at"
        
        thread_id = self.config.get(full_thread_key)
        thread_needs_rotation = False
        
        if thread_id:
            try:
                thread = self.client.beta.threads.retrieve(thread_id)
                
                # Check if thread needs rotation
                if created_at_key in self.config:
                    try:
                        created_at = datetime.fromisoformat(self.config[created_at_key])
                        days_old = (datetime.now() - created_at).days
                        if days_old > retention_days:
                            thread_needs_rotation = True
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing thread creation date: {e}")
                        thread_needs_rotation = True
            except Exception as e:
                logger.error(f"Error retrieving thread: {e}")
                thread_needs_rotation = True
        
        if not thread_id or thread_needs_rotation:
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            
            # Save the new thread ID and creation time
            self.config[full_thread_key] = thread_id
            self.config[created_at_key] = datetime.now().isoformat()
            self._save_config()
            
            logger.info(f"Created new thread with ID: {thread_id}")
        
        return thread_id
    
    def run_assistant(self, thread_id: str, prompt: str, max_retries: int = 1) -> Optional[str]:
        """
        Run the assistant with the given prompt.
        
        Args:
            thread_id: Thread ID to use
            prompt: User prompt to send
            max_retries: Maximum number of times to retry on assistant errors
            
        Returns:
            Optional[str]: The assistant's response or None if failed
        """
        # Get the assistant ID, creating if needed
        assistant_id, was_created = self.get_or_create_assistant()
        
        # Create message
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )
        
        # Try to run with retries
        retries = 0
        while retries <= max_retries:
            try:
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id
                )
                
                # Wait for completion
                while True:
                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    if run_status.status == "completed":
                        break
                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        raise RuntimeError(f"Run failed with status {run_status.status}")
                    time.sleep(1)
                
                # Get messages
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content[0].text.value
                
                return None
                
            except Exception as e:
                logger.error(f"Error running assistant (attempt {retries+1}): {e}")
                
                # If there's an assistant-related error and we have retries left
                if "assistant" in str(e).lower() and retries < max_retries:
                    logger.info("Assistant error detected, recreating assistant...")
                    
                    # Force recreation by deleting and getting a new one
                    self.delete_assistant()
                    assistant_id, _ = self.get_or_create_assistant()
                    
                    retries += 1
                    continue
                else:
                    # Other error or out of retries
                    if retries >= max_retries:
                        logger.error(f"Exceeded maximum retries ({max_retries})")
                    raise
        
        return None


def get_assistant_manager(
    client: OpenAI,
    module_name: str,
    assistant_name: str,
    config_dir: Optional[Path] = None,
    model_name: str = "gpt-4o",
    instructions: str = "",
    tools: List[Dict[str, Any]] = None
) -> OpenAIAssistantManager:
    """
    Factory function to create an assistant manager for a specific module.
    
    Args:
        client: OpenAI client
        module_name: Name of the module (used for config path)
        assistant_name: Name of the assistant
        config_dir: Optional custom config directory
        model_name: Model to use
        instructions: Instructions for the assistant
        tools: Tools for the assistant
        
    Returns:
        OpenAIAssistantManager: Configured assistant manager
    """
    # If no config dir provided, use a default path
    if config_dir is None:
        # Find the voice_diary root directory
        script_dir = Path(__file__).resolve().parent.parent
        config_dir = script_dir / "config" / "assistants"
    
    # Create config path
    config_file = config_dir / f"{module_name}_assistants.json"
    
    return OpenAIAssistantManager(
        client=client,
        config_path=config_file,
        assistant_name=assistant_name,
        model_name=model_name,
        instructions=instructions,
        tools=tools
    ) 