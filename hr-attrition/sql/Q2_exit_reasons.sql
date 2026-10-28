-- Q2: Top exit reasons
-- ================================
-- This query lists every exit reason, how many employees left for each reason,
-- and what percentage of all leavers that represents.
-- Results are sorted so the most common reason appears first.

-- The denominator is a subquery that counts all leavers (rows where AttritionFlag = 'Yes'
-- and ExitReason is not NULL). This gives us the total pool of exits to calculate percentages.
SELECT
    ExitReason                                                           AS exit_reason,
    COUNT(*)                                                              AS exit_count,
    ROUND(
        100.0 * COUNT(*)
        / (SELECT COUNT(*) FROM attrition_fact
           WHERE AttritionFlag = 'Yes' AND ExitReason IS NOT NULL), 2
    )                                                                     AS pct_of_all_exits
FROM attrition_fact
WHERE ExitReason IS NOT NULL
  AND AttritionFlag = 'Yes'

-- GROUP BY ExitReason so each reason gets its own row
GROUP BY ExitReason

-- ORDER BY count descending so the biggest reasons are at the top
ORDER BY exit_count DESC;
