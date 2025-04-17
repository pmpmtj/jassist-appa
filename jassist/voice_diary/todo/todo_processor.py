"""
To-do processor module.

This module processes to-do entries and inserts them into the database.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
from .db.todo_db import save_todo_entry
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("todo_processor", module="todo")

def process_todo_entry(text: str, db_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a voice entry for a to-do task.
    
    Args:
        text: The voice entry text
        db_id: Optional ID of the database record this is associated with
        
    Returns:
        Tuple containing (success status, task data)
    """
    try:
        logger.info("Processing to-do entry")
        
        # For a basic implementation, we'll extract the task text without additional processing
        # We could enhance this later to extract due dates or priorities
        
        # Basic parsing for due dates (looking for "by", "due", "on", etc.)
        due_date = None
        priority = "medium"  # Default priority
        
        # Simple patterns for date extraction (could be enhanced with NLP)
        date_patterns = [
            r"by\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"due\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"on\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                time_term = match.group(1)
                today = datetime.now().date()
                
                if time_term == "today":
                    due_date = today
                elif time_term == "tomorrow":
                    due_date = today + timedelta(days=1)
                elif time_term in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    # Find the next occurrence of the day
                    days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
                           "friday": 4, "saturday": 5, "sunday": 6}
                    today_weekday = today.weekday()
                    days_until = (days[time_term] - today_weekday) % 7
                    if days_until == 0:  # If today is the day mentioned, go to next week
                        days_until = 7
                    due_date = today + timedelta(days=days_until)
                break
        
        # Simple patterns for priority extraction
        if any(term in text.lower() for term in ["urgent", "important", "critical", "high priority"]):
            priority = "high"
        elif any(term in text.lower() for term in ["low priority", "when you can", "not urgent"]):
            priority = "low"
        
        # Convert due_date to string if it's a datetime object
        due_date_str = due_date.isoformat() if due_date else None
        
        # Save to database
        task_id = save_todo_entry(
            task=text,
            due_date=due_date_str,
            priority=priority,
            source_transcription_id=db_id
        )
        
        if not task_id:
            logger.error("Failed to save to-do entry to database")
            return False, None
        
        logger.info(f"To-do entry saved with ID: {task_id}")
        
        # Return task data
        task_data = {
            "id": task_id,
            "task": text,
            "due_date": due_date_str,
            "priority": priority
        }
        
        return True, task_data
        
    except Exception as e:
        logger.exception(f"Error during to-do processing: {e}")
        return False, None 