import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

try:
    from query_handler import policy_data_assistant
except ImportError:
    policy_data_assistant = None  # e.g. google-genai not installed

st.set_page_config(page_title="AI Incident Dashboard", layout="wide")

# Data path (edit if your file is elsewhere)
FILE_PATH = "AI_Incidents_Master_Dataset.xlsx"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    return df

def pick_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def to_year(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series([pd.NA] * 0, dtype="Int64")
    s = series.copy()
    if pd.api.types.is_numeric_dtype(s):
        s = pd.to_numeric(s, errors="coerce")
        s = s.where((s >= 1900) & (s <= 2100))
        return s.astype("Int64")
    dt = pd.to_datetime(s, errors="coerce", utc=False)
    if dt.notna().sum() > 0:
        return dt.dt.year.astype("Int64")
    extracted = s.astype(str).str.extract(r"(\d{4})")[0]
    extracted = pd.to_numeric(extracted, errors="coerce")
    extracted = extracted.where((extracted >= 1900) & (extracted <= 2100))
    return extracted.astype("Int64")

def to_datetime_safe(series: pd.Series) -> pd.Series:
    if series is None or series.empty:
        return pd.Series([pd.NaT] * len(series) if hasattr(series, "__len__") else [])
    return pd.to_datetime(series, errors="coerce", utc=False)

def options_for(df, col):
    if col is None or col not in df.columns:
        return ["All"]
    vals = sorted(df[col].fillna("Unknown").astype(str).unique().tolist())
    return ["All"] + vals

def safe_vc(df, col, topn=20):
    if col is None or col not in df.columns:
        return pd.DataFrame({"label": [], "count": []})
    vc = df[col].fillna("Unknown").astype(str).value_counts().head(topn).reset_index()
    vc.columns = ["label", "count"]
    return vc

# Load data
st.title("AI Incident Dashboard")
df = load_data(FILE_PATH)

# Map columns (tries common names; adjust if your Excel uses different headers)
col_year = pick_col(df, ["Incident Year", "Year", "Occurred Year", "Date", "Occurred Date", "Incident Date"])
col_date_occurred = pick_col(df, ["Occurred Date", "Incident Date", "Date", "Incident Year"])
col_date_reported = pick_col(df, ["Reported Date", "Report Date", "Date Reported", "Publication Date"])
col_date_resolved = pick_col(df, ["Resolution Date", "Resolved Date", "Closed Date", "Date Closed"])
col_date_submit = pick_col(df, ["Submit Date", "Date Submitted", "Submitted Date", "Submission Date"])
col_date_publish = pick_col(df, ["Publish Date", "Publication Date", "Date Published", "Published Date"])
col_harm_level = pick_col(df, ["AI Harm Level", "Harm Level", "Severity", "Priority"])
col_harm_domain = pick_col(df, ["Harm Domain", "Risk Domain", "Risk Subdomain", "Category"])
col_sector = pick_col(df, ["Sector of Deployment", "Sector", "Industry"])
col_region = pick_col(df, ["Location Region", "Region"])
col_country = pick_col(df, ["Country Code", "Country", "Location Country"])
col_tech = pick_col(df, ["AI Technology", "AI System Type", "System Type"])
col_lives = pick_col(df, ["Lives Lost"])
col_injuries = pick_col(df, ["Injuries"])
col_desc = pick_col(df, ["Description", "Incident Description", "Summary", "Title"])
col_problem_desc = pick_col(df, ["Problem Description", "Issue Description", "What went wrong", "Description", "Incident Description", "Summary"])
col_status = pick_col(df, ["Status", "State", "Resolution Status"])
col_source = pick_col(df, ["Source", "Data Source", "Origin"])
col_id = pick_col(df, ["ID", "Incident ID", "Case ID", "Index"])
col_vendor = pick_col(df, ["Company", "Vendor", "Organization", "Developer", "Manufacturer", "Deploying Organization"])

# Remove duplicate rows so filters and metrics use unique incidents
if col_id and col_id in df.columns:
    df = df.drop_duplicates(subset=[col_id], keep="first").reset_index(drop=True)
else:
    df = df.drop_duplicates(keep="first").reset_index(drop=True)

df_dash = df.copy()
df_dash["_year"] = to_year(df_dash[col_year]) if col_year else pd.Series([pd.NA] * len(df_dash), dtype="Int64")

# Derived dates and day counts
df_dash["_dt_occurred"] = to_datetime_safe(df_dash[col_date_occurred]) if col_date_occurred else pd.Series([pd.NaT] * len(df_dash))
df_dash["_dt_reported"] = to_datetime_safe(df_dash[col_date_reported]) if col_date_reported else pd.Series([pd.NaT] * len(df_dash))
df_dash["_dt_resolved"] = to_datetime_safe(df_dash[col_date_resolved]) if col_date_resolved else pd.Series([pd.NaT] * len(df_dash))
df_dash["_turnaround_days"] = np.nan
if col_date_resolved and df_dash["_dt_resolved"].notna().any():
    df_dash["_turnaround_days"] = (df_dash["_dt_resolved"] - df_dash["_dt_occurred"]).dt.days
elif col_date_reported and df_dash["_dt_reported"].notna().any():
    df_dash["_turnaround_days"] = (df_dash["_dt_reported"] - df_dash["_dt_occurred"]).dt.days
df_dash["_reporting_lag_days"] = np.nan
if col_date_reported and col_date_occurred and df_dash["_dt_reported"].notna().any() and df_dash["_dt_occurred"].notna().any():
    df_dash["_reporting_lag_days"] = (df_dash["_dt_reported"] - df_dash["_dt_occurred"]).dt.days
df_dash["_dt_submit"] = to_datetime_safe(df_dash[col_date_submit]) if col_date_submit else pd.Series([pd.NaT] * len(df_dash))
df_dash["_dt_publish"] = to_datetime_safe(df_dash[col_date_publish]) if col_date_publish else pd.Series([pd.NaT] * len(df_dash))
df_dash["_vet_days"] = np.nan
if col_date_submit and col_date_publish and df_dash["_dt_submit"].notna().any() and df_dash["_dt_publish"].notna().any():
    df_dash["_vet_days"] = (df_dash["_dt_publish"] - df_dash["_dt_submit"]).dt.days
has_vet = pd.notna(df_dash["_vet_days"]).any()

for c in [col_lives, col_injuries]:
    if c is not None and c in df_dash.columns:
        df_dash[c] = pd.to_numeric(df_dash[c], errors="coerce")

years = sorted([y for y in df_dash["_year"].dropna().unique().tolist()])
ymin = int(min(years)) if years else 2000
ymax = int(max(years)) if years else 2026

# Sidebar filters
st.sidebar.header("Filters")

year_range = st.sidebar.slider("Year range", min_value=ymin, max_value=ymax, value=(ymin, ymax), step=1)

domain_sel = st.sidebar.multiselect("Harm/Risk domain", options=options_for(df_dash, col_harm_domain), default=["All"])
level_sel = st.sidebar.multiselect("Harm level / Severity", options=options_for(df_dash, col_harm_level), default=["All"])
sector_sel = st.sidebar.multiselect("Sector", options=options_for(df_dash, col_sector), default=["All"])
region_sel = st.sidebar.multiselect("Region", options=options_for(df_dash, col_region), default=["All"])
country_sel = st.sidebar.multiselect("Country", options=options_for(df_dash, col_country), default=["All"])
tech_sel = st.sidebar.multiselect("AI Technology", options=options_for(df_dash, col_tech), default=["All"])
if col_status:
    status_sel = st.sidebar.multiselect("Status", options=options_for(df_dash, col_status), default=["All"])
else:
    status_sel = ["All"]
if col_source:
    source_sel = st.sidebar.multiselect("Source", options=options_for(df_dash, col_source), default=["All"])
else:
    source_sel = ["All"]

search_text = st.sidebar.text_input("Search text (title/description)", value="")

st.sidebar.subheader("Impact filters")
has_casualties = st.sidebar.checkbox("Only incidents with lives lost or injuries", value=False)
min_lives = st.sidebar.number_input("Min lives lost", min_value=0, value=0, step=1)
min_injuries = st.sidebar.number_input("Min injuries", min_value=0, value=0, step=1)

has_turnaround = pd.notna(df_dash["_turnaround_days"]).any()
turnaround_range = (0, 365)
if has_turnaround:
    tmin = int(df_dash["_turnaround_days"].min()) if pd.notna(df_dash["_turnaround_days"].min()) else 0
    tmax = int(df_dash["_turnaround_days"].max()) if pd.notna(df_dash["_turnaround_days"].max()) else 365
    turnaround_range = st.sidebar.slider("Turnaround (days)", min_value=max(0, tmin), max_value=min(3650, tmax), value=(max(0, tmin), min(3650, tmax)), step=1)
if has_vet:
    vmin = int(df_dash["_vet_days"].min()) if pd.notna(df_dash["_vet_days"].min()) else 0
    vmax = int(df_dash["_vet_days"].max()) if pd.notna(df_dash["_vet_days"].max()) else 365
    vet_range = st.sidebar.slider("Time to vet (days)", min_value=max(0, vmin), max_value=min(3650, vmax), value=(max(0, vmin), min(3650, vmax)), step=1)
else:
    vet_range = (0, 365)

# Apply filters to get filtered dataframe d
d = df_dash.copy()

if years:
    lo, hi = year_range
    d = d[(d["_year"].isna()) | ((d["_year"] >= lo) & (d["_year"] <= hi))]

def apply_multiselect(col, selected):
    global d
    if col is None or col not in d.columns:
        return
    if selected and "All" not in selected:
        d = d[d[col].fillna("Unknown").astype(str).isin(selected)]

apply_multiselect(col_harm_domain, domain_sel)
apply_multiselect(col_harm_level, level_sel)
apply_multiselect(col_sector, sector_sel)
apply_multiselect(col_region, region_sel)
apply_multiselect(col_country, country_sel)
apply_multiselect(col_tech, tech_sel)
apply_multiselect(col_status, status_sel)
apply_multiselect(col_source, source_sel)

q = (search_text or "").strip().lower()
if q and col_desc and col_desc in d.columns:
    d = d[d[col_desc].fillna("").astype(str).str.lower().str.contains(q, na=False)]

if has_casualties:
    lives_col = d[col_lives] if col_lives and col_lives in d.columns else pd.Series(0, index=d.index)
    inj_col = d[col_injuries] if col_injuries and col_injuries in d.columns else pd.Series(0, index=d.index)
    d = d[((lives_col.fillna(0) > 0) | (inj_col.fillna(0) > 0))]

if col_lives and col_lives in d.columns:
    d = d[d[col_lives].fillna(0) >= min_lives]
if col_injuries and col_injuries in d.columns:
    d = d[d[col_injuries].fillna(0) >= min_injuries]

if has_turnaround and turnaround_range is not None:
    lo_t, hi_t = turnaround_range
    d = d[(d["_turnaround_days"].isna()) | ((d["_turnaround_days"] >= lo_t) & (d["_turnaround_days"] <= hi_t))]
if has_vet and vet_range is not None:
    lo_v, hi_v = vet_range
    d = d[(d["_vet_days"].isna()) | ((d["_vet_days"] >= lo_v) & (d["_vet_days"] <= hi_v))]

# KPIs (only shown when data exists)
total = len(d)
high_harm = int((d[col_harm_level].fillna("").astype(str).str.lower().str.contains("high|severe|critical").sum())) if col_harm_level and col_harm_level in d.columns else None
lives_val = int(np.nansum(d[col_lives])) if col_lives and col_lives in d.columns else None
injuries_val = int(np.nansum(d[col_injuries])) if col_injuries and col_injuries in d.columns else None
required = [c for c in [col_harm_domain, col_harm_level, col_sector, col_region] if c]
usable_pct = (int(d[required].notna().all(axis=1).sum()) / total * 100) if required and total else None
yoy_pct = None
if years and len(years) >= 2:
    lo, hi = year_range
    curr, prev = len(d[(d["_year"] == hi) & d["_year"].notna()]), len(d[(d["_year"] == hi - 1) & d["_year"].notna()])
    if prev: yoy_pct = ((curr - prev) / prev) * 100
with_fatalities = int((d[col_lives].fillna(0) > 0).sum()) if col_lives and col_lives in d.columns else None
with_injuries = int((d[col_injuries].fillna(0) > 0).sum()) if col_injuries and col_injuries in d.columns else None
turnaround_vals = d["_turnaround_days"].dropna()
turnaround_vals = turnaround_vals[(turnaround_vals >= 0) & (turnaround_vals <= 3650)]
avg_turnaround = float(turnaround_vals.mean()) if len(turnaround_vals) > 0 else None
median_turnaround = float(turnaround_vals.median()) if len(turnaround_vals) > 0 else None
vet_vals = d["_vet_days"].dropna()
vet_vals = vet_vals[(vet_vals >= 0) & (vet_vals <= 3650)]
avg_vet = float(vet_vals.mean()) if len(vet_vals) > 0 else None
pending_count = int(d[col_status].fillna("").astype(str).str.lower().str.contains("pending|open|under review|submitted").sum()) if col_status and col_status in d.columns else None

kpi_items = [
    ("Total incidents", f"{total:,}", f"{yoy_pct:+.1f}% YoY" if yoy_pct is not None else None),
    ("High-harm (heuristic)", f"{high_harm:,}", None) if high_harm is not None else None,
    ("Lives lost (sum)", f"{lives_val:,}", None) if lives_val is not None else None,
    ("Injuries (sum)", f"{injuries_val:,}", None) if injuries_val is not None else None,
    ("Usable %", f"{usable_pct:.1f}%", None) if usable_pct is not None else None,
    ("Incidents w/ fatalities", f"{with_fatalities:,}", None) if with_fatalities is not None else None,
    ("Incidents w/ injuries", f"{with_injuries:,}", None) if with_injuries is not None else None,
    ("Avg turnaround (days)", f"{avg_turnaround:.0f}", None) if avg_turnaround is not None else None,
    ("Median turnaround (days)", f"{median_turnaround:.0f}", None) if median_turnaround is not None else None,
    ("With turnaround data", f"{int(turnaround_vals.count()):,}", None) if has_turnaround else None,
    ("Avg time to vet (days)", f"{avg_vet:.0f}", None) if avg_vet is not None else None,
    ("Incidents pending / open", f"{pending_count:,}", None) if pending_count is not None else None,
    ("With vet data", f"{len(vet_vals):,}", None) if has_vet else None,
]
kpi_items = [x for x in kpi_items if x is not None]
if kpi_items:
    st.subheader("Key metrics")
    ncols = 5
    for i in range(0, len(kpi_items), ncols):
        cols = st.columns(ncols)
        for j, c in enumerate(cols):
            idx = i + j
            if idx < len(kpi_items):
                label, val, delta = kpi_items[idx]
                c.metric(label, val, delta=delta)
    st.divider()

# Decision-maker section (risk heatmap, time to vet, human impact)
has_risk_heatmap = col_harm_domain and (col_sector or col_tech)
if has_risk_heatmap:
    axis_domain = col_sector if col_sector else col_tech
    heat_df = d.dropna(subset=[col_harm_domain, axis_domain])
    heat_df = heat_df[heat_df[col_harm_domain].astype(str).str.strip() != ""]
    heat_df = heat_df[heat_df[axis_domain].astype(str).str.strip() != ""]
    has_risk_heatmap = not heat_df.empty
if has_risk_heatmap:
    st.subheader("For decision-makers: risk, discovery lag, human impact, and accountability")
    st.caption("These views translate AI incident data into business and societal risk—for boards, policymakers, and procurement.")
    with st.expander("1. Executive risk exposure — Where could AI failures hit the business?", expanded=True):
        st.markdown("*Translate abstract AI failures into concrete business risk.*")
        top_harms = heat_df[col_harm_domain].fillna("Unknown").astype(str).value_counts().head(12).index.tolist()
        top_domains = heat_df[axis_domain].fillna("Unknown").astype(str).value_counts().head(12).index.tolist()
        heat_df = heat_df[heat_df[col_harm_domain].astype(str).isin(top_harms) & heat_df[axis_domain].astype(str).isin(top_domains)]
        pivot = heat_df.groupby([axis_domain, col_harm_domain]).size().unstack(fill_value=0)
        fig = px.imshow(pivot, labels=dict(x="Type of harm", y="AI domain (sector/technology)", color="Incidents"), aspect="auto", color_continuous_scale="Reds", text_auto="d")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

vet_days = d["_vet_days"].dropna()
vet_days = vet_days[(vet_days >= 0) & (vet_days <= 3650)]
if len(vet_days) > 0:
    if not has_risk_heatmap:
        st.subheader("For decision-makers")
    with st.expander("2. Time to vet the incident — How long from submit to publish?", expanded=True):
        st.markdown("*Time from submit until published.*")
        if col_sector and col_sector in d.columns:
            vet_by_sector = d[d["_vet_days"].notna() & (d["_vet_days"] >= 0) & (d["_vet_days"] <= 3650)].groupby(col_sector)["_vet_days"].agg(["mean", "count"]).reset_index()
            vet_by_sector = vet_by_sector[vet_by_sector["count"] >= 1].sort_values("mean", ascending=True).tail(12)
            if not vet_by_sector.empty:
                fig = px.bar(vet_by_sector, x="mean", y=col_sector, orientation="h", labels=dict(mean="Avg days (submit → publish)", x=col_sector))
                fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        lag_incidents = d[d["_vet_days"].notna() & (d["_vet_days"] >= 0)].copy().nlargest(20, "_vet_days")
        lag_incidents["_label"] = lag_incidents[col_desc].fillna("").astype(str).str[:50] + "…" if col_desc and col_desc in lag_incidents.columns else ("Incident #" + lag_incidents.index.astype(str))
        fig2 = px.bar(lag_incidents, y="_label", x="_vet_days", orientation="h", labels=dict(_vet_days="Days (submit → publish)", _label="Incident"))
        fig2.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"), xaxis_title="Time to vet (days)")
        st.plotly_chart(fig2, use_container_width=True)

has_human_impact = False
if col_sector and col_sector in d.columns:
    sector_grp = d.groupby(d[col_sector].fillna("Unknown").astype(str))
    agg = sector_grp.size().reset_index(name="incident_count").rename(columns={col_sector: "sector"})
    if col_lives and col_lives in d.columns:
        lives_grp = sector_grp[col_lives].sum().reset_index()
        lives_grp = lives_grp.rename(columns={lives_grp.columns[0]: "sector", col_lives: "lives_lost"})
        agg = agg.merge(lives_grp[["sector", "lives_lost"]], on="sector", how="left")
    else:
        agg["lives_lost"] = 0
    if col_injuries and col_injuries in d.columns:
        inj_grp = sector_grp[col_injuries].sum().reset_index()
        inj_grp = inj_grp.rename(columns={inj_grp.columns[0]: "sector", col_injuries: "injuries"})
        agg = agg.merge(inj_grp[["sector", "injuries"]], on="sector", how="left")
    else:
        agg["injuries"] = 0
    agg["lives_lost"] = agg["lives_lost"].fillna(0)
    agg["injuries"] = agg["injuries"].fillna(0)
    agg["human_impact"] = agg["lives_lost"] + agg["injuries"]
    agg = agg[agg["sector"] != "Unknown"].head(20)
    has_human_impact = not agg.empty
    if has_human_impact:
        with st.expander("3. Human impact — Who is affected by AI failures?", expanded=True):
            st.markdown("*Sectors and physical harm (lives lost, injuries).*")
            fig = px.scatter(agg, x="sector", y="human_impact", size="incident_count", color="incident_count", hover_data=["lives_lost", "injuries"], size_max=45)
            fig.update_layout(height=400, xaxis_tickangle=-45, margin=dict(l=10, r=10, t=10, b=80), yaxis_title="Lives lost + injuries (sum)", xaxis_title="Sector")
            st.plotly_chart(fig, use_container_width=True)

if has_risk_heatmap or len(vet_days) > 0 or has_human_impact:
    st.divider()

# Trends: volume by year and severity bar
if years:
    g = d.dropna(subset=["_year"]).groupby("_year").size().reset_index(name="count")
    if not g.empty:
        st.subheader("Trends")
        left, right = st.columns(2)
        with left:
            st.markdown("**Incident volume by year**")
            fig = px.line(g, x="_year", y="count", markers=True)
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Year")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            if col_harm_level:
                vc = safe_vc(d, col_harm_level, topn=15)
                if not vc.empty:
                    st.markdown("**Severity / harm level**")
                    fig = px.bar(vc, x="count", y="label", orientation="h")
                    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
        st.divider()

# Pie charts: sector and severity
p1, p2 = None, None
if col_sector and col_sector in d.columns:
    vc = d[col_sector].fillna("Unknown").astype(str).value_counts().head(10).reset_index()
    vc.columns = ["label", "count"]
    if not vc.empty and vc["count"].sum() > 0:
        p1 = ("By sector", vc)
if col_harm_level and col_harm_level in d.columns:
    vc = d[col_harm_level].fillna("Unknown").astype(str).value_counts().head(10).reset_index()
    vc.columns = ["label", "count"]
    if not vc.empty and vc["count"].sum() > 0:
        p2 = ("By severity", vc)

if p1 or p2:
    st.subheader("Charts")
    c1, c2 = st.columns(2)
    if p1:
        with c1:
            st.markdown("**By sector**")
            fig = px.pie(p1[1], values="count", names="label", title=None)
            fig.update_layout(height=300, margin=dict(l=5, r=5, t=5, b=5), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    if p2:
        with c2:
            st.markdown("**By severity**")
            fig = px.pie(p2[1], values="count", names="label", title=None)
            fig.update_layout(height=300, margin=dict(l=5, r=5, t=5, b=5), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    st.divider()

# By source (MIT, GMF, CSET) when Source column exists
if col_source and col_source in d.columns:
    src_upper = d[col_source].fillna("").astype(str).str.upper()
    d_mit = d[src_upper.str.contains("MIT")]
    d_gmf = d[src_upper.str.contains("GMF")]
    d_cset = d[src_upper.str.contains("CSET")]

    def _render_source_section(label: str, dx: pd.DataFrame) -> None:
        if dx.empty:
            return
        st.subheader(f"By source: {label}")
        st.caption(f"{len(dx):,} incidents from this source.")
        c1, c2 = st.columns(2)
        with c1:
            if "_year" in dx.columns and dx["_year"].notna().any():
                g = dx.dropna(subset=["_year"]).groupby("_year").size().reset_index(name="count")
                if not g.empty:
                    fig = px.line(g, x="_year", y="count", markers=True)
                    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), title=f"{label} — Incidents by year")
                    st.plotly_chart(fig, use_container_width=True)
            if col_sector and col_sector in dx.columns:
                vc = dx[col_sector].fillna("Unknown").astype(str).value_counts().head(10).reset_index()
                vc.columns = ["label", "count"]
                if not vc.empty:
                    fig = px.bar(vc, x="count", y="label", orientation="h")
                    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), title=f"{label} — Top sectors", yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
        with c2:
            if col_harm_domain and col_harm_domain in dx.columns:
                vc = dx[col_harm_domain].fillna("Unknown").astype(str).value_counts().head(10).reset_index()
                vc.columns = ["label", "count"]
                if not vc.empty:
                    fig = px.bar(vc, x="count", y="label", orientation="h")
                    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), title=f"{label} — Harm domain", yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
            if col_harm_level and col_harm_level in dx.columns:
                vc = dx[col_harm_level].fillna("Unknown").astype(str).value_counts().head(8).reset_index()
                vc.columns = ["label", "count"]
                if not vc.empty:
                    fig = px.pie(vc, values="count", names="label", title=f"{label} — Severity")
                    fig.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)

    if not d_mit.empty or not d_gmf.empty or not d_cset.empty:
        st.subheader("Incidents by data source")
        if not d_mit.empty:
            _render_source_section("MIT", d_mit)
            st.divider()
        if not d_gmf.empty:
            _render_source_section("GMF", d_gmf)
            st.divider()
        if not d_cset.empty:
            _render_source_section("CSET", d_cset)
            st.divider()

