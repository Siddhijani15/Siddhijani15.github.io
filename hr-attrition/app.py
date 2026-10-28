"""
HR Attrition Analytics
======================
A Streamlit dashboard that answers 10 business questions about employee
attrition using SQL queries against a SQLite database (hr.db).

Run with:  streamlit run app.py
"""

import sqlite3
import os
import glob
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hr.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- Page config ---
st.set_page_config(
    page_title="HR Attrition Analytics",
    page_icon="📊",
    layout="wide",
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_sql_questions():
    """Return a list of (question_id, label, filename) for all SQL files in /sql."""
    files = sorted(glob.glob(os.path.join(SQL_DIR, "Q*.sql")))
    questions = []
    for f in files:
        fname = os.path.basename(f)
        # Extract question title from filename, e.g. "Q1_attrition_rate.sql" -> "Q1: Attrition Rate"
        stem = os.path.splitext(fname)[0]
        parts = stem.split("_", 1)
        qid = parts[0].upper()  # e.g. "Q1"
        title = parts[1].replace("_", " ").title() if len(parts) > 1 else stem
        questions.append((qid, title, fname))
    return questions


def read_sql_file(filename):
    path = os.path.join(SQL_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def run_query(sql_text):
    conn = get_db()
    try:
        df = pd.read_sql_query(sql_text, conn)
    finally:
        conn.close()
    return df


# --- Sidebar ---
st.sidebar.title("HR Attrition Analytics")
st.sidebar.markdown("---")

questions = list_sql_questions()
question_labels = {qid: title for qid, title, _ in questions}
selected_qid = st.sidebar.radio(
    "Select a question to run:",
    options=[q[0] for q in questions],
    format_func=lambda x: f"{x}: {question_labels.get(x, x)}",
)

st.sidebar.markdown("---")

# Database info
st.sidebar.subheader("Database Info")
conn = get_db()
tables_info = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
for t in tables_info:
    tname = t[0]
    cnt = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
    st.sidebar.caption(f"{tname}: {cnt} rows")
conn.close()

# --- Main content ---
idx = [q[0] for q in questions].index(selected_qid)
qid, title, filename = questions[idx]

st.header(f"{qid}: {title}")

# Show the SQL in an expander
sql_text = read_sql_file(filename)
with st.expander("View SQL query", expanded=False):
    st.code(sql_text, language="sql")

# Run query and show results
with st.spinner("Running query..."):
    df = run_query(sql_text)

if df.empty:
    st.warning("No results returned.")
else:
    # Format and display
    st.dataframe(df, width="stretch")

    # Charts — pick up to 2 numeric columns for visualisation
    num_cols = [c for c in df.columns if df[c].dtype in ("float64", "int64", "bool")]
    cat_cols = [c for c in df.columns if c not in num_cols and df[c].dtype == "object"]

    if num_cols:
        label_col = cat_cols[0] if cat_cols else None
        # Build a list of (metric, kind) to visualise
        chart_specs = []
        for col in num_cols[:2]:
            lower = col.lower()
            if any(k in lower for k in ["pct", "rate"]):
                chart_specs.append((col, "bar_pct"))
            elif any(k in lower for k in ["count", "leaver", "exits", "size", "total"]):
                chart_specs.append((col, "bar"))
            else:
                chart_specs.append((col, "bar"))

        for col, kind in chart_specs:
            if label_col and label_col in df.columns:
                chart_df = df[[label_col, col]].dropna(subset=[label_col]).copy()
                if chart_df.empty:
                    continue
                # Ensure label is a string to avoid index issues
                chart_df[label_col] = chart_df[label_col].astype(str)
                # Drop duplicate labels (keep first)
                chart_df = chart_df.drop_duplicates(subset=[label_col], keep="first")
                st.markdown(f"### Chart: {col} by {label_col}")
                st.bar_chart(chart_df.set_index(label_col)[col])
            elif label_col is None:
                # Single-series bar chart using row numbers as labels
                st.markdown(f"### Chart: {col}")
                st.bar_chart(df[col])

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.info(
    "Data sources: `data/attrition_fact.csv` + supporting dimension "
    "tables (employees, departments). "
    "Database: `hr.db` (SQLite)."
)
