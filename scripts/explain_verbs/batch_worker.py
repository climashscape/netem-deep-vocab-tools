import os
import sys
import json
import sqlite3
import time
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

# Ensure we can import modules from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from explain_verbs import get_client, explain_verb
    from markdown_utils import clean_markdown
    from settings import settings, load_settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))
    from scripts.explain_verbs.explain_verbs import get_client, explain_verb
    from scripts.explain_verbs.markdown_utils import clean_markdown
    from scripts.explain_verbs.settings import settings, load_settings

# Constants (mirrored from app.py)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")
VERBS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../netem_full_list.json"))

KNOWN_FUNCTION_WORDS = {
    "about", "above", "across", "after", "against", "along", "amid", "among", "around", "as", "at", 
    "before", "behind", "below", "beneath", "beside", "between", "beyond", "by", 
    "concerning", "considering", "despite", "down", "during", "except", "for", "from", 
    "in", "inside", "into", "like", "near", "of", "off", "on", "onto", "out", "outside", "over", 
    "past", "regarding", "round", "since", "through", "throughout", "till", "to", "toward", 
    "under", "underneath", "until", "up", "upon", "versus", "via", "with", "within", "without",
    "and", "but", "or", "so", "yet", "nor", "although", "because", "if", "unless", "while", "whereas", "whether"
}

KNOWN_PRONOUNS = {
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "mine", "yours", "his", "hers", "its", "ours", "theirs", "my", "your", "his", "her", "its", "our", "their",
    "myself", "yourself", "himself", "herself", "itself", "ourselves", "yourselves", "themselves",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what",
    "anyone", "anybody", "anything", "everyone", "everybody", "everything", 
    "someone", "somebody", "something", "noone", "nobody", "nothing", "none",
    "one", "ones", "all", "another", "any", "both", "each", "either", "few", 
    "many", "neither", "other", "others", "several", "some", "such"
}

KNOWN_ARTICLES = {"a", "an", "the"}

KNOWN_ADJ_ADV = {
    "more", "most", "less", "least", "much", "many", "better", "best", "worse", "worst",
    "few", "fewer", "fewest", "little", "some", "any", "enough", "several", "all",
    "either", "neither", "each", "every", "only", "just", "very", "really", "quite", "rather", "too", "so", "well",
    "often", "always", "never", "sometimes", "seldom", "rarely", "usually", "perhaps", "maybe", "probably", "possibly",
    "now", "then", "here", "there", "where", "when", "why", "how", "again", "once", "twice",
    "already", "yet", "still", "even", "else", "away", "back", "forward", "backward",
    "high", "low", "far", "near", "long", "short", "deep", "wide", "broad", "first", "last", "next", "previous", "prior",
    "good", "bad", "great", "new", "old", "young", "right", "wrong", "own", "same", "different", "able", "possible", "likely", "certain", "sure"
}

# Database and counter locks for thread safety
db_lock = threading.Lock()
counter_lock = threading.Lock()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def generate_image_url(verb: str):
    import urllib.parse
    import hashlib
    
    # Check current setting
    if settings.image_provider == "pollinations":
        prompt_text = f"minimalist vector illustration of action {verb} white background"
        encoded_prompt = urllib.parse.quote(prompt_text)
        # Use stable seed based on verb to allow browser caching
        seed = int(hashlib.md5(verb.encode('utf-8')).hexdigest(), 16) % 1000000
        
        if settings.pollinations_api_key:
             return f"https://gen.pollinations.ai/image/{encoded_prompt}?model={settings.pollinations_model}&nologo=true&seed={seed}"
        else:
             return f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={settings.pollinations_model}&nologo=true&seed={seed}"
    else:
        # Default to DiceBear
        return f"https://api.dicebear.com/9.x/icons/svg?seed={verb}"

