"""
Persist validated StreamVault analytical datasets.
"""

from pathlib import Path

import pandas as pd

from pipeline.checks import validate_transformed_data


def save_datasets(data: dict, output_dir: Path) -> dict:
    """
    Validate and save analytical DataFrames as Parquet files.

    Returns a dictionary mapping dataset names to output paths.
    """

    # Prevent invalid datasets from being persisted.
    validate_transformed_data(data)

    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = {}

    for dataset_name, frame in data.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{dataset_name} must be a pandas DataFrame")

        output_path = output_dir / f"{dataset_name}.parquet"

        frame.to_parquet(
            output_path,
            engine="pyarrow",
            index=False,
        )

        output_paths[dataset_name] = output_path

    return output_paths