# Word cloud from problem/description text
if col_problem_desc:
    text = " ".join(d[col_problem_desc].fillna("").astype(str).tolist()).strip()
    if len(text) > 20:
        st.subheader("Word cloud — what goes wrong (problem descriptions)")
        wc = WordCloud(width=1400, height=500, background_color="white", collocations=False).generate(text)
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
        st.caption("Built from the field that explains the problem.")
        st.divider()

# Filtered incidents table and export
st.subheader("Incidents (filtered)")
candidates = [col_id, "_year", col_harm_level, col_harm_domain, col_sector, col_region, col_country, col_tech, col_status, col_lives, col_injuries, "_turnaround_days", col_desc]
table_cols = [c for c in candidates if c and (c in d.columns or c in ("_year", "_turnaround_days"))]

display_df = d[table_cols].copy()
if "_turnaround_days" in display_df.columns:
    display_df["_turnaround_days"] = display_df["_turnaround_days"].apply(lambda x: f"{x:.0f}" if pd.notna(x) and x == x else "")

table_size = st.selectbox("Rows to show", [100, 250, 500, 1000, "All"], index=2)
n_show = len(display_df) if table_size == "All" else int(table_size)
st.dataframe(display_df.head(n_show), use_container_width=True)

# Export
csv = display_df.head(10000).to_csv(index=False)
st.download_button("Download filtered incidents (CSV)", data=csv, file_name="ai_incidents_filtered.csv", mime="text/csv")

