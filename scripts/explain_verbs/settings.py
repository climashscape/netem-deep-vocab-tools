import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv

# Search for .env in current and parent directories
def find_and_load_dotenv():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # List of possible keys to clear before reloading
    keys_to_clear = [
        "OPENAI_API_KEY", "OPENAI_BASE_URL", "DEFAULT_MODEL", 
        "IMAGE_PROVIDER", "POLLINATIONS_API_KEY", "POLLINATIONS_MODEL"
    ]
    
    # Try local .env
    local_env = os.path.join(current_dir, ".env")
    local_exists = os.path.exists(local_env)
    
    # Try project root .env (up two levels)
    root_env = os.path.join(current_dir, "..", "..", ".env")
    root_exists = os.path.exists(root_env)

    # If NO .env file exists, we MUST clear the environment variables 
    # because load_dotenv doesn't unset variables when the file is missing
    if not local_exists and not root_exists:
        for key in keys_to_clear:
            if key in os.environ:
                del os.environ[key]
        return

    if local_exists:
        # Use override=True to ensure hot-reload picks up changes
        load_dotenv(local_env, override=True)
    
    if root_exists:
        # Use override=True to ensure hot-reload picks up changes
        load_dotenv(root_env, override=True)

# Load env first (for defaults)
find_and_load_dotenv()

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

class AppSettings(BaseModel):
    # LLM Settings
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o"
    
    # Image Settings
    image_provider: str = "dicebear" # "dicebear" or "pollinations"
    pollinations_api_key: str = "" # Optional
    pollinations_model: str = "flux" # "flux", "turbo", etc.
    
    def __init__(self, **data):
        # If values aren't provided in data, try to get from environment
        if 'openai_api_key' not in data:
            data['openai_api_key'] = os.environ.get("OPENAI_API_KEY", "")
        if 'openai_base_url' not in data:
            data['openai_base_url'] = os.environ.get("OPENAI_BASE_URL", "")
        if 'openai_model' not in data:
            data['openai_model'] = os.environ.get("DEFAULT_MODEL", "gpt-4o")
        if 'image_provider' not in data:
            data['image_provider'] = os.environ.get("IMAGE_PROVIDER", "dicebear")
        if 'pollinations_api_key' not in data:
            data['pollinations_api_key'] = os.environ.get("POLLINATIONS_API_KEY", "")
        if 'pollinations_model' not in data:
            data['pollinations_model'] = os.environ.get("POLLINATIONS_MODEL", "flux")
        
        super().__init__(**data)

    def save(self):
        # We don't save API keys to config.json if they are in env
        # but for simplicity, we save current state
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

def load_settings() -> AppSettings:
    # 0. Force reload .env from disk to pick up latest changes
    find_and_load_dotenv()
    
    # 1. Load defaults from Environment Variables
    settings_obj = AppSettings()
    
    # 2. Layer config.json on top if it exists
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Only update if the config value is not empty and NOT the default
                # This ensures env vars (which are in settings_obj) aren't overwritten by empty strings in config.json
                for k, v in data.items():
                    if hasattr(settings_obj, k) and v:
                        # If the current value (from env) is empty, or the new value is different from default, use config value
                        setattr(settings_obj, k, v)
                return settings_obj
        except Exception as e:
            print(f"Error loading config.json: {e}")
            return settings_obj
    return settings_obj

# Global instance
settings = load_settings()
