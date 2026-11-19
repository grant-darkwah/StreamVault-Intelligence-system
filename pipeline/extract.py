"""
StreamVault TMDb extraction module.

Responsibilities:
1. Fetch movie details and credits from TMDb.
2. Cache successful raw JSON responses.
3. Record acquisition outcomes and timestamps.
4. Extract each unique valid candidate ID once.
5. Preserve original candidate records for reconciliation.
6. Generate acquisition summaries and reconciliation outputs.
"""

import json
import logging
from datetime import UTC, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline.config import (
    CACHE_DIR,
    OUTPUT_DIR,
    REQUEST_TIMEOUT,
    TMDB_API_KEY,
    TMDB_BASE_URL,
    require_api_key,
)
from pipeline.ingest import load_candidate_ids


# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------

# Configure logging without exposing API credentials.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Extraction configuration
# ---------------------------------------------------------------------

# Store each endpoint's responses separately.
DETAILS_CACHE_DIR = CACHE_DIR / "details"
CREDITS_CACHE_DIR = CACHE_DIR / "credits"

# Use an append-only manifest for acquisition events.
MANIFEST_FILE = CACHE_DIR / "acquisition_manifest.jsonl"

# Define the supported TMDb endpoints.
VALID_ENDPOINTS = {"details", "credits"}


# ---------------------------------------------------------------------
# HTTP session configuration
# ---------------------------------------------------------------------


def create_session() -> requests.Session:
    """Create an HTTP session with retry handling."""

    # Retry temporary server failures and rate limits.
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

    # Reuse connections and apply the retry policy.
    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    # Use the TMDb API key for authentication.
    session.params = {"api_key": TMDB_API_KEY}

    # Identify the application in outgoing requests.
    session.headers.update({"User-Agent": "StreamVault-Intelligence-System/1.0"})

    return session


# ---------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------


def get_cache_path(movie_id: int, endpoint: str):
    """Return the cache filename for a movie endpoint."""

    # Reject unsupported endpoints.
    if endpoint not in VALID_ENDPOINTS:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    # Keep details and credits in separate directories.
    cache_directory = DETAILS_CACHE_DIR if endpoint == "details" else CREDITS_CACHE_DIR

    return cache_directory / f"{movie_id}.json"


def load_cached_response(movie_id: int, endpoint: str):
    """Load a cached response when one exists."""

    cache_path = get_cache_path(movie_id, endpoint)

    if not cache_path.exists():
        return None

    # Read the original JSON response from disk.
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

    # Ensure the cache directory exists.
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve the original response and retrieval metadata.
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


# ---------------------------------------------------------------------
# Acquisition manifest
# ---------------------------------------------------------------------


def append_manifest(record: dict) -> None:
    """Append one acquisition event to the JSON Lines manifest."""

    # Ensure the cache directory exists.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Each acquisition event occupies one independent JSON line.
    with MANIFEST_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------
# Individual endpoint extraction
# ---------------------------------------------------------------------


def fetch_endpoint(
    session: requests.Session,
    movie_id: int,
    endpoint: str,
) -> dict:
    """Fetch one TMDb endpoint or return its cached response."""

    # Validate the requested endpoint.
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

        # Record the cache hit without duplicating the raw response.
        manifest_record = {key: value for key, value in result.items() if key != "data"}

        append_manifest(manifest_record)

        return result

    # Build the appropriate TMDb endpoint URL.
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"

    if endpoint == "credits":
        url += "/credits"

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        # Treat missing movie records as an explicit outcome.
        if response.status_code == 404:
            result = {
                "movie_id": movie_id,
                "endpoint": endpoint,
                "status": "not_found",
                "http_status": 404,
            }

        else:
            # Raise an exception for other unsuccessful responses.
            response.raise_for_status()

            # Parse the original API response.
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
        # Record invalid JSON responses separately.
        result = {
            "movie_id": movie_id,
            "endpoint": endpoint,
            "status": "invalid_json",
        }

    except requests.RequestException as error:
        # Record failures without storing request URLs or credentials.
        result = {
            "movie_id": movie_id,
            "endpoint": endpoint,
            "status": "request_failed",
            "error_type": type(error).__name__,
        }

        # Preserve HTTP status codes when available.
        if isinstance(error, requests.HTTPError) and error.response is not None:
            result["http_status"] = error.response.status_code

    # Record when the acquisition attempt finished.
    result["recorded_at"] = datetime.now(UTC).isoformat()

    append_manifest(result)

    return result


# ---------------------------------------------------------------------
# Individual movie extraction
# ---------------------------------------------------------------------


def extract_movie(
    session: requests.Session,
    movie_id: int,
) -> dict:
    """Fetch details and credits for one movie."""

    # Request both endpoint responses independently.
    details = fetch_endpoint(session, movie_id, "details")
    credits = fetch_endpoint(session, movie_id, "credits")

    return {
        "movie_id": movie_id,
        "details": details,
        "credits": credits,
    }


