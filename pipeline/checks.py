"""
Data quality checks for StreamVault transformation outputs.
"""

import pandas as pd

TABLE_KEYS = {
    "films": ["movie_id"],
    "cast": ["movie_id", "credit_id"],
    "crew": ["movie_id", "credit_id"],
    "film_genres": ["movie_id", "id"],
    "film_companies": ["movie_id", "id"],
}


def validate_transformed_data(data: dict) -> dict:
    """
    Validate required tables, keys, and film relationships.

    Returns a summary of validation results.
    Raises ValueError when a check fails.
    """

    errors = []
    results = {}

    # Confirm all expected tables are present.
    missing_tables = set(TABLE_KEYS) - set(data)

    if missing_tables:
        raise ValueError(f"Missing required tables: {sorted(missing_tables)}")

    films = data["films"]

    # Validate each table's keys and required structure.
    for table_name, keys in TABLE_KEYS.items():
        frame = data[table_name]

        missing_columns = set(keys) - set(frame.columns)

        if missing_columns:
            errors.append(f"{table_name}: missing columns {sorted(missing_columns)}")
            continue

        missing_keys = int(frame[keys].isna().any(axis=1).sum())
        duplicate_keys = int(frame.duplicated(keys).sum())

        results[table_name] = {
            "rows": len(frame),
            "missing_keys": missing_keys,
            "duplicate_keys": duplicate_keys,
        }

        if missing_keys:
            errors.append(f"{table_name}: {missing_keys} rows have missing keys")

        if duplicate_keys:
            errors.append(f"{table_name}: {duplicate_keys} duplicate keys found")

    # Check that every child-table movie ID exists in films.
    film_ids = set(films["movie_id"].dropna())

    for table_name in ("cast", "crew", "film_genres", "film_companies"):
        child_ids = set(data[table_name]["movie_id"].dropna())
        orphan_ids = child_ids - film_ids

        if orphan_ids:
            errors.append(
                f"{table_name}: {len(orphan_ids)} movie IDs do not exist in films"
            )

    # Check that each film appears exactly once.
    if films["movie_id"].duplicated().any():
        errors.append("films: movie_id is not unique")

    if errors:
        raise ValueError("Data validation failed:\n- " + "\n- ".join(errors))

    return {
        "status": "passed",
        "tables": results,
        "total_films": len(films),
    }
