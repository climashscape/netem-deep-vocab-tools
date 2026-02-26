import json
from collections import Counter

file_path = 'netem_full_list.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        items = data.get("5530考研词汇词频排序表", [])
        words = [item.get("单词", "").strip().lower() for item in items if "单词" in item]
        
        print(f"Total items: {len(items)}")
        print(f"Total words: {len(words)}")
        
        counts = Counter(words)
        duplicates = [word for word, count in counts.items() if count > 1]
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate words:")
            for word in duplicates:
                print(f"  {word}: {counts[word]}")
        else:
            print("No duplicate words found.")
            
except Exception as e:
    print(f"Error: {e}")
