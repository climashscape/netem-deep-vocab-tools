import os
import json
import nltk
from nltk.corpus import wordnet as wn

# Ensure wordnet is downloaded
try:
    # Check if 'wordnet' resource is available
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

def is_verb(word):
    """Check if a word is primarily a verb using WordNet."""
    synsets = wn.synsets(word, pos=wn.VERB)
    return len(synsets) > 0

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct path relative to script directory
    # Script is in scripts/generate-doc/
    # JSON is in root/netem_full_list.json
    input_file = os.path.join(script_dir, '../../netem_full_list.json')
    output_file = os.path.join(script_dir, '../../netem_verbs.json')

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return

    # Extract the list of words
    # The JSON structure is {"5530考研词汇词频排序表": [...]}
    key = list(data.keys())[0]
    word_list = data[key]

    verbs = []
    for item in word_list:
        word = item.get('单词', '').lower()
        if word and is_verb(word):
            verbs.append(item)

    # Sort by frequency (descending)
    # The original list is sorted by frequency, but let's ensure it.
    verbs.sort(key=lambda x: x.get('词频', 0), reverse=True)

    # Save to JSON
    output_data = {f"{key} (Verbs Only)": verbs}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Filtered {len(verbs)} verbs from {len(word_list)} words.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
