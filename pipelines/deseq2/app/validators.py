import os
import pandas as pd

def validate_file_exists(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

def validate_dataframe_not_empty(df, name):
    if df.empty:
        raise ValueError(f"{name} is empty")

def validate_required_columns(df, columns, name):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")

def validate_numeric_counts(df):
    try:
        df.apply(pd.to_numeric)
    except Exception as e:
        raise ValueError(f"Counts matrix contains non-numeric values: {e}")

def validate_sample_overlap(counts_df, meta_df):
    overlap = counts_df.columns.intersection(meta_df.index)

    if len(overlap) == 0:
        raise ValueError("No overlapping samples between metadata and counts")

def validate_metadata_file(meta_file):

    validate_file_exists(meta_file)

    df = pd.read_csv(meta_file)

    required = ["Sample Name"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Metadata missing required columns: {missing}"
        )