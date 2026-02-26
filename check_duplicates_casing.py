import json
from collections import Counter

file_path = 'netem_full_list.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        items = data.get("5530考研词汇词频排序表", [])
        
        # Keep original words to check casing
        original_words = [item.get("单词", "").strip() for item in items if "单词" in item]
        lowercased_words = [w.lower() for w in original_words]
        
        print(f"Total items: {len(items)}")
        
        counts = Counter(lowercased_words)
        duplicates = [word for word, count in counts.items() if count > 1]
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate words (case-insensitive):")
            for dup in duplicates:
                print(f"  Duplicate: {dup}")
                # Find original occurrences
                occurrences = [w for w in original_words if w.lower() == dup]
                print(f"    Originals: {occurrences}")
        else:
            print("No duplicate words found.")
            
except Exception as e:
    print(f"Error: {e}")
