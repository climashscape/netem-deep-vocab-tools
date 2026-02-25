import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'verbs.db')

def check_verb(verb):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Based on sqlite schema dump, table is 'explanations', cols: mode, query_key, content
    try:
        c.execute("SELECT content FROM explanations WHERE query_key=?", (verb,))
        row = c.fetchone()
        
        if row:
            print(f"--- START {verb} ---")
            content = row[0]
            print(content[:500]) # Print first 500 chars
            print(f"REPR: {repr(content[:100])}")
            print("...")
            # Check for our split keys
            print(f"Has '**三维理解': {'**三维理解' in content}")
            print(f"Has '** 三维理解': {'** 三维理解' in content}")
            print(f"Has '### 三维理解': {'### 三维理解' in content}")
            print(f"Has '### 1. **三维理解**': {'### 1. **三维理解**' in content}")
            print(f"Has '### 1. 三维理解': {'### 1. 三维理解' in content}")
            print(f"--- END {verb} ---")
        else:
            print(f"Verb '{verb}' not found in DB")
            
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_verb("make")
    check_verb("do")
    check_verb("have")
    check_verb("be")
