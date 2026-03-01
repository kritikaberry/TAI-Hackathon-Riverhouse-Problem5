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

## 🌐 Streamlit — Data Visualization : (#-https://aiidsdatahouse.streamlit.app)

- **Live dashboard** from the Master Dataset (no spreadsheets required)
- **Filters + search:** time, domain, severity, sector, geography, AI tech, status, source + keyword search
- **Impact & speed lenses:** lives lost/injuries thresholds, turnaround time, time-to-vet
- **KPI tiles:** totals, high-harm (heuristic), usable %, avg/median times, open/pending, YoY shifts
- **Decision views:** risk heatmap, time-to-vet leaders/laggards, human-impact bubble/scatter
- **Trends & themes:** yearly volume, severity mix, pies, word cloud
- **Export & share:** filtered table → CSV download + one Streamlit Cloud link

---

## 🤖 Ask a Question - Query the Database with Custom LLM

- Ask in plain English; no SQL needed  
- Gemini maps your question to dataset filters/columns. Any user from any background can query as per their requirement. For instance, "What is the highest concern in ai incidents with impact to humans?". 
- Shows results in a data table + SQL query

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
