#!/usr/bin/env python3
"""
Simple script to check database content
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

def get_db_url():
    # First try to load from .env file
    env_path = Path(__file__).resolve().parent / "jassist" / "voice_diary" / "config" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    return os.environ.get("DATABASE_URL")

def check_table(table_name):
    db_url = get_db_url()
    if not db_url:
        print("DATABASE_URL not found in environment variables")
        return
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No rows found in table: {table_name}")
            return
        
        print(f"Contents of {table_name} table:")
        for row in rows:
            print(row)
        
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in cursor.fetchall()]
        print(f"Columns: {columns}")
        
    except Exception as e:
        print(f"Error querying table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Check which tables to display
    if len(sys.argv) > 1:
        tables = sys.argv[1:]
    else:
        tables = ["contacts", "entities", "transcriptions"]
    
    for table in tables:
        check_table(table)
        print("-" * 80) 