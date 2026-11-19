"""Tests for the StreamVault TMDb extraction module."""

import json

import pandas as pd
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

    movie_data = {"id": 155, "title": "The Dark Knight"}  # noqa: F841

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


def test_extract_candidates_processes_unique_valid_ids(monkeypatch):
    """Verify only unique valid IDs are sent for extraction."""

    candidates = pd.DataFrame(
        {
            "tmdb_id": ["155", "165", "155", "", "-1", "242"],
            "is_valid": [True, True, True, False, False, True],
        }
    )

    extracted_ids = []

    def fake_extract_movie(session, movie_id):
        extracted_ids.append(movie_id)

        return {
            "movie_id": movie_id,
            "details": {"status": "success"},
            "credits": {"status": "success"},
        }

    monkeypatch.setattr(extract, "extract_movie", fake_extract_movie)

    results = extract.extract_candidates(candidates, session=None)

    assert extracted_ids == [155, 165, 242]
    assert len(results) == 3


def test_summarize_acquisition_counts_endpoint_statuses():
    """Verify endpoint outcomes are counted independently."""

    results = [
        {
            "movie_id": 155,
            "details": {"status": "success"},
            "credits": {"status": "success"},
        },
        {
            "movie_id": 165,
            "details": {"status": "cache_hit"},
            "credits": {"status": "not_found"},
        },
        {
            "movie_id": 242,
            "details": {"status": "request_failed"},
            "credits": {"status": "success"},
        },
    ]

    summary = extract.summarize_acquisition(results)

    assert summary["unique_movies_processed"] == 3
    assert summary["details"] == {
        "success": 1,
        "cache_hit": 1,
        "request_failed": 1,
    }
    assert summary["credits"] == {
        "success": 2,
        "not_found": 1,
    }


def test_reconciliation_preserves_duplicate_and_invalid_rows():
    """Verify the first duplicate occurrence represents extraction."""

    candidates = pd.DataFrame(
        {
            "source_row": [1, 2, 3, 4],
            "tmdb_id_raw": ["155", "155", "", "-1"],
            "tmdb_id": ["155", "155", "", "-1"],
            "is_valid": [True, True, False, False],
            "is_duplicate": [True, True, False, False],
        }
    )

    results = [
        {
            "movie_id": 155,
            "details": {"status": "success"},
            "credits": {"status": "success"},
        }
    ]

    report = extract.build_reconciliation_report(candidates, results)

    assert len(report) == 4
    assert report["source_row"].tolist() == [1, 2, 3, 4]

    assert report["extraction_reference"].tolist() == [
        "unique_record",
        "duplicate_reference",
        "invalid_id",
        "invalid_id",
    ]

    assert report["details_status"].tolist() == [
        "success",
        "success",
        "invalid_id",
        "invalid_id",
    ]


def test_empty_extraction_summary():
    """Verify summary generation when no valid IDs are available."""

    summary = extract.summarize_acquisition([])

    assert summary["unique_movies_processed"] == 0
    assert summary["details"] == {}
    assert summary["credits"] == {}


def test_session_has_retry_configuration():
    """Verify transient HTTP failures have a retry policy."""

    session = extract.create_session()

    adapter = session.get_adapter("https://")
    retry_policy = adapter.max_retries

    assert retry_policy.total == 5
    assert retry_policy.connect == 5
    assert retry_policy.read == 2
    assert retry_policy.status == 5
    assert retry_policy.respect_retry_after_header is True

    assert {429, 500, 502, 503, 504}.issubset(set(retry_policy.status_forcelist))

    session.close()


def test_extract_movie_reuses_both_cached_endpoints(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify an interrupted extraction can resume from both caches."""

    details_data = {
        "id": 155,
        "title": "The Dark Knight",
    }

    credits_data = {
        "id": 155,
        "cast": [],
        "crew": [],
    }

    extract.save_cached_response(155, "details", details_data)
    extract.save_cached_response(155, "credits", credits_data)

    session = requests.Session()

    def unexpected_request(*args, **kwargs):
        pytest.fail("An API request occurred despite cached responses.")

    monkeypatch.setattr(session, "get", unexpected_request)

    result = extract.extract_movie(session, 155)

    assert result["details"]["status"] == "cache_hit"
    assert result["credits"]["status"] == "cache_hit"

    assert result["details"]["data"] == details_data
    assert result["credits"]["data"] == credits_data

    session.close()


def test_save_extraction_outputs(
    temporary_extraction_paths,
    monkeypatch,
):
    """Verify acquisition outputs are saved correctly."""

    import pandas as pd

    output_dir = temporary_extraction_paths["cache_dir"].parent / "out"

    monkeypatch.setattr(extract, "OUTPUT_DIR", output_dir)

    summary = {
        "unique_movies_processed": 1,
        "details": {"success": 1},
        "credits": {"success": 1},
    }

    reconciliation = pd.DataFrame(
        {
            "source_row": [1],
            "tmdb_id": ["155"],
            "extraction_reference": ["unique_record"],
            "details_status": ["success"],
            "credits_status": ["success"],
        }
    )

    extract.save_extraction_outputs(summary, reconciliation)

    summary_path = output_dir / "acquisition_summary.json"
    reconciliation_path = output_dir / "candidate_reconciliation.csv"

    assert summary_path.exists()
    assert reconciliation_path.exists()

    with summary_path.open("r", encoding="utf-8") as file:
        saved_summary = json.load(file)

    saved_reconciliation = pd.read_csv(reconciliation_path)

    assert saved_summary == summary
    assert len(saved_reconciliation) == 1
    assert saved_reconciliation.loc[0, "tmdb_id"] == 155
