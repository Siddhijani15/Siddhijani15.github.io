-- Q1: Overall attrition rate
-- ================================
-- This query calculates the overall attrition rate:
--   - Total employees in the company
--   - Number of leavers (employees who left)
--   - Attrition rate as a percentage
-- It uses COUNT and CASE expressions to count leavers.
-- Since we have a Department column in the joined 'employees' table,
-- it also shows the attrition rate broken down per department.

-- Part A: Overall summary row
-- COUNT(*) counts every employee. CASE converts 'Yes' to 1, everything else to 0,
-- so SUM gives us the total number of leavers.
-- 'department' is NULL for the overall row.

SELECT
    'OVERALL'  AS scope,
    NULL       AS department,
    COUNT(*)   AS total_employees,
    SUM(CASE WHEN AttritionFlag = 'Yes' THEN 1 ELSE 0 END) AS leavers,
    ROUND(
        100.0 * SUM(CASE WHEN AttritionFlag = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS attrition_rate_pct
FROM attrition_fact

UNION ALL

-- Part B: Attrition rate per department
-- JOIN attrition_fact to employees on EmployeeID to get each person's department.
-- GROUP BY department so each department gets its own row.
SELECT
    'DEPARTMENT'  AS scope,
    COALESCE(e.Department, 'Unknown') AS department,
    COUNT(*)      AS total_employees,
    SUM(CASE WHEN f.AttritionFlag = 'Yes' THEN 1 ELSE 0 END) AS leavers,
    ROUND(
        100.0 * SUM(CASE WHEN f.AttritionFlag = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS attrition_rate_pct
FROM attrition_fact f
JOIN employees e ON f.EmployeeID = e.EmployeeID
GROUP BY COALESCE(e.Department, 'Unknown')

-- Sort: overall first (DESC puts 'OVERALL' above 'DEPARTMENT'),
-- then departments by highest attrition rate
ORDER BY scope DESC, attrition_rate_pct DESC;
