import nltk
try:
    from nltk.corpus import wordnet as wn
    print("NLTK and WordNet are available.")
    # Test a word
    print(f"Test 'run': {wn.synsets('run')}")
except ImportError:
    print("NLTK not installed.")
except LookupError:
    print("WordNet data not found. Need to download.")
