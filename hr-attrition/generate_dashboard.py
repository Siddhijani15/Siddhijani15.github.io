"""
Generate a standalone HTML dashboard from SQL query results.

Reads all Q1-Q10 SQL files, executes them against hr.db, and renders
an HTML page with tables and Chart.js visualizations.

Usage:
    python generate_dashboard.py

Output:
    dashboard.html  (self-contained, open in any browser)
"""

import sqlite3
import os
import html
import json
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hr.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")
OUTPUT_PATH = os.path.join(BASE_DIR, "dashboard.html")

# Descriptive metadata for each question (shown in the HTML)
QUESTION_INFO = {
    "Q1": {
        "title": "Overall Attrition Rate",
        "description": "Total employees, leavers, and attrition rate as a percentage. Also shows the rate per department.",
    },
    "Q2": {
        "title": "Top Exit Reasons",
        "description": "Exit reasons ranked by count and percentage share of all exits.",
    },
    "Q3": {
        "title": "Voluntary vs Involuntary Exits",
        "description": "Exits classified by type with the top reason in each group.",
    },
    "Q4": {
        "title": "Tenure Bands",
        "description": "Leavers grouped by tenure at exit, with first-year leavers highlighted.",
    },
    "Q5": {
        "title": "Tenure by Exit Reason",
        "description": "Average, minimum, and maximum tenure for each exit reason (5+ exits only).",
    },
    "Q6": {
        "title": "Exits by Quarter (Running Total)",
        "description": "Quarterly exit counts with a cumulative running total.",
    },
    "Q7": {
        "title": "Quarter-over-Quarter Change",
        "description": "Period-to-period change in exits using LAG().",
    },
    "Q8": {
        "title": "Top Exit Reason Per Year",
        "description": "Most common exit reason for each year (2023 and 2026 flagged as partial).",
    },
    "Q9": {
        "title": "Attrition by Department",
        "description": "Attrition rate broken down by department using a JOIN.",
    },
    "Q10": {
        "title": "Managers Above Average",
        "description": "Managers whose team attrition rate exceeds the company average.",
    },
}


def run_sql(filename):
    """Execute a SQL file against hr.db and return (columns, rows)."""
    path = os.path.join(SQL_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(sql)
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return columns, rows


def build_chart_config(chart_id, title, labels, datasets):
    """Build a Chart.js v4 config object as a JSON string."""
    config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {"display": len(datasets) > 1},
                "title": {"display": True, "text": title},
            },
            "scales": {
                "x": {"stacked": False},
                "y": {"stacked": False, "beginAtZero": True},
            },
        },
    }
    return json.dumps(config)


