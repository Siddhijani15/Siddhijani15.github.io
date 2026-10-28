-- Q3: Voluntary vs involuntary exits
-- ================================
-- This query classifies each exit as either 'Voluntary' or 'Involuntary':
--   - Any ExitReason that starts with 'Involuntary' is classified as Involuntary.
--   - Everything else is Voluntary.
-- It shows the count and percentage for each group.
-- It also finds the top reason within each group.

-- Step 1: Classify each leaver using CASE/LIKE
WITH classified AS (
    SELECT
        CASE
            WHEN ExitReason LIKE 'Involuntary%' THEN 'Involuntary'
            ELSE 'Voluntary'
        END   AS exit_type,
        ExitReason
    FROM attrition_fact
    WHERE AttritionFlag = 'Yes'
      AND ExitReason IS NOT NULL
),

-- Step 2: Count exits per type and per reason
type_counts AS (
    SELECT
        exit_type,
        COUNT(*) AS type_count,
        ROUND(
            100.0 * COUNT(*) / (SELECT COUNT(*) FROM classified), 2
        ) AS pct_of_all_exits
    FROM classified
    GROUP BY exit_type
),

reason_counts AS (
    SELECT
        exit_type,
        ExitReason,
        COUNT(*) AS reason_count
    FROM classified
    GROUP BY exit_type, ExitReason
),

-- Step 3: Rank reasons within each type by count (descending)
ranked_reasons AS (
    SELECT
        exit_type,
        ExitReason,
        reason_count,
        ROW_NUMBER() OVER (PARTITION BY exit_type ORDER BY reason_count DESC) AS rn
    FROM reason_counts
)

-- Step 4: Combine the type-level summary with the top reason for each type
SELECT
    tc.exit_type,
    tc.type_count,
    tc.pct_of_all_exits,
    rr.ExitReason           AS top_reason,
    rr.reason_count         AS top_reason_count
FROM type_counts tc
LEFT JOIN (
    SELECT exit_type, ExitReason, reason_count
    FROM ranked_reasons
    WHERE rn = 1          -- keep only the #1 reason per type
) rr ON tc.exit_type = rr.exit_type
ORDER BY tc.type_count DESC;