st.divider()

# Gemini query: one text box, result table below
st.subheader("Ask a question (Gemini)")
st.caption("Enter a question about the incidents; the result table appears below. (API key: set in Streamlit Secrets when deployed, or in query_handler.py for local runs.)")
query_text = st.text_input("Your query", placeholder="e.g. Show me incidents in healthcare with high severity", key="gemini_query")
# Use API key from Streamlit Secrets (deploy) or None so query_handler uses its default (local)
_gemini_key = None
try:
    _gemini_key = st.secrets.get("google_api_key") or (st.secrets.get("api") or {}).get("google_api_key")
except Exception:
    pass
if st.button("Run query"):
    if policy_data_assistant is None:
        st.error("Gemini support not installed. Run: **pip install google-genai** then restart the app.")
    elif not (query_text or "").strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Running query…"):
            try:
                # Pass API key from Streamlit Secrets (_gemini_key) into query_handler
                out = policy_data_assistant((query_text or "").strip(), _gemini_key, df)
                result_df = out.get("result")
                sql_like = out.get("sql_like", "")
                if result_df is not None and not result_df.empty:
                    st.success(f"Found {len(result_df)} row(s).")
                    if sql_like:
                        with st.expander("Query plan (SQL-like)"):
                            st.code(sql_like)
                    st.dataframe(result_df, use_container_width=True)
                else:
                    st.info("No rows returned.")
                    if sql_like:
                        with st.expander("Query plan (SQL-like)"):
                            st.code(sql_like)
            except Exception as e:
                st.error(f"Query failed: {e}")
