"""
Summary module adapter for OpenAI Assistant Client.

This module provides a specialized interface for text summarization
using the OpenAI Assistant Client.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from ..api_assistants_cliente import OpenAIAssistantClient
from ..config_manager import load_assistant_config
from ..exceptions import AssistantClientError, ConfigError

logger = setup_logger("sample_adapter", module="api_assistants_cliente")

class SummaryAssistantAdapter:
    """
    Adapter for using the OpenAI Assistant Client with text summarization.
    """
    
    def __init__(
        self,
        client: Optional[OpenAIAssistantClient] = None,
        config_file: Optional[Path] = None,
        prompts_file: Optional[Path] = None
    ):
        """
        Initialize the summary assistant adapter.
        
        Args:
            client: Optional pre-configured OpenAI Assistant Client
            config_file: Optional path to a specific config file
            prompts_file: Optional path to a specific prompts file
            
        Raises:
            ConfigError: If required configuration or prompt files are missing
        """
        # Module name for this adapter
        self.module_name = "summary"
        
        # Create or use the provided client
        if client:
            self.client = client
        else:
            # Load configuration
            config = load_assistant_config(
                module_name=self.module_name,
                assistant_name="Text Summarizer",
                config_file=config_file
            )
            
            # Create client with summary-specific settings
            self.client = OpenAIAssistantClient(
                config=config,
                assistant_name="Text Summarizer",
                module_name=self.module_name
            )
        
        # Load prompts - use either the provided file or the module's config file
        if prompts_file:
            prompts_path = prompts_file
        else:
            # Use the module's config path
            voice_diary_dir = Path(__file__).resolve().parent.parent.parent.parent
            prompts_path = voice_diary_dir / "summary" / "config" / "prompts.yaml"
        
        # Load prompts from the file
        self.prompts = self._load_prompt_file(prompts_path)
    
    def _load_prompt_file(self, prompts_path: Path) -> Dict[str, Any]:
        """
        Load prompts from a specific file.
        
        Args:
            prompts_path: Path to the prompts file
            
        Returns:
            Dict: Prompts dictionary
            
        Raises:
            ConfigError: If the prompts file is missing or invalid
        """
        if not prompts_path.exists():
            raise ConfigError(f"Prompts file not found: {prompts_path}")
            
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                prompts_data = yaml.safe_load(f)
                prompts = prompts_data.get('prompts', {})
                if not prompts:
                    raise ConfigError(f"No prompts found in file: {prompts_path}")
                return prompts
        except Exception as e:
            raise ConfigError(f"Error loading prompts file {prompts_path}: {e}")
    
    def get_prompt_template(self, prompt_name: str) -> str:
        """
        Get a prompt template by name.
        
        Args:
            prompt_name: Name of the prompt template
            
        Returns:
            str: The prompt template text
            
        Raises:
            ConfigError: If the prompt template is not found
        """
        prompt_data = self.prompts.get(prompt_name)
        if not prompt_data:
            raise ConfigError(f"Prompt '{prompt_name}' not found in {self.module_name} prompts")

        template = prompt_data.get("template")
        if not template:
            raise ConfigError(f"Template not found for prompt '{prompt_name}'")

        return template
    
    def summarize_text(
        self, 
        text: str, 
        summary_type: str = "comprehensive", 
        target_length: int = 100,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Summarize text using the OpenAI assistant.
        
        Args:
            text: The text to summarize
            summary_type: Type of summary (comprehensive, bullet_points, etc.)
            target_length: Target word count for summary
            focus_areas: Optional specific areas to focus on
            
        Returns:
            str: The summary
            
        Raises:
            AssistantClientError: If processing fails
            ConfigError: If required configuration is missing
        """
        try:
            # Get prompt template - no defaults, must exist
            prompt_template = self.get_prompt_template("summarize_text")
            
            # Get assistant instructions
            assistant_instructions = self.get_prompt_template("assistant_instructions")
            
            # Set up template variables
            template_vars = {
                "input_text": text,
                "summary_type": summary_type,
                "target_length": str(target_length),
                "focus_areas": ", ".join(focus_areas) if focus_areas else "the main points"
            }
            
            # Update client instructions
            self.client.instructions = assistant_instructions
            
            # Process with the client
            response = self.client.process_with_prompt_template(
                input_text=text,
                prompt_template=prompt_template,
                template_vars=template_vars
            )
            
            return response
            
        except ConfigError as e:
            # Re-raise configuration errors
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            error_msg = f"Error generating summary: {e}"
            logger.error(error_msg)
            raise AssistantClientError(error_msg)


def summarize_text(
    text: str, 
    summary_type: str = "comprehensive", 
    target_length: int = 100,
    focus_areas: Optional[List[str]] = None
) -> str:
    """
    Summarize text using a summary assistant.
    
    This function provides a simple interface to summarize text
    without needing to manage the adapter instance directly.
    
    Args:
        text: The text to summarize
        summary_type: Type of summary (comprehensive, bullet_points, etc.)
        target_length: Target word count for summary
        focus_areas: Optional specific areas to focus on
        
    Returns:
        str: The summary
        
    Raises:
        ConfigError: If required configuration is missing
        AssistantClientError: If processing fails
    """
    adapter = SummaryAssistantAdapter()
    return adapter.summarize_text(
        text=text,
        summary_type=summary_type,
        target_length=target_length,
        focus_areas=focus_areas
    ) 