-- Q8: Top exit reason per year
-- ================================
-- This query finds the single most common exit reason for each year.
-- It uses a CTE and the RANK() window function:
--   RANK() OVER (PARTITION BY year ORDER BY count DESC) gives rank 1
--   to the reason with the most exits in that year.
-- Years 2023 and 2026 are flagged as partial years because the data
-- starts in September 2023 and ends in September 2026.

-- Step 1: Count exits per (year, reason)
WITH reason_by_year AS (
    SELECT
        strftime('%Y', ExitDate)   AS exit_year,
        ExitReason                 AS exit_reason,
        COUNT(*)                   AS exit_count
    FROM attrition_fact
    WHERE AttritionFlag = 'Yes'
      AND ExitDate IS NOT NULL
      AND ExitReason IS NOT NULL
    GROUP BY
        strftime('%Y', ExitDate),
        ExitReason
),

-- Step 2: Rank each reason within its year by exit_count (descending)
ranked AS (
    SELECT
        exit_year,
        exit_reason,
        exit_count,
        RANK() OVER (PARTITION BY exit_year ORDER BY exit_count DESC) AS rnk
    FROM reason_by_year
)

-- Step 3: Keep only the top-ranked reason (rank = 1) for each year
SELECT
    exit_year,
    exit_count,
    exit_reason     AS top_reason,
    -- Flag partial years: 2023 data starts Sep, 2026 data ends Sep
    CASE
        WHEN exit_year IN ('2023', '2026')
        THEN 'PARTIAL YEAR'
        ELSE ''
    END AS year_note
FROM ranked
WHERE rnk = 1
ORDER BY exit_year;
