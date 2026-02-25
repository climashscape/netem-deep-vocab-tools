from fastapi import FastAPI, Request, HTTPException, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
import shutil
import zipfile
import tempfile
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import sqlite3
import requests
import httpx # For async requests
import logging
from datetime import datetime, timedelta

# Filter for /api/image/ access logs
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/api/image/") == -1

# List of common English prepositions and conjunctions for auto-detection
KNOWN_FUNCTION_WORDS = {
    # Prepositions
    "about", "above", "across", "after", "against", "along", "amid", "among", "around", "as", "at", 
    "before", "behind", "below", "beneath", "beside", "between", "beyond", "by", 
    "concerning", "considering", "despite", "down", "during", "except", "for", "from", 
    "in", "inside", "into", "like", "near", "of", "off", "on", "onto", "out", "outside", "over", 
    "past", "regarding", "round", "since", "through", "throughout", "till", "to", "toward", 
    "under", "underneath", "until", "up", "upon", "versus", "via", "with", "within", "without",
    # Conjunctions
    "and", "but", "or", "so", "yet", "nor", "although", "because", "if", "unless", "while", "whereas", "whether"
}

# List of common English pronouns for auto-detection
KNOWN_PRONOUNS = {
    # Personal Pronouns (Subject)
    "i", "you", "he", "she", "it", "we", "they",
    # Personal Pronouns (Object)
    "me", "him", "her", "us", "them",
    # Possessive Pronouns
    "mine", "yours", "his", "hers", "its", "ours", "theirs",
    # Possessive Adjectives (often treated as pronouns in broad sense)
    "my", "your", "his", "her", "its", "our", "their",
    # Reflexive Pronouns
    "myself", "yourself", "himself", "herself", "itself", "ourselves", "yourselves", "themselves",
    # Demonstrative Pronouns
    "this", "that", "these", "those",
    # Relative/Interrogative Pronouns
    "who", "whom", "whose", "which", "what",
    # Indefinite Pronouns
    "anyone", "anybody", "anything", "everyone", "everybody", "everything", 
    "someone", "somebody", "something", "noone", "nobody", "nothing", "none",
    "one", "ones", "all", "another", "any", "both", "each", "either", "few", 
    "many", "neither", "other", "others", "several", "some", "such"
}

# List of articles
KNOWN_ARTICLES = {"a", "an", "the"}

# List of common adjectives/adverbs that might be misclassified as nouns/verbs
KNOWN_ADJ_ADV = {
    # Comparatives/Superlatives/Quantifiers
    "more", "most", "less", "least", "much", "many", 
    "better", "best", "worse", "worst",
    "few", "fewer", "fewest", "little", "some", "any", "enough", "several", "all",
    "either", "neither", "each", "every",
    # Common Adverbs/Adjectives often mislabeled
    "only", "just", "very", "really", "quite", "rather", "too", "so", "well",
    "often", "always", "never", "sometimes", "seldom", "rarely", "usually",
    "perhaps", "maybe", "probably", "possibly",
    "now", "then", "here", "there", "where", "when", "why", "how", # Interrogatives/Adverbs
    "again", "once", "twice",
    "already", "yet", "still", "even", "else",
    "away", "back", "forward", "backward",
    "high", "low", "far", "near", "long", "short", "deep", "wide", "broad",
    "first", "last", "next", "previous", "prior",
    "good", "bad", "great", "new", "old", "young", "right", "wrong",
    "own", "same", "different", "able", "possible", "likely", "certain", "sure"
}

# Ensure we can import the explain_verbs logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from explain_verbs import get_client, explain_verb
    from markdown_utils import clean_markdown
    from settings import settings, AppSettings, CONFIG_FILE
except ImportError:
    # If running from root
    from scripts.explain_verbs.explain_verbs import get_client, explain_verb
    from scripts.explain_verbs.markdown_utils import clean_markdown
    from scripts.explain_verbs.settings import settings, AppSettings

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, verbs_data
    
    # Filter out /api/image/ logs to reduce noise
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    
    http_client = httpx.AsyncClient(timeout=5.0)
    
    # Pre-load verbs data to memory
    if os.path.exists(VERBS_JSON_PATH):
        try:
            with open(VERBS_JSON_PATH, "r", encoding="utf-8") as f:
                verbs_data = json.load(f)
            print("Verbs data pre-loaded into memory.")
        except Exception as e:
            print(f"Error loading verbs.json: {e}")
            
    yield
    
    if http_client:
        await http_client.aclose()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Silence Vite HMR client 404s from Trae/VSCode injection