# ---------------------------------------------------------------------
# Candidate extraction orchestration
# ---------------------------------------------------------------------


def extract_candidates(
    candidates,
    session: requests.Session,
) -> list[dict]:
    """Extract details and credits for unique valid candidate IDs."""

    # Select valid IDs and preserve their original order.
    valid_ids = candidates.loc[candidates["is_valid"], "tmdb_id"].drop_duplicates()

    results = []

    logger.info(
        "Unique valid candidate IDs: %s",
        len(valid_ids),
    )

    # Fetch both endpoints once for each unique valid ID.
    for position, raw_id in enumerate(valid_ids, start=1):
        movie_id = int(raw_id)

        logger.info(
            "Extracting movie %s of %s: TMDb ID %s",
            position,
            len(valid_ids),
            movie_id,
        )

        result = extract_movie(session, movie_id)
        results.append(result)

    return results


# ---------------------------------------------------------------------
# Acquisition summary
# ---------------------------------------------------------------------


def summarize_acquisition(results: list[dict]) -> dict:
    """Calculate acquisition outcomes independently for each endpoint."""

    summary = {
        "unique_movies_processed": len(results),
        "details": {},
        "credits": {},
    }

    # Count each endpoint's acquisition statuses independently.
    for endpoint in VALID_ENDPOINTS:
        statuses = {}

        for movie in results:
            status = movie[endpoint]["status"]

            statuses[status] = statuses.get(status, 0) + 1

        summary[endpoint] = statuses

    return summary


# ---------------------------------------------------------------------
# Candidate reconciliation
# ---------------------------------------------------------------------


def build_reconciliation_report(
    candidates,
    results: list[dict],
):
    """Preserve source rows and identify extraction representatives."""

    # Index extraction results by their unique TMDb identifier.
    results_by_id = {str(movie["movie_id"]): movie for movie in results}

    # Work on a copy to preserve the original candidate DataFrame.
    report = candidates.copy()

    # Initialise outcome columns for every original candidate row.
    report["extraction_reference"] = "not_processed"
    report["details_status"] = "not_processed"
    report["credits_status"] = "not_processed"

    # Track the first source occurrence of each valid ID.
    seen_ids = set()

    for index, row in report.iterrows():
        movie_id = row["tmdb_id"]

        # Preserve invalid records without attempting API requests.
        if not row["is_valid"]:
            report.at[index, "extraction_reference"] = "invalid_id"
            report.at[index, "details_status"] = "invalid_id"
            report.at[index, "credits_status"] = "invalid_id"

            continue

        # The first occurrence represents the extraction request.
        if movie_id not in seen_ids:
            seen_ids.add(movie_id)
            reference_status = "unique_record"
        else:
            reference_status = "duplicate_reference"

        report.at[index, "extraction_reference"] = reference_status

        # Attach the acquisition outcomes for this valid ID.
        movie = results_by_id.get(str(movie_id))

        if movie is not None:
            report.at[index, "details_status"] = movie["details"]["status"]
            report.at[index, "credits_status"] = movie["credits"]["status"]

    return report


# ---------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------


def save_extraction_outputs(
    summary: dict,
    reconciliation,
) -> None:
    """Save acquisition summary and candidate reconciliation outputs."""

    # Ensure the output directory exists.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = OUTPUT_DIR / "acquisition_summary.json"
    reconciliation_path = OUTPUT_DIR / "candidate_reconciliation.csv"

    # Save the endpoint-level acquisition summary.
    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    # Save every original candidate row and its acquisition outcome.
    reconciliation.to_csv(
        reconciliation_path,
        index=False,
    )

    logger.info("Acquisition summary saved: %s", summary_path)
    logger.info("Candidate reconciliation saved: %s", reconciliation_path)


# ---------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------


def main():
    """Run the complete candidate extraction workflow."""

    # Validate API configuration before starting.
    require_api_key()

    # Load and validate all original candidate records.
    candidates = load_candidate_ids()

    logger.info(
        "Original candidate rows: %s",
        len(candidates),
    )

    logger.info(
        "Unique valid IDs: %s",
        candidates.loc[candidates["is_valid"], "tmdb_id"].nunique(),
    )

    # Prepare cache directories.
    DETAILS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CREDITS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create one reusable HTTP session.
    session = create_session()

    try:
        # Extract each unique valid candidate ID.
        results = extract_candidates(candidates, session)

        # Calculate acquisition outcomes.
        summary = summarize_acquisition(results)

        # Reconcile API outcomes against all original source rows.
        reconciliation = build_reconciliation_report(
            candidates,
            results,
        )

        # Persist reproducible acquisition outputs.
        save_extraction_outputs(summary, reconciliation)

        logger.info("Extraction workflow completed.")

        logger.info(
            "Unique movies processed: %s",
            summary["unique_movies_processed"],
        )

    finally:
        # Always close the HTTP session.
        session.close()


if __name__ == "__main__":
    main()
