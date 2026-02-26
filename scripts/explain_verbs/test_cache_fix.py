import os
import sys
import sqlite3

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_cached_result, init_db

def test_cache():
    # Ensure DB is initialized
    init_db()
    
    # Test for 'lean'
    print("Testing cache for 'lean'...")
    result = get_cached_result("single", "lean")
    if result:
        print("Success! Found 'lean' in cache.")
        print(f"Content snippet: {result['content'][:100]}...")
    else:
        print("Failure: 'lean' not found in cache.")

if __name__ == "__main__":
    test_cache()
