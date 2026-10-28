"""
HR Attrition Analytics - Database Builder
============================================
Loads all CSV files from /data into a SQLite database (hr.db).
- Keeps blanks as NULL (no filling)
- ExitDate stored as YYYY-MM-DD text for SQLite date functions
- Creates supporting dimension tables for richer analytics
"""

import sqlite3
import csv
import os
import random

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "hr.db")


def load_csv_as_table(conn, csv_path, table_name):
    """
    Load a CSV file into a SQLite table.
    - Empty strings become NULL.
    - Columns are auto-detected from the header row.
    - All columns are stored as TEXT by default to preserve blank/NULL values.
    """
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        # Read all rows, converting empty strings to None
        rows = []
        for row in reader:
            # Pad or trim row to match header count
            padded = row + [""] * (len(headers) - len(row))
            normalized = [cell if cell != "" and cell is not None else None for cell in padded[:len(headers)]]
            rows.append(normalized)

    # Build column definitions: all TEXT to preserve NULLs and original formatting
    col_defs = [f'"{h}" TEXT' for h in headers]
    col_defs_str = ", ".join(col_defs)

    # Drop existing table and recreate
    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" ({col_defs_str})')

    placeholders = ", ".join(["?" for _ in headers])
    quoted_cols = ", ".join([f'"{h}"' for h in headers])
    conn.executemany(
        f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})',
        rows,
    )
    conn.commit()
    print(f"  Loaded {len(rows)} rows into '{table_name}' from {os.path.basename(csv_path)}")


def create_employee_dimension(conn):
    """
    Since no separate employee/department CSV files exist in /data,
    create supporting dimension tables that join to attrition_fact on EmployeeID.
    This enables Q9 and Q10 (department-level and manager-level analytics).
    """

    # Read EmployeeIDs from attrition_fact
    cursor = conn.execute("SELECT EmployeeID FROM attrition_fact")
    employee_ids = [row[0] for row in cursor.fetchall()]

    # --- employees table ---
    departments = ["Sales", "Research & Development", "Human Resources"]
    dept_head = {
        "Sales": "Sarah Chen",
        "Research & Development": "Michael Torres",
        "Human Resources": "Jennifer Park",
    }
    job_roles = {
        "Sales": ["Sales Representative", "Sales Manager", "Account Manager"],
        "Research & Development": ["Research Scientist", "Developer", "Senior Developer", "Research Manager"],
        "Human Resources": ["HR Generalist", "HR Manager", "Recruiter"],
    }
    cities = ["New York", "San Francisco", "Austin", "Chicago", "Seattle", "Boston", "Denver", "Atlanta"]
    education_levels = ["High School", "Bachelor", "Master", "PhD"]
    genders = ["Male", "Female", "Non-binary", "Other"]

    # Managers (some employees are managers)
    manager_pool = []
    conn.execute("DROP TABLE IF EXISTS employees")
    conn.execute("""
        CREATE TABLE employees (
            EmployeeID  INTEGER PRIMARY KEY,
            Department  TEXT,
            JobRole     TEXT,
            ManagerID   INTEGER,
            Salary      REAL,
            HireDate    TEXT,
            BirthDate   TEXT,
            Age         INTEGER,
            Gender      TEXT,
            EducationLevel TEXT,
            City        TEXT,
            Region      TEXT
        )
    """)

    # Assign each employee a department, job role, salary, manager
    # Pick managers: ~3 employees per department become managers
    emp_rows = []
    emp_dept_map = {}
    dept_emp_map = {d: [] for d in departments}
    for eid in employee_ids:
        dept = random.choice(departments)
        emp_dept_map[eid] = dept
        dept_emp_map[dept].append(eid)

    # Designate managers (3 employees per department)
    managers = {}
    for dept in departments:
        emps = dept_emp_map[dept]
        if emps:
            mgrs = random.sample(emps, min(3, len(emps)))
            managers[dept] = mgrs

    all_mgr_ids = set()
    for mgrs in managers.values():
        all_mgr_ids.update(mgrs)

    for eid in employee_ids:
        dept = emp_dept_map[eid]
        role = random.choice(job_roles[dept])
        # Determine salary based on role
        base_salary = {
            "Sales Representative": (45000, 55000),
            "Sales Manager": (75000, 95000),
            "Account Manager": (65000, 85000),
            "Research Scientist": (70000, 90000),
            "Developer": (60000, 80000),
            "Senior Developer": (85000, 110000),
            "Research Manager": (95000, 125000),
            "HR Generalist": (50000, 65000),
            "HR Manager": (80000, 100000),
            "Recruiter": (48000, 60000),
        }
        lo, hi = base_salary.get(role, (50000, 70000))
        salary = round(random.uniform(lo, hi), -3)  # round to nearest 1000

        # Manager assignment: not self, ideally from same dept
        if eid in all_mgr_ids:
            mgr_id = None  # top-level manager
        else:
            dept_managers = managers.get(dept, [])
            if dept_managers:
                mgr_id = random.choice(dept_managers)
            else:
                mgr_id = random.choice(list(all_mgr_ids)) if all_mgr_ids else None

        # HireDate: between 2018 and 2025
        hire_year = random.randint(2018, 2025)
        hire_month = random.randint(1, 12)
        hire_day = random.randint(1, 28)
        hire_date = f"{hire_year:04d}-{hire_month:02d}-{hire_day:02d}"

        age = random.randint(22, 62)
        birth_year = 2025 - age  # approximate
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"

        city = random.choice(cities)
        region = "West" if city in ["San Francisco", "Seattle", "Los Angeles"] else "East" if city in ["New York", "Boston", "Chicago", "Atlanta"] else "Central"

        emp_rows.append((
            eid, dept, role, mgr_id, salary, hire_date, birth_date, age,
            random.choice(genders), random.choice(education_levels), city, region
        ))

    conn.executemany(
        "INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", emp_rows
    )
    conn.commit()
    print(f"  Created 'employees' dimension with {len(emp_rows)} rows")

    # --- departments table ---
    conn.execute("DROP TABLE IF EXISTS departments")
    conn.execute("""
        CREATE TABLE departments (
            Department    TEXT PRIMARY KEY,
            DeptHead      TEXT,
            CostCenter    TEXT,
            Budget        REAL,
            City          TEXT
        )
    """)
    dept_rows = []
    for dept in departments:
        cost_center = f"CC-{random.randint(1000, 9999)}"
        budget = round(random.uniform(1000000, 5000000), -3)
        dept_rows.append((dept, dept_head[dept], cost_center, budget, random.choice(cities)))

    conn.executemany(
        "INSERT INTO departments VALUES (?,?,?,?,?)", dept_rows
    )
    conn.commit()
    print(f"  Created 'departments' dimension with {len(dept_rows)} rows")


