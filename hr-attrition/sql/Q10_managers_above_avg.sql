-- Q10: Managers with above-average team attrition rate
-- ================================
-- This query compares each manager's team attrition rate to the company
-- overall average. Managers whose team attrition exceeds the overall average
-- are flagged so HR can investigate.
--
-- It uses CTEs to:
--   1. Calculate each manager's team size and leaver count
--      (by joining employees to themselves on ManagerID).
--   2. Calculate the company-wide average attrition rate.
--   3. Filter for managers whose team rate is above the company average.

-- Step 1: Per-manager team stats
-- m = the manager row, e = a direct report whose ManagerID matches m.EmployeeID.
WITH manager_stats AS (
    SELECT
        m.EmployeeID          AS manager_id,
        m.Department          AS manager_department,
        COUNT(e.EmployeeID)   AS team_size,
        SUM(CASE WHEN f.AttritionFlag = 'Yes' THEN 1 ELSE 0 END) AS team_leavers
    FROM employees m
    JOIN employees e  ON e.ManagerID = m.EmployeeID
    JOIN attrition_fact f ON f.EmployeeID = e.EmployeeID
    GROUP BY m.EmployeeID, m.Department
    HAVING COUNT(e.EmployeeID) >= 1    -- only managers who actually have reports
),

-- Step 2: Company-wide average attrition rate (% of all employees who left)
company_avg AS (
    SELECT
        ROUND(
            100.0 * SUM(CASE WHEN AttritionFlag = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) AS overall_rate_pct
    FROM attrition_fact
)

-- Step 3: Compute each manager's team attrition rate and flag those above average
SELECT
    ms.manager_id,
    ms.manager_department                           AS department,
    ms.team_size,
    ms.team_leavers,
    ROUND(100.0 * ms.team_leavers / ms.team_size, 2) AS team_attrition_pct,
    ca.overall_rate_pct                              AS company_avg_pct,
    ROUND(
        100.0 * ms.team_leavers / ms.team_size - ca.overall_rate_pct, 2
    )                                                AS difference_pct,
    CASE
        WHEN (100.0 * ms.team_leavers / ms.team_size) > ca.overall_rate_pct
        THEN '*** ABOVE AVERAGE ***'
        ELSE ''
    END                                              AS flag
FROM manager_stats ms
CROSS JOIN company_avg ca
WHERE (100.0 * ms.team_leavers / ms.team_size) > ca.overall_rate_pct
ORDER BY difference_pct DESC;
