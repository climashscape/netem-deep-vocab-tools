import json
import sqlite3
import os
import sys

# Add parent directory to path to allow importing settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(__file__), 'verbs.db')
DIST_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dist', 'static')
LEGACY_JSON_PATH = os.path.join(DIST_STATIC_DIR, 'legacy_data.json')
LEGACY_JS_PATH = os.path.join(DIST_STATIC_DIR, 'js', 'data_legacy.js')

def export_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Fetching explanations from database...")
    try:
        # Fetch all single mode explanations
        c.execute("SELECT query_key, content, image_url, image_dicebear, image_pollinations FROM explanations WHERE mode='single'")
        rows = c.fetchall()
        
        legacy_data = {}
        export_list = []
        
        for row in rows:
            query_key = row[0]
            content = row[1]
            image_url = row[2]
            
            # Prefer specific provider images if available, fallback to generic
            # logic mirroring local_api.js preference
            # But legacy_data.json structure seems to store raw rows?
            # Let's check import_legacy_data.py again to match structure.
            # It expects a list under 'explanations' key for JSON, 
            # and a dictionary for JS.
            
            # Prepare dictionary entry for JS file
            # Format: "word:verb": { content: "...", image_url: "..." }
            # Most keys in DB are just "word" (lowercase)
            # But legacy data often uses "word:verb".
            # Let's stick to the DB key if it's unique, or append :verb if it's a verb.
            # Actually, the DB key is what we use for lookup.
            
            legacy_data[query_key] = {
                "content": content,
                "image_url": image_url,
                "image_dicebear": row[3],
                "image_pollinations": row[4]
            }
            
            # Prepare list entry for JSON file (mirroring import format)
            export_list.append({
                "mode": "single",
                "query_key": query_key,
                "content": content,
                "image_url": image_url,
                "image_dicebear": row[3],
                "image_pollinations": row[4],
                "created_at": None # We don't have this in select, maybe add if needed
            })
            
    except Exception as e:
        print(f"Error exporting data: {e}")
        conn.close()
        return

    conn.close()
    
    # 1. Write legacy_data.json
    print(f"Writing {len(export_list)} items to {LEGACY_JSON_PATH}...")
    with open(LEGACY_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump({"explanations": export_list}, f, ensure_ascii=False, indent=2)
        
    # 2. Write data_legacy.js
    print(f"Writing JS object to {LEGACY_JS_PATH}...")
    # Wrap in window.NETEM_LEGACY_DATA = ...
    json_str = json.dumps(legacy_data, ensure_ascii=False)
    js_content = f"window.NETEM_LEGACY_DATA = {json_str};"
    
    with open(LEGACY_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print("Export complete.")

if __name__ == "__main__":
    export_data()
