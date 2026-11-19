"""
StreamVault TMDb extraction module.

Fetches movie details and credits.
Caches successful raw JSON responses.
Records acquisition outcomes and timestamps.
"""

import json
import logging
from datetime import UTC, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline.config import (
    CACHE_DIR,
    REQUEST_TIMEOUT,
    TMDB_API_KEY,
    TMDB_BASE_URL,
    require_api_key,
)

# Configure logging without exposing API credentials.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# Store each endpoint's responses separately.
DETAILS_CACHE_DIR = CACHE_DIR / "details"
CREDITS_CACHE_DIR = CACHE_DIR / "credits"

# Use an append-only manifest for acquisition events.
MANIFEST_FILE = CACHE_DIR / "acquisition_manifest.jsonl"

VALID_ENDPOINTS = {"details", "credits"}


def create_session() -> requests.Session:
    """Create an HTTP session with retry handling."""

    retry_strategy = Retry(
        total=5,
        connect=5,
        read=2,
        status=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)

    # Use the TMDb API key for authentication.
    session.params = {"api_key": TMDB_API_KEY}

    # Identify the application in outgoing requests.
    session.headers.update({"User-Agent": "StreamVault-Intelligence-System/1.0"})

    return session


def get_cache_path(movie_id: int, endpoint: str):
    """Return the cache filename for a movie endpoint."""

    if endpoint not in VALID_ENDPOINTS:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    cache_directory = DETAILS_CACHE_DIR if endpoint == "details" else CREDITS_CACHE_DIR

    return cache_directory / f"{movie_id}.json"


def load_cached_response(movie_id: int, endpoint: str):
    """Load a cached response when one exists."""

    cache_path = get_cache_path(movie_id, endpoint)

    if not cache_path.exists():
        return None

    with cache_path.open("r", encoding="utf-8") as file:
        cached_record = json.load(file)

    return cached_record["data"]


def save_cached_response(
    movie_id: int,
    endpoint: str,
    data: dict,
) -> None:
    """Save raw JSON data with its retrieval timestamp."""

    cache_path = get_cache_path(movie_id, endpoint)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    cached_record = {
        "movie_id": movie_id,
        "endpoint": endpoint,
        "fetched_at": datetime.now(UTC).isoformat(),
        "data": data,
    }

    # Write atomically to avoid incomplete cache files.
    temporary_path = cache_path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(cached_record, file, ensure_ascii=False, indent=2)

    temporary_path.replace(cache_path)


def append_manifest(record: dict) -> None:
    """Append one acquisition event to the JSON Lines manifest."""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Each event occupies one independent JSON line.
    with MANIFEST_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def fetch_endpoint(
    session: requests.Session,
    movie_id: int,
    endpoint: str,
) -> dict:
    """Fetch one TMDb endpoint or return its cached response."""

    if endpoint not in VALID_ENDPOINTS:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    # Reuse cached data to avoid unnecessary API requests.
    cached_data = load_cached_response(movie_id, endpoint)

    if cached_data is not None:
        result = {
            "movie_id": movie_id,
            "endpoint": endpoint,
            "status": "cache_hit",
            "recorded_at": datetime.now(UTC).isoformat(),
            "data": cached_data,
        }
        append_manifest({key: value for key, value in result.items() if key != "data"})
        return result

    # Build the appropriate TMDb endpoint URL.
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"

    if endpoint == "credits":
        url += "/credits"

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)

        if response.status_code == 404:
            result = {
                "movie_id": movie_id,
                "endpoint": endpoint,
                "status": "not_found",
                "http_status": 404,
            }
        else:
            response.raise_for_status()

            # Invalid JSON is handled separately below.
            data = response.json()

            # Cache successful responses before further processing.
            save_cached_response(movie_id, endpoint, data)

            result = {
                "movie_id": movie_id,
                "endpoint": endpoint,
                "status": "success",
                "http_status": response.status_code,
            }

    except requests.exceptions.JSONDecodeError:
        result = {
            "movie_id": movie_id,
            "endpoint": endpoint,
            "status": "invalid_json",
        }

    except requests.RequestException as error:
        result = {
            "movie_id": movie_id,
            "endpoint": endpoint,
            "status": "request_failed",
            "error_type": type(error).__name__,
        }

        # Preserve HTTP status codes without storing request URLs.
        if isinstance(error, requests.HTTPError) and error.response is not None:
            result["http_status"] = error.response.status_code

    # Record when the acquisition attempt finished.
    result["recorded_at"] = datetime.now(UTC).isoformat()
    append_manifest(result)

    return result


def extract_movie(
    session: requests.Session,
    movie_id: int,
) -> dict:
    """Fetch details and credits for one movie."""

    details = fetch_endpoint(session, movie_id, "details")
    credits = fetch_endpoint(session, movie_id, "credits")

    return {
        "movie_id": movie_id,
        "details": details,
        "credits": credits,
    }


def main():
    """Validate configuration and initialise extraction."""

    require_api_key()

    DETAILS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CREDITS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    session = create_session()

    try:
        logger.info("TMDb extraction module is ready.")
        logger.info("Details cache: %s", DETAILS_CACHE_DIR)
        logger.info("Credits cache: %s", CREDITS_CACHE_DIR)
        logger.info("Manifest: %s", MANIFEST_FILE)
    finally:
        session.close()


if __name__ == "__main__":
    main()
