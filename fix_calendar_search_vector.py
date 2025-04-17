"""
Fix for the update_search_vector function to properly handle calendar_events table.

This script updates the database trigger function that generates the search vector
for full-text search to correctly handle the calendar_events table schema.
"""
import logging
from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("fix_calendar_search_vector")

@db_connection_handler
def fix_search_vector_function(conn):
    """
    Update the search_vector trigger function to handle calendar_events table correctly.
    
    The calendar_events table doesn't have a 'content' field, but has 'summary' and 'description'
    which should be included in the search vector.
    """
    try:
        logger.info("Updating the update_search_vector function...")
        cur = conn.cursor()
        
        # Create or replace the function with improved table detection for calendar_events
        cur.execute("""
        CREATE OR REPLACE FUNCTION update_search_vector()
        RETURNS trigger AS $$
        DECLARE
            table_name text := TG_TABLE_NAME;
        BEGIN
            IF table_name = 'transcriptions' THEN
                NEW.search_vector := to_tsvector('english',
                    coalesce(NEW.content, '') ||
                    coalesce(NEW.tag, '') ||
                    coalesce(NEW.filename, '')
                );
            ELSIF table_name = 'calendar_events' THEN
                NEW.search_vector := to_tsvector('english',
                    coalesce(NEW.summary, '') ||
                    coalesce(NEW.description, '') ||
                    coalesce(NEW.location, '')
                );
            ELSE
                NEW.search_vector := to_tsvector('english',
                    coalesce(NEW.content, '') ||
                    coalesce(NEW.summary, '') ||
                    coalesce(NEW.description, '') ||
                    coalesce(NEW.note, '') ||
                    coalesce(NEW.name, '') ||
                    coalesce(NEW.context, '') ||
                    coalesce(NEW.first_name, '') ||
                    coalesce(NEW.last_name, '') ||
                    coalesce(NEW.location, '')
                );
            END IF;
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        logger.info("Successfully updated the update_search_vector function!")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update search vector function: {e}")
        return False

def main():
    print("Fixing the update_search_vector function to handle calendar_events...")
    success = fix_search_vector_function()
    
    if success:
        print("✅ Successfully fixed the update_search_vector function!")
    else:
        print("❌ Failed to fix the update_search_vector function. See logs for details.")

if __name__ == "__main__":
    main() 