def save_to_cache(mode: str, query_key: str, content: str, image_url: str = None):
    # Optimize markdown before saving
    optimized_content = clean_markdown(content)
    
    with db_lock:
        conn = get_db_connection()
        c = conn.cursor()
        try:
            # Fetch existing data to preserve fields
            c.execute("SELECT image_url, image_dicebear, image_pollinations FROM explanations WHERE mode=? AND query_key=?", (mode, query_key))
            existing = c.fetchone()
            
            current_image_url = image_url
            current_dicebear = None
            current_pollinations = None
            
            if existing:
                # Preserve existing if new is None
                if current_image_url is None:
                    current_image_url = existing[0]
                
                current_dicebear = existing[1]
                current_pollinations = existing[2]
                
            # Update specific columns based on new image_url
            if current_image_url:
                if "dicebear.com" in current_image_url:
                    current_dicebear = current_image_url
                elif "pollinations.ai" in current_image_url:
                    current_pollinations = current_image_url
            
            c.execute("""
                INSERT OR REPLACE INTO explanations (mode, query_key, content, image_url, image_dicebear, image_pollinations)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mode, query_key, optimized_content, current_image_url, current_dicebear, current_pollinations))
            conn.commit()
        except Exception as e:
            print(f"Error saving to cache: {e}")
        finally:
            conn.close()

def get_explained_verbs() -> set:
    with db_lock:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT query_key FROM explanations WHERE mode = 'single'")
        explained = {row[0] for row in c.fetchall()}
        conn.close()
    return explained

def process_single_verb(item: Dict[str, Any], client: Any, settings: Any, count_info: Dict[str, int]):
    verb = item['单词'].strip()
    verb_lower = verb.lower()
    
    # Determine POS
    pos = item.get('pos')
    if verb_lower in KNOWN_FUNCTION_WORDS:
        pos = "prep_conj"
    elif verb_lower in KNOWN_PRONOUNS or verb_lower in KNOWN_ARTICLES:
        pos = "other"
    elif verb_lower in KNOWN_ADJ_ADV:
        pos = "adj_adv"
    
    # Update progress display
    with counter_lock:
        count_info['started'] += 1
        idx = count_info['started']
    
    total = count_info['total']
    
    print(f"[{idx}/{total}] Processing: {verb} (POS: {pos})...")
    
    try:
        # Generate AI explanation
        prompt = f"请解析\"{verb}\""
        raw_res = explain_verb(client, prompt, model=settings.openai_model, pos=pos)
        
        if "Error calling API" in raw_res:
            print(f"[{idx}/{total}] FAILED: {verb} (AI error)")
            return False
        
        content = clean_markdown(raw_res)
        
        # Generate image URL
        image_url = generate_image_url(verb_lower)
        
        # Save to database
        save_to_cache("single", verb_lower, content, image_url)
        
        print(f"[{idx}/{total}] DONE: {verb}")
        return True
        
    except Exception as e:
        print(f"[{idx}/{total}] FAILED: {verb} (Unexpected error: {e})")
        return False

def process_all_verbs(max_workers: int = 5, force: bool = False, limit: int = 0):
    # 1. Load verbs
    if not os.path.exists(VERBS_JSON_PATH):
        print(f"Error: {VERBS_JSON_PATH} not found.")
        return

    with open(VERBS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    key = "5530考研词汇词频排序表 (Verbs Only)"
    if key not in data:
        key = list(data.keys())[0]
    
    verbs_list = data[key]
    total_verbs = len(verbs_list)
    print(f"Found {total_verbs} verbs in total.")

    # 2. Get explained verbs
    if force:
        print("Force mode enabled. Ignoring existing cache.")
        to_process = verbs_list
    else:
        explained_verbs = get_explained_verbs()
        print(f"{len(explained_verbs)} verbs already have explanations.")
        # 3. Filter verbs
        to_process = [item for item in verbs_list if item['单词'].strip().lower() not in explained_verbs]
    
    if limit > 0:
        to_process = to_process[:limit]
        print(f"Limiting to first {limit} verbs.")

    print(f"{len(to_process)} verbs need processing.")

    if not to_process:
        print("All verbs are already processed!")
        return

    # 4. Initialize AI client
    global settings
    settings = load_settings()
    client = get_client(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    if not client:
        print("Error: Could not initialize AI client. Check your settings.")
        return

    # 5. Process each verb using ThreadPoolExecutor
    print(f"Starting concurrent processing with {max_workers} workers...")
    
    count_info = {'started': 0, 'total': len(to_process), 'success': 0}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_verb, item, client, settings, count_info): item for item in to_process}
        
        for future in as_completed(futures):
            if future.result():
                count_info['success'] += 1

    end_time = time.time()
    duration = end_time - start_time
    print(f"\nBatch processing complete!")
    print(f"Processed {count_info['success']} verbs in {duration:.2f} seconds.")
    print(f"Average time per verb: {duration/max(1, count_info['success']):.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process verb explanations.")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing explanations")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of verbs to process")
    
    args = parser.parse_args()
    
    process_all_verbs(max_workers=args.workers, force=args.force, limit=args.limit)
