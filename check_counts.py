import json
import os

files = [
    'netem_full_list.json',
    'scripts/explain_verbs/static/netem_full_list.json',
    'netem_verbs.json'
]

for file_path in files:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"File: {file_path}")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  Key: {key}, Count: {len(value)}")
                    else:
                        print(f"  Key: {key}, Type: {type(value)}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")
