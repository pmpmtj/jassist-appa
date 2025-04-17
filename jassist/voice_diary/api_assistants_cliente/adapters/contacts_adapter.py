"""
Contacts Adapter

Adapter for processing contact information with OpenAI Assistants.
"""

from pathlib import Path
import yaml
from typing import Dict, Any, Optional

from jassist.voice_diary.api_assistants_cliente.api_assistants_cliente import OpenAIAssistantClient
from jassist.voice_diary.api_assistants_cliente.config_manager import get_module_config, get_module_dir
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("contacts_adapter", module="api_assistants_cliente")

def load_prompts() -> Dict[str, Any]:
    """
    Load prompts from the YAML file.
    
    Returns:
        Dict[str, Any]: Dictionary of loaded prompts
    """
    try:
        module_dir = get_module_dir("contacts")
        prompt_file = module_dir / "config" / "prompts.yaml"
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompts_data = yaml.safe_load(f)
            
        return prompts_data.get("prompts", {})
    except Exception as e:
        logger.error(f"Error loading prompts from YAML: {e}")
        return {}

def get_contacts_assistant_client() -> OpenAIAssistantClient:
    """
    Get a configured OpenAI Assistant client for contacts processing.
    
    Returns:
        OpenAIAssistantClient: Configured client
    """
    # Load the config for contacts assistant
    config = get_module_config("contacts", "contacts_assistant_config.json")
    
    # Load instructions from prompts file
    prompts = load_prompts()
    instructions = prompts.get("assistant_instructions", {}).get("template", "")
    
    # Update config with instructions if available
    if instructions:
        config["instructions"] = instructions
    
    # Create the client with this config
    client = OpenAIAssistantClient(
        config=config,
        module_name="contacts"
    )
    
    return client

def process_with_contacts_assistant(text: str) -> str:
    """
    Process text with the contacts assistant to extract contact information.
    
    Args:
        text: Text to process for contact information
        
    Returns:
        str: JSON-structured response from the assistant
    """
    # Get the client
    client = get_contacts_assistant_client()
    
    # Load parsing prompt from YAML
    prompts = load_prompts()
    parse_prompt = prompts.get("parse_entry_prompt", {}).get("template", "")
    
    # Format the prompt with the entry content
    if parse_prompt:
        template = parse_prompt.replace("{entry_content}", "{input_text}")
    else:
        # Fall back to the config template if YAML prompt not available
        template = client.config.get("prompt_template", 
            "Extract contact information from the following text. " +
            "Provide the extracted info in JSON format with fields: " +
            "first_name, last_name, phone, email, and note. " +
            "If information for a field is not available, use an empty string. " +
            "Return a valid JSON object without any additional text, explanations, or markdown formatting. " +
            "\n\nText: {input_text}"
        )
    
    # Process with the assistant - do NOT pass assistant_instructions
    response = client.process_with_prompt_template(
        input_text=text,
        prompt_template=template
    )
    
    return response 