@app.get("/@vite/client", include_in_schema=False)
async def vite_client_silencer():
    return Response(content="console.log('Vite client silencer')", media_type="application/javascript")

verbs_data = None
http_client = None

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error for {request.method} {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
@app.get("/api/settings")
def get_settings():
    from settings import load_settings
    global settings
    settings = load_settings()
    return settings.model_dump()

@app.post("/api/settings")
def update_settings(new_settings: AppSettings):
    global settings
    # Update current settings
    settings = new_settings
    # Save to file
    settings.save()
    return {"status": "success", "settings": settings.model_dump()}

import json

# Database Setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")
VERBS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../netem_full_list.json"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # Ensure MEMORY journal mode on EVERY connection to prevent Recycle Bin spam
    conn.execute("PRAGMA journal_mode=MEMORY;")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Use MEMORY mode to avoid creating/deleting journal files on disk
    # This completely stops the Recycle Bin spam issue as the journal lives in RAM.
    mode = c.execute("PRAGMA journal_mode;").fetchone()[0]
    print(f"Database journal mode set to: {mode}")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL,
            query_key TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(mode, query_key)
        )
    ''')
    
    # Ebbinghaus Learning Progress Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            verb TEXT PRIMARY KEY,
            stage INTEGER DEFAULT 0,
            last_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new'
        )
    ''')
    
    # Check-ins table
    c.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            date TEXT PRIMARY KEY
        )
    ''')
    
    # Current learning batch table
    c.execute('''
        CREATE TABLE IF NOT EXISTS learn_batch (
            verb TEXT PRIMARY KEY
        )
    ''')
    
    # Add new columns for dual storage
    try:
        c.execute("ALTER TABLE explanations ADD COLUMN image_dicebear TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE explanations ADD COLUMN image_pollinations TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Migrate existing data (if not already migrated)
    # This ensures existing URLs are preserved in specific columns
    try:
        # Check if any row needs migration (DiceBear URL but null column, or Pollinations URL but null column)
        c.execute("SELECT 1 FROM explanations WHERE (image_url LIKE '%dicebear%' AND image_dicebear IS NULL) OR (image_url LIKE '%pollinations%' AND image_pollinations IS NULL) LIMIT 1")
        needs_migration = c.fetchone()
        
        if needs_migration:
            print("Starting DB migration...")
            c.execute("SELECT id, image_url FROM explanations WHERE image_url IS NOT NULL")
            rows = c.fetchall()
            for row in rows:
                row_id, url = row
                if url and "dicebear.com" in url:
                    c.execute("UPDATE explanations SET image_dicebear=? WHERE id=? AND (image_dicebear IS NULL OR image_dicebear='')", (url, row_id))
                elif url and "pollinations.ai" in url:
                     c.execute("UPDATE explanations SET image_pollinations=? WHERE id=? AND (image_pollinations IS NULL OR image_pollinations='')", (url, row_id))
            conn.commit()
            print("Migration completed.")
    except Exception as e:
        print(f"Migration error: {e}")
             
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

import random
import requests
import urllib.parse
from fastapi import Response

def get_cached_result(mode: str, query_key: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Fetch all image columns
        c.execute("SELECT content, image_url, image_dicebear, image_pollinations FROM explanations WHERE mode=? AND query_key=?", (mode, query_key))
        result = c.fetchone()
    except sqlite3.OperationalError:
        # Fallback
        c.execute("SELECT content, image_url FROM explanations WHERE mode=? AND query_key=?", (mode, query_key))
        row = c.fetchone()
        result = (row[0], row[1], None, None) if row else None
        
    conn.close()
    
    if result:
        content = result[0]
        legacy_url = result[1]
        img_dicebear = result[2]
        img_pollinations = result[3]
        
        # Select image based on settings
        target_img = None
        if settings.image_provider == "pollinations":
            target_img = img_pollinations
        else:
            target_img = img_dicebear
            
        # Fallback to legacy if specific column empty, but check provider match
        if not target_img and legacy_url:
            if settings.image_provider == "pollinations" and "pollinations.ai" in legacy_url:
                target_img = legacy_url
            elif settings.image_provider == "dicebear" and "dicebear.com" in legacy_url:
                target_img = legacy_url
        
        return {
            "content": content, 
            "image_url": target_img
        }
    return None

def save_to_cache(mode: str, query_key: str, content: str, image_url: str = None):
    # Optimize markdown before saving
    optimized_content = clean_markdown(content)
    
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
            INSERT OR REPLACE INTO explanations 
            (mode, query_key, content, image_url, image_dicebear, image_pollinations) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mode, query_key, optimized_content, current_image_url, current_dicebear, current_pollinations))
        
        conn.commit()
    except Exception as e:
        print(f"Error saving to cache: {e}")
    finally:
        conn.close()

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

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

class VerbRequest(BaseModel):
    verbs: str
    mode: str
    refresh: bool = False
    skip_content: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request},
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    )

# Ebbinghaus Intervals (in minutes)
EBBINGHAUS_STAGES = [
    5,      # Stage 1: 5 minutes
    30,     # Stage 2: 30 minutes
    720,    # Stage 3: 12 hours
    1440,   # Stage 4: 1 day
    2880,   # Stage 5: 2 days
    5760,   # Stage 6: 4 days
    10080,  # Stage 7: 7 days
    21600,  # Stage 8: 15 days
    43200   # Stage 9: 30 days
]

class ReviewResult(BaseModel):
    verb: str
    result: str # 'remembered' or 'forgotten'

@app.post("/api/ebbinghaus/record")
async def record_review(data: ReviewResult):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Get current progress
        c.execute("SELECT stage, review_count FROM learning_progress WHERE verb = ?", (data.verb,))
        row = c.fetchone()
        
        now = datetime.now()
        
        if not row:
            # First time learning
            stage = 0
            review_count = 0
        else:
            stage, review_count = row
            
        if data.result == 'remembered':
            # Advance to next stage
            new_stage = min(stage + 1, len(EBBINGHAUS_STAGES))
        else:
            # Reset to stage 0 if forgotten (any other result like 'forgotten')
            new_stage = 0
            
        # Calculate next review time
        if new_stage == 0:
            next_review = now + timedelta(minutes=EBBINGHAUS_STAGES[0])
        elif new_stage <= len(EBBINGHAUS_STAGES):
            next_review = now + timedelta(minutes=EBBINGHAUS_STAGES[new_stage-1])
        else:
            # Mastered (Stage 9) - Set to a far future or just stop reviewing
            next_review = now + timedelta(days=30)
            
        status = 'learning' if new_stage < len(EBBINGHAUS_STAGES) else 'mastered'
        
        c.execute("""
            INSERT OR REPLACE INTO learning_progress 
            (verb, stage, last_review, next_review, review_count, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.verb, new_stage, now.isoformat(), next_review.isoformat(), review_count + 1, status))
        
        conn.commit()
        return {"status": "success", "new_stage": new_stage, "next_review": next_review.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/mastery")
async def mark_mastered(data: ReviewResult):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = datetime.now()
        # Stage 9 is mastered (length of EBBINGHAUS_STAGES)
        stage = len(EBBINGHAUS_STAGES)
        next_review = now + timedelta(days=365) # 1 year later
        status = 'mastered'
        
        c.execute("""
            INSERT OR REPLACE INTO learning_progress 
            (verb, stage, last_review, next_review, review_count, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.verb, stage, now.isoformat(), next_review.isoformat(), 1, status))
        
        conn.commit()
        return {"status": "success", "new_stage": stage}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/ebbinghaus/due")
async def get_due_verbs():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = datetime.now().isoformat()
        # Find verbs where next_review <= now
        c.execute("SELECT verb, stage, next_review, status FROM learning_progress WHERE next_review <= ? AND status != 'mastered'", (now,))
        rows = c.fetchall()
        
        return [
            {
                "verb": row[0],
                "stage": row[1],
                "next_review": row[2],
                "status": row[3]
            }
            for row in rows
        ]
    finally:
        conn.close()

@app.get("/api/stats/daily_goal")
async def get_daily_goal_stats():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # 1. Count new words learned today (first time entry into DB today)
        # Note: We assume first entry means stage was 0 or row didn't exist, 
        # but simplified: any word with last_review >= today_start AND review_count = 1
        c.execute("SELECT count(*) FROM learning_progress WHERE last_review >= ? AND review_count = 1", (today_start,))
        new_words_today = c.fetchone()[0]
        
        # 2. Count remaining due reviews
        c.execute("SELECT count(*) FROM learning_progress WHERE next_review <= ? AND status = 'learning'", (now.isoformat(),))
        due_words_remaining = c.fetchone()[0]
        
        return {
            "new_words_today": new_words_today,
            "due_words_remaining": due_words_remaining
        }
    finally:
        conn.close()

@app.get("/api/ebbinghaus/status")
async def get_all_status():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT verb, stage, last_review, next_review, review_count, status FROM learning_progress")
        rows = c.fetchall()
        
        status_map = {}
        for row in rows:
            status_map[row[0]] = {
                "stage": row[1],
                "last_review": row[2],
                "next_review": row[3],
                "review_count": row[4],
                "status": row[5]
            }
        return status_map
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/export")
async def export_data(excluded_verbs: str = ""):
    try:
        # Create a temporary ZIP file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"netem_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add database if exists
            if os.path.exists(DB_PATH):
                # Ensure DB is not locked by connecting/closing or using a copy
                db_copy = os.path.join(temp_dir, "verbs.db")
                shutil.copy2(DB_PATH, db_copy)
                zipf.write(db_copy, "verbs.db")
            
            # Add config if exists
            if os.path.exists(CONFIG_FILE):
                zipf.write(CONFIG_FILE, "config.json")
            
            # Add excluded verbs if provided
            if excluded_verbs:
                excluded_path = os.path.join(temp_dir, "excluded.json")
                with open(excluded_path, 'w', encoding='utf-8') as f:
                    f.write(excluded_verbs)
                zipf.write(excluded_path, "excluded.json")
                
        return FileResponse(
            zip_path, 
            media_type="application/zip", 
            filename=os.path.basename(zip_path),
            background=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    try:
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, file.filename)
        
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result_data = {"status": "success", "message": "Data and configuration restored successfully"}
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Extract to temp dir first to validate
            zipf.extractall(temp_dir)
            
            # Restore database
            if "verbs.db" in zipf.namelist():
                shutil.copy2(os.path.join(temp_dir, "verbs.db"), DB_PATH)
                
            # Restore config
            if "config.json" in zipf.namelist():
                shutil.copy2(os.path.join(temp_dir, "config.json"), CONFIG_FILE)
                # Reload settings in memory
                global settings
                from settings import load_settings
                settings = load_settings()
            
            # Restore excluded verbs
            if "excluded.json" in zipf.namelist():
                with open(os.path.join(temp_dir, "excluded.json"), 'r', encoding='utf-8') as f:
                    result_data["excluded_verbs"] = f.read()
                
        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/api/ebbinghaus/clear_all")
async def clear_all_learning_progress(reset_settings: bool = False):
    try:
        # 1. Clear learning progress, synced data and AI explanations
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM learning_progress")
        c.execute("DELETE FROM checkins")
        c.execute("DELETE FROM learn_batch")
        c.execute("DELETE FROM explanations")
        conn.commit()
        conn.close()

        # 2. Optionally reset settings
        if reset_settings:
            global settings
            # 1. Clear config file
            if os.path.exists(CONFIG_FILE):
                try:
                    os.remove(CONFIG_FILE)
                    print(f"Successfully deleted {CONFIG_FILE}")
                except Exception as e:
                    print(f"Failed to remove config file: {e}")
            
            # 2. Clear .env file if exists (check both local and root)
            # NOTE: We NO LONGER delete .env files during reset to protect user's API keys
            # We only clear the keys from memory so they can be re-loaded or changed
            for key in ["OPENAI_API_KEY", "OPENAI_BASE_URL", "DEFAULT_MODEL", "IMAGE_PROVIDER", "POLLINATIONS_API_KEY", "POLLINATIONS_MODEL"]:
                if key in os.environ:
                    del os.environ[key]
            
            # 3. Reset in-memory settings to true defaults
            # We create a new instance which will have pydantic defaults
            settings = AppSettings(
                openai_api_key="",
                openai_base_url="",
                openai_model="",
                image_provider="dicebear",
                pollinations_api_key="",
                pollinations_model="flux"
            )
            # Explicitly save the clean state to disk (this will create an empty config.json)
            settings.save()
            print("Settings memory reset and saved to disk")
            
        return {"status": "success", "message": "Clearance completed"}
    except Exception as e:
        print(f"Error in clear_all: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/checkins")
async def get_checkins():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT date FROM checkins")
        dates = [row[0] for row in c.fetchall()]
        conn.close()
        return dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/checkins")
async def add_checkin(data: dict):
    date = data.get("date")
    if not date:
        raise HTTPException(status_code=400, detail="Date is required")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO checkins (date) VALUES (?)", (date,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/checkins/{date}")
async def delete_checkin(date: str):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM checkins WHERE date = ?", (date,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learn_batch")
async def get_learn_batch():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT verb FROM learn_batch")
        verbs = [row[0] for row in c.fetchall()]
        conn.close()
        return verbs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learn_batch")
async def update_learn_batch(data: List[str]):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM learn_batch")
        for verb in data:
            c.execute("INSERT INTO learn_batch (verb) VALUES (?)", (verb,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/learn_batch")
async def clear_learn_batch():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM learn_batch")
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/verbs")
def get_verbs(limit: int = 50, offset: int = 0):
    global verbs_data
    try:
        # Use cached verbs data if available, otherwise load it
        data = verbs_data
        if not data:
            if not os.path.exists(VERBS_JSON_PATH):
                return {"total": 0, "items": [], "error": "Verbs file not found"}
            with open(VERBS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                verbs_data = data # Cache it
        
        # The key might be slightly different depending on file generation
        key = "5530考研词汇词频排序表 (Verbs Only)"
        if key not in data:
            # Fallback: check first key
            key = list(data.keys())[0]
        
        verbs_list = data[key]
        total = len(verbs_list)
        paginated = verbs_list[offset : offset + limit]
        
        # Enrich with cache status and override POS for prepositions
        conn = get_db_connection()
        c = conn.cursor()
        
        # Extract verbs to check
        verb_keys = [v['单词'].strip().lower() for v in paginated if '单词' in v]
        cached_info = {}
        
        if verb_keys:
            # Optimization: If checking many verbs, fetch all cached keys instead of massive IN clause
            if len(verb_keys) > 200:
                try:
                    c.execute("SELECT query_key, image_url FROM explanations WHERE mode='single'")
                    rows = c.fetchall()
                    # Create lookup map
                    full_cache = {row[0]: row[1] for row in rows}
                    
                    for k in verb_keys:
                        if k in full_cache:
                            cached_info[k] = {"has_cache": True, "image_url": full_cache[k]}
                except Exception as e:
                    print(f"Error checking cache (full fetch): {e}")
            else:
                # Use standard IN clause for small batches
                placeholders = ','.join(['?'] * len(verb_keys))
                try:
                    query = f"SELECT query_key, image_url FROM explanations WHERE mode='single' AND query_key IN ({placeholders})"
                    c.execute(query, verb_keys)
                    for row in c.fetchall():
                        cached_info[row[0]] = {"has_cache": True, "image_url": row[1]}
                except Exception as e:
                    print(f"Error checking cache (batch): {e}")
        
        conn.close()
        
        for item in paginated:
            if '单词' in item:
                key = item['单词'].strip().lower()
                
                # Override POS for prepositions/conjunctions
                if key in KNOWN_FUNCTION_WORDS:
                    item['pos'] = 'prep_conj'
                # Override POS for pronouns -> other
                elif key in KNOWN_ARTICLES or key in KNOWN_PRONOUNS:
                    item['pos'] = 'other'
                # Override POS for common adj/adv -> adj_adv
                elif key in KNOWN_ADJ_ADV:
                    item['pos'] = 'adj_adv'
                    
                info = cached_info.get(key, {"has_cache": False, "image_url": None})
                item['has_cache'] = info["has_cache"]
                # Use cached image or generate one on the fly (stable seed)
                item['image_url'] = info["image_url"] if info["image_url"] else generate_image_url(key)
            else:
                item['has_cache'] = False
                item['image_url'] = None
        
        return JSONResponse(content={
            "total": total,
            "items": paginated,
            "limit": limit,
            "offset": offset
        }, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/check_cache")
async def check_cache(request: Dict[str, List[str]]):
    verbs = request.get("verbs", [])
    if not verbs:
        return []
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        placeholders = ','.join(['?'] * len(verbs))
        # Only return verbs that have an entry in the explanations table
        c.execute(f"SELECT query_key FROM explanations WHERE mode='single' AND query_key IN ({placeholders})", verbs)
        cached_verbs = [row[0] for row in c.fetchall()]
        return cached_verbs
    finally:
        conn.close()

def get_verb_info(word: str):
    global verbs_data
    if not verbs_data:
        return None
    
    word_lower = word.strip().lower()
    for key, items in verbs_data.items():
        for item in items:
            if item.get("单词", "").strip().lower() == word_lower:
                return item
    return None

@app.post("/api/explain")
def explain_verbs_endpoint(request: VerbRequest):
    try:
        # Get client but don't fail immediately if we have cached results
        client = get_client(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        
        verbs_input = request.verbs
        mode = request.mode
        refresh = request.refresh
        
        if "," in verbs_input:
            verbs = [v.strip() for v in verbs_input.split(",")]
        else:
            verbs = verbs_input.split()
            
        if not verbs:
            return JSONResponse(content={"result": "Please enter at least one verb."}, status_code=400)

        result_text = ""
        
        if mode == "single":
            results = []
            images = {}
            for verb in verbs:
                # Normalize key
                key = verb.strip().lower()
                cached_data = get_cached_result("single", key)
                cached_content = cached_data["content"] if cached_data else None
                cached_image = cached_data.get("image_url") if cached_data else None
                
                # Determine if we need to regenerate content or image
                need_content = refresh or not cached_content
                need_image = refresh or not cached_image
                
                new_content = cached_content
                new_image = cached_image
                
                # Generate Image if needed
                if need_image:
                    new_image = generate_image_url(verb)
                
                # Generate Content if needed
                if need_content:
                    if not client:
                         if cached_content:
                              new_content = cached_content
                         else:
                              return JSONResponse(content={"error": "API Key not configured and no cache found."}, status_code=500)
                    else:
                        prompt = f"请解析\"{verb}\""
                        # Look up POS
                        verb_info = get_verb_info(verb)
                        pos = verb_info.get("pos") if verb_info else None
                        
                        # Override pos for known prepositions/conjunctions
                        if verb.strip().lower() in KNOWN_FUNCTION_WORDS:
                            pos = "prep_conj" # Use new prompt logic in explain_verbs.py
                        elif verb.strip().lower() in KNOWN_PRONOUNS or verb.strip().lower() in KNOWN_ARTICLES:
                            pos = "other"
                        elif verb.strip().lower() in KNOWN_ADJ_ADV:
                            pos = "adj_adv"
                        
                        raw_res = explain_verb(client, prompt, model=settings.openai_model, pos=pos)
                        if "Error calling API" in raw_res:
                             if cached_content:
                                  new_content = cached_content
                             else:
                                  return JSONResponse(content={"error": raw_res}, status_code=500)
                        else:
                             new_content = clean_markdown(raw_res)
                
                # Save if anything changed
                if need_content or need_image:
                    save_to_cache("single", key, new_content, new_image)
                
                results.append(new_content)
                if new_image:
                    images[verb] = new_image
                
            result_text = "\n\n---\n\n".join(results)
            return JSONResponse(content={"result": result_text, "images": images})


        elif mode == "list":
             # Normalize key: sorted list of lowercase verbs
             key = ",".join(sorted([v.strip().lower() for v in verbs]))
             cached_data = get_cached_result("list", key)
             cached_content = cached_data["content"] if cached_data else None
             
             if cached_content and not refresh:
                 result_text = cached_content
             else:
                 if not client:
                     if cached_content:
                          result_text = cached_content
                     else:
                          return JSONResponse(content={"error": "API Key not configured and no cache found."}, status_code=500)
                 else:
                      prompt = f"请解析这组动词：[{', '.join(verbs)}]"
                      raw_res = explain_verb(client, prompt, model=settings.openai_model)
                      if "Error calling API" in raw_res:
                           if cached_content:
                                result_text = cached_content
                           else:
                                return JSONResponse(content={"error": raw_res}, status_code=500)
                      else:
                           result_text = clean_markdown(raw_res)
                           save_to_cache("list", key, result_text)

        elif mode == "compare":
             # Normalize key: sorted list of lowercase verbs
             key = ",".join(sorted([v.strip().lower() for v in verbs]))
             cached_data = get_cached_result("compare", key)
             cached_content = cached_data["content"] if cached_data else None
             
             if cached_content and not refresh:
                 result_text = cached_content
             else:
                 if not client:
                     if cached_content:
                          result_text = cached_content
                     else:
                          return JSONResponse(content={"error": "API Key not configured and no cache found."}, status_code=500)
                 else:
                      prompt = f"请对比以下动词：{', '.join(verbs)}"
                      raw_res = explain_verb(client, prompt, model=settings.openai_model)
                      if "Error calling API" in raw_res:
                           if cached_content:
                                result_text = cached_content
                           else:
                                return JSONResponse(content={"error": raw_res}, status_code=500)
                      else:
                           result_text = clean_markdown(raw_res)
                           save_to_cache("compare", key, result_text)
        
        else:
            return JSONResponse(content={"error": "Invalid mode selected."}, status_code=400)
            
        return JSONResponse(content={"result": result_text})

            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"result": f"Server Error: {str(e)}"}, status_code=500)

@app.get("/api/image/{verb}")
async def get_verb_image(verb: str):
    import asyncio
    try:
        # Normalize key
        key = verb.strip().lower()
        loop = asyncio.get_event_loop()
        
        # 1. DB Read (in thread pool)
        def read_db(k):
            conn = get_db_connection()
            c = conn.cursor()
            try:
                c.execute("SELECT image_url, image_dicebear, image_pollinations FROM explanations WHERE mode=? AND query_key=?", ("single", k))
                row = c.fetchone()
            except:
                # Fallback for old schema
                c.execute("SELECT image_url FROM explanations WHERE mode=? AND query_key=?", ("single", k))
                r = c.fetchone()
                row = (r[0], None, None) if r else None
            conn.close()
            return row

        row = await loop.run_in_executor(None, read_db, key)

        image_url = None
        if row:
             legacy = row[0]
             dicebear = row[1]
             pollinations = row[2]
             
             if settings.image_provider == "pollinations":
                 image_url = pollinations
             else:
                 image_url = dicebear
                 
             if not image_url and legacy:
                 # Check legacy match
                 if settings.image_provider == "pollinations" and "pollinations.ai" in legacy:
                     image_url = legacy
                 elif settings.image_provider == "dicebear" and "dicebear.com" in legacy:
                     image_url = legacy
        
        # If no image found, generate new one
        if not image_url:
            image_url = generate_image_url(verb)
            
            # 2. DB Write (in thread pool)
            def write_db(k, url, provider):
                col = "image_pollinations" if provider == "pollinations" else "image_dicebear"
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    query = f"UPDATE explanations SET {col}=?, image_url=? WHERE mode=? AND query_key=?"
                    c.execute(query, (url, url, "single", k))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    pass
                    # print(f"Error updating DB: {e}")
            
            await loop.run_in_executor(None, write_db, key, image_url, settings.image_provider)
            
        # Optimization: Redirect immediately for DiceBear (fast, reliable, public)
        if "dicebear.com" in image_url:
            return RedirectResponse(image_url)
            
        # For Pollinations, we use proxy to handle flakiness and fallbacks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        if "gen.pollinations.ai" in image_url and settings.pollinations_api_key:
             headers["Authorization"] = f"Bearer {settings.pollinations_api_key}"
             
        try:
             # Use shared client for efficiency
             if http_client:
                 resp = await http_client.get(image_url, headers=headers)
             else:
                 async with httpx.AsyncClient(timeout=5.0) as client:
                     resp = await client.get(image_url, headers=headers)
        except Exception as e:
             # print(f"Fetch error for {verb}: {e}")
             resp = None
            
        # Validation: must be 200 OK and NOT HTML
        if not resp or resp.status_code != 200 or "text/html" in resp.headers.get("Content-Type", ""):
            # print(f"Primary image source failed for {verb}. Switching to fallback.")
            # Fallback to DiceBear via Redirect
            fallback_url = f"https://api.dicebear.com/9.x/icons/svg?seed={verb}"
            
            # Try to update DB with fallback URL asynchronously
            def fallback_db_update(k, url):
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE explanations SET image_dicebear=?, image_url=? WHERE mode=? AND query_key=?", (url, url, "single", k))
                    conn.commit()
                    conn.close()
                except:
                    pass
            
            # Fire and forget update (or await if critical)
            # We await to avoid race conditions
            await loop.run_in_executor(None, fallback_db_update, key, fallback_url)
                
            return RedirectResponse(fallback_url)
        
        return Response(content=resp.content, media_type=resp.headers.get("Content-Type", "image/svg+xml"))
             
    except Exception as e:
        # print(f"Error in get_verb_image: {e}")
        # Final fallback
        return RedirectResponse(f"https://api.dicebear.com/9.x/icons/svg?seed={verb}")

if __name__ == "__main__":
    import uvicorn
    # Using 0.0.0.0 and port 8080 to avoid common localhost/8000 conflicts
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
