import logging

from pipeline.config import OUTPUT_DIR, require_api_key
from pipeline.ingest import load_candidate_ids, report_candidate_ids
from pipeline.extract import (
    DETAILS_CACHE_DIR,
    CREDITS_CACHE_DIR,
    create_session,
    extract_candidates,
    summarize_acquisition,
    build_reconciliation_report,
    save_extraction_outputs,
)
from pipeline.transform import transform_cached_data
from pipeline.checks import validate_transformed_data
from pipeline.load import save_datasets


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

    logger.info("Pipeline completed successfully.")

    for dataset, path in saved_files.items():
        logger.info("%s saved to %s", dataset, path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
