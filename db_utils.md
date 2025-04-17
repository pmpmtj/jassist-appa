# Database Utilities Design Guide

This document provides a comprehensive overview of the database utilities module in the jassist application. Rather than describing a flow, it focuses on the architecture, design patterns, and best practices implemented in the database layer.

## Module Structure

The database utilities are organized in a modular structure that separates concerns:

```
jassist/voice_diary/db_utils/
├── __init__.py                   # Package initialization 
├── db_manager.py                 # Facade pattern implementation
├── db_config.py                  # Configuration management
├── db_connection.py              # Connection pooling and decorator
├── db_schema.py                  # Table definitions and creation
├── setup_database.py             # CLI tool for database setup
├── transcription_repository.py   # Transcription CRUD operations
├── summary_repository.py         # Summary CRUD operations
└── calendar_repository.py        # Calendar CRUD operations
```

## Key Design Patterns

### 1. Repository Pattern

The database layer implements the Repository pattern, which abstracts the data access logic and provides a collection-like interface for domain objects.

Each entity type (transcription, summary, calendar event) has its own repository with specific CRUD operations:

```python
# Example from transcription_repository.py
@db_connection_handler
def save_transcription(conn, content, filename=None, audio_path=None, model_type=None,
                      duration_seconds=None, metadata=None, tag=None):
    # Implementation...

@db_connection_handler
def get_transcription(conn, transcription_id):
    # Implementation...
```

### 2. Facade Pattern

The `db_manager.py` module implements the Facade pattern, providing a simplified interface to the complex database subsystem:

```python
"""
Database Manager Module

This module serves as a facade for the database components.
It provides a centralized interface to the database operations.
"""

from jassist.voice_diary.db_utils.db_connection import (
    initialize_db, 
    close_all_connections
)
from jassist.voice_diary.db_utils.db_schema import create_tables
from jassist.voice_diary.db_utils.transcription_repository import (
    save_transcription,
    get_transcription,
    get_latest_transcriptions,
    get_transcriptions_by_date_range
)
# ... more imports ...

# Re-export all functions to maintain a clean API
__all__ = [
    # Connection management
    'initialize_db',
    'close_all_connections',
    'create_tables',
    
    # Transcription operations
    'save_transcription',
    # ... more functions ...
]
```

Clients interact with this facade rather than with individual repository modules:

```python
from jassist.voice_diary.db_utils.db_manager import (
    save_transcription, 
    get_latest_transcriptions
)

# Client code
transcription_id = save_transcription(content="Hello world", tag="diary")
recent_entries = get_latest_transcriptions(limit=5)
```

### 3. Decorator Pattern for Connection Management

The database connection management is implemented using a decorator pattern, which elegantly handles connection acquisition, error handling, and connection release:

```python
def db_connection_handler(func):
    """
    Decorator for database operations that handles connection management.
    Automatically acquires a connection from the pool, handles exceptions,
    and returns the connection to the pool when done.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_connection()
            return func(conn, *args, **kwargs)
        except Exception as e:
            if conn and not kwargs.get('_skip_rollback', False):
                conn.rollback()
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return an appropriate default value based on the function's purpose
            if func.__name__.startswith('get_'):
                return [] if 'fetchall' in func.__code__.co_names else None
            elif func.__name__.startswith('save_'):
                return None
            elif func.__name__.startswith('update_') or func.__name__.startswith('delete_'):
                return False
            elif func.__name__.startswith('check_'):
                return False
            else:
                return None
        finally:
            if conn:
                return_connection(conn)
    return wrapper
```

This decorator is used throughout the repository modules:

```python
@db_connection_handler
def save_calendar_event(conn, summary, start_datetime, end_datetime, ...):
    # Implementation...
```

## Connection Pooling

The database utilities implement connection pooling for efficient database connection management:

