import sys
# Override sqlite3 with pysqlite3-binary on Linux (Streamlit Cloud) to bypass older SQLite versions (M3)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import warnings

# Suppress the FutureWarnings from deprecated google.generativeai package (M14)
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

# Skip GCE metadata server lookup to avoid connection timeouts in non-GCE environments
os.environ["NO_GCE_CHECK"] = "True"

from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load local environment variables if a .env exists
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"

# Create directories if they do not exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# API Keys and Models configurations
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
PREMIUM_GEMINI_MODEL = "gemini-1.5-pro"
EMBEDDING_MODEL = "models/text-embedding-004"

_api_active_cache = None

def get_api_key():
    """Retrieves the Gemini API key from environment variables."""
    return os.getenv("GEMINI_API_KEY")

def init_gemini(api_key=None):
    """
    Initializes the google.generativeai SDK and verifies if the key is valid.
    Priority:
    1. Provided parameter `api_key`
    2. Environment variable `GEMINI_API_KEY`
    """
    global _api_active_cache
    key = api_key or get_api_key()
    if not key:
        _api_active_cache = False
        return False
    
    try:
        genai.configure(api_key=key)
        # Force a network request to verify the key.
        next(iter(genai.list_models()))
        _api_active_cache = True
        return True
    except Exception:
        # Reset configuration on failure so invalid keys don't linger in memory
        genai.configure(api_key="")
        _api_active_cache = False
        return False

def is_gemini_api_active():
    """Checks if a verified Gemini API key is configured and active."""
    global _api_active_cache
    if _api_active_cache is not None:
        return _api_active_cache
        
    if not get_api_key():
        _api_active_cache = False
        return False
        
    try:
        next(iter(genai.list_models()))
        _api_active_cache = True
        return True
    except Exception:
        _api_active_cache = False
        return False
