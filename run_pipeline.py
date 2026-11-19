import logging

from pipeline.analyze import (
    calculate_film_metrics,
    load_analytical_data,
    rank_franchise_collections,
    rank_standalone_titles,
)
from pipeline.checks import validate_transformed_data
from pipeline.config import OUTPUT_DIR, require_api_key
from pipeline.extract import (
    CREDITS_CACHE_DIR,
    DETAILS_CACHE_DIR,
    build_reconciliation_report,
    create_session,
    extract_candidates,
    save_extraction_outputs,
    summarize_acquisition,
)
from pipeline.ingest import load_candidate_ids, report_candidate_ids
from pipeline.load import save_datasets
from pipeline.transform import transform_cached_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Execute the complete StreamVault data pipeline."""

    logger.info("Starting StreamVault pipeline.")

    # 1. Validate configuration.
    require_api_key()

    # 2. Ingest and audit candidate IDs.
    candidates = load_candidate_ids()
    report_candidate_ids(candidates)

    # 3. Extract TMDb details and credits.
    DETAILS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CREDITS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    session = create_session()

    try:
        results = extract_candidates(candidates, session)
    finally:
        session.close()

    # 4. Summarize and reconcile acquisition results.
    summary = summarize_acquisition(results)

    reconciliation = build_reconciliation_report(
        candidates,
        results,
    )

    save_extraction_outputs(summary, reconciliation)

    logger.info("Acquisition stage completed.")

    # 5. Transform cached data into analytical datasets.
    datasets = transform_cached_data(
        DETAILS_CACHE_DIR,
        CREDITS_CACHE_DIR,
    )

    # 6. Validate transformed datasets.
    validation_report = validate_transformed_data(datasets)
    logger.info("Validation report: %s", validation_report)

    # 7. Persist validated datasets as Parquet.
    saved_files = save_datasets(datasets, OUTPUT_DIR)

    logger.info("Analytical datasets saved successfully.")

    for dataset, path in saved_files.items():
        logger.info("%s saved to %s", dataset, path)

    # 8. Load persisted analytical datasets.
    analytical_data = load_analytical_data(OUTPUT_DIR)

    # 9. Calculate film-level analytical metrics.
    films = calculate_film_metrics(analytical_data["films"])

    # 10. Create the 2000-onward comparison dataset.
    recent_films = films.loc[films["release_year"] >= 2000].copy()

    # 11. Generate franchise and standalone rankings.
    rankings = {
        "franchise_rankings_all_years": (rank_franchise_collections(films)),
        "franchise_rankings_2000_onward": (rank_franchise_collections(recent_films)),
        "standalone_rankings_all_years": (rank_standalone_titles(films)),
        "standalone_rankings_2000_onward": (rank_standalone_titles(recent_films)),
    }

    # 12. Export decision-support results.
    for name, ranking in rankings.items():
        output_path = OUTPUT_DIR / f"{name}.csv"

        ranking.to_csv(
            output_path,
            index=False,
        )

        logger.info(
            "%s exported: %s rows -> %s",
            name,
            len(ranking),
            output_path,
        )

    logger.info("Decision-support analysis completed successfully.")

    logger.info("StreamVault pipeline completed successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
