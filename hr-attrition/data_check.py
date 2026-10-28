import sqlite3, os

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "hr.db"))

dates = conn.execute("SELECT MIN(ExitDate), MAX(ExitDate) FROM attrition_fact WHERE ExitDate IS NOT NULL").fetchone()
print(f"ExitDate range: {dates[0]} to {dates[1]}")

years = conn.execute("SELECT strftime('%Y', ExitDate) as yr, COUNT(*) FROM attrition_fact WHERE ExitDate IS NOT NULL GROUP BY yr ORDER BY yr").fetchall()
print(f"Exits by year: {years}")

flags = conn.execute("SELECT AttritionFlag, COUNT(*) FROM attrition_fact GROUP BY AttritionFlag").fetchall()
print(f"AttritionFlag counts: {flags}")

join_cast = conn.execute("SELECT COUNT(*) FROM attrition_fact f INNER JOIN employees e ON CAST(f.EmployeeID AS INTEGER) = e.EmployeeID").fetchone()
print(f"Join test (CAST): {join_cast[0]} rows")

join_using = conn.execute("SELECT COUNT(*) FROM attrition_fact f INNER JOIN employees e USING (EmployeeID)").fetchone()
print(f"Join test (USING): {join_using[0]} rows")

reasons = conn.execute("SELECT ExitReason, COUNT(*) as cnt FROM attrition_fact WHERE ExitReason IS NOT NULL GROUP BY ExitReason ORDER BY cnt DESC").fetchall()
print(f"Exit reasons ({len(reasons)}):")
for r in reasons:
    print(f"  {r[0]}: {r[1]}")

conn.close()