```python
def initialize_db():
    """Initialize the database connection pool"""
    global connection_pool

    try:
        db_url = get_db_url()
        if not db_url:
            logger.error("Cannot initialize database: DATABASE_URL is not set.")
            return False
            
        logger.info("Initializing DB with connection string (details hidden)")

        logger.info("Testing direct connection...")
        try:
            test_conn = psycopg2.connect(db_url)
            logger.info(f"Connected. PostgreSQL version: {test_conn.server_version}")
            test_conn.close()
        except Exception as conn_error:
            logger.error(f"Direct connection failed: {conn_error}")
            return False

        logger.info("Creating connection pool...")
        connection_pool = pool.SimpleConnectionPool(1, 10, db_url)
        logger.info("Connection pool created")
        return True

    except Exception as e:
        logger.error("DB initialization failed.")
        logger.error(traceback.format_exc())
        return False
```

Benefits of connection pooling:

1. **Performance**: Reusing connections avoids the overhead of establishing new ones
2. **Resource Management**: Limits the number of concurrent connections to the database
3. **Reliability**: Connection failures are handled gracefully

## Schema Management

Database schema is defined separately from the repository operations in `db_schema.py`:

```python
@db_connection_handler
def create_tables(conn):
    """Create all database tables if they don't exist"""
    try:
        cur = conn.cursor()

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
            tag TEXT
        )
        """)

        # ... more table definitions ...

        conn.commit()
        logger.info("All tables created or verified successfully.")
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Error during table creation.")
        logger.error(traceback.format_exc())
        raise
```

This separation of concerns allows for:

1. **Clean Repository Code**: Repository modules focus purely on data access
2. **Schema Evolution**: Schema changes can be managed independently
3. **Database Initialization**: A clean process for setting up the database

## Error Handling Strategy

The database utilities implement a comprehensive error handling strategy:

1. **Transaction Management**: Automatic `commit` on success and `rollback` on failure
2. **Contextual Logging**: Detailed error logs with function name and stack trace
3. **Graceful Degradation**: Appropriate default return values based on function type
4. **Error Propagation Control**: Errors are contained and don't crash the application

```python
# Example of intelligent default return values
if func.__name__.startswith('get_'):
    return [] if 'fetchall' in func.__code__.co_names else None
elif func.__name__.startswith('save_'):
    return None
elif func.__name__.startswith('update_') or func.__name__.startswith('delete_'):
    return False
elif func.__name__.startswith('check_'):
    return False
else:
    return None
```

## Configuration Management

Database configuration is managed in `db_config.py` which uses environment variables loaded from a `.env` file:

```python
def get_db_url():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment.")
        return None
    logger.debug(f"Using DB URL: {db_url}")
    logger.info("Using DB URL (connection string available)")
    return db_url
```

This approach provides:

1. **Security**: Sensitive database credentials aren't hardcoded
2. **Environment Adaptability**: Works across development, testing, and production
3. **Configuration Flexibility**: Easy to change during deployment

## Dynamic Query Building

For more complex operations, the database utilities use dynamic query building:

```python
@db_connection_handler
def update_calendar_event(conn, event_id, **kwargs):
    """Update a calendar event"""
    # Process complex objects
    if 'attendees' in kwargs and isinstance(kwargs['attendees'], list):
        kwargs['attendees'] = json.dumps(kwargs['attendees'])
    # ... more processing ...
    
    # Build the update query dynamically based on provided fields
    fields = []
    values = []
    
    for key, value in kwargs.items():
        fields.append(f"{key} = %s")
        values.append(value)
        
    if not fields:
        logger.warning("No fields to update")
        return False
        
    values.append(event_id)  # For the WHERE clause
    
    query = f"""
    UPDATE calendar_events
    SET {", ".join(fields)}
    WHERE id = %s
    """
    
    cur = conn.cursor()
    cur.execute(query, values)
    # ... finish operation ...
```

Benefits of this approach:

1. **Flexibility**: Only update fields that are provided
2. **SQL Injection Prevention**: Properly parameterized queries
3. **Code Reuse**: One function handles all update scenarios

