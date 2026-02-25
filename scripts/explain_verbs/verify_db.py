import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")

def verify_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Count all words in learning_progress
    c.execute("SELECT count(*) FROM learning_progress")
    total = c.fetchone()[0]
    
    # Count due words
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("SELECT count(*) FROM learning_progress WHERE status='learning' AND next_review <= ?", (now,))
    due = c.fetchone()[0]
    
    # Count mastered words
    c.execute("SELECT count(*) FROM learning_progress WHERE status='mastered'")
    mastered = c.fetchone()[0]
    
    # List first 5 words
    c.execute("SELECT verb, status, next_review FROM learning_progress LIMIT 5")
    print("\nFirst 5 words in DB:")
    for row in c.fetchall():
        print(row)
    
    # List one word that might be the extra one (if any)
    # Check verbs NOT in the 100-150 range
    with open(VERBS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        all_verbs_list = data.get("5530考研词汇词频排序表", [])
        test_verbs_set = set(v['单词'].lower() for v in all_verbs_list[100:150])
    
    c.execute("SELECT verb, status, next_review FROM learning_progress")
    all_db_verbs = c.fetchall()
    extra_verbs = [v for v in all_db_verbs if v[0] not in test_verbs_set]
    print(f"\nExtra verbs not in test set ({len(extra_verbs)}):")
    for v in extra_verbs:
        print(v)

    
    conn.close()

if __name__ == "__main__":
    verify_data()
