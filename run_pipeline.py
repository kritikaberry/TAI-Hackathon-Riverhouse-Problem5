"""Entry-point script for modular CSET notebook refactor."""

from __future__ import annotations

from pathlib import Path

from analysis import run_all_analyses
from data_utils import load_dataset
from preprocess import preprocess_data


def main() -> None:
    raw = load_dataset("dataset/classifications_CSETv1.csv")
    clean = preprocess_data(raw)

    Path("outputs").mkdir(exist_ok=True)
    clean.to_csv("outputs/csetv1_cleaned_refactored.csv", index=False)

    run_all_analyses(clean, output_dir=Path("outputs/figures"), show=False)
    print("Saved cleaned data to outputs/csetv1_cleaned_refactored.csv")
    print("Saved charts to outputs/figures/")


if __name__ == "__main__":
    main()
