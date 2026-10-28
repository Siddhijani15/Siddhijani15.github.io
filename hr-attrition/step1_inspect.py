"""
Step 1: Data Inspection
=======================
Lists every table, columns, data types, row count, 5 sample rows.
Checks which tables join to attrition_fact on EmployeeID without duplicates.
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hr.db")


def inspect_database():
    conn = sqlite3.connect(DB_PATH)

    # --- List all tables ---
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t[0] for t in tables]

    print("=" * 80)
    print("DATABASE SUMMARY: hr.db")
    print("=" * 80)
    print(f"Tables found: {table_names}")
    print()

    for tname in table_names:
        # Columns and types
        schema = conn.execute(f"PRAGMA table_info('{tname}')").fetchall()
        col_info = [(row[1], row[2]) for row in schema]  # (name, type)

        # Row count
        row_count = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]

        # 5 sample rows
        samples = conn.execute(f'SELECT * FROM "{tname}" LIMIT 5').fetchall()

        print(f"--- Table: {tname} ---")
        print(f"  Columns & Types:")
        for col_name, col_type in col_info:
            print(f"    {col_name}: {col_type}")
        print(f"  Row count: {row_count}")
        print(f"  Sample rows (first 5):")
        for i, row in enumerate(samples, 1):
            print(f"    [{i}] {row}")
        print()

    # --- Join analysis on EmployeeID ---
    print("=" * 80)
    print("JOIN ANALYSIS: Tables joining to attrition_fact on EmployeeID")
    print("=" * 80)

    fact_col_count = conn.execute(
        "SELECT COUNT(*) FROM attrition_fact"
    ).fetchone()[0]

    for tname in table_names:
        if tname == "attrition_fact":
            continue
        # Check if EmployeeID exists
        cols = conn.execute(f'PRAGMA table_info("{tname}")').fetchall()
        col_names = [c[1] for c in cols]
        if "EmployeeID" in col_names:
            # Check the join does not create duplicate rows
            joined_count = conn.execute(
                f'SELECT COUNT(*) FROM "attrition_fact" '
                f'INNER JOIN "{tname}" USING (EmployeeID)'
            ).fetchone()[0]

            # Check max multiplicity (each fact row should match exactly one dim row)
            max_dup = conn.execute(
                f'SELECT MAX(cnt) FROM ('
                f'  SELECT EmployeeID AS emp_id, COUNT(*) AS cnt '
                f'  FROM "{tname}" GROUP BY EmployeeID'
                f')'
            ).fetchone()[0]

            has_dup = "YES (duplicates!)" if max_dup > 1 else "NO (1:1 join, safe)"
            print(f"\n  Table: {tname}")
            print(f"    Fact rows: {fact_col_count}")
            print(f"    Joined rows: {joined_count}")
            print(f"    Max multiplicity per EmployeeID in {tname}: {max_dup}")
            print(f"    Duplicate rows created: {has_dup}")
        else:
            print(f"\n  Table: {tname}")
            print(f"    EmployeeID column: NOT present — cannot join on EmployeeID")

    conn.close()


if __name__ == "__main__":
    inspect_database()
