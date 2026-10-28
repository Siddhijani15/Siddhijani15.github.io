-- Q9: Attrition rate by department
-- ================================
-- This query calculates the overall attrition rate for each department.
-- It JOINs attrition_fact to the employees table on EmployeeID,
-- then GROUPs BY department to count total employees and leavers
-- and compute the rate as a percentage.

-- The LEFT JOIN ensures we keep all employees even if some are missing
-- from the employees dimension (though in this dataset all match).
SELECT
    COALESCE(e.Department, 'Unknown')         AS department,
    COUNT(*)                                   AS total_employees,
    SUM(CASE WHEN f.AttritionFlag = 'Yes' THEN 1 ELSE 0 END) AS leavers,
    ROUND(
        100.0 * SUM(CASE WHEN f.AttritionFlag = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                          AS attrition_rate_pct
FROM attrition_fact f
JOIN employees e ON f.EmployeeID = e.EmployeeID
GROUP BY COALESCE(e.Department, 'Unknown')
ORDER BY attrition_rate_pct DESC;
