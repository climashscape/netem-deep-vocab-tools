import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'verbs.db')

def debug_db():
    print(f"File size of {DB_PATH}: {os.path.getsize(DB_PATH)} bytes")
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- Database Info ---")
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f"Tables: {tables}")
    
    for table_tuple in tables:
        table = table_tuple[0]
        c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        schema = c.fetchone()[0]
        print(f"\nSchema for '{table}':\n{schema}")
        
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"Table '{table}' has {count} rows")
    
    # Check for 'lean' specifically
    print("\n--- Checking for 'lean' ---")
    c.execute("SELECT mode, query_key FROM explanations WHERE query_key LIKE '%lean%'")
    results = c.fetchall()
    print(f"Results for 'lean': {results}")

    print("\n--- Checking for other suffixes ---")
    c.execute("SELECT DISTINCT SUBSTR(query_key, INSTR(query_key, ':')) FROM explanations WHERE query_key LIKE '%:%'")
    suffixes = c.fetchall()
    print(f"Suffixes found: {suffixes}")
    
    conn.close()

if __name__ == "__main__":
    debug_db()
