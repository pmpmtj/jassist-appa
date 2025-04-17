import logging
import os
from typing import Optional, Dict, Any
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("model_handler", module="transcribe")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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
