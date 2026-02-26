import sqlite3
import json
import os

DB_PATH = 'scripts/explain_verbs/verbs.db'
JSON_PATH = 'scripts/explain_verbs/static/netem_full_list.json'
LEGACY_DATA_PATH = 'scripts/explain_verbs/static/legacy_data.json'

def export_legacy_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check word count in DB (if there is a verbs table or just count distinct explanations)
    try:
        cursor.execute("SELECT COUNT(*) FROM explanations")
        count = cursor.fetchone()[0]
        print(f"Total explanations in DB: {count}")
    except Exception as e:
        print(f"Error counting explanations: {e}")

    # 2. Export explanations to legacy_data.json
    try:
        cursor.execute("SELECT query_key, content, image_url, image_dicebear, image_pollinations FROM explanations")
        rows = cursor.fetchall()
        
        legacy_data = {}
        for row in rows:
            # Skip if query_key is None
            if not row[0]: continue
            
            key = row[0].lower() # Normalize key
            
            # New format: Value is an object, not just string
            legacy_data[key] = {
                "content": row[1],
                "image_url": row[2],
                "image_dicebear": row[3],
                "image_pollinations": row[4]
            }
            
        print(f"Exporting {len(legacy_data)} records...")
        
        # Define targets for JSON and JS files
        json_targets = [
            'scripts/explain_verbs/static/legacy_data.json',
            'dist/static/legacy_data.json'
        ]
        
        js_targets = [
            'scripts/explain_verbs/static/js/data_legacy.js',
            'dist/static/js/data_legacy.js'
        ]
        
        # 1. Save JSON files
        for target in json_targets:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(legacy_data, f, ensure_ascii=False)
                print(f"Saved JSON to {target}")
            except Exception as e:
                print(f"Failed to save JSON to {target}: {e}")
        
        # 2. Save JS files (Window Variable Wrapper)
        js_content = f"window.NETEM_LEGACY_DATA = {json.dumps(legacy_data, ensure_ascii=False)};"
        for target in js_targets:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                print(f"Saved JS to {target}")
            except Exception as e:
                print(f"Failed to save JS to {target}: {e}")
            
        print("Export complete.")
        
    except Exception as e:
        print(f"Error exporting legacy data: {e}")
        
    conn.close()

def check_full_list():
    if not os.path.exists(JSON_PATH):
        print(f"Error: JSON not found at {JSON_PATH}")
        return

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        key = "5530考研词汇词频排序表"
        if key in data:
            print(f"Total words in netem_full_list.json: {len(data[key])}")
            # Check last few words
            print("Last 3 words:", [item.get("单词") for item in data[key][-3:]])
        else:
            print(f"Key '{key}' not found in JSON")
            
    except Exception as e:
        print(f"Error reading JSON: {e}")

if __name__ == "__main__":
    print("--- Checking Data Integrity ---")
    check_full_list()
    print("\n--- Exporting Legacy Data ---")
    export_legacy_data()
