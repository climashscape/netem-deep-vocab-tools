import os
import json
import nltk
from pathlib import Path
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

def _resolve_within(base_dir, *parts):
    """Resolve *parts* under base_dir and refuse path escapes (CWE-22).

    The candidate path is fully resolved (``..`` segments and symlinks
    collapsed via realpath); anything landing outside base_dir — including
    absolute paths and ``..`` traversal — is rejected with ValueError.
    """
    base = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, candidate]) != base:
        raise ValueError(
            "Refusing path outside %s: %r" % (base, os.path.join(*parts))
        )
    return candidate

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Repo root: this script lives in tools/generate-doc/. The dataset files
    # are canonical in tools/data/ (the historical repo-root copies no longer
    # exist), so anchor both paths there and validate the boundary.
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(repo_root, 'tools', 'data')
    input_file = _resolve_within(data_dir, 'netem_full_list.json')
    output_file = _resolve_within(data_dir, 'netem_verbs.json')

    try:
        data = json.loads(Path(input_file).read_text(encoding='utf-8'))
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
    Path(output_file).write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f"Filtered {len(verbs)} verbs from {len(word_list)} words.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
