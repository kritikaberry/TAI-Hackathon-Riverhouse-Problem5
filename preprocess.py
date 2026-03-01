"""Data cleaning/preprocessing for CSET analytics."""

from __future__ import annotations

import pandas as pd

from data_utils import parse_yes_no_maybe


TRI_STATE_COLUMNS = [
    "published",
    "quality_control",
    "physical_objects",
    "entertainment_industry",
    "report_test_or_study_of_data",
    "deployed",
    "producer_test_in_controlled_conditions",
    "producer_test_in_operational_conditions",
    "user_test_in_controlled_conditions",
    "user_test_in_operational_conditions",
    "harm_domain",
    "ai_system",
    "clear_link_to_technology",
    "clear_link_to_technology_1",
    "impact_on_critical_services",
    "rights_violation",
    "involving_minor",
    "detrimental_content",
    "protected_characteristic",
    "special_interest_intangible_harm",
    "public_sector_deployment",
    "multiple_ai_interaction",
    "embedded",
    "estimated_date",
    "estimated_harm_quantities",
]

NUMERIC_COLUMNS = [
    "incident_id",
    "incident_number",
    "date_of_incident_year",
    "date_of_incident_day",
    "lives_lost",
    "injuries",
]

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply notebook-equivalent cleaning and feature engineering."""
    clean = df.copy()

    # Trim text fields and normalize empty values.
    obj_cols = clean.select_dtypes(include="object").columns
    for col in obj_cols:
        clean[col] = clean[col].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA})

    # Standardize tri-state fields.
    for col in TRI_STATE_COLUMNS:
        if col in clean.columns:
            clean[col] = parse_yes_no_maybe(clean[col])

    # Convert numeric-like columns.
    for col in NUMERIC_COLUMNS:
        if col in clean.columns:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")

    # Normalize month into numeric month.
    if "date_of_incident_month" in clean.columns:
        month = clean["date_of_incident_month"].astype(str).str.lower().str.strip()
        clean["date_of_incident_month_num"] = pd.to_numeric(month, errors="coerce").fillna(
            month.map(MONTH_MAP)
        )

    # Build estimated incident date when available.
    required = {"date_of_incident_year", "date_of_incident_month_num", "date_of_incident_day"}
    if required.issubset(clean.columns):
        clean["incident_date_estimated"] = pd.to_datetime(
            {
                "year": clean["date_of_incident_year"],
                "month": clean["date_of_incident_month_num"].fillna(1),
                "day": clean["date_of_incident_day"].fillna(1),
            },
            errors="coerce",
        )

    return clean.drop_duplicates().reset_index(drop=True)
