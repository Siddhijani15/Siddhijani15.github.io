AGENTS.md
=========

Project: HR Attrition Analytics
Stack: Python, SQLite, Streamlit

## Setup
    pip install -r requirements.txt

## Commands

### Build database (from scratch)
    python build_db.py
    Loads data/attrition_fact.csv into hr.db, creates employee/department
    dimension tables, and cleans data (NULLs, type casting).

### Run Streamlit dashboard
    streamlit run app.py

### Generate standalone HTML dashboard
    python generate_dashboard.py
    Creates dashboard.html with charts and tables.

### Inspect data (Step 1 summary)
    python step1_inspect.py

### Test all SQL queries
    python test_queries.py

## Linting / Typecheck
    # Python syntax check
    python -m py_compile build_db.py app.py generate_dashboard.py

## Project layout
    data/         - CSV source files
    sql/          - One .sql file per question (Q1-Q10)
    hr.db         - SQLite database (generated)
    app.py        - Streamlit dashboard
    generate_dashboard.py  - builds dashboard.html
    dashboard.html  - standalone HTML dashboard
