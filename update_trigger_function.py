"""
Script to update the search_vector trigger function in the database.
"""

import logging
from jassist.voice_diary.db_utils.db_manager import initialize_db
from jassist.voice_diary.db_utils.db_connection import db_connection_handler

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@db_connection_handler
def update_search_vector_function(conn):
    """Update the search_vector trigger function in the database."""
    
    cursor = conn.cursor()
    
    # Drop existing function
    logger.info("Dropping existing search_vector function...")
    cursor.execute("""
    DROP FUNCTION IF EXISTS update_search_vector() CASCADE;
    """)
    
    # Create new function with table-specific handling
    logger.info("Creating new search_vector function...")
    cursor.execute("""
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
        ELSIF table_name = 'diary' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.content, '') ||
                coalesce(NEW.mood, '')
            );
        ELSIF table_name = 'to_do' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.task, '') ||
                coalesce(NEW.priority, '') ||
                coalesce(NEW.status, '')
            );
        ELSIF table_name = 'calendar_events' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.summary, '') ||
                coalesce(NEW.description, '') ||
                coalesce(NEW.location, '')
            );
        ELSIF table_name = 'contacts' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.first_name, '') ||
                coalesce(NEW.last_name, '') ||
                coalesce(NEW.email, '') ||
                coalesce(NEW.phone, '') ||
                coalesce(NEW.note, '')
            );
        ELSIF table_name = 'entities' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.name, '') ||
                coalesce(NEW.type, '') ||
                coalesce(NEW.context, '')
            );
        ELSIF table_name = 'vday_summaries' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.content, '')
            );
        ELSIF table_name = 'accounts' THEN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.entry_type, '') ||
                coalesce(NEW.note, '') ||
                coalesce(NEW.currency, '')
            );
        ELSE
            -- Fallback for any other tables
            NEW.search_vector := to_tsvector('english', '');
        END IF;
        RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    """)
    
    # Recreate all triggers
    logger.info("Recreating triggers...")
    
    # Transcriptions trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_transcriptions
    BEFORE INSERT OR UPDATE ON transcriptions
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # Diary trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_diary
    BEFORE INSERT OR UPDATE ON diary
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # To-Do trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_todo
    BEFORE INSERT OR UPDATE ON to_do
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # Calendar events trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_calendar
    BEFORE INSERT OR UPDATE ON calendar_events
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # Contacts trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_contacts
    BEFORE INSERT OR UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # Entities trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_entities
    BEFORE INSERT OR UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # vday_summaries trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_vday
    BEFORE INSERT OR UPDATE ON vday_summaries
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # Accounts trigger
    cursor.execute("""
    CREATE TRIGGER trg_update_search_vector_accounts
    BEFORE INSERT OR UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    conn.commit()
    logger.info("Search vector function and triggers updated successfully.")
    return True

if __name__ == "__main__":
    logger.info("Starting update of search vector function...")
    if initialize_db():
        success = update_search_vector_function()
        if success:
            logger.info("Successfully updated search vector function.")
        else:
            logger.error("Failed to update search vector function.")
    else:
        logger.error("Failed to initialize database connection.") 