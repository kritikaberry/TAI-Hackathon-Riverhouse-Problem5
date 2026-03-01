"""Utility helpers for CSET analytics refactor."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_INPUT_PATH = Path("dataset/classifications_CSETv1.csv")


def normalize_col(col: str) -> str:
    """Normalize a column name to snake_case with safe characters."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", col.lower())).strip("_")


def deduplicate_columns(cols: list[str]) -> list[str]:
    """Add numeric suffixes for repeated column names."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)
    return result


def parse_yes_no_maybe(series: pd.Series) -> pd.Series:
    """Standardize mixed boolean/tri-state text into yes/no/maybe."""
    mapper = {
        "yes": "yes",
        "no": "no",
        "maybe": "maybe",
        "true": "yes",
        "false": "no",
        "y": "yes",
        "n": "no",
    }
    normalized = series.astype(str).str.strip().str.lower()
    mapped = normalized.map(mapper)
    return mapped.where(mapped.notna(), normalized.replace("nan", np.nan))


def top_counts(df: pd.DataFrame, col: str, n: int = 10) -> pd.DataFrame:
    """Return top-N value counts for a column."""
    if col not in df.columns:
        return pd.DataFrame(columns=[col, "count"])

    vc = (
        df[col]
        .fillna("missing")
        .astype(str)
        .str.strip()
        .value_counts()
        .head(n)
        .reset_index()
    )
    vc.columns = [col, "count"]
    return vc


def load_dataset(input_path: Path | str = DEFAULT_INPUT_PATH) -> pd.DataFrame:
    """Load the raw CSET dataset with normalized unique columns."""
    df = pd.read_csv(Path(input_path), low_memory=False)
    normalized_cols = [normalize_col(col) for col in df.columns]
    df.columns = deduplicate_columns(normalized_cols)
    return df
