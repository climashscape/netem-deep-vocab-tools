import sqlite3
import os
import json
import random
from datetime import datetime, timedelta

# Database Setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")
VERBS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../netem_full_list.json"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=MEMORY;")
    return conn

def inject_test_data():
    if not os.path.exists(VERBS_JSON_PATH):
        print(f"Error: {VERBS_JSON_PATH} not found.")
        return

    with open(VERBS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        all_verbs_list = data.get("5530考研词汇词频排序表", [])

    if not all_verbs_list:
        print("Error: No verbs found in JSON.")
        return

    conn = get_db_connection()
    c = conn.cursor()

    # Get some verbs to inject
    # We want to cover stages 0 to 7, and 'mastered' status
    stages = list(range(8)) # 0, 1, 2, 3, 4, 5, 6, 7
    statuses = ['learning', 'review', 'mastered']
    
    # Select a few verbs for each stage/status combo
    # Let's just pick the first 50 verbs and distribute them
    test_verbs = all_verbs_list[100:150] # Skip common words like 'the', 'be'
    
    now = datetime.now()
    
    print(f"Injecting {len(test_verbs)} test verbs into {DB_PATH}...")

    for i, verb_entry in enumerate(test_verbs):
        verb = verb_entry['单词'].lower()
        
        # Cycle through stages and statuses
        stage = i % 8
        
        # Logic for status and next_review
        if i % 10 == 9: # Every 10th verb is mastered
            status = 'mastered'
            stage = 7
            next_review = (now + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            status = 'learning'
            # Set some to be due for review (past) and some in the future
            if i % 2 == 0:
                next_review = (now - timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S')
            else:
                next_review = (now + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S')

        last_review = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        review_count = random.randint(1, 10)

        c.execute('''
            INSERT OR REPLACE INTO learning_progress 
            (verb, stage, last_review, next_review, review_count, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (verb, stage, last_review, next_review, review_count, status))

    conn.commit()
    conn.close()
    print("Injection complete. Please refresh the application.")

if __name__ == "__main__":
    inject_test_data()
