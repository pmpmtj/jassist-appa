from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
import traceback

logger = setup_logger("db_update", module="db_utils")

@db_connection_handler
def update_fts_function(conn):
    """Update the full-text search function to handle different tables correctly"""
    try:
        cur = conn.cursor()

        # Updated FTS function with table-specific indexing
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
        logger.info("FTS function updated successfully.")
        return True

    except Exception as e:
        conn.rollback()
        logger.error("Error updating FTS function.")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = update_fts_function()
    if success:
        print("Successfully updated the full-text search function.")
    else:
        print("Failed to update the full-text search function. Check logs for details.") 