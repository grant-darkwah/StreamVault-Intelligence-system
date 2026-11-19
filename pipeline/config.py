
import os
from pathlib import Path

from dotenv import load_dotenv

# Locate the root directory of the StreamVault project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Load API credentials from the project's .env file.
load_dotenv(PROJECT_ROOT / ".env")


# Define paths for input data, cached responses and outputs.
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = PROJECT_ROOT / "out"


# Define TMDb API connection settings.
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Connection timeout: 3.05 seconds; response timeout: 10 seconds.
REQUEST_TIMEOUT = (3.05, 10)


def require_api_key():
    """Raise an error when the TMDb API key is unavailable."""
    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing. Check your project .env file."
        )
