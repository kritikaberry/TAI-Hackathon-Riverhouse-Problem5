"""
Gemini-based query planner for policy-oriented questions on a DataFrame.
Call: policy_data_assistant(user_query, api_key, merged_df)
If api_key is empty/None, GEMINI_API_KEY below is used (hardcode your key there).
"""
import json
import re
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from google import genai

# Hardcode your Gemini API key here (or pass it when calling policy_data_assistant)
GEMINI_API_KEY = "ADD YOUR KEY HERE"


# =========================
# JSON-safe conversion
# =========================

def make_json_safe(obj: Any) -> Any:
    """
    Recursively convert pandas/numpy objects into JSON-serializable Python types.
    Fixes issues like: TypeError: Object of type Timestamp is not JSON serializable
    """
    if obj is None:
        return None

    # pandas NaT
    if obj is pd.NaT:
        return None

    # pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    # numpy scalar types
    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v

    if isinstance(obj, np.bool_):
        return bool(obj)

    # numpy arrays
    if isinstance(obj, np.ndarray):
        return [make_json_safe(x) for x in obj.tolist()]

    # dict/list/tuple
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [make_json_safe(x) for x in obj]

    # fall-through for str/int/float/bool, etc.
    return obj


# =========================
# Column matching helpers
# =========================

def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().strip())

def _best_col_match(df: pd.DataFrame, candidate_names: List[str]) -> Optional[str]:
    """
    Try to match a semantic column name (platform/region/date/etc.) to an actual df column.
    Uses normalization + contains matching.
    """
    cols = list(df.columns)
    norm_cols = {_normalize(c): c for c in cols}

    # direct normalized match
    for cand in candidate_names:
        nc = _normalize(cand)
        if nc in norm_cols:
            return norm_cols[nc]

    # contains match
    for cand in candidate_names:
        nc = _normalize(cand)
        for ncol, orig in norm_cols.items():
            if nc and (nc in ncol or ncol in nc):
                return orig

    return None


# =========================
# SAFE query plan executor
# =========================

def execute_query_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Executes a restricted JSON plan on df.
    Returns (result_df, generated_sql_like_string).

    Allowed plan keys:
      - filters: list of {col, op, value, case_insensitive}
      - select_cols: list[str] or []
      - sort: {col, ascending}
      - limit: int
      - groupby: {by: [cols], agg: [{col, fn, as}]}
    """
    working = df.copy()

    filters = plan.get("filters", []) or []
    where_clauses = []

    for f in filters:
        col = f.get("col")
        op = f.get("op")
        val = f.get("value")
        ci = bool(f.get("case_insensitive", True))

        if not col or col not in working.columns or not op:
            continue

        series = working[col]

        # String-ish operations
        if op in ("contains", "equals", "in"):
            s = series.astype(str)
            if ci:
                s_cmp = s.str.lower()
                if isinstance(val, list):
                    val_cmp = [str(x).lower() for x in val]
                else:
                    val_cmp = str(val).lower()
            else:
                s_cmp = s
                val_cmp = val

            if op == "contains":
                working = working[s_cmp.str.contains(str(val_cmp), na=False)]
                where_clauses.append(f"{col} ILIKE '%{val}%'")
            elif op == "equals":
                working = working[s_cmp == str(val_cmp)]
                where_clauses.append(f"{col} ILIKE '{val}'" if ci else f"{col} = '{val}'")
            elif op == "in":
                if not isinstance(val_cmp, list):
                    val_cmp = [val_cmp]
                working = working[s_cmp.isin(val_cmp)]
                where_clauses.append(f"{col} IN ({', '.join([repr(x) for x in (val or [])])})")

        # Numeric/date comparisons (best effort)
        elif op in ("gt", "gte", "lt", "lte"):
            s_num = pd.to_numeric(series, errors="coerce")
            v_num = pd.to_numeric(pd.Series([val]), errors="coerce").iloc[0]

            if pd.isna(v_num):
                # try datetime
                s_dt = pd.to_datetime(series, errors="coerce")
                v_dt = pd.to_datetime(val, errors="coerce")
                if pd.isna(v_dt):
                    continue

                if op == "gt":
                    working = working[s_dt > v_dt]
                    where_clauses.append(f"{col} > '{val}'")
                elif op == "gte":
                    working = working[s_dt >= v_dt]
                    where_clauses.append(f"{col} >= '{val}'")
                elif op == "lt":
                    working = working[s_dt < v_dt]
                    where_clauses.append(f"{col} < '{val}'")
                elif op == "lte":
                    working = working[s_dt <= v_dt]
                    where_clauses.append(f"{col} <= '{val}'")
            else:
                if op == "gt":
                    working = working[s_num > v_num]
                    where_clauses.append(f"{col} > {val}")
                elif op == "gte":
                    working = working[s_num >= v_num]
                    where_clauses.append(f"{col} >= {val}")
                elif op == "lt":
                    working = working[s_num < v_num]
                    where_clauses.append(f"{col} < {val}")
                elif op == "lte":
                    working = working[s_num <= v_num]
                    where_clauses.append(f"{col} <= {val}")

    # Groupby + Agg
    groupby = plan.get("groupby")
    sql_select_parts = []

    if isinstance(groupby, dict):
        by_cols = [c for c in (groupby.get("by") or []) if c in working.columns]
        aggs = groupby.get("agg") or []

        agg_map = {}
        for a in aggs:
            col = a.get("col")
            fn = a.get("fn")
            alias = a.get("as") or f"{fn}_{col}"

            if col in working.columns and fn in ("count", "nunique", "sum", "mean", "max", "min"):
                if fn == "count":
                    agg_map[alias] = (col, "count")
                else:
                    agg_map[alias] = (col, fn)

        if by_cols and agg_map:
            working = working.groupby(by_cols, dropna=False).agg(**agg_map).reset_index()

            sql_select_parts.extend(by_cols)
            for alias, (col, fn) in agg_map.items():
                if fn == "count":
                    sql_select_parts.append(f"COUNT({col}) AS {alias}")
                else:
                    sql_select_parts.append(f"{fn.upper()}({col}) AS {alias}")

    # select columns
    select_cols = plan.get("select_cols") or []
    if select_cols:
        select_cols = [c for c in select_cols if c in working.columns]
        if select_cols:
            working = working[select_cols]

    # sorting
    sort = plan.get("sort")
    order_clause = ""
    if isinstance(sort, dict):
        scol = sort.get("col")
        asc = bool(sort.get("ascending", False))
        if scol in working.columns:
            working = working.sort_values(by=scol, ascending=asc)
            order_clause = f"ORDER BY {scol} {'ASC' if asc else 'DESC'}"

    # limit
    limit = plan.get("limit", 10)
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    if limit > 0:
        working = working.head(limit)

    sql_select = ", ".join(sql_select_parts) if sql_select_parts else (
        ", ".join(select_cols) if select_cols else "*"
    )
    sql_where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    sql_limit = f"LIMIT {limit}" if limit else ""
    sql_like = f"SELECT {sql_select} FROM merged_df {sql_where} {order_clause} {sql_limit}".strip()

    return working, sql_like


# =========================
# Gemini planner
# =========================

def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()

    # pure JSON case
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # find first JSON object
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON found in Gemini output.")
    return json.loads(m.group(0))


def plan_query_with_gemini(
    user_query: str,
    api_key: str,
    df: pd.DataFrame,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    client = genai.Client(api_key=api_key)

    cols = df.columns.tolist()
    sample_rows = make_json_safe(df.head(5).to_dict(orient="records"))

    semantic_hints = {
        "platform": _best_col_match(df, ["platform", "system", "application", "product", "source", "site", "service"]),
        "region": _best_col_match(df, ["region", "country", "continent", "location", "jurisdiction", "market"]),
        "date": _best_col_match(df, ["date", "incident_date", "reported_date", "created_at", "timestamp", "year"]),
        "severity": _best_col_match(df, ["severity", "priority", "risk", "impact", "level"]),
        "category": _best_col_match(df, ["category", "type", "taxonomy", "incident_type", "topic"]),
        "status": _best_col_match(df, ["status", "active", "state", "resolved"]),
        "title": _best_col_match(df, ["title", "summary", "description", "incident"]),
    }

    system_instructions = """