def generate_table_html(columns, rows, highlight_col=None, highlight_func=None):
    """Generate an HTML table from query results."""
    lines = ['<table class="data-table">']
    lines.append("<thead><tr>")
    for col in columns:
        lines.append(f"<th>{html.escape(col)}</th>")
    lines.append("</tr></thead>")
    lines.append("<tbody>")
    for row in rows:
        tr_class = ""
        if highlight_col is not None and highlight_func:
            idx = columns.index(highlight_col)
            val = row[idx]
            css_class = highlight_func(val)
            if css_class:
                tr_class = f' class="{css_class}"'
        lines.append(f"<tr{tr_class}>")
        for val in row:
            if val is None:
                display = ""
            elif isinstance(val, float):
                # Format floats nicely
                if val == int(val):
                    display = str(int(val))
                else:
                    display = f"{val:.2f}"
            else:
                display = str(val)
            lines.append(f"<td>{html.escape(display)}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def generate_dashboard():
    sections = []

    # --- Header ---
    sections.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Attrition Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa;
            color: #2c3e50;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 24px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 8px; }
        .header p { opacity: 0.85; }
        .section {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .section h2 {
            color: #2c3e50;
            font-size: 1.3em;
            margin-bottom: 4px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }
        .section .desc { color: #7f8c8d; font-size: 0.9em; margin-bottom: 16px; }
        .chart-row {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: flex-start;
        }
        .chart-container {
            flex: 1;
            min-width: 300px;
            background: #fafbfc;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #e1e4e8;
        }
        .chart-container canvas { max-height: 320px; }
        .table-container {
            overflow-x: auto;
            margin-top: 12px;
            min-width: 100%;
        }
        table.data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }
        table.data-table th {
            background: #34495e;
            color: white;
            padding: 8px 12px;
            text-align: left;
            border: 1px solid #2c3e50;
            position: sticky;
            top: 0;
        }
        table.data-table td {
            padding: 8px 12px;
            border: 1px solid #e1e4e8;
        }
        table.data-table tr:nth-child(even) { background: #f8f9fa; }
        table.data-table tr.risk-row { background: #fff3cd; }
        table.data-table tr.above-avg { background: #fff3cd; }
        .summary-cards {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .summary-card {
            background: #fff;
            border-radius: 8px;
            padding: 16px 24px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            flex: 1;
            min-width: 140px;
        }
        .summary-card .value { font-size: 1.8em; font-weight: 700; color: #2c3e50; }
        .summary-card .label { font-size: 0.8em; color: #7f8c8d; text-transform: uppercase; }
        .summary-card.green .value { color: #27ae60; }
        .tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
        }
        .tag-partial { background: #fff3cd; color: #856404; }
        .tag-full { background: #d4edda; color: #155724; }
        .footer {
            text-align: center;
            color: #95a5a6;
            font-size: 0.85em;
            padding: 16px;
        }
    </style>
</head>
<body>
<div class="header">
    <h1>HR Attrition Analytics</h1>
    <p>Q1 2023 - Q3 2026 | 1,000 Employees | 210 Attritions (21.0%)</p>
</div>
""")

    # --- Q1: Attrition Rate ---
    cols, rows = run_sql("Q1_attrition_rate.sql")
    overall = [r for r in rows if r[0] == "OVERALL"][0]
    dept_rows = [r for r in rows if r[0] == "DEPARTMENT"]

    sections.append("""
<div class="section">
    <h2>Q1: Overall Attrition Rate</h2>
    <div class="desc">Total employees, leavers, and attrition rate as a percentage. Also shows the rate per department.</div>
""")

    # Summary cards
    sections.append(f"""
    <div class="summary-cards">
        <div class="summary-card">
            <div class="value">{overall[2]}</div>
            <div class="label">Total Employees</div>
        </div>
        <div class="summary-card">
            <div class="value">{overall[3]}</div>
            <div class="label">Leavers</div>
        </div>
        <div class="summary-card green">
            <div class="value">{overall[4]}%</div>
            <div class="label">Attrition Rate</div>
        </div>
    </div>
""")

    # Table
    sections.append(f'<div class="table-container">{generate_table_html(cols, rows)}</div>')

    # Chart: department attrition rate
    dept_labels = [r[1] for r in dept_rows]
    dept_values = [r[4] for r in dept_rows]
    chart_config = build_chart_config(
        "chart-q1-dept",
        "Attrition Rate by Department",
        dept_labels,
        [{"label": "Attrition Rate (%)", "data": dept_values, "backgroundColor": "#e74c3c"}],
    )
    sections.append(f"""
    <div class="chart-container">
        <canvas id="chart-q1-dept"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q1-dept'), {chart_config});
</script>
""")

    # --- Q2: Exit Reasons ---
    cols, rows = run_sql("Q2_exit_reasons.sql")
    sections.append(f"""
<div class="section">
    <h2>Q2: Top Exit Reasons</h2>
    <div class="desc">Exit reasons ranked by count and percentage share of all exits.</div>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="chart-q2"></canvas>
        </div>
        <div class="table-container">{generate_table_html(cols, rows)}</div>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q2'), {build_chart_config(
        "chart-q2", "Exit Reasons (Count)",
        [r[0] for r in rows],
        [{"label": "Count", "data": [r[1] for r in rows], "backgroundColor": "#3498db"}]
    )});
</script>
""")

    # --- Q3: Voluntary vs Involuntary ---
    cols, rows = run_sql("Q3_voluntary_vs_involuntary.sql")
    sections.append(f"""
<div class="section">
    <h2>Q3: Voluntary vs Involuntary Exits</h2>
    <div class="desc">Exits classified by type with the top reason in each group.</div>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="chart-q3"></canvas>
        </div>
        <div class="table-container">{generate_table_html(cols, rows)}</div>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q3'), {build_chart_config(
        "chart-q3", "Voluntary vs Involuntary",
        [r[0] for r in rows],
        [{"label": "Count", "data": [r[1] for r in rows], "backgroundColor": ["#27ae60", "#e74c3c"]}]
    )});
</script>
""")

    # --- Q4: Tenure Bands ---
    cols, rows = run_sql("Q4_tenure_bands.sql")
    sections.append(f"""
<div class="section">
    <h2>Q4: Tenure Bands</h2>
    <div class="desc">Leavers grouped by tenure at exit, with first-year leavers highlighted as high risk.</div>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="chart-q4"></canvas>
        </div>
        <div class="table-container">
            {generate_table_html(cols, rows, highlight_col="highlight", highlight_func=lambda v: "risk-row" if v and "HIGH RISK" in v else None)}
        </div>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q4'), {build_chart_config(
        "chart-q4", "Leavers by Tenure Band",
        [r[0] for r in rows],
        [{"label": "Count", "data": [r[1] for r in rows], "backgroundColor": ["#e74c3c", "#f39c12", "#f1c40f", "#27ae60"]}]
    )});
</script>
""")

    # --- Q5: Tenure by Reason ---
    cols, rows = run_sql("Q5_tenure_by_reason.sql")
    sections.append(f"""
<div class="section">
    <h2>Q5: Tenure by Exit Reason</h2>
    <div class="desc">Average, minimum, and maximum tenure for each exit reason (reasons with at least 5 exits).</div>
    <div class="table-container">{generate_table_html(cols, rows)}</div>
""")
    chart_config = build_chart_config(
        "chart-q5", "Average Tenure by Exit Reason (years)",
        [r[0] for r in rows],
        [{"label": "Avg Tenure", "data": [r[2] for r in rows], "backgroundColor": "#8e44ad"}],
    )
    sections.append(f"""
    <div class="chart-container" style="margin-top: 16px;">
        <canvas id="chart-q5"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q5'), {chart_config});
</script>
""")

    # --- Q6: Exits by Quarter ---
    cols, rows = run_sql("Q6_exits_by_quarter.sql")
    sections.append(f"""
<div class="section">
    <h2>Q6: Exits by Quarter (Running Total)</h2>
    <div class="desc">Quarterly exit counts with a cumulative running total.</div>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="chart-q6"></canvas>
        </div>
        <div class="table-container">{generate_table_html(cols, rows)}</div>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q6'), {build_chart_config(
        "chart-q6", "Exits by Quarter",
        [r[0] for r in rows],
        [
            {"label": "Exits", "data": [r[1] for r in rows], "backgroundColor": "#3498db"},
            {"label": "Running Total", "data": [r[2] for r in rows], "backgroundColor": "#9b59b6"}
        ]
    )});
