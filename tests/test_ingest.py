import pandas as pd
import pytest
from pipeline.ingest import load_candidate_ids


def create_test_csv(tmp_path, values):
    """Create a temporary candidate CSV for testing."""
    file_path = tmp_path / "test_ids.csv"

    # Write test identifiers without modifying the real candidate file.
    pd.DataFrame({"tmdb_id": values}).to_csv(file_path, index=False)

    return file_path


def test_duplicate_ids_are_detected(tmp_path):
    """Both occurrences of a repeated valid ID must be flagged."""
    file_path = create_test_csv(tmp_path, ["155", "155", "680", "242"])

    df = load_candidate_ids(file_path)

    # Both occurrences of 155 should be duplicates.
    duplicates = df.loc[df["is_duplicate"], "tmdb_id"].tolist()

    assert duplicates == ["155", "155"]
    assert df["is_duplicate"].sum() == 2


def test_invalid_ids_are_not_duplicates(tmp_path):
    """Invalid identifiers must not be flagged as duplicates."""
    file_path = create_test_csv(tmp_path, ["-1", "N/A", "tt0468569", ""])

    df = load_candidate_ids(file_path)

    # None of the invalid values should be marked as duplicates.
    assert df["is_duplicate"].sum() == 0
    assert df["is_valid"].sum() == 0


def test_invalid_id_classification(tmp_path):
    """Missing, non-numeric and non-positive IDs must be distinguished."""
    file_path = create_test_csv(tmp_path, ["-1", "N/A", "tt0468569", ""])

    df = load_candidate_ids(file_path)

    assert df["is_missing"].sum() == 1
    assert (~df["is_numeric"] & ~df["is_missing"]).sum() == 2
    assert (df["is_numeric"] & ~df["is_positive"]).sum() == 1


def test_unique_valid_ids_are_not_duplicates(tmp_path):
    """Unique positive numeric IDs must remain valid."""
    file_path = create_test_csv(tmp_path, ["155", "680", "242"])

    df = load_candidate_ids(file_path)

    assert df["is_valid"].all()
    assert not df["is_duplicate"].any()


def test_source_rows_are_preserved(tmp_path):
    """Every input record must retain its original row position."""
    file_path = create_test_csv(tmp_path, ["155", "155", "-1", "680"])

    df = load_candidate_ids(file_path)

    assert len(df) == 4
    assert df["source_row"].tolist() == [1, 2, 3, 4]
