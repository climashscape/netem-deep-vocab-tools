import json

JSON_PATH = 'scripts/explain_verbs/static/netem_full_list.json'

def check_duplicates():
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        key = "5530考研词汇词频排序表"
        items = data.get(key, [])
        
        print(f"Total items: {len(items)}")
        
        seen = set()
        duplicates = []
        
        for item in items:
            word = item.get("单词", "").strip().lower()
            if word in seen:
                duplicates.append(word)
            seen.add(word)
            
        print(f"Unique words (lowercase): {len(seen)}")
        print(f"Duplicates found: {len(duplicates)}")
        if duplicates:
            print("Duplicate words:", duplicates)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicates()
