with open('verbs.db', 'rb') as f:
    data = f.read(100)
    print(data)
    print(f"Length: {len(data)}")
