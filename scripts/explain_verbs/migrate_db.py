import sqlite3
import os
import sys

# Ensure we can import the explain_verbs logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from markdown_utils import clean_markdown

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")

def migrate_db():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Get all records
        c.execute("SELECT id, content, query_key FROM explanations")
        rows = c.fetchall()
        
        print(f"Found {len(rows)} records to process.")
        
        updated_count = 0
        for row in rows:
            record_id, content, key = row
            
            # Clean content
            new_content = clean_markdown(content)
            
            # Check if content actually changed (optional, but good for logging)
            if new_content != content:
                c.execute("UPDATE explanations SET content = ? WHERE id = ?", (new_content, record_id))
                updated_count += 1
                print(f"Updated record {record_id} (Key: {key})")
        
        conn.commit()
        print(f"Migration complete. Updated {updated_count} records.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
