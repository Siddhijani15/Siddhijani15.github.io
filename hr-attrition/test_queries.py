"""Run all SQL query files against hr.db and print results."""
import sqlite3
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hr.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql_files = sorted(glob.glob(os.path.join(SQL_DIR, "*.sql")))
for sql_path in sql_files:
    name = os.path.basename(sql_path)
    print("=" * 70)
    print(f"Running: {name}")
    print("=" * 70)
    with open(sql_path, "r") as f:
        sql = f.read()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description] if cursor.description else []
        print(f"Columns: {col_names}")
        print(f"Rows: {len(rows)}")
        for i, row in enumerate(rows):
            if i < 20:
                print(f"  {dict(row) if isinstance(row, sqlite3.Row) else row}")
            elif i == 20:
                print(f"  ... and {len(rows) - 20} more rows")
    except Exception as e:
        print(f"ERROR: {e}")
    print()

conn.close()
