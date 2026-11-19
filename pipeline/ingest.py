"""
StreamVault candidate ID ingestion and validation.

Responsibilities:
1. Load the original TMDb candidate ID CSV.
2. Preserve original values and source-row positions.
3. Validate missing, numeric and positive IDs.
4. Identify duplicate valid IDs without flagging invalid values.
5. Produce a candidate reconciliation report.

The original CSV is never modified by this module.
"""

from pathlib import Path

import pandas as pd

from pipeline.config import RAW_DIR

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# Path to the original candidate ID file.
ID_FILE = RAW_DIR / "id_list.csv"

# Expected number of candidate records specified in the project brief.
EXPECTED_CANDIDATE_COUNT = 127

# Required column in the original CSV.
ID_COLUMN = "tmdb_id"


# ---------------------------------------------------------------------
# Candidate ID loading
# ---------------------------------------------------------------------


def load_candidate_ids(
    file_path: Path = ID_FILE,
) -> pd.DataFrame:
    """
    Load candidate IDs and preserve the original source records.

    IDs are initially read as strings to prevent unwanted type
    conversion. Blank lines are retained for reconciliation.
    """

    # Confirm that the input file exists before attempting to load it.
    if not file_path.exists():
        raise FileNotFoundError(f"Candidate ID file not found: {file_path}")

    # Read the CSV without automatically interpreting values such
    # as N/A as missing. Retain blank lines for investigation.
    df = pd.read_csv(
        file_path,
        dtype={ID_COLUMN: "string"},
        keep_default_na=False,
        skip_blank_lines=False,
    )

    # Stop execution if the required identifier column is absent.
    if ID_COLUMN not in df.columns:
        raise ValueError(
            f"Required column '{ID_COLUMN}' is missing. "
            f"Available columns: {list(df.columns)}"
        )

    # Preserve the original identifier exactly as loaded.
    df = df.rename(columns={ID_COLUMN: "tmdb_id_raw"})

    # Create a working identifier with surrounding whitespace removed.
    # Fill any parser-generated missing values with empty strings.
    df["tmdb_id"] = df["tmdb_id_raw"].fillna("").astype("string").str.strip()

    # Record the source row position, excluding the CSV header.
    # This allows every flagged record to be traced back to the file.
    df.insert(
        0,
        "source_row",
        range(1, len(df) + 1),
    )

    # Identify empty or whitespace-only identifiers.
    df["is_missing"] = df["tmdb_id"].eq("")

    # Accept signed integer strings so that -1 is recognised as
    # numeric and can be classified correctly as non-positive.
    df["is_numeric"] = df["tmdb_id"].str.fullmatch(r"[+-]?\d+").fillna(False)

    # Check positivity only for values that passed numeric validation.
    # Python's int conversion avoids floating-point precision issues.
    df["is_positive"] = False

    numeric_mask = df["is_numeric"]

    df.loc[numeric_mask, "is_positive"] = df.loc[numeric_mask, "tmdb_id"].map(
        lambda value: int(value) > 0
    )

    # An ID is valid only if it is numeric, positive and nonblank.
    df["is_valid"] = ~df["is_missing"] & df["is_numeric"] & df["is_positive"]

    # Initialise duplicate flags to False for all records.
    # Invalid identifiers must never be included in duplicate checks.
    df["is_duplicate"] = False

    # Select only valid IDs for duplicate detection.
    valid_ids = df.loc[df["is_valid"], "tmdb_id"]

    # Mark every occurrence belonging to a duplicate group.
    duplicate_mask = valid_ids.duplicated(keep=False)

    df.loc[valid_ids.index, "is_duplicate"] = duplicate_mask

    return df


# ---------------------------------------------------------------------
# Candidate ID reporting
# ---------------------------------------------------------------------


def report_candidate_ids(df: pd.DataFrame) -> None:
    """
    Print a reconciliation and validation report.

    Duplicate group rows and excess duplicate occurrences are
    reported separately to avoid confusing the two measures.
    """

    # Calculate the number of valid, distinct candidate IDs.
    valid_ids = df.loc[df["is_valid"], "tmdb_id"]

    unique_valid_count = valid_ids.nunique()

    # Count valid rows belonging to duplicate groups.
    duplicate_group_rows = int(df["is_duplicate"].sum())

    # Count repeated occurrences beyond the first occurrence of each ID.
    duplicate_excess = int(valid_ids.duplicated(keep="first").sum())

    # Count invalid records by validation category.
    missing_count = int(df["is_missing"].sum())

    non_numeric_count = int((~df["is_numeric"] & ~df["is_missing"]).sum())

    non_positive_count = int((df["is_numeric"] & ~df["is_positive"]).sum())

    invalid_count = int((~df["is_valid"]).sum())

    # Calculate the difference from the expected candidate count.
    candidate_difference = len(df) - EXPECTED_CANDIDATE_COUNT

    # Print the main reconciliation summary.
    print("\nSTREAMVAULT CANDIDATE ID AUDIT")
    print("=" * 45)

    print(f"Expected candidate rows: {EXPECTED_CANDIDATE_COUNT}")
    print(f"Loaded candidate rows:   {len(df)}")
    print(f"Candidate count difference: {candidate_difference:+d}")

    print("-" * 45)

    print(f"Unique valid IDs: {unique_valid_count}")
    print(f"Missing IDs: {missing_count}")
    print(f"Non-numeric IDs: {non_numeric_count}")
    print(f"Non-positive IDs: {non_positive_count}")
    print(f"Invalid records: {invalid_count}")

    print("-" * 45)

    print(f"Rows in duplicate groups: {duplicate_group_rows}")
    print(f"Excess duplicate occurrences: {duplicate_excess}")

    # Identify records requiring investigation.
    issues = df.loc[(~df["is_valid"]) | df["is_duplicate"]]

    if issues.empty:
        print("\nNo candidate ID issues detected.")
    else:
        print("\nRECORDS REQUIRING INVESTIGATION")
        print("-" * 45)

        print(
            issues[
                [
                    "source_row",
                    "tmdb_id_raw",
                    "tmdb_id",
                    "is_missing",
                    "is_numeric",
                    "is_positive",
                    "is_valid",
                    "is_duplicate",
                ]
            ].to_string(index=False)
        )

    # Explicitly report whether the candidate count reconciles.
    print("\nRECONCILIATION STATUS")
    print("-" * 45)

    if candidate_difference == 0:
        print("Candidate row count matches the expected 127.")
    else:
        print(
            "Candidate row count does not match the expected "
            f"{EXPECTED_CANDIDATE_COUNT}. Investigate the source file."
        )


# ---------------------------------------------------------------------
# Module execution
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Load the original candidate records.
    candidates = load_candidate_ids()

    # Print the candidate validation and reconciliation report.
    report_candidate_ids(candidates)