## JSON Handling

The database utilities seamlessly handle JSON data:

```python
# Convert Python objects to JSON for storage
if attendees and isinstance(attendees, list):
    attendees = json.dumps(attendees)
    
if recurrence and isinstance(recurrence, list):
    recurrence = json.dumps(recurrence)
    
if reminders and isinstance(reminders, dict):
    reminders = json.dumps(reminders)

# Save to database
cur.execute("""
INSERT INTO calendar_events 
(summary, ..., attendees, recurrence, reminders, ...)
VALUES (%s, ..., %s, %s, %s, ...)
""", (summary, ..., attendees, recurrence, reminders, ...))
```

This allows for:

1. **Complex Data Storage**: Store rich data structures in SQL databases
2. **Schema Flexibility**: Add new fields without altering the database schema
3. **Data Integrity**: Complex objects are properly serialized and deserialized

## CLI Tools

The `setup_database.py` module provides a command-line interface for database setup:

```python
def main():
    parser = argparse.ArgumentParser(description='Set up the PostgreSQL database')
    args = parser.parse_args()

    # ... logging setup ...

    env_path = Path(__file__).parents[1] / "config" / ".env"
    if not env_path.exists():
        logger.warning(f".env file not found at expected location: {env_path}")
        response = input("Continue without .env? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    logger.info("Initializing database...")
    if initialize_db():
        logger.info("Creating database tables...")
        if create_tables():
            logger.info("Database setup completed successfully.")
        else:
            logger.error("Table creation failed.")
            sys.exit(1)
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)
```

This provides:

1. **Easy Setup**: Simple command to set up the database
2. **Interactive**: Asks for confirmation when configuration is missing
3. **Clear Feedback**: Detailed logging during the setup process

## Best Practices for New Applications

When creating new applications that use a database, consider the following practices demonstrated in this module:

### 1. Separation of Concerns

- **Connection Management**: Separate from business logic
- **Schema Definition**: Independent from data access code
- **Repository Organization**: One repository per entity type

### 2. Use Decorators for Cross-Cutting Concerns

- **Connection Handling**: Automatic acquisition and release
- **Transaction Management**: Automatic commit and rollback
- **Error Handling**: Consistent across all database operations

### 3. Implement a Facade Pattern

- **Simplified API**: Provide a clean, unified interface
- **Encapsulation**: Hide the complexity of the database layer
- **Maintainability**: Change implementations without affecting clients

### 4. Use Connection Pooling

- **Performance**: Avoid the overhead of creating connections
- **Resource Management**: Control the number of connections
- **Reliability**: Handle connection failures gracefully

### 5. Implement Proper Error Handling

- **Transaction Safety**: Ensure data consistency with proper rollbacks
- **Detailed Logging**: Provide context for debugging
- **Graceful Degradation**: Return sensible defaults on failure

### 6. Use Dynamic Query Building

- **Flexibility**: Adapt queries to runtime conditions
- **Reuse**: Create generic functions for similar operations
- **Security**: Always use parameterized queries

### 7. Handle Complex Data Types

- **JSON Serialization**: Convert between Python objects and JSON
- **Data Validation**: Ensure data integrity before storage
- **Schema Flexibility**: Store complex objects in JSON columns

### 8. Provide CLI Tools

- **Setup Automation**: Make database initialization easy
- **Maintenance Utilities**: Tools for common administrative tasks
- **Developer Experience**: Streamline the development workflow

## Summary

The database utilities module demonstrates a well-architected approach to database access with:

1. **Clean Separation of Concerns**: Each module has a specific responsibility
2. **Elegant Use of Decorators**: For connection and transaction management
3. **Comprehensive Error Handling**: For robustness and reliability
4. **Flexible Query Building**: For adaptable database operations
5. **Strong Type Handling**: For complex data structures
6. **Connection Pooling**: For performance and resource management

By following these patterns and best practices, you can create database utilities that are maintainable, efficient, and robust for your own applications.
