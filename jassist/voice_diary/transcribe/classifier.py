import logging
from typing import Optional, Union, Dict, Any
from openai import OpenAI
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("classifier", module="transcribe")

def classify_text(client: OpenAI, transcription: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Classify the purpose of the transcribed text as 'diary', 'calendar', 'to do', or 'accounts'.
    If the text contains multiple contexts, it will be separated into different entries with appropriate tags.
    """
    try:
        logger.info("Sending transcription to LLM for classification...")
        
        # Handle dictionary transcription result
        if isinstance(transcription, dict):
            text = transcription.get("text", "")
        else:
            text = transcription

        prompt = (
        "Read the following entry and separate it into different contexts if applicable. "
        "Classify each context into one of these categories based on its content:\n"
        "- 'diary' for personal reflections, moods, or subjective experiences\n"
        "- 'calendar' for events with date/time\n"
        "- 'to_do' for tasks or action items : be aware that if to comes up, there may be a calendar event associated with it\n"
        "- 'accounts' for financial information like income or expenses\n"
        "- 'contacts' for names, phone numbers, or emails\n"
        "- 'entities' for organizations, companies, or web sites\n\n"
        "For each context, respond in this exact format:\n"
        'text: \"the extracted text content\"\n'
        "tag: the appropriate category (one of: diary, calendar, to_do, accounts, contacts, entities)\n\n"
        "If there are multiple contexts, separate them with a blank line.\n\n"
        f'Input: \"{text.strip()}\"'
    )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a text context separator and classifier. You extract different contexts from user input and classify each one appropriately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        tag = response.choices[0].message.content.strip()
        print(f"Received tag: {tag}")
        # If in development mode, uncomment this line to pause for inspection
        # input("Press Enter to continue...")
        logger.info(f"Received tag: {tag}")
        return tag

    except Exception as e:
        logger.error("Failed to classify text.", exc_info=True)
        return None
