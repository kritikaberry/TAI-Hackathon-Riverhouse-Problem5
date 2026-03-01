# AI Incident Database (AIID) Master Dataset Builder

> **One-click pipeline to transform fragmented AI incident reports into a clean, analysis-ready Master Dataset.**  
> Built for researchers, policy teams, and analysts who want insights.

---

## 📋 Table of Contents
- [✨ Quick Start](#-quick-start)
- [📦 What's Included](#-whats-included)
- [🛠️ How to Customize](#-how-to-customize)
- [🔍 Key Features](#-key-features)
- [❓ Support & Documentation](#-support--documentation)

---

## ✨ Quick Start

Choose the tool that fits your workflow:

| Tool | Best For | Link |
|------|----------|------|
| **🔄 Data Pipeline** | Download & build the latest Master Dataset from scratch | [Open in Google Colab](https://drive.google.com/file/d/1CCEmcRsECJjxkxj6UJQOqFn-3c7ulu5V/view?usp=drive_link) |
| **📊 Visualizations** | Generate charts & insights from your existing `AIID_Master_Dataset.xlsx` | [Open in Google Colab](https://drive.google.com/file/d/1nM53_u8GWCeAFzoSXLw8tXW74cHeMyDc/view?usp=drive_link) |
| **🌐 Live Dashboard** | Explore consolidated data interactively (no download needed) | [View Streamlit Dashboard](https://your-streamlit-app-link.streamlit.app/) |

### How It Works
1. **Pipeline Notebook**: Visits the official AI Incident Database website → downloads the latest archive → cleans, deduplicates, and merges source files → exports a polished Excel workbook.
2. **Visualization Notebook**: Upload your Master Dataset → instantly generate trend charts, risk domain breakdowns, and harm analytics.
3. **Streamlit Dashboard**: Filter, search, and export insights through a user-friendly web interface.

---

## 📦 What's Included: Dataset Overview

The pipeline intelligently merges **5 source files** from the AI Incident Database using `Incident ID` as the primary key:

| Source File | Key Content | Purpose |
|-------------|-------------|---------|
| `incidents.csv` | Titles, descriptions, involved entities | Core incident records |
| `MIT FutureTech` | Risk domains, intent, deployment timeline | Technical risk classification |
| `GMF (Goals, Methods & Failures)` | AI objectives, failure modes, technical analysis | Root-cause insights |
| `CSETv1` | Harm severity, affected sectors, geographic data | Policy & impact context |
| `duplicates.csv` | Duplicate record identifiers | Automated deduplication |

✅ **Output**: A single, well-structured `AIID_Master_Dataset.xlsx` with consistent formatting and enriched metadata.

---

## 🛠️ How to Customize (No Code Required!)

The pipeline is designed for easy maintenance. All configuration lives in **Cell 1: ⚙️ Configuration**.

### 🔁 If a source column is renamed:

# Update the COLUMNS mapping dictionary
`
COLUMNS = {
    "old_source_column_name": "master_column_name",  # ← Change left side only
    ...
}
`

### ➕ To add a new field:
1. Add the column to the relevant source dictionary in `COLUMNS`
2. Include it in the `MASTER_COLUMN_ORDER` list to control output sequence

### 🩺 Schema Health Check (Cell 4)
- Automatically detects missing or unexpected columns
- Warns *before* processing begins—no silent failures
- Helps you adapt quickly to AIID updates

> 💡 **Pro Tip**: Always run Cell 4 first when updating the pipeline to validate compatibility.

---

## 🔍 Key Features

| Feature | Benefit |
|---------|---------|
| **🤖 Fully Automated Scraping** | Fetches the latest AIID archive—no manual downloads |
| **🔍 Data Provenance Tracking** | Every row includes a `Data Sources` flag showing which research team contributed the classification |
| **📄 Polished Excel Export** | Includes: (1) Master dataset, (2) Plain-English data dictionary, (3) Source coverage map |
| **🧹 Smart Data Cleaning** | Standardizes dates, removes numeric prefixes (e.g., "1. Bias"), and normalizes internal codes |
| **🛡️ Future-Proof Design** | Configuration-driven architecture adapts to schema changes without code rewrites |

---

## 🌐 Streamlit — Data Visualization

Streamlit turns the Master Dataset into a **live, interactive dashboard** in the browser. **Sidebar filters** let users narrow by year range, harm/risk domain, severity, sector, region, country, AI technology, status, and data source; a free-text search runs over titles and descriptions, and **impact filters** restrict to incidents with lives lost or injuries (with minimum thresholds) or by turnaround (occurred → resolved) and time-to-vet (submit → publish) in days. A **Key metrics** row shows total incidents, high-harm count (heuristic), lives lost and injuries (sums and counts), usable data percentage, average and median turnaround and vet time, and pending/open count, with year-over-year change where applicable. A **decision-maker** block offers an **executive risk heatmap** (incident counts by harm domain vs sector or technology), **time to vet** (average days by sector plus the slowest incidents), and a **human-impact** scatter (sector vs lives lost + injuries, sized by incident count). **Trends** include incident volume by year (line chart) and severity/harm-level distribution (bar). **Charts** add pie views by sector and by severity. When the dataset has a source field, **Incidents by data source** gives separate breakdowns for MIT, GMF, and CSET (year trends, top sectors, harm domain, severity). A **word cloud** is built from problem-description text to surface recurring themes. The **Incidents (filtered)** table shows the current filter set with a configurable row limit (100 / 250 / 500 / 1000 / All) and a **Download filtered incidents (CSV)** button. Deploy to Streamlit Community Cloud to share one URL so researchers and policy teams can explore and export the data without opening Excel or Colab.

---

## 🤖 Ask a Question (Gemini / SQL-like Query)

The **Ask a question (Gemini)** feature adds **natural-language search** over the same dataset. Users type a question in plain English (e.g. *“Show me healthcare incidents with high severity”* or *“Which sectors have the most lives lost?”*); the app sends it to the **query handler**, which uses Google’s Gemini API to interpret the question, map it to the dataset’s columns and filters, and produce a query plan. That plan is executed on the loaded DataFrame and the **result table** is shown below; an expandable **Query plan (SQL-like)** section shows the logic so users can see how the answer was built. No pre-built filters or charts are required—the AI bridges “what I want to know” and “what the data can answer.” For deployment, the Gemini API key is set in the app’s **Settings → Secrets** as `google_api_key` so the feature works in production without hardcoding keys in the repo.
---

## ❓ Support & Documentation

📚 **Full Documentation**:  
For limitations, methodology notes, and FAQ, see the [AIID Master Dataset Guide](https://docs.google.com/document/d/1WzPJILZaSqp_xKALNayNcByV_Q9XE-_4/edit?usp=drive_link&ouid=112845759301634096831&rtpof=true&sd=true).

🛠️ **Troubleshooting Tips**:
- Ensure you're signed into Google to access Colab notebooks
- If links don't open, copy/paste the URL directly into your browser
- For dashboard access issues, verify the Streamlit app is publicly deployed

💬 **Have feedback or need help?**  
Reach out to the project maintainers or open an issue in the repository.

---

> 🎯 **Ready to get started?**  
> Click the [Data Pipeline](https://drive.google.com/file/d/1CCEmcRsECJjxkxj6UJQOqFn-3c7ulu5V/view?usp=drive_link) to build your first Master Dataset in under 5 minutes.

*Last updated: March 2026 | Compatible with Python 3.8+ and Google Colab*
```
