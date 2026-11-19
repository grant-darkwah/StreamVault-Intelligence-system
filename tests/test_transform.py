"""Tests for StreamVault data transformation and validation."""

import json

import pandas as pd
import pytest
from pipeline.checks import validate_transformed_data
from pipeline.load import save_datasets
from pipeline.transform import transform_cached_data


def write_cache_file(directory, movie_id, data):
    """Write a cache record using the production cache structure."""

    directory.mkdir(parents=True, exist_ok=True)

    record = {
        "movie_id": movie_id,
        "endpoint": directory.name,
        "fetched_at": "2026-01-01T00:00:00",
        "data": data,
    }

    file_path = directory / f"{movie_id}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(record, file)


@pytest.fixture
def sample_cache(tmp_path):
    """Create a minimal details and credits cache for one film."""

    details_dir = tmp_path / "cache" / "details"
    credits_dir = tmp_path / "cache" / "credits"

    details = {
        "id": 155,
        "title": "Test Film",
        "original_title": "Test Film",
        "release_date": "2020-01-01",
        "budget": 1000000,
        "revenue": 5000000,
        "popularity": 10.5,
        "vote_average": 7.5,
        "vote_count": 100,
        "runtime": 120,
        "original_language": "en",
        "status": "Released",
        "homepage": "",
        "belongs_to_collection": None,
        "genres": [{"id": 12, "name": "Adventure"}],
        "production_companies": [{"id": 10, "name": "Test Studio"}],
    }

    credits = {
        "id": 155,
        "cast": [
            {
                "id": 1,
                "name": "Test Actor",
                "credit_id": "cast-1",
                "character": "Lead",
                "order": 0,
            }
        ],
        "crew": [
            {
                "id": 2,
                "name": "Test Director",
                "credit_id": "crew-1",
                "department": "Directing",
                "job": "Director",
            }
        ],
    }

    write_cache_file(details_dir, 155, details)
    write_cache_file(credits_dir, 155, credits)

    return details_dir, credits_dir


def test_transform_creates_expected_tables(sample_cache):
    """Verify transformation creates all five normalized tables."""

    details_dir, credits_dir = sample_cache

    data = transform_cached_data(details_dir, credits_dir)

    assert set(data) == {
        "films",
        "cast",
        "crew",
        "film_genres",
        "film_companies",
    }

    assert len(data["films"]) == 1
    assert len(data["cast"]) == 1
    assert len(data["crew"]) == 1
    assert len(data["film_genres"]) == 1
    assert len(data["film_companies"]) == 1

    assert data["films"].iloc[0]["release_year"] == 2020


def test_transformed_data_passes_validation(sample_cache):
    """Verify valid normalized data passes all integrity checks."""

    details_dir, credits_dir = sample_cache

    data = transform_cached_data(details_dir, credits_dir)
    result = validate_transformed_data(data)

    assert result["status"] == "passed"
    assert result["total_films"] == 1


def test_mismatched_cache_populations_raise_error(sample_cache):
    """Verify missing endpoint records are detected."""

    details_dir, credits_dir = sample_cache

    (credits_dir / "155.json").unlink()

    with pytest.raises(ValueError, match="populations do not match"):
        transform_cached_data(details_dir, credits_dir)


def test_cache_payload_id_mismatch_raises_error(sample_cache):
    """Verify cache wrapper and payload IDs must agree."""

    details_dir, _ = sample_cache

    file_path = details_dir / "155.json"

    with file_path.open("r", encoding="utf-8") as file:
        record = json.load(file)

    record["data"]["id"] = 999

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(record, file)

    with pytest.raises(ValueError, match="Cache ID mismatch"):
        transform_cached_data(details_dir, sample_cache[1])


def test_validation_detects_duplicate_film_keys(sample_cache):
    """Verify duplicate movie IDs are rejected."""

    details_dir, credits_dir = sample_cache

    data = transform_cached_data(details_dir, credits_dir)

    data["films"] = pd.concat(
        [data["films"], data["films"]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicate keys"):
        validate_transformed_data(data)


def test_validation_detects_orphan_movie_ids(sample_cache):
    """Verify child records must reference an existing film."""

    details_dir, credits_dir = sample_cache

    data = transform_cached_data(details_dir, credits_dir)
    data["cast"].loc[0, "movie_id"] = 999

    with pytest.raises(ValueError, match="do not exist in films"):
        validate_transformed_data(data)


def test_parquet_files_can_be_saved_and_reloaded(
    sample_cache,
    tmp_path,
):
    """Verify saved Parquet datasets preserve their row counts."""

    details_dir, credits_dir = sample_cache

    data = transform_cached_data(details_dir, credits_dir)
    output_dir = tmp_path / "out"

    paths = save_datasets(data, output_dir)

    assert len(paths) == 5

    for name, path in paths.items():
        assert path.exists()

        restored = pd.read_parquet(path)

        assert len(restored) == len(data[name])
        assert list(restored.columns) == list(data[name].columns)
