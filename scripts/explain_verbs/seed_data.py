import sqlite3
import os
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), "verbs.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

now = datetime.now()

test_cases = [
    # Due now (Next review was 1 hour ago)
    ('abandon', 1, (now - timedelta(hours=2)).isoformat(), (now - timedelta(hours=1)).isoformat(), 1, 'learning'),
    # Waiting (Next review in 2 hours)
    ('ability', 4, (now - timedelta(days=1)).isoformat(), (now + timedelta(hours=2)).isoformat(), 4, 'learning'),
    # Mastered
    ('abroad', 9, (now - timedelta(days=15)).isoformat(), (now + timedelta(days=15)).isoformat(), 9, 'mastered'),
    # Waiting (Next review in 5 minutes)
    ('academic', 0, (now - timedelta(minutes=10)).isoformat(), (now + timedelta(minutes=5)).isoformat(), 1, 'learning'),
]

for verb, stage, last, next_t, count, status in test_cases:
    c.execute("""
        INSERT OR REPLACE INTO learning_progress 
        (verb, stage, last_review, next_review, review_count, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (verb, stage, last, next_t, count, status))

conn.commit()
conn.close()
print("Test data seeded successfully!")