</script>
""")

    # --- Q7: Quarter-over-Quarter ---
    cols, rows = run_sql("Q7_quarter_change.sql")
    sections.append(f"""
<div class="section">
    <h2>Q7: Quarter-over-Quarter Change</h2>
    <div class="desc">How exit counts change from quarter to quarter using LAG().</div>
    <div class="table-container">{generate_table_html(cols, rows)}</div>
""")
    chart_config = build_chart_config(
        "chart-q7", "QoQ % Change in Exits",
        [r[0] for r in rows],
        [{"label": "% Change", "data": [r[4] if r[4] is not None else 0 for r in rows], "backgroundColor": "#17a2b8"}],
    )
    sections.append(f"""
    <div class="chart-container" style="margin-top: 16px;">
        <canvas id="chart-q7"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q7'), {chart_config});
</script>
""")

    # --- Q8: Top Reason Per Year ---
    cols, rows = run_sql("Q8_top_reason_per_year.sql")
    sections.append(f"""
<div class="section">
    <h2>Q8: Top Exit Reason Per Year</h2>
    <div class="desc">Most common exit reason for each year. 2023 and 2026 are flagged as partial years.</div>
    <div class="table-container">
        {generate_table_html(cols, rows, highlight_col="year_note", highlight_func=lambda v: "risk-row" if v and "PARTIAL" in v else None)}
    </div>
""")
    chart_config = build_chart_config(
        "chart-q8", "Top Exit Reason Count by Year",
        [f'{r[0]} ({r[2]})' for r in rows],
        [{"label": "Exit Count", "data": [r[1] for r in rows], "backgroundColor": "#2ecc71"}],
    )
    sections.append(f"""
    <div class="chart-container" style="margin-top: 16px;">
        <canvas id="chart-q8"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q8'), {chart_config});
</script>
""")

    # --- Q9: Attrition by Department ---
    cols, rows = run_sql("Q9_attrition_by_department.sql")
    sections.append(f"""
<div class="section">
    <h2>Q9: Attrition by Department</h2>
    <div class="desc">Attrition rate broken down by department using a JOIN to the employees table.</div>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="chart-q9"></canvas>
        </div>
        <div class="table-container">{generate_table_html(cols, rows)}</div>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q9'), {build_chart_config(
        "chart-q9", "Attrition Rate by Department",
        [r[0] for r in rows],
        [{"label": "Rate (%)", "data": [r[3] for r in rows], "backgroundColor": "#e67e22"}]
    )});
</script>
""")

    # --- Q10: Managers Above Average ---
    cols, rows = run_sql("Q10_managers_above_avg.sql")
    sections.append(f"""
<div class="section">
    <h2>Q10: Managers Above Average</h2>
    <div class="desc">Managers whose team attrition rate exceeds the company average (21.0%).</div>
    <div class="table-container">
        {generate_table_html(cols, rows, highlight_col="flag", highlight_func=lambda v: "above-avg" if v and "ABOVE" in v else None)}
    </div>
""")
    chart_config = build_chart_config(
        "chart-q10", "Team Attrition vs Company Average",
        [f'Mgr {r[0]} ({r[1]})' for r in rows],
        [
            {"label": "Team Rate (%)", "data": [r[4] for r in rows], "backgroundColor": "#e74c3c"},
            {"label": "Company Avg", "data": [r[5] for r in rows], "backgroundColor": "#3498db"},
        ],
    )
    sections.append(f"""
    <div class="chart-container" style="margin-top: 16px;">
        <canvas id="chart-q10"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart-q10'), {chart_config});
</script>
""")

    # --- Footer ---
    sections.append("""
<div class="footer">
    <p>HR Attrition Analytics &mdash; Generated by <code>generate_dashboard.py</code></p>
    <p>Data source: <code>data/attrition_fact.csv</code> | Database: <code>hr.db</code> | Queries in <code>sql/</code></p>
</div>
</body>
</html>
""")

    # Write the final HTML
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))

    print(f"Dashboard generated at: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_dashboard()