You are a data query planner. You will receive:
- a pandas DataFrame named merged_df (columns provided)
- a user’s policy-oriented question

Your job: output a JSON query plan ONLY, matching this schema:

{
  "intent": "retrieve_examples" | "trend" | "breakdown" | "kpi",
  "filters": [
    {"col": "<exact df column>", "op": "contains|equals|in|gt|gte|lt|lte", "value": "<string|number|list>", "case_insensitive": true}
  ],
  "groupby": {
    "by": ["<col1>", "<col2>"],
    "agg": [{"col":"<col>", "fn":"count|nunique|sum|mean|max|min", "as":"<alias>"}]
  },
  "select_cols": ["<col>", "..."],
  "sort": {"col":"<col>", "ascending": false},
  "limit": 10,
  "notes": "<1 short sentence explaining what you’re returning>"
}

Rules:
- Use only columns that exist in the provided columns list.
- Prefer practical outputs for policy work: top incidents, breakdown by category, severity distribution, recent incidents.
- If the user mentions a platform (e.g., YouTube), filter using the best matching column (platform/title/description).
- If the user mentions region (e.g., North America), filter using the best matching location/jurisdiction column.
- If no exact region column exists, approximate by filtering country in ["United States", "Canada", "Mexico"] if a country column exists.
- Keep it simple: 1 query plan, limit 10 by default.
Output JSON only. No markdown.
""".strip()

    payload = make_json_safe({
        "columns": cols,
        "semantic_hints": semantic_hints,
        "sample_rows": sample_rows,
        "user_query": user_query,
    })

    resp = client.models.generate_content(
        model=model,
        contents=[system_instructions, json.dumps(payload)],
    )

    plan = _extract_json(resp.text)
    return plan


# =========================
# Main assistant function
# =========================

def policy_data_assistant(
    user_query: str,
    api_key: Optional[str],
    merged_df: pd.DataFrame,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """
    End-to-end:
      1) Gemini produces a JSON query plan
      2) We execute it safely on merged_df (no eval)
      3) Return plan + SQL-like string + result df
    """
    key = (api_key or "").strip() or GEMINI_API_KEY
    if not key:
        raise ValueError("Set GEMINI_API_KEY in query_handler.py or pass api_key")
    plan = plan_query_with_gemini(user_query, key, merged_df, model=model)
    result_df, sql_like = execute_query_plan(merged_df, plan)

    return {
        "query_plan": plan,
        "sql_like": sql_like,
        "result": result_df,
    }