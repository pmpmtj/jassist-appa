from jassist.voice_diary.db_utils.db_connection import db_connection_handler
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
import traceback

logger = setup_logger("db_schema", module="db_utils")

@db_connection_handler
def create_tables(conn):
    """Create all database tables with full-text search and relationships"""
    try:
        cur = conn.cursor()

        # Shared FTS function
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

        # Transcriptions table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            filename TEXT,
            audio_path TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            duration_seconds FLOAT,
            metadata JSONB,
            tag TEXT,
            destination_table TEXT,
            destination_id INTEGER,
            is_processed BOOLEAN DEFAULT FALSE,
            search_vector tsvector
        )
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at ON transcriptions(created_at)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_transcriptions_search_vector ON transcriptions USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_transcriptions
        BEFORE INSERT OR UPDATE ON transcriptions
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # vday_summaries
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vday_summaries (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            summary_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            filename TEXT,
            date_range_start TIMESTAMP WITH TIME ZONE,
            date_range_end TIMESTAMP WITH TIME ZONE,
            search_vector tsvector
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vday_summaries_date ON vday_summaries(summary_date)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vday_summaries_search_vector ON vday_summaries USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_vday
        BEFORE INSERT OR UPDATE ON vday_summaries
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # Calendar events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id SERIAL PRIMARY KEY,
            summary TEXT,
            location TEXT,
            description TEXT,
            start_dateTime TEXT,
            start_timeZone TEXT,
            end_dateTime TEXT,
            end_timeZone TEXT,
            attendees TEXT,
            recurrence TEXT,
            reminders TEXT,
            visibility TEXT,
            colorId TEXT,
            transparency TEXT,
            status TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            search_vector tsvector
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_start_datetime ON calendar_events(start_dateTime)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_end_datetime ON calendar_events(end_dateTime)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_date_range ON calendar_events(start_dateTime, end_dateTime)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_search_vector ON calendar_events USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_calendar
        BEFORE INSERT OR UPDATE ON calendar_events
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # Diary
        cur.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            entry_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            mood TEXT,
            tags TEXT[],
            search_vector tsvector,
            source_transcription_id INTEGER REFERENCES transcriptions(id) ON DELETE SET NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_diary_entry_date ON diary(entry_date)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_diary_search_vector ON diary USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_diary
        BEFORE INSERT OR UPDATE ON diary
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # To-Do
        cur.execute("""
        CREATE TABLE IF NOT EXISTS to_do (
            id SERIAL PRIMARY KEY,
            task TEXT NOT NULL,
            due_date TIMESTAMP WITH TIME ZONE,
            priority TEXT,
            status TEXT DEFAULT 'pending',
            search_vector tsvector,
            source_transcription_id INTEGER REFERENCES transcriptions(id) ON DELETE SET NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_to_do_due_date ON to_do(due_date)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_to_do_search_vector ON to_do USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_todo
        BEFORE INSERT OR UPDATE ON to_do
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # Contacts
        cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            email TEXT,
            note TEXT,
            search_vector tsvector,
            source_transcription_id INTEGER REFERENCES transcriptions(id) ON DELETE SET NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_contacts_search_vector ON contacts USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_contacts
        BEFORE INSERT OR UPDATE ON contacts
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # Entities
        cur.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            context TEXT,
            relevance_score FLOAT,
            search_vector tsvector,
            source_transcription_id INTEGER REFERENCES transcriptions(id) ON DELETE SET NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_entities_search_vector ON entities USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_entities
        BEFORE INSERT OR UPDATE ON entities
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        # Accounts
        cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            entry_type TEXT CHECK (entry_type IN ('income', 'expense')) NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            currency TEXT DEFAULT 'EUR',
            note TEXT,
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            search_vector tsvector,
            source_transcription_id INTEGER REFERENCES transcriptions(id) ON DELETE SET NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_accounts_date ON accounts(date)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_accounts_search_vector ON accounts USING GIN(search_vector)
        """)
        cur.execute("""
        CREATE TRIGGER trg_update_search_vector_accounts
        BEFORE INSERT OR UPDATE ON accounts
        FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """)

        conn.commit()
        logger.info("All tables with FTS created successfully.")
        return True

    except Exception as e:
        conn.rollback()
        logger.error("Error during table creation.")
        logger.error(traceback.format_exc())
        raise
