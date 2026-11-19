"""
StreamVault analytical data transformation.

Transforms successful cached TMDb details and credits responses
into five normalized pandas DataFrames.
"""

import json
from pathlib import Path

import pandas as pd


def load_cache_records(cache_dir: Path) -> dict:
    """Load cached JSON responses, indexed by movie ID."""

    records = {}

    for file_path in sorted(cache_dir.glob("*.json")):
        with file_path.open("r", encoding="utf-8") as file:
            cached_record = json.load(file)

        movie_id = int(cached_record["movie_id"])
        data = cached_record["data"]

        if int(data["id"]) != movie_id:
            raise ValueError(
                f"Cache ID mismatch in {file_path.name}: "
                f"wrapper={movie_id}, payload={data['id']}"
            )

        if movie_id in records:
            raise ValueError(f"Duplicate cached movie ID: {movie_id}")

        records[movie_id] = data

    return records


def transform_cached_data(
    details_dir: Path,
    credits_dir: Path,
) -> dict:
    """
    Transform cached TMDb responses into normalized DataFrames.

    Returns:
        Dictionary containing films, cast, crew,
        film_genres, and film_companies.
    """

    details_records = load_cache_records(details_dir)
    credits_records = load_cache_records(credits_dir)

    # Both endpoints must be available for an analysed movie.
    details_ids = set(details_records)
    credits_ids = set(credits_records)

    if details_ids != credits_ids:
        missing_credits = sorted(details_ids - credits_ids)
        missing_details = sorted(credits_ids - details_ids)

        raise ValueError(
            "Details and credits populations do not match. "
            f"Missing credits: {missing_credits}; "
            f"missing details: {missing_details}"
        )

    film_rows = []
    cast_rows = []
    crew_rows = []
    genre_rows = []
    company_rows = []

    for movie_id, details in details_records.items():
        credits = credits_records[movie_id]

        if int(credits["id"]) != movie_id:
            raise ValueError(f"Credits payload ID mismatch for movie {movie_id}")

        # Film-level attributes: exactly one row per movie.
        collection = details.get("belongs_to_collection")

        film_rows.append(
            {
                "movie_id": movie_id,
                "title": details.get("title"),
                "original_title": details.get("original_title"),
                "poster_path": details.get("poster_path"),
                "backdrop_path": details.get("backdrop_path"),
                "release_date": details.get("release_date"),
                "release_year": (
                    int(details["release_date"][:4])
                    if details.get("release_date")
                    and details["release_date"][:4].isdigit()
                    else pd.NA
                ),
                "budget": details.get("budget"),
                "revenue": details.get("revenue"),
                "popularity": details.get("popularity"),
                "vote_average": details.get("vote_average"),
                "vote_count": details.get("vote_count"),
                "runtime": details.get("runtime"),
                "original_language": details.get("original_language"),
                "status": details.get("status"),
                "homepage": details.get("homepage"),
                "collection_id": collection.get("id") if collection else None,
                "collection_name": collection.get("name") if collection else None,
                "belongs_to_collection": collection,
            }
        )

        # One row per movie-cast credit.
        for credit in credits.get("cast", []):
            cast_rows.append(
                {
                    "movie_id": movie_id,
                    **credit,
                }
            )

        # One row per movie-crew credit.
        for credit in credits.get("crew", []):
            crew_rows.append(
                {
                    "movie_id": movie_id,
                    **credit,
                }
            )

        # One row per movie-genre association.
        for genre in details.get("genres", []):
            genre_rows.append(
                {
                    "movie_id": movie_id,
                    **genre,
                }
            )

        # One row per movie-production-company association.
        for company in details.get("production_companies", []):
            company_rows.append(
                {
                    "movie_id": movie_id,
                    **company,
                }
            )

    # Construct normalized DataFrames.
    films = pd.DataFrame(film_rows)
    cast = pd.DataFrame(cast_rows)
    crew = pd.DataFrame(crew_rows)
    film_genres = pd.DataFrame(genre_rows)
    film_companies = pd.DataFrame(company_rows)

    # Apply consistent nullable integer types.
    films["release_year"] = films["release_year"].astype("Int64")

    return {
        "films": films,
        "cast": cast,
        "crew": crew,
        "film_genres": film_genres,
        "film_companies": film_companies,
    }
