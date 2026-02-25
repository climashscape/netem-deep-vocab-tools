
import sqlite3
import json
import os

db_path = "scripts/explain_verbs/verbs.db"
export_path = "dist/static/legacy_data.json"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get schema
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='explanations'")
if not cursor.fetchone():
    print("Error: Table 'explanations' not found in database")
    exit(1)

# Get columns
cursor.execute("PRAGMA table_info(explanations)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Columns in explanations: {columns}")

# Map columns
mode_col = 'mode' if 'mode' in columns else None
query_key_col = 'query_key' if 'query_key' in columns else ('verb' if 'verb' in columns else columns[0])
content_col = 'content' if 'content' in columns else ('explanation' if 'explanation' in columns else columns[1])
image_col = 'image_url' if 'image_url' in columns else None

# Get explanations data
query = "SELECT "
cols_to_select = []
if mode_col: cols_to_select.append(mode_col)
cols_to_select.append(query_key_col)
cols_to_select.append(content_col)
if image_col: cols_to_select.append(image_col)
query += ", ".join(cols_to_select) + " FROM explanations"

cursor.execute(query)
rows = cursor.fetchall()
legacy_data = {}
for row in rows:
    idx = 0
    # Skip mode if exists
    if mode_col: idx += 1
    query_key = row[idx]; idx += 1
    content = row[idx]
    
    if query_key and content:
        legacy_data[query_key.lower()] = content

with open(export_path, 'w', encoding='utf-8') as f:
    json.dump(legacy_data, f, ensure_ascii=False, indent=2)

print(f"Exported {len(legacy_data)} AI results to {export_path}")
conn.close()
