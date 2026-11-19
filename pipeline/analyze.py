from pathlib import Path

import pandas as pd

from pipeline.config import OUTPUT_DIR


def load_analytical_data(output_dir: Path = OUTPUT_DIR) -> dict:
    """Load transformed Parquet datasets for analysis."""

    dataset_names = [
        "films",
        "cast",
        "crew",
        "film_genres",
        "film_companies",
    ]

    datasets = {}

    for name in dataset_names:
        file_path = output_dir / f"{name}.parquet"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required analytical dataset not found: {file_path}"
            )

        datasets[name] = pd.read_parquet(file_path)

    return datasets


def classify_franchises(films: pd.DataFrame) -> pd.DataFrame:
    """Classify films using their TMDb collection membership."""

    result = films.copy()

    collection_counts = (
        result.dropna(subset=["collection_id"])
        .groupby("collection_id")["movie_id"]
        .transform("count")
    )

    result["franchise_type"] = "standalone"

    has_collection = result["collection_id"].notna()

    result.loc[has_collection, "franchise_type"] = "single_film_collection"

    result.loc[
        has_collection & (collection_counts.reindex(result.index).fillna(0) > 1),
        "franchise_type",
    ] = "multi_film_collection"

    return result


def calculate_film_metrics(films: pd.DataFrame) -> pd.DataFrame:
    """Calculate film-level financial and audience indicators."""

    result = films.copy()

    result["revenue_budget_ratio"] = result["revenue"] / result["budget"].where(
        result["budget"] > 0
    )

    result["release_period"] = pd.NA
    result.loc[result["release_year"] < 2000, "release_period"] = "pre_2000"
    result.loc[result["release_year"] >= 2000, "release_period"] = "2000_onward"

    return result


def rank_standalone_titles(films: pd.DataFrame) -> pd.DataFrame:
    """Rank standalone titles using equal-weighted percentile indicators."""

    metrics = ["vote_average", "vote_count", "popularity", "revenue"]

    result = films.loc[films["collection_id"].isna()].copy()

    if result.empty:
        result["composite_score"] = pd.Series(dtype="float64")
        return result

    percentile_ranks = result[metrics].rank(pct=True)
    result["composite_score"] = percentile_ranks.mean(axis=1)

    return result.sort_values(
        ["composite_score", "vote_average", "vote_count"],
        ascending=False,
    )


def rank_franchise_collections(films: pd.DataFrame) -> pd.DataFrame:
    """Rank collections containing at least two sampled titles."""

    metrics = [
        "median_rating",
        "median_votes",
        "median_popularity",
        "median_revenue",
    ]

    collections = (
        films.dropna(subset=["collection_id"])
        .groupby(["collection_id", "collection_name"], as_index=False)
        .agg(
            sampled_titles=("movie_id", "nunique"),
            median_revenue=("revenue", "median"),
            median_ratio=("revenue_budget_ratio", "median"),
            median_rating=("vote_average", "median"),
            median_votes=("vote_count", "median"),
            median_popularity=("popularity", "median"),
        )
    )

    collections = collections.loc[collections["sampled_titles"] >= 2].copy()

    if collections.empty:
        collections["composite_score"] = pd.Series(dtype="float64")
        return collections

    percentile_ranks = collections[metrics].rank(pct=True)
    collections["composite_score"] = percentile_ranks.mean(axis=1)

    return collections.sort_values(
        ["composite_score", "median_rating", "median_votes"],
        ascending=False,
    )
