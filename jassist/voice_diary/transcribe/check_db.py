import sys
from pathlib import Path
from jassist.voice_diary.db_utils.db_manager import db_connection_handler

# Make sure we can import from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

@db_connection_handler
def check_recent_transcriptions(conn):
    cur = conn.cursor()
    
    # Query the database to check if tags are stored
    cur.execute("""
    SELECT id, filename, tag, created_at 
    FROM transcriptions 
    ORDER BY id DESC
    LIMIT 5
    """)
    
    rows = cur.fetchall()
    
    if not rows:
        print("No records found in the database.")
        return
        
    print(f"\nFound {len(rows)} transcription records:")
    print("-" * 50)
    for row in rows:
        id, filename, tag, created_at = row
        print(f"ID: {id}")
        print(f"Filename: {filename}")
        print(f"Tag: {tag}")
        print(f"Created at: {created_at}")
        print("-" * 50)

def main():
    try:
        print("Connecting to database...")
        check_recent_transcriptions()
    except Exception as e:
        print(f"Error: {e}")
            
if __name__ == "__main__":
    main() 