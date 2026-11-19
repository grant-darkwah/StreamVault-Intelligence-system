import pandas as pd
from pipeline.analyze import (
    calculate_film_metrics,
    classify_franchises,
    rank_franchise_collections,
    rank_standalone_titles,
)


def test_calculate_film_metrics_preserves_missing_release_year():
    films = pd.DataFrame(
        {
            "release_year": [1999, 2005, pd.NA],
            "revenue": [100, 200, 300],
            "budget": [50, 100, 150],
        }
    )

    result = calculate_film_metrics(films)

    assert result["release_period"].iloc[0] == "pre_2000"
    assert result["release_period"].iloc[1] == "2000_onward"
    assert pd.isna(result["release_period"].iloc[2])
    assert result["revenue_budget_ratio"].tolist() == [2.0, 2.0, 2.0]


def test_classify_franchises():
    films = pd.DataFrame(
        {
            "movie_id": [1, 2, 3],
            "collection_id": [10, 10, None],
        }
    )

    result = classify_franchises(films)

    assert result["franchise_type"].tolist() == [
        "multi_film_collection",
        "multi_film_collection",
        "standalone",
    ]


def test_rank_standalone_titles_excludes_collection_films():
    films = pd.DataFrame(
        {
            "movie_id": [1, 2, 3],
            "title": ["Film A", "Film B", "Film C"],
            "collection_id": [None, None, 10],
            "vote_average": [8.0, 7.0, 9.0],
            "vote_count": [100, 200, 300],
            "popularity": [10.0, 20.0, 30.0],
            "revenue": [1000, 2000, 3000],
        }
    )

    result = rank_standalone_titles(films)

    assert len(result) == 2
    assert set(result["title"]) == {"Film A", "Film B"}
    assert result["composite_score"].is_monotonic_decreasing


def test_rank_franchise_collections_requires_two_sampled_titles():
    films = pd.DataFrame(
        {
            "movie_id": [1, 2, 3],
            "collection_id": [10, 10, 20],
            "collection_name": ["Collection A", "Collection A", "Collection B"],
            "revenue_budget_ratio": [2.0, 3.0, 4.0],
            "revenue": [1000, 2000, 3000],
            "vote_average": [8.0, 7.0, 9.0],
            "vote_count": [100, 200, 300],
            "popularity": [10.0, 20.0, 30.0],
        }
    )

    result = rank_franchise_collections(films)

    assert len(result) == 1
    assert result.iloc[0]["collection_name"] == "Collection A"
    assert result.iloc[0]["sampled_titles"] == 2