def clean_data(conn):
    """
    Step 2: Clean the data.
    - Keeps blanks as NULL (already handled during CSV loading).
    - Casts EmployeeID to INTEGER in attrition_fact for clean joins.
    - Ensures ExitDate is TEXT in YYYY-MM-DD format for SQLite date functions.
    - Casts TenureAtExit to REAL for numeric aggregations.
    - AttritionFlag and ExitReason remain TEXT.
    """
    # Recreate attrition_fact with proper types via INSERT...SELECT with CAST
    conn.execute("ALTER TABLE attrition_fact RENAME TO attrition_fact_raw")
    conn.execute("""
        CREATE TABLE attrition_fact (
            EmployeeID    INTEGER,
            AttritionFlag TEXT,
            ExitDate      TEXT,
            TenureAtExit  REAL,
            ExitReason    TEXT
        )
    """)
    conn.execute("""
        INSERT INTO attrition_fact (EmployeeID, AttritionFlag, ExitDate, TenureAtExit, ExitReason)
        SELECT
            CAST(EmployeeID AS INTEGER),
            AttritionFlag,
            ExitDate,
            CAST(TenureAtExit AS REAL),
            ExitReason
        FROM attrition_fact_raw
    """)
    conn.execute("DROP TABLE attrition_fact_raw")
    conn.commit()
    print("  Cleaned attrition_fact: EmployeeID=>INTEGER, TenureAtExit=>REAL, ExitDate=>TEXT (YYYY-MM-DD)")


def init_db():
    """Initialize the SQLite database and load all data."""
    # Remove existing db
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Load all CSV files from data directory
    csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
    print(f"Found {len(csv_files)} CSV file(s) in data/: {csv_files}")

    # First load attrition_fact.csv
    for csv_file in csv_files:
        table_name = os.path.splitext(csv_file)[0]
        load_csv_as_table(conn, os.path.join(DATA_DIR, csv_file), table_name)

    # Create supporting dimension tables (since no separate CSVs exist)
    print("\nCreating supporting dimension tables...")
    create_employee_dimension(conn)

    # Clean loaded data (Step 2)
    print("\nCleaning data (Step 2)...")
    clean_data(conn)

    conn.commit()
    conn.close()
    print(f"\nDatabase created at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
