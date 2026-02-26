import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'verbs.db')
LEGACY_DATA_PATH = os.path.join(os.path.dirname(__file__), 'static', 'legacy_data.json')

def import_data():
    if not os.path.exists(LEGACY_DATA_PATH):
        print(f"Error: {LEGACY_DATA_PATH} not found")
        return

    with open(LEGACY_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    explanations = data.get('explanations', [])
    if not explanations:
        print("No explanations found in legacy_data.json")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print(f"Importing {len(explanations)} explanations...")
    
    count = 0
    for item in explanations:
        mode = item.get('mode')
        query_key = item.get('query_key')
        content = item.get('content')
        image_url = item.get('image_url')
        created_at = item.get('created_at')

        # Map image_url to specific columns if applicable
        image_dicebear = None
        image_pollinations = None
        if image_url:
            if 'dicebear.com' in image_url:
                image_dicebear = image_url
            elif 'pollinations.ai' in image_url:
                image_pollinations = image_url

        try:
            c.execute("""
                INSERT OR IGNORE INTO explanations 
                (mode, query_key, content, image_url, image_dicebear, image_pollinations, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mode, query_key, content, image_url, image_dicebear, image_pollinations, created_at))
            if c.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"Error importing {query_key}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully imported {count} new explanations.")

if __name__ == "__main__":
    import_data()
