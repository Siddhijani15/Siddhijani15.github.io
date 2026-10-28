-- Q7: Quarter-over-quarter change in exits
-- ================================
-- This query shows how the number of exits changes from one quarter
-- to the next. It uses the LAG() window function to access the previous
-- quarter's count, then computes the absolute change and percentage change.

-- Step 1: Count exits per quarter (same logic as Q6)
WITH quarterly_exits AS (
    SELECT
        strftime('%Y', ExitDate) || '-Q' ||
        ((CAST(strftime('%m', ExitDate) AS INTEGER) - 1) / 3 + 1)   AS quarter,
        COUNT(*)                                                          AS exits
    FROM attrition_fact
    WHERE AttritionFlag = 'Yes'
      AND ExitDate IS NOT NULL
    GROUP BY
        strftime('%Y', ExitDate),
        ((CAST(strftime('%m', ExitDate) AS INTEGER) - 1) / 3 + 1)
),

-- Step 2: Use LAG() to bring the previous quarter's exit count into each row
with_lag AS (
    SELECT
        quarter,
        exits,
        LAG(exits) OVER (ORDER BY quarter) AS prev_quarter_exits
    FROM quarterly_exits
)

-- Step 3: Compute the change and percentage change
SELECT
    quarter,
    prev_quarter_exits         AS prev_quarter_exits,
    exits                        AS current_quits,
    -- Absolute change: current minus previous
    (exits - prev_quarter_exits)  AS change,
    -- Percentage change: (change / previous) * 100, rounded to 2 decimals
    CASE
        WHEN prev_quarter_exits IS NOT NULL
        THEN ROUND(100.0 * (exits - prev_quarter_exits) / prev_quarter_exits, 2)
        ELSE NULL
    END                           AS pct_change
FROM with_lag
ORDER BY quarter;
