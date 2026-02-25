import os
import sys
from dotenv import load_dotenv

# Try root .env first
if os.path.exists(".env"):
    load_dotenv(".env")
else:
    # Fallback to subdirectory
    env_path = os.path.join("scripts", "explain_verbs", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

key = os.getenv("OPENAI_API_KEY")
print(f"Key exists: {bool(key)}, length: {len(key) if key else 0}")
