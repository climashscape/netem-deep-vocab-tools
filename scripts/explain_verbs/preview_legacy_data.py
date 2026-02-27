import json
import sqlite3
import os
import sys

# Add parent directory to path to allow importing settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(__file__), 'verbs.db')

def preview_export():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Fetching top 10 explanations for preview...")
    try:
        # Fetch top 10 single mode explanations
        # We can order by rowid or query_key to be deterministic
        c.execute("SELECT query_key, content, image_url FROM explanations WHERE mode='single' LIMIT 10")
        rows = c.fetchall()
        
        preview_list = []
        
        for row in rows:
            query_key = row[0]
            content = row[1]
            image_url = row[2]
            
            # Show the last 300 characters to verify "In a Nutshell"
            preview_len = 300
            content_end = content[-preview_len:] if content and len(content) > preview_len else content
            
            preview_list.append({
                "word": query_key,
                "content_tail": "..." + content_end if content and len(content) > preview_len else content,
                "image_url": image_url
            })
            
        print(json.dumps(preview_list, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"Error exporting data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    preview_export()
