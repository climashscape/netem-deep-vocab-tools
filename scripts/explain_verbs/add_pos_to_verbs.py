import json
import os
import nltk
from nltk.corpus import wordnet as wn

# Path to netem_full_list.json
JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../netem_full_list.json"))

def get_pos_category(word):
    # Strip spaces and lower case
    word = word.strip().lower()
    
    # Check synsets
    # If not in WordNet, try to guess or mark as 'other'
    synsets = wn.synsets(word)
    if not synsets:
        return "other"
        
    is_noun = bool(wn.synsets(word, pos=wn.NOUN))
    is_verb = bool(wn.synsets(word, pos=wn.VERB))
    is_adj = bool(wn.synsets(word, pos=wn.ADJ))
    is_adv = bool(wn.synsets(word, pos=wn.ADV))
    
    if is_noun and is_verb:
        return "noun_verb"
    elif is_noun:
        return "noun"
    elif is_verb:
        return "verb"
    elif is_adj or is_adv:
        return "adj_adv"
    else:
        return "other"

def main():
    if not os.path.exists(JSON_PATH):
        print(f"File not found: {JSON_PATH}")
        return

    print(f"Reading from {JSON_PATH}")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Backup
    backup_path = JSON_PATH + ".bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Backup created at {backup_path}")

    # Process
    count = 0
    stats = {"noun": 0, "verb": 0, "noun_verb": 0, "other": 0, "adj_adv": 0}
    
    # Assuming the structure is {"key": [list of words]}
    for key, words in data.items():
        print(f"Processing key: {key}")
        for item in words:
            word = item.get("单词", "")
            if word:
                pos = get_pos_category(word)
                item["pos"] = pos
                stats[pos] += 1
                count += 1
                if count % 1000 == 0:
                    print(f"Processed {count} words...")

    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Save
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {JSON_PATH} with POS info.")

if __name__ == "__main__":
    main()
