## AI Incident Database (AIID) Master Dataset Builder

This project provides an automated pipeline to consolidate multiple, unstructured AI incident datasets into a single, clean, and comprehensive **Master Dataset**. It is designed for researchers, policy teams, and analysts to explore AI safety records without manual data wrangling.

---

### 🚀 Access the Tools

Depending on your needs, you can run the data pipeline, visualize existing data, or explore the live dashboard.

#### **1. Data Pipeline (Google Colab)**

Use this to download the latest raw data from AIID and build your own Master Dataset.

* **Action:** [](https://drive.google.com/file/d/1CCEmcRsECJjxkxj6UJQOqFn-3c7ulu5V/view?usp=drive_link)
* 
**How it works:** This notebook visits the AIID website, downloads the latest archive, cleans the files, and joins them into one Excel spreadsheet.



#### **2. Visualizations (Google Colab)**

Use this if you already have a Master Dataset and want to generate automated charts and insights.

* **Action:** [](https://drive.google.com/file/d/1nM53_u8GWCeAFzoSXLw8tXW74cHeMyDc/view?usp=drive_link)
* **How it works:** Upload your `AIID_Master_Dataset.xlsx` file to the notebook to see growth trends, top risk domains, and harm rate analytics.

#### **3. Interactive Dashboard (Streamlit)**

Explore the consolidated data in a live, web-based interface.

* **Action:** **[View Live Streamlit Dashboard](https://www.google.com/search?q=https://your-streamlit-app-link.streamlit.app/)**

---

### 📦 Dataset Overview

The pipeline joins five key files from the **AI Incident Database** using the **Incident ID** as the common link:

* 
**incidents.csv**: The backbone containing titles, descriptions, and entities involved.


* 
**MIT FutureTech**: Risk domains, intent, and deployment timing.


* 
**GMF (Goals, Methods & Failures)**: Technical analysis of AI goals and failure modes.


* 
**CSETv1**: Policy details including harm levels, sectors, and geographic location.


* 
**duplicates.csv**: Used to automatically filter out duplicate records.



---

### 🛠️ Configuration & Updates

If the AIID team renames a column or adds new fields, you can update the pipeline without writing new code. All settings live in **Cell 1 (⚙️ Configuration)**:

* 
**Renamed Columns**: If a source column is renamed, update the left side of the mapping in the `COLUMNS` dictionary.


* 
**New Columns**: To include new data, add the column name to the relevant dictionary and the `MASTER_COLUMN_ORDER` list.


* 
**Schema Health Check**: Cell 4 proactively flags missing or new columns before processing, preventing silent failures.



---

### 🔍 Key Features

* 
**Automated Pipeline**: Scrapes the AIID website to find and download the latest data snapshot automatically.


* 
**Data Provenance**: Includes a `Data Sources` flag for every row, showing which research teams classified that incident.


* 
**Formatted Excel Export**: Generates a workbook with the full dataset, a plain-English data dictionary, and a coverage map.


* 
**Data Cleaning**: Automatically standardizes dates, removes numeric prefixes from labels, and cleans internal code names.



---

### 📖 Documentation & Support

For detailed information on limitations, assumptions, and a full FAQ, please refer to the [AIID Documentation]([https://www.google.com/search?q=./AIID_Documentation.docx](https://docs.google.com/document/d/1WzPJILZaSqp_xKALNayNcByV_Q9XE-_4/edit?usp=drive_link&ouid=112845759301634096831&rtpof=true&sd=true)).

Would you like me to generate a summary table of the most common columns that will appear in your Master Dataset?
