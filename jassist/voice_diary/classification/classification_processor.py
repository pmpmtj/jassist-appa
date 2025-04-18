"""
Classification Processor

Main module for classifying text into different categories using OpenAI Assistants.
"""

from pathlib import Path
import yaml
from typing import Dict, Any, Optional, Union

from openai import OpenAI
from jassist.voice_diary.api_assistants_cliente.api_assistants_cliente import OpenAIAssistantClient
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.utils.path_utils import resolve_path

logger = setup_logger("classification_processor", module="classification")

class ClassificationProcessor:
    """
    Processor for classifying text using the OpenAI Assistant.
    """
    
    def __init__(self):
        """
        Initialize the classification processor with the OpenAI Assistant client.
        """
        # Load configuration and create the client
        self.client = self._initialize_client()
        
    def _initialize_client(self) -> OpenAIAssistantClient:
        """
        Initialize the OpenAI Assistant client with the classification config.
        
        Returns:
            OpenAIAssistantClient: Configured client for classification
        """
        # Get the config file path
        module_dir = Path(__file__).resolve().parent
        config_file = resolve_path("config/classification_assistant_config.json", module_dir)
        
        # Load prompts file
        prompts_file = resolve_path("config/prompts.yaml", module_dir)
        instructions = self._load_instructions(prompts_file)
        
        # Create the client
        client = OpenAIAssistantClient(
            config_path=config_file,
            module_name="classification",
            instructions=instructions
        )
        
        return client
    
    def _load_instructions(self, prompts_file: Path) -> str:
        """
        Load assistant instructions from prompts file.
        
        Args:
            prompts_file: Path to the prompts YAML file
            
        Returns:
            str: Assistant instructions
        """
        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                prompts_data = yaml.safe_load(f)
                
            instructions = prompts_data.get("prompts", {}).get("assistant_instructions", {}).get("template", "")
            return instructions
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return ""
    
    def classify_text(self, text: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Classify the purpose of the transcribed text using the OpenAI Assistant.
        
        Args:
            text: The text to classify or a dict containing the text
            
        Returns:
            Optional[str]: Classification result or None if classification failed
        """
        try:
            logger.info("Classifying text with Assistant...")
            
            # Extract text content if input is a dictionary
            if isinstance(text, dict):
                content = text.get("text", "")
            else:
                content = text
                
            # Get or create assistant and thread
            assistant_id, was_created = self.client.get_or_create_assistant()
            thread_id = self.client.get_or_create_thread()
            
            logger.info(f"Using assistant ID: {assistant_id} (newly created: {was_created})")
            logger.info(f"Using thread ID: {thread_id}")
            
            # Load parsing prompt from prompts file
            module_dir = Path(__file__).resolve().parent
            prompts_file = resolve_path("config/prompts.yaml", module_dir)
            
            try:
                with open(prompts_file, "r", encoding="utf-8") as f:
                    prompts_data = yaml.safe_load(f)
                    
                parse_prompt = prompts_data.get("prompts", {}).get("parse_entry_prompt", {}).get("template", "")
            except Exception as e:
                logger.error(f"Error loading parse prompt: {e}")
                parse_prompt = ""
           
            # Process with the assistant - use entry_content as the template variable
            template_vars = {
                "entry_content": content
            }
            
            response = self.client.process_with_prompt_template(
                input_text=content,
                prompt_template=parse_prompt,
                template_vars=template_vars,
                assistant_id=assistant_id,
                thread_id=thread_id
            )
            
            if response:
                logger.info(f"Classification successful: {response[:100]}...")
                return response
            else:
                logger.error("No response from classification assistant")
                return None
                
        except Exception as e:
            logger.error(f"Error during classification: {e}", exc_info=True)
            return None


# Create a singleton instance for easy access
_processor = None

def classify_text(text: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Global function to classify text using the classification processor.
    
    Args:
        text: The text to classify or a dict containing the text
        
    Returns:
        Optional[str]: Classification result or None if classification failed
    """
    global _processor
    
    # Initialize processor if not already done
    if _processor is None:
        _processor = ClassificationProcessor()
        
    # Classify the text
    return _processor.classify_text(text)
