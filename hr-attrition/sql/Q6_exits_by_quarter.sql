-- Q6: Exits by quarter with running total
-- ================================
-- This query counts how many employees exited in each calendar quarter
-- (e.g. 2023-Q3, 2024-Q1, etc.) and shows a running total across all quarters.
-- The running total uses a window function: SUM(...) OVER (ORDER BY ...).

-- strftime extracts the year and month from the ExitDate text.
-- We divide the month by 3 (integer division) to get the quarter number 1-4.
WITH quarterly_exits AS (
    SELECT
        -- Build a 'YYYY-QN' label from the date
        strftime('%Y', ExitDate) || '-Q' ||
        ((CAST(strftime('%m', ExitDate) AS INTEGER) - 1) / 3 + 1)   AS quarter,
        COUNT(*)                                                          AS exits
    FROM attrition_fact
    WHERE AttritionFlag = 'Yes'
      AND ExitDate IS NOT NULL

    -- Group by year and quarter
    GROUP BY
        strftime('%Y', ExitDate),
        ((CAST(strftime('%m', ExitDate) AS INTEGER) - 1) / 3 + 1)

    -- Order chronologically by year then quarter
    ORDER BY
        strftime('%Y', ExitDate),
        ((CAST(strftime('%m', ExitDate) AS INTEGER) - 1) / 3 + 1)
)

SELECT
    quarter,
    exits,
    -- Running total: adds up all exit counts from the first quarter to the current one
    SUM(exits) OVER (ORDER BY quarter)  AS running_total
FROM quarterly_exits;
