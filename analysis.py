"""Analysis and plotting routines for CSET dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from data_utils import top_counts


sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update(
    {
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    }
)


def _save_or_show(fig: plt.Figure, output_dir: Path | None, filename: str, show: bool) -> None:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / filename, bbox_inches="tight", dpi=160)
    if show:
        plt.show()
    plt.close(fig)


def run_all_analyses(clean: pd.DataFrame, output_dir: Path | None = Path("outputs/figures"), show: bool = False) -> None:
    """Run modularized chart generation equivalent to the notebook sections."""
    # 1. Incidents over time.
    if "date_of_incident_year" in clean.columns:
        yr = clean["date_of_incident_year"].dropna().astype(int)
        yr_df = yr.value_counts().sort_index().rename_axis("year").reset_index(name="incidents")
        if not yr_df.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=yr_df, x="year", y="incidents", marker="o", linewidth=2, markersize=8, ax=ax)
            ax.set_title("1. AI Incidents Over Time", fontweight="bold")
            ax.set_xlabel("Year")
            ax.set_ylabel("Number of Incidents")
            ax.grid(True, alpha=0.3)
            _save_or_show(fig, output_dir, "01_incidents_over_time.png", show)

    # 2. Tangible harm by sector.
    if {"tangible_harm", "sector_of_deployment"}.issubset(clean.columns):
        tmp = clean[["tangible_harm", "sector_of_deployment"]].dropna()
        tmp = tmp[tmp["tangible_harm"].astype(str).str.len() > 2]
        if not tmp.empty:
            top_sectors = tmp["sector_of_deployment"].value_counts().head(8).index
            tmp = tmp[tmp["sector_of_deployment"].isin(top_sectors)]
            tmp["sector_short"] = tmp["sector_of_deployment"].apply(
                lambda x: (str(x)[:37] + "...") if len(str(x)) > 40 else str(x)
            )
            ct_pct = pd.crosstab(tmp["sector_short"], tmp["tangible_harm"])
            ct_pct = ct_pct.div(ct_pct.sum(axis=1), axis=0) * 100
            fig, ax = plt.subplots(figsize=(11, 6))
            ct_pct.plot(kind="barh", stacked=True, ax=ax, colormap="tab10")
            ax.set_title("2. Harm Type by Sector (%)", fontweight="bold")
            ax.set_xlabel("Percent of incidents in sector")
            ax.set_ylabel("Sector")
            _save_or_show(fig, output_dir, "02_harm_by_sector.png", show)

    # 3. Public sector vs harm level.
    if {"public_sector_deployment", "ai_harm_level"}.issubset(clean.columns):
        ct = pd.crosstab(clean["public_sector_deployment"], clean["ai_harm_level"])
        if ct.size > 0:
            fig, ax = plt.subplots(figsize=(12, 5))
            sns.heatmap(ct, annot=True, fmt="d", cmap="YlGnBu", ax=ax, cbar_kws={"label": "Count"})
            ax.set_title("3. Government vs Private AI: Harm Level", fontweight="bold")
            ax.set_xlabel("AI Harm Level")
            ax.set_ylabel("Public Sector Deployment")
            _save_or_show(fig, output_dir, "03_public_vs_harm_level.png", show)

    # 4. Rights violation & minors over time.
    if {"date_of_incident_year", "rights_violation", "involving_minor"}.issubset(clean.columns):
        tmp = clean[["date_of_incident_year", "rights_violation", "involving_minor"]].copy()
        tmp["year"] = pd.to_numeric(tmp["date_of_incident_year"], errors="coerce")
        tmp = tmp.dropna(subset=["year"])
        agg = tmp.groupby("year", as_index=False).agg(
            rights_pct=("rights_violation", lambda x: (x == "yes").mean() * 100),
            minor_pct=("involving_minor", lambda x: (x == "yes").mean() * 100),
        )
        if not agg.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=agg, x="year", y="rights_pct", marker="o", linewidth=2, label="Rights violation %", ax=ax)
            sns.lineplot(data=agg, x="year", y="minor_pct", marker="s", linewidth=2, label="Involving minor %", ax=ax)
            ax.set_title("4. Human Rights & Minors Over Time", fontweight="bold")
            ax.set_xlabel("Year")
            ax.set_ylabel("Percent of incidents")
            _save_or_show(fig, output_dir, "04_rights_and_minors.png", show)

    # 5. Geographic concentration.
    if "location_region" in clean.columns:
        t = top_counts(clean, "location_region", n=10)
        t = t[t["location_region"].astype(str).str.len() > 2]
        if not t.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=t, y="location_region", x="count", palette="crest", ax=ax)
            ax.set_title("5. Top Incident Regions", fontweight="bold")
            ax.set_xlabel("Number of Incidents")
            ax.set_ylabel("Region")
            _save_or_show(fig, output_dir, "05_top_regions.png", show)
