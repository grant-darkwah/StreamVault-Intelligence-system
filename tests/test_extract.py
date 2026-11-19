"""Tests for the StreamVault TMDb extraction module."""

import json

import pytest
import requests
from pipeline import extract


@pytest.fixture
def temporary_extraction_paths(tmp_path, monkeypatch):
    """Redirect extraction files to a temporary test directory."""

    cache_dir = tmp_path / "cache"
    details_dir = cache_dir / "details"
    credits_dir = cache_dir / "credits"
    manifest_file = cache_dir / "acquisition_manifest.jsonl"

    monkeypatch.setattr(extract, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(extract, "DETAILS_CACHE_DIR", details_dir)
    monkeypatch.setattr(extract, "CREDITS_CACHE_DIR", credits_dir)
    monkeypatch.setattr(extract, "MANIFEST_FILE", manifest_file)

    return {
        "cache_dir": cache_dir,
        "details_dir": details_dir,
        "credits_dir": credits_dir,
        "manifest_file": manifest_file,
    }


def test_successful_response_is_cached(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify successful responses are cached and recorded."""

    movie_data = {
        "id": 155,
        "title": "The Dark Knight",
    }

    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(movie_data).encode("utf-8")
    response.headers["Content-Type"] = "application/json"

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: response)

    result = extract.fetch_endpoint(session, 155, "details")

    assert result["status"] == "success"

    cache_file = temporary_extraction_paths["details_dir"] / "155.json"
    assert cache_file.exists()

    with cache_file.open("r", encoding="utf-8") as file:
        cached_record = json.load(file)

    assert cached_record["data"] == movie_data
    assert cached_record["movie_id"] == 155

    session.close()


def test_cache_hit_avoids_api_request(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify cached data is reused without another API request."""

    movie_data = {"id": 155, "title": "The Dark Knight"}

    extract.save_cached_response(155, "details", movie_data)

    session = requests.Session()

    def unexpected_request(*args, **kwargs):
        pytest.fail("An API request was made despite a cache hit.")

    monkeypatch.setattr(session, "get", unexpected_request)

    result = extract.fetch_endpoint(session, 155, "details")

    assert result["status"] == "cache_hit"
    assert result["data"] == movie_data

    session.close()


def test_not_found_response_is_recorded(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify HTTP 404 responses are classified correctly."""

    response = requests.Response()
    response.status_code = 404

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: response)

    result = extract.fetch_endpoint(session, 999999999, "details")

    assert result["status"] == "not_found"
    assert result["http_status"] == 404

    session.close()


def test_invalid_json_response_is_classified(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify invalid JSON is not classified as a request failure."""

    response = requests.Response()
    response.status_code = 200
    response._content = b"not-valid-json"
    response.headers["Content-Type"] = "application/json"

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: response)

    result = extract.fetch_endpoint(session, 155, "details")

    assert result["status"] == "invalid_json"

    session.close()


def test_request_failure_is_recorded(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify request failures are classified correctly."""

    session = requests.Session()

    def failed_request(*args, **kwargs):
        raise requests.Timeout("Connection timed out")

    monkeypatch.setattr(session, "get", failed_request)

    result = extract.fetch_endpoint(session, 155, "details")

    assert result["status"] == "request_failed"
    assert result["error_type"] == "Timeout"

    session.close()


def test_manifest_records_acquisition_events(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify acquisition events are appended to the manifest."""

    movie_data = {"id": 155, "title": "The Dark Knight"}

    extract.append_manifest(
        {
            "movie_id": 155,
            "endpoint": "details",
            "status": "success",
        }
    )

    extract.append_manifest(
        {
            "movie_id": 155,
            "endpoint": "credits",
            "status": "success",
        }
    )

    manifest_file = temporary_extraction_paths["manifest_file"]

    with manifest_file.open("r", encoding="utf-8") as file:
        records = [json.loads(line) for line in file]

    assert len(records) == 2
    assert records[0]["endpoint"] == "details"
    assert records[1]["endpoint"] == "credits